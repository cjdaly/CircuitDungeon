# The MIT License (MIT)
#
# Copyright (c) 2026 Chris J Daly (github user cjdaly)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

# The logical button model that sits above hardware.read_buttons() — turns the
# raw 8-key state dict into a stream of named events for the turn loop, menus,
# and diagnostics. Pure: no displayio, no board, no time import (the caller
# passes `now`), so it runs and is tested off-device with synthetic input.
#
# Governed by doc/INPUT.md and doc/ENGINE.md section 1.
# Bead cd-e3p.11.

# -- event names ----------------------------------------------------------
# d-pad (edge-triggered, then auto-repeated while held)
MOVE_N = "move_n"
MOVE_S = "move_s"
MOVE_E = "move_e"
MOVE_W = "move_w"
# face buttons (fire once per press; no long-press / repeat in v1)
CONFIRM = "confirm"   # A
CANCEL = "cancel"     # B
AUX_X = "aux_x"       # X
AUX_Y = "aux_y"       # Y
# chord events use the caller's binding-table name verbatim (e.g. "diag", "menu")

_DPAD = {"up": MOVE_N, "down": MOVE_S, "left": MOVE_W, "right": MOVE_E}
_FACE = {"a": CONFIRM, "b": CANCEL, "x": AUX_X, "y": AUX_Y}

DEFAULT_CHORDS = {
    frozenset(("x", "y")): "diag",
    frozenset(("a", "b")): "menu",
}

# A chord-participating button holds its single-press this long (seconds) to
# see whether the other half of a chord arrives. ~50 ms — one tick at 20 fps,
# imperceptible in a turn-based game (doc/ENGINE.md 1.1).
CHORD_WINDOW = 0.05

_TRACE_SIZE = 32


