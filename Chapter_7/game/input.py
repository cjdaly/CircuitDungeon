# SPDX-FileCopyrightText: 2026 Chris J Daly (github user cjdaly)
#
# SPDX-License-Identifier: MIT

# The logical button model that sits above hardware.read_buttons() — turns the
# raw 8-key state dict into a stream of named events for the turn loop, menus,
# and diagnostics. Pure: no displayio, no board, no time import (the caller
# passes `now`), so it runs and is tested off-device with synthetic input.
#
# Governed by doc/INPUT.md and doc/ENGINE.md section 1.
# Beads cd-e3p.11 (model), cd-e3p.14 (wait chords + per-chord stats).
#
# The per-event ring trace that fed the old two-page diag was dropped once the
# wait-chord bindings were settled (cd-e3p.14/.15 closed) — it was ~2 KB
# resident plus an allocation per keypress (cd-dsc.6). `chord_stats()` and
# `snapshot()` stay; they're what the one-screen diag still shows.

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
_EVENT = dict(_DPAD)
_EVENT.update(_FACE)

# PicoSystem face-button diamond (Chris's unit): X top, Y left, A right, B bottom.
# "wait" is DOWN+B — "both thumbs down". cd-e3p.14 shipped three candidates
# (also LEFT+RIGHT / UP+DOWN); the 2026-08-30 hardware run (cd-e3p.15) showed
# the opposing-d-pad squeezes never form on the real rocker, so they're gone.
DEFAULT_CHORDS = {
    frozenset(("x", "y")): "diag",
    frozenset(("down", "b")): "wait",
}
# A+B -> "menu" was here; dropped with the menu stub (cd-dsc.6). Without it,
# A (CONFIRM) is no longer chord-eligible and fires on press with no window
# delay. Restore the entry when cd-e3p.13 builds the real menu.

# A chord-participating button holds its single-press this long (seconds) to
# see whether the other half of a chord arrives. ~50 ms — one tick at 20 fps,
# imperceptible in a turn-based game (doc/ENGINE.md 1.1). Of the d-pad, only
# DOWN is chord-eligible now (via DOWN+B), so only down-moves take the delay;
# UP / LEFT / RIGHT fire immediately.
CHORD_WINDOW = 0.05


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
        self._pending = {}             # button -> [deadline, event, consumed]
        self._singled = set()          # buttons whose single-press already fired this hold
        self._chord_fired = set()      # chord combos (frozensets) fired, awaiting re-arm
        self._chord_missed = set()     # combos already counted as a miss this attempt
        self._queue = []               # bounded output queue
        self._queue_max = 4            # drop-oldest; stale turn-based input is worthless

        # per-binding effectiveness, for the diagnostics screen (cd-e3p.14):
        #   fired   - chord landed
        #   missed  - both members held but a member had already fired its move
        #             (the d-pad rock/chatter failure)
        #   last_spread_ms - |press-time gap| between the two members, last fire
        self._chord_stats = {
            combo: {"name": name, "fired": 0, "missed": 0, "last_spread_ms": None}
            for combo, name in self.chords.items()
        }
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

    def _fire_single(self, b, now, out):
        """Emit button `b`'s single-press event and, for a d-pad button, arm
        its auto-repeat from here."""
        out.append(_EVENT[b])
        self._singled.add(b)
        if b in _DPAD:
            self._repeat_at[b] = now + self.repeat_delay

    def _on_press(self, b, now, out):
        self._held_since[b] = now
        self._singled.discard(b)          # fresh hold
        if b in self._chord_buttons:
            # defer the single-press — a chord may still form within the window.
            # Applies to d-pad and face buttons alike (the wait chords make
            # every d-pad direction chord-eligible).
            self._pending[b] = [now + CHORD_WINDOW, _EVENT[b], False]
        else:
            self._fire_single(b, now, out)

    def _on_release(self, b, now, out):
        self._held_since.pop(b, None)
        self._repeat_at.pop(b, None)

        pend = self._pending.pop(b, None)
        if pend is not None and not pend[2]:
            # released before the window closed and no chord claimed it -> a tap
            self._fire_single(b, now, out)

        self._singled.discard(b)
        # re-arm / clear miss-tracking for any chord this button belongs to
        for combo in self.chords:
            if b in combo:
                self._chord_fired.discard(combo)
                self._chord_missed.discard(combo)

    # -- chords -------------------------------------------------------

    def _check_chords(self, buttons, now, out):
        for combo, name in self.chords.items():
            if combo in self._chord_fired:
                continue
            all_held = all(buttons.get(x) for x in combo)
            if any(x in self._singled for x in combo):
                if all_held and combo not in self._chord_missed:
                    # both members down, but one already fired its move — the
                    # squeeze was too slow / the pad rocked. Count it once.
                    self._chord_stats[combo]["missed"] += 1
                    self._chord_missed.add(combo)
                continue
            if all_held:
                out.append(name)
                self._chord_fired.add(combo)
                self._record_fire(combo, now)
                for x in combo:
                    if x in self._pending:
                        self._pending[x][2] = True   # consumed; release won't fire it
                        self._pending.pop(x, None)

    def _record_fire(self, combo, now):
        s = self._chord_stats[combo]
        s["fired"] += 1
        times = [self._held_since[x] for x in combo if x in self._held_since]
        if len(times) >= 2:
            s["last_spread_ms"] = int((max(times) - min(times)) * 1000)

    def _resolve_pending(self, buttons, now, out):
        done = []
        for b, pend in self._pending.items():
            deadline, _event, consumed = pend
            if consumed:
                done.append(b)
            elif not buttons.get(b):
                done.append(b)                       # handled in _on_release
            elif now >= deadline:
                self._fire_single(b, now, out)
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

    # -- queue -----------------------------------------------------

    def _enqueue(self, ev):
        self._queue.append(ev)
        if len(self._queue) > self._queue_max:
            self._queue.pop(0)

    # -- instrumentation (rendered by the diag screen, cd-89o.6) ----------

    @staticmethod
    def _combo_label(combo):
        return "+".join(sorted(combo))

    def snapshot(self):
        """Live state for the diagnostics input page."""
        now = self._last_now
        held = [b for b in self._prev if self._prev[b]]
        hold_ms = {b: int((now - t) * 1000) for b, t in self._held_since.items()}
        candidates = []
        for combo in self.chords:
            n_down = sum(1 for x in combo if self._prev.get(x))
            if 0 < n_down < len(combo):
                candidates.append(self._combo_label(combo))
        return {
            "held": held,
            "hold_ms": hold_ms,
            "chord_candidates": candidates,
            "chord_armed": [self._combo_label(c) for c in self._chord_fired],
            "queue_depth": len(self._queue),
        }

    def chord_stats(self):
        """Per-binding effectiveness, for the diagnostics screen. One row per
        chord binding: {combo, name, fired, missed, last_spread_ms}."""
        rows = []
        for combo, s in self._chord_stats.items():
            rows.append({
                "combo": self._combo_label(combo),
                "name": s["name"],
                "fired": s["fired"],
                "missed": s["missed"],
                "last_spread_ms": s["last_spread_ms"],
            })
        return rows
