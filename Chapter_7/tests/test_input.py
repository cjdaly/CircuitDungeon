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
        steps = [({"right": True}, t / 100.0) for t in range(0, 60, 2)]  # held 0.00-0.58s
        evs = feed(m, steps)
        # press at t=0, first repeat at >=0.28, second at >=0.41, third at >=0.54
        self.assertEqual(evs.count(im.MOVE_E), 4)

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


class Chords(unittest.TestCase):
    def test_simultaneous_pair_fires_chord_not_singles(self):
        m = im.InputModel()
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
        m = im.InputModel()
        steps = [({"a": True, "b": True}, t / 100.0) for t in range(0, 50, 2)]
        evs = feed(m, steps)
        self.assertEqual(evs, ["menu"])

    def test_chord_rearms_after_releasing_one_member(self):
        m = im.InputModel()
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
        m = im.InputModel()
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
    def test_trace_is_oldest_first_and_has_kinds(self):
        m = im.InputModel()
        feed(m, [({"a": True, "b": True}, 0.0), ({}, 0.05)])
        kinds = [rec[1] for rec in m.trace()]
        self.assertEqual(kinds[0], "press")
        self.assertIn("chord", kinds)
        self.assertIn("release", kinds)
        # timestamps non-decreasing
        ts = [rec[0] for rec in m.trace()]
        self.assertEqual(ts, sorted(ts))

    def test_trace_ring_wraps_and_stays_bounded(self):
        m = im.InputModel()
        for t in range(200):
            feed(m, [({"up": True}, t / 10.0), ({}, t / 10.0 + 0.05)])
        self.assertEqual(len(m.trace()), 32)

    def test_snapshot_reports_held_and_candidates(self):
        m = im.InputModel()
        m.tick({k: (k == "a") for k in _KEYS}, 1.0)
        m.tick({k: (k == "a") for k in _KEYS}, 1.1)
        snap = m.snapshot()
        self.assertEqual(snap["held"], ["a"])
        self.assertGreaterEqual(snap["hold_ms"]["a"], 90)
        self.assertIn(["a", "b"], snap["chord_candidates"])  # a down, b not -> candidate


if __name__ == "__main__":
    unittest.main()
