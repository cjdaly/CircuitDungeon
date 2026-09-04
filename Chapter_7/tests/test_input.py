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

# Off-device tests for game/input.py — the button model is pure, so synthetic
# (buttons, now) streams exercise every path.
#
#   python3 Chapter_7/tests/test_input.py

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "game"))

import input as im  # noqa: E402

_KEYS = ("up", "down", "left", "right", "a", "b", "x", "y")


def feed(model, steps):
    """steps: iterable of (held_dict_partial, now). Returns every event across
    all ticks, in order."""
    events = []
    for partial, now in steps:
        b = {k: False for k in _KEYS}
        b.update(partial)
        events.extend(model.tick(b, now))
    return events


class DPad(unittest.TestCase):
    def test_press_fires_once(self):
        m = im.InputModel()
        evs = feed(m, [({"up": True}, 0.0), ({"up": True}, 0.01), ({}, 0.02)])
        self.assertEqual(evs, [im.MOVE_N])

    def test_hold_auto_repeats(self):
        m = im.InputModel(repeat_delay=0.28, repeat_interval=0.13)
        steps = [({"right": True}, t / 100.0) for t in range(0, 72, 2)]  # held 0.00-0.70s
        evs = feed(m, steps)
        # right is not in any chord -> press fires MOVE_E at once, then repeats
        # at +0.28, +0.13, +0.13, +0.13
        self.assertGreaterEqual(evs.count(im.MOVE_E), 4)
        self.assertLessEqual(evs.count(im.MOVE_E), 5)

    def test_repeat_paused(self):
        m = im.InputModel()
        m.repeat_paused = True
        steps = [({"left": True}, t / 100.0) for t in range(0, 80, 2)]
        evs = feed(m, steps)
        self.assertEqual(evs, [im.MOVE_W])  # initial press only

    def test_direction_mapping(self):
        m = im.InputModel()
        evs = feed(m, [
            ({"up": True}, 0.0), ({}, 0.05),
            ({"down": True}, 0.1), ({}, 0.15),
            ({"left": True}, 0.2), ({}, 0.25),
            ({"right": True}, 0.3), ({}, 0.35),
        ])
        self.assertEqual(evs, [im.MOVE_N, im.MOVE_S, im.MOVE_W, im.MOVE_E])


class FaceButtons(unittest.TestCase):
    def test_non_chord_button_fires_immediately(self):
        m = im.InputModel(chords={})  # no chords -> no deferral
        evs = feed(m, [({"a": True}, 0.0), ({}, 0.01)])
        self.assertEqual(evs, [im.CONFIRM])

    def test_chord_button_alone_fires_after_window(self):
        m = im.InputModel()  # default chords -> 'a' participates in {a,b}
        evs = feed(m, [
            ({"a": True}, 0.00),   # deferred
            ({"a": True}, 0.03),   # still within CHORD_WINDOW (0.05)
            ({"a": True}, 0.06),   # window passed -> CONFIRM
            ({"a": True}, 0.09),
        ])
        self.assertEqual(evs, [im.CONFIRM])

    def test_quick_tap_still_registers(self):
        m = im.InputModel()
        evs = feed(m, [({"a": True}, 0.00), ({}, 0.02)])  # released before window
        self.assertEqual(evs, [im.CONFIRM])

    def test_no_long_press_event(self):
        m = im.InputModel(chords={})
        steps = [({"x": True}, t / 10.0) for t in range(0, 20)]  # held 2 seconds
        evs = feed(m, steps)
        self.assertEqual(evs, [im.AUX_X])  # exactly one, no LONG_* ever


# A generic two-face-button chord for exercising the chord engine. The app's
# real table (input.DEFAULT_CHORDS) only chords X+Y and Down+B now that the
# menu stub is gone (cd-dsc.6); these tests declare their own so they test the
# mechanism, not the bindings.
_AB = {frozenset(("a", "b")): "menu"}


