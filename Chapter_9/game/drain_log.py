# SPDX-License-Identifier: MIT
"""Battery drain logger -- cd-342.29.

How long does a charge last? Rather than guess current draw, log it: every
`interval` seconds, append one record to microcontroller.nvm (4 KB of flash
that survives a dead battery and a reset). Next day, on USB,
tools/drain_report.py reads the log back and prints the discharge curve.

Off unless settings.toml has POWER_LOG = "<minutes between records>" (see
main.py): every record rewrites the nvm flash sector, which wears it (~100k
erase cycles: about three years of 10-minute records) and stalls the CPU
briefly.

Each record is 12 bytes, packed little-endian:

    magic   u8   0xD2, so blank flash (0xFF) and other data read as empty
                 (0xD1 was the first, 10-byte layout: clear those logs)
    kind    u8   KIND_BOOT (first record after a reset) or KIND_SAMPLE
    lit     u8   % of the interval the backlight was on
    deep    u8   % of the interval spent in deep idle (power.py)
    seq     u16  ever-increasing record number, so the ring's newest is findable
    minutes u16  since this boot
    raw     u16  BAT_ADC reading (0-65535, averaged). Kept raw because the
                 board's divider ratio is still unconfirmed (cd-bp3.6.1);
                 the report converts it.
    wakes   u8   motion wakes from deep idle during the interval
    peak    u8   the biggest of those wakes' moves from rest, x10 (m/s^2),
                 so false wakes (just over power.WAKE_SHIFT) stand out

The log is a ring of RECORDS slots: when full, the oldest record goes.

Pure logic -- `nvm` is anything sliceable and `read_raw` any callable, so this
runs under plain desktop Python (see tests/test_drain_log.py).
"""
import struct

MAGIC = 0xD2
KIND_BOOT = 0
KIND_SAMPLE = 1
_FORMAT = "<BBBBHHHBB"
SIZE = 12


def records(nvm):
    """Every valid record, oldest first: (kind, lit, deep, seq, minutes, raw, wakes, peak)."""
    found = []
    for slot in range(len(nvm) // SIZE):
        start = slot * SIZE
        fields = struct.unpack(_FORMAT, bytes(nvm[start:start + SIZE]))
        if fields[0] == MAGIC:
            found.append(fields[1:])
    found.sort(key=lambda record: record[3])
    return found


class DrainLog:
    """Call .tick(now, lit, asleep) every loop (it writes a record when one is due),
    and .woke(shift) on each motion wake from deep idle."""

    def __init__(self, nvm, read_raw, interval, now):
        self._nvm = nvm
        self._read_raw = read_raw
        self._interval = interval
        self._slots = len(nvm) // SIZE
        self._started = now
        self._last = now
        self._lit = self._deep = self._total = 0.0
        self._wakes, self._peak = 0, 0.0
        self.writes = 0
        self.failed = None  # the error that stopped logging, if one did

        newest = None
        for slot in range(self._slots):
            start = slot * SIZE
            fields = struct.unpack(_FORMAT, bytes(nvm[start:start + SIZE]))
            if fields[0] == MAGIC and (newest is None or fields[4] > newest[1]):
                newest = (slot, fields[4])
        if newest is None:
            self._slot, self._seq = 0, 0
        else:
            self._slot, self._seq = (newest[0] + 1) % self._slots, newest[1] + 1
        self._write(KIND_BOOT, now, 100, 0)
        self._next = now + interval

    def tick(self, now, lit, asleep):
        if self.failed is not None:
            return
        dt = now - self._last
        self._last = now
        self._total += dt
        if lit:
            self._lit += dt
        if asleep:
            self._deep += dt
        if now >= self._next:
            total = self._total or 1.0
            self._write(KIND_SAMPLE, now, self._lit * 100 / total, self._deep * 100 / total)
            self._lit = self._deep = self._total = 0.0
            self._wakes, self._peak = 0, 0.0
            self._next = now + self._interval

    def woke(self, shift):
        self._wakes += 1
        self._peak = max(self._peak, shift)

    def _write(self, kind, now, lit_pct, deep_pct):
        minutes = min(int((now - self._started) / 60), 0xFFFF)
        record = struct.pack(
            _FORMAT, MAGIC, kind, int(lit_pct + 0.5), int(deep_pct + 0.5),
            self._seq & 0xFFFF, minutes, self._read_raw(),
            min(self._wakes, 255), min(int(self._peak * 10 + 0.5), 255),
        )
        start = self._slot * SIZE
        try:
            self._nvm[start:start + SIZE] = record
        except Exception as exc:  # noqa: BLE001 -- never take the game down for a log
            self.failed = exc
            print("drain log stopped:", repr(exc))
            return
        self.writes += 1
        self._slot = (self._slot + 1) % self._slots
        self._seq += 1