class InputModel:
    def __init__(self, chords=None, repeat_delay=0.28, repeat_interval=0.13):
        self.chords = dict(DEFAULT_CHORDS if chords is None else chords)
        # buttons that appear in some chord get the CHORD_WINDOW single-press delay
        self._chord_buttons = set()
        for combo in self.chords:
            self._chord_buttons |= set(combo)

        # instance config so the settings screen (cd-e3p.13) can retune live
        self.repeat_delay = repeat_delay
        self.repeat_interval = repeat_interval
        # engine sets this each tick (pause repeat while a monster is in view —
        # doc/ENGINE.md 1.3 — or while a non-play mode is up)
        self.repeat_paused = False

        self._prev = {b: False for b in list(_DPAD) + list(_FACE)}
        self._held_since = {}          # button -> now it went down
        self._repeat_at = {}           # d-pad button -> next repeat time
        self._pending = {}             # face button -> [deadline, event, consumed]
        self._singled = set()          # buttons whose single-press already fired this hold
        self._chord_fired = set()      # chord names fired and awaiting re-arm
        self._queue = []               # bounded output queue
        self._queue_max = 4            # drop-oldest; stale turn-based input is worthless

        self._trace = []               # ring of (t_ms, kind, detail)
        self._trace_i = 0
        self._last_now = 0.0

    # -- main entry point -------------------------------------------------

    def tick(self, buttons, now):
        """Advance the model by one poll. `buttons` is hardware.read_buttons()'s
        dict (keys up/down/left/right/a/b/x/y -> bool); `now` is monotonic
        seconds. Returns the list of events produced this tick (also enqueued
        for get())."""
        self._last_now = now
        produced = []

        pressed = [b for b in self._prev if buttons.get(b) and not self._prev[b]]
        released = [b for b in self._prev if not buttons.get(b) and self._prev[b]]

        for b in released:
            self._on_release(b, now, produced)
        for b in pressed:
            self._on_press(b, now, produced)

        self._check_chords(buttons, now, produced)
        self._resolve_pending(buttons, now, produced)
        self._auto_repeat(buttons, now, produced)

        self._prev = {b: bool(buttons.get(b)) for b in self._prev}

        for ev in produced:
            self._enqueue(ev)
        return produced

    def get(self):
        """Pop the oldest queued event, or None. The turn loop pulls one per
        tick (doc/ENGINE.md 1.5)."""
        if self._queue:
            return self._queue.pop(0)
        return None

    # -- press / release ------------------------------------------------

    def _on_press(self, b, now, out):
        self._held_since[b] = now
        self._singled.discard(b)          # fresh hold
        self._trace_add(now, "press", b)
        if b in _DPAD:
            out.append(_DPAD[b])
            self._repeat_at[b] = now + self.repeat_delay
        elif b in _FACE:
            if b in self._chord_buttons:
                # defer: a chord may still form this window
                self._pending[b] = [now + CHORD_WINDOW, _FACE[b], False]
            else:
                out.append(_FACE[b])
                self._singled.add(b)

    def _on_release(self, b, now, out):
        self._held_since.pop(b, None)
        self._repeat_at.pop(b, None)
        self._trace_add(now, "release", b)

        pend = self._pending.pop(b, None)
        if pend is not None and not pend[2]:
            # released before the window closed and no chord claimed it -> a tap
            out.append(pend[1])
            self._trace_add(now, "single", b)

        self._singled.discard(b)
        # re-arm any chord this button belongs to
        for combo, name in self.chords.items():
            if b in combo and name in self._chord_fired:
                self._chord_fired.discard(name)

    # -- chords -------------------------------------------------------

    def _check_chords(self, buttons, now, out):
        for combo, name in self.chords.items():
            if name in self._chord_fired:
                continue
            if any(x in self._singled for x in combo):
                continue  # a member already fired its single this hold — not a chord
            if all(buttons.get(x) for x in combo):
                out.append(name)
                self._chord_fired.add(name)
                self._trace_add(now, "chord", name)
                for x in combo:
                    if x in self._pending:
                        self._pending[x][2] = True   # consumed; release won't fire it
                        self._pending.pop(x, None)

    def _resolve_pending(self, buttons, now, out):
        done = []
        for b, pend in self._pending.items():
            deadline, event, consumed = pend
            if consumed:
                done.append(b)
            elif not buttons.get(b):
                done.append(b)                       # handled in _on_release
            elif now >= deadline:
                out.append(event)
                self._singled.add(b)
                self._trace_add(now, "single", b)
                done.append(b)
        for b in done:
            self._pending.pop(b, None)

    # -- auto-repeat -------------------------------------------------

    def _auto_repeat(self, buttons, now, out):
        if self.repeat_paused:
            return
        for b in _DPAD:
            if buttons.get(b) and b in self._repeat_at and now >= self._repeat_at[b]:
                out.append(_DPAD[b])
                self._repeat_at[b] = now + self.repeat_interval
                self._trace_add(now, "repeat", b)

    # -- queue -----------------------------------------------------

    def _enqueue(self, ev):
        self._queue.append(ev)
        if len(self._queue) > self._queue_max:
            self._queue.pop(0)

    # -- trace / instrumentation (rendered by cd-89o.6) ------------

    def _trace_add(self, now, kind, detail):
        rec = (int(now * 1000) & 0xFFFFFF, kind, detail)
        if len(self._trace) < _TRACE_SIZE:
            self._trace.append(rec)
        else:
            self._trace[self._trace_i] = rec
        self._trace_i = (self._trace_i + 1) % _TRACE_SIZE

    def trace(self):
        """Recent input records, oldest first: list of (t_ms, kind, detail)."""
        if len(self._trace) < _TRACE_SIZE:
            return list(self._trace)
        return self._trace[self._trace_i:] + self._trace[: self._trace_i]

    def snapshot(self):
        """Live state for the diagnostics input page."""
        now = self._last_now
        held = [b for b in self._prev if self._prev[b]]
        hold_ms = {b: int((now - t) * 1000) for b, t in self._held_since.items()}
        candidates = []
        for combo in self.chords:
            n_down = sum(1 for x in combo if self._prev.get(x))
            if 0 < n_down < len(combo):
                candidates.append(sorted(combo))
        return {
            "held": held,
            "hold_ms": hold_ms,
            "chord_candidates": candidates,
            "chord_fired": sorted(self._chord_fired),
            "queue_depth": len(self._queue),
        }
