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

# Off-device tests for the ModeStack routing in game/modes.py. ModeStack
# imports no displayio, so fake modes + a fake screen exercise it fully.
#
#   python3 Chapter_7/tests/test_modes.py

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "game"))

# modes.py imports only `input` at module level (displayio et al. are lazy,
# inside the mode classes), so ModeStack imports cleanly off-device.
import modes  # noqa: E402
import input as im  # noqa: E402


class FakeMode:
    def __init__(self, name, exit_on=None):
        self.name = name
        self.group = ("group", name)   # identity sentinel
        self.seen = []                 # event lists passed to tick()
        self.render_count = 0
        self._exit_on = exit_on

    def tick(self, events, now):
        self.seen.append(list(events))
        if self._exit_on is not None and self._exit_on in events:
            return "exit"
        return None

    def render(self):
        self.render_count += 1


class FakeScreen:
    def __init__(self):
        self._group = None
        self.assignments = 0

    @property
    def root_group(self):
        return self._group

    @root_group.setter
    def root_group(self, g):
        self._group = g
        self.assignments += 1


def stack():
    play = FakeMode("play")
    menu = FakeMode("menu", exit_on=im.CANCEL)
    diag = FakeMode("diag", exit_on=im.CANCEL)
    s = modes.ModeStack(play, {"menu": menu, "diag": diag})
    return s, play, menu, diag


class Routing(unittest.TestCase):
    def test_events_go_to_base_when_no_overlay(self):
        s, play, menu, diag = stack()
        s.handle([im.MOVE_N, im.CONFIRM], 0.0)
        self.assertEqual(play.seen, [[im.MOVE_N, im.CONFIRM]])
        self.assertEqual(menu.seen, [])
        self.assertEqual(s.depth, 1)
        self.assertFalse(s.overlay_active())

    def test_chord_opens_overlay_and_is_consumed(self):
        s, play, menu, diag = stack()
        s.handle(["menu"], 0.0)
        self.assertIs(s.top, menu)
        self.assertTrue(s.overlay_active())
        # the "menu" event never reached any mode's tick
        self.assertEqual(menu.seen, [[]])
        self.assertEqual(play.seen, [])

    def test_overlay_receives_events_play_is_frozen(self):
        s, play, menu, diag = stack()
        s.handle(["menu"], 0.0)
        s.handle([im.MOVE_N], 0.1)
        s.handle([im.MOVE_E], 0.2)
        self.assertEqual(menu.seen, [[], [im.MOVE_N], [im.MOVE_E]])
        self.assertEqual(play.seen, [])          # no turn advanced while menu up

    def test_same_chord_toggles_back_to_play(self):
        s, play, menu, diag = stack()
        s.handle(["diag"], 0.0)
        self.assertIs(s.top, diag)
        s.handle(["diag"], 0.1)
        self.assertIs(s.top, play)
        self.assertEqual(s.depth, 1)

    def test_other_chord_swaps_overlay_not_stacks(self):
        s, play, menu, diag = stack()
        s.handle(["menu"], 0.0)
        s.handle(["diag"], 0.1)
        self.assertIs(s.top, diag)
        self.assertEqual(s.depth, 2)             # base + one overlay, never 3

    def test_cancel_passes_through_and_stub_exits(self):
        s, play, menu, diag = stack()
        s.handle(["menu"], 0.0)
        s.handle([im.CANCEL], 0.1)               # stub returns "exit"
        self.assertIs(s.top, play)

    def test_toggle_events_never_reach_play(self):
        s, play, menu, diag = stack()
        for ev in ("menu", "diag", "menu", "diag"):
            s.handle([ev], 0.0)
        for seen in play.seen:
            self.assertNotIn("menu", seen)
            self.assertNotIn("diag", seen)


class Rendering(unittest.TestCase):
    def test_render_sets_root_group_to_top(self):
        s, play, menu, diag = stack()
        screen = FakeScreen()
        s.render(screen)
        self.assertEqual(screen.root_group, play.group)
        s.handle(["menu"], 0.0)
        s.render(screen)
        self.assertEqual(screen.root_group, menu.group)

    def test_render_only_reassigns_on_change(self):
        s, play, menu, diag = stack()
        screen = FakeScreen()
        s.render(screen)
        s.render(screen)
        s.render(screen)
        self.assertEqual(screen.assignments, 1)  # play group set once, not thrice
        s.handle(["diag"], 0.0)
        s.render(screen)
        self.assertEqual(screen.assignments, 2)


class WithRealInputModel(unittest.TestCase):
    def test_xy_chord_from_input_model_opens_diag(self):
        s, play, menu, diag = stack()
        model = im.InputModel()
        keys = {k: False for k in ("up", "down", "left", "right", "a", "b", "x", "y")}
        events = model.tick({**keys, "x": True, "y": True}, 0.0)
        s.handle(events, 0.0)
        self.assertIs(s.top, diag)


if __name__ == "__main__":
    unittest.main()
