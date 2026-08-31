# SPDX-FileCopyrightText: 2026 Chris J Daly (github user cjdaly)
#
# SPDX-License-Identifier: MIT

# Runtime metrics for the on-device diagnostic screen (bead cd-89o.6). Pure:
# only gc / os / sys / time — no displayio, no board. The engine loop feeds
# it; DiagMode's SYSTEM page reads the fields.
#
# RAM: `gc.mem_free()` on its own under-reports — garbage that hasn't been
# collected yet still counts as allocated. A truthful reading needs
# `gc.collect()` first, and collect costs a few ms on RP2040, so the engine
# calls `maybe_sample_ram()` every tick but it only actually collects on a
# ~0.5 Hz timer. `free_low` is the low-water mark: the number that tells you
# how close to the edge you actually came, not just where you happen to be
# when the diag page is open.

import gc
import os
import sys
import time

RAM_INTERVAL = 2.0        # seconds between gc.collect() + RAM samples


def _now_ns():
    try:
        return time.monotonic_ns()
    except AttributeError:                       # CPython < 3.3 / odd builds
        return int(time.monotonic() * 1_000_000_000)


def _gc_reader(name):
    """gc.mem_free / gc.mem_alloc exist on CircuitPython/MicroPython only.
    Off-device (CPython test host) there is no equivalent, so those fields
    read as None and DiagMode shows '-'."""
    fn = getattr(gc, name, None)
    return fn if callable(fn) else None


class Metrics:
    def __init__(self, ram_interval=RAM_INTERVAL):
        self._ram_interval = ram_interval
        self._ram_next = 0.0
        self.free = 0            # bytes free after the last gc.collect()
        self.free_low = None     # lowest `free` seen since boot (low-water)
        self.alloc = 0           # bytes allocated after the last gc.collect()
        self.collect_ms = 0.0    # cost of the last gc.collect()
        self.ram_samples = 0
        self.frame_ms = 0.0
        self.frame_ms_max = 0.0

    # -- fed by the engine loop -------------------------------------------

    def maybe_sample_ram(self, now):
        """Cheap gate — a timestamp compare on most ticks, a real collect+read
        only once per `ram_interval`."""
        if now >= self._ram_next:
            self.sample_ram()
            self._ram_next = now + self._ram_interval

    def sample_ram(self):
        t0 = _now_ns()
        gc.collect()
        self.collect_ms = (_now_ns() - t0) / 1_000_000.0
        mem_free, mem_alloc = _gc_reader("mem_free"), _gc_reader("mem_alloc")
        self.free = mem_free() if mem_free else None
        self.alloc = mem_alloc() if mem_alloc else None
        if self.free is not None and (
            self.free_low is None or self.free < self.free_low
        ):
            self.free_low = self.free
        self.ram_samples += 1

    def note_frame(self, dt):
        self.frame_ms = dt * 1000.0
        if self.frame_ms > self.frame_ms_max:
            self.frame_ms_max = self.frame_ms

    # -- read by DiagMode ------------------------------------------------

    @property
    def heap(self):
        if self.free is None or self.alloc is None:
            return None
        return self.free + self.alloc

    def flash(self):
        """(free_bytes, total_bytes) for the filesystem at '/', or
        (None, None) when statvfs isn't available (some builds / hosts)."""
        try:
            st = os.statvfs("/")
        except (OSError, AttributeError):
            return (None, None)
        frsize = st[1]                          # f_frsize
        return (frsize * st[4], frsize * st[2])  # f_bavail, f_blocks

    def environment(self):
        """(cpython_or_circuitpython_version, os_name) — best effort."""
        impl = sys.implementation
        ver = ".".join(str(n) for n in tuple(impl.version)[:3])
        try:
            osname = os.uname().sysname
        except (AttributeError, OSError):
            osname = getattr(impl, "name", "python")
        return (ver, osname)
