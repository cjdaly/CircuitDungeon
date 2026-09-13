# SPDX-License-Identifier: MIT
# Off-device tests for game/edge_gesture.py -- pure logic (touch.py only
# needs adafruit_cst8xx inside SafeTouch.poll(), not at import time), so
# this runs under plain desktop Python.
#
#   python3 Chapter_9/tests/test_edge_gesture.py

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "game"))

import edge_gesture  # noqa: E402
import rooms  # noqa: E402

WIDTH = HEIGHT = 240
MARGIN = edge_gesture.EDGE_MARGIN
MID = WIDTH // 2


class TestEdgeGestureTracker(unittest.TestCase):
    def setUp(self):
        self.tracker = edge_gesture.EdgeGestureTracker(WIDTH, HEIGHT)

    def _tap(self, x, y, t=0.0):
        """A tap: one touch point, then release on the next tick."""
        self.assertIsNone(self.tracker.update((x, y), t))
        return self.tracker.update(None, t + 0.05)

    def test_tap_near_left_edge_is_left(self):
        self.assertEqual(self._tap(2, MID), rooms.LEFT)

    def test_tap_near_right_edge_is_right(self):
        self.assertEqual(self._tap(WIDTH - 2, MID), rooms.RIGHT)

    def test_tap_near_top_edge_is_up(self):
        self.assertEqual(self._tap(MID, 2), rooms.UP)

    def test_tap_near_bottom_edge_is_down(self):
        self.assertEqual(self._tap(MID, HEIGHT - 2), rooms.DOWN)

    def test_tap_in_the_middle_is_none(self):
        self.assertIsNone(self._tap(MID, MID))

    def test_tap_in_a_corner_is_ambiguous_and_dropped(self):
        self.assertIsNone(self._tap(2, 2))
        self.assertIsNone(self._tap(WIDTH - 2, HEIGHT - 2))

    def test_direction_comes_from_start_edge_not_swipe_direction(self):
        # Starts near the LEFT edge but swipes rightward -- edge_gesture
        # only cares where it started, unlike a plain screen-direction swipe.
        t = 0.0
        self.assertIsNone(self.tracker.update((2, MID), t))
        self.assertIsNone(self.tracker.update((100, MID), t + 0.05))
        self.assertEqual(self.tracker.update(None, t + 0.1), rooms.LEFT)

    def test_gesture_starting_mid_screen_ending_near_edge_is_none(self):
        # Started away from any edge; where it ends doesn't count.
        t = 0.0
        self.assertIsNone(self.tracker.update((MID, MID), t))
        self.assertIsNone(self.tracker.update((2, MID), t + 0.05))
        self.assertIsNone(self.tracker.update(None, t + 0.1))

    def test_margin_boundary(self):
        self.assertEqual(self._tap(MARGIN - 1, MID), rooms.LEFT)
        self.assertIsNone(self._tap(MARGIN, MID))

    def test_consecutive_gestures_each_get_their_own_start(self):
        self.assertEqual(self._tap(2, MID, t=0.0), rooms.LEFT)
        self.assertEqual(self._tap(WIDTH - 2, MID, t=1.0), rooms.RIGHT)


if __name__ == "__main__":
    unittest.main()