class Chords(unittest.TestCase):
    def test_simultaneous_pair_fires_chord_not_singles(self):
        m = im.InputModel(chords=_AB)
        evs = feed(m, [
            ({"a": True}, 0.00),
            ({"a": True, "b": True}, 0.02),  # both down within the window
            ({"a": True, "b": True}, 0.08),
            ({}, 0.10),
        ])
        self.assertEqual(evs, ["menu"])
        self.assertNotIn(im.CONFIRM, evs)
        self.assertNotIn(im.CANCEL, evs)

    def test_xy_is_diag(self):
        m = im.InputModel()
        evs = feed(m, [({"x": True, "y": True}, 0.0), ({}, 0.05)])
        self.assertEqual(evs, ["diag"])

    def test_chord_fires_once_per_hold(self):
        m = im.InputModel(chords=_AB)
        steps = [({"a": True, "b": True}, t / 100.0) for t in range(0, 50, 2)]
        evs = feed(m, steps)
        self.assertEqual(evs, ["menu"])

    def test_chord_rearms_after_releasing_one_member(self):
        m = im.InputModel(chords=_AB)
        evs = feed(m, [
            ({"a": True, "b": True}, 0.00),  # menu
            ({"b": True}, 0.05),             # release a -> re-arm
            ({"a": True, "b": True}, 0.10),  # menu again
            ({}, 0.15),
        ])
        self.assertEqual(evs, ["menu", "menu"])

    def test_late_second_button_does_not_form_chord(self):
        # hold A past its window (CONFIRM fires), then press B — that's two
        # separate presses, not a chord.
        m = im.InputModel(chords=_AB)
        evs = feed(m, [
            ({"a": True}, 0.00),
            ({"a": True}, 0.07),            # window passed -> CONFIRM, a is "singled"
            ({"a": True, "b": True}, 0.30),  # b joins late
            ({"a": True, "b": True}, 0.40),  # b's window passes -> CANCEL
            ({}, 0.45),
        ])
        self.assertEqual(evs, [im.CONFIRM, im.CANCEL])
        self.assertNotIn("menu", evs)

    def test_custom_binding_name_is_emitted_verbatim(self):
        m = im.InputModel(chords={frozenset(("up", "a")): "special"})
        evs = feed(m, [({"up": True, "a": True}, 0.0), ({}, 0.05)])
        self.assertIn("special", evs)


class Queue(unittest.TestCase):
    def test_get_pops_oldest(self):
        m = im.InputModel()
        feed(m, [({"up": True}, 0.0), ({}, 0.05), ({"down": True}, 0.1), ({}, 0.15)])
        self.assertEqual(m.get(), im.MOVE_N)
        self.assertEqual(m.get(), im.MOVE_S)
        self.assertIsNone(m.get())

    def test_queue_is_bounded_drop_oldest(self):
        m = im.InputModel(repeat_delay=0.02, repeat_interval=0.02)
        # hammer repeats without ever draining
        feed(m, [({"right": True}, t / 100.0) for t in range(0, 40, 2)])
        depth = 0
        while m.get() is not None:
            depth += 1
        self.assertLessEqual(depth, 4)


class Instrumentation(unittest.TestCase):
    def test_snapshot_reports_held_and_candidates(self):
        m = im.InputModel(chords=_AB)
        m.tick({k: (k == "a") for k in _KEYS}, 1.0)
        m.tick({k: (k == "a") for k in _KEYS}, 1.1)
        snap = m.snapshot()
        self.assertEqual(snap["held"], ["a"])
        self.assertGreaterEqual(snap["hold_ms"]["a"], 90)
        self.assertIn("a+b", snap["chord_candidates"])  # a down, b not -> chord forming


class WaitChords(unittest.TestCase):
    def _hold(self, m, combo, t0=0.0):
        keys = {k: (k in combo) for k in _KEYS}
        return feed(m, [(keys, t0), (keys, t0 + 0.02), ({k: False for k in _KEYS}, t0 + 0.1)])

    def test_down_b_emits_wait_and_suppresses_the_moves(self):
        m = im.InputModel()   # DOWN+B is the only wait chord (cd-e3p.15)
        evs = self._hold(m, ("down", "b"))
        self.assertEqual(evs, ["wait"])
        self.assertNotIn(im.MOVE_S, evs)   # down's move suppressed
        self.assertNotIn(im.CANCEL, evs)   # b's single suppressed

    def test_opposing_dpad_is_no_longer_a_chord(self):
        m = im.InputModel()
        evs = self._hold(m, ("left", "right"))
        self.assertNotIn("wait", evs)
        self.assertIn(im.MOVE_W, evs)      # both just move (immediately —
        self.assertIn(im.MOVE_E, evs)      # left/right aren't chord-eligible)

    def test_chord_stats_count_fires(self):
        m = im.InputModel()
        self._hold(m, ("down", "b"))
        self._hold(m, ("down", "b"), t0=1.0)
        row = next(r for r in m.chord_stats() if r["combo"] == "b+down")
        self.assertEqual(row["fired"], 2)
        self.assertEqual(row["name"], "wait")
        self.assertIsNotNone(row["last_spread_ms"])

    def test_chord_stats_count_misses(self):
        # press DOWN, let it single (window passes), THEN press B while still
        # holding DOWN -> too slow to be a chord: a miss, no wait.
        m = im.InputModel()
        keys_d = {k: (k == "down") for k in _KEYS}
        keys_db = {k: (k in ("down", "b")) for k in _KEYS}
        evs = feed(m, [
            (keys_d, 0.0), (keys_d, 0.07),          # DOWN singles -> MOVE_S
            (keys_db, 0.10), (keys_db, 0.20),       # B joins late
            ({k: False for k in _KEYS}, 0.25),
        ])
        self.assertIn(im.MOVE_S, evs)
        self.assertNotIn("wait", evs)
        row = next(r for r in m.chord_stats() if r["combo"] == "b+down")
        self.assertEqual(row["fired"], 0)
        self.assertEqual(row["missed"], 1)


if __name__ == "__main__":
    unittest.main()
