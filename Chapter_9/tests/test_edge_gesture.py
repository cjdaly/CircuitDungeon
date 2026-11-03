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

    def test_tap_in_the_middle_is_a_center_tap_not_a_direction(self):
        self.assertIsNone(self._tap(MID, MID))
        self.assertTrue(self.tracker.center_tapped)

    def test_center_tap_only_lasts_one_tick(self):
        self._tap(MID, MID)
        self.tracker.update(None, 1.0)
        self.assertFalse(self.tracker.center_tapped)

    def test_edge_tap_is_not_a_center_tap(self):
        self._tap(2, MID)
        self.assertFalse(self.tracker.center_tapped)

    def test_corner_tap_is_not_a_center_tap(self):
        self.assertIsNone(self._tap(2, 2))
        self.assertFalse(self.tracker.center_tapped)

    def test_swipe_starting_in_the_middle_is_not_a_center_tap(self):
        self.tracker.update((MID, MID), 0.0)
        self.tracker.update((MID + 60, MID), 0.1)
        self.tracker.update(None, 0.15)
        self.assertFalse(self.tracker.center_tapped)

    def test_every_finished_gesture_counts_as_done(self):
        self._tap(MID, MID)
        self.assertTrue(self.tracker.gesture_done)
        self._tap(2, MID, t=1.0)
        self.assertTrue(self.tracker.gesture_done)
        self._tap(2, 2, t=2.0)  # a corner has no direction, but it's still a tap
        self.assertTrue(self.tracker.gesture_done)

    def test_a_swipe_counts_as_done(self):
        self.tracker.update((MID, MID), 0.0)
        self.tracker.update((MID + 60, MID), 0.1)
        self.tracker.update(None, 0.15)
        self.assertTrue(self.tracker.gesture_done)

    def test_gesture_done_only_lasts_one_tick(self):
        self._tap(MID, MID)
        self.tracker.update(None, 1.0)
        self.assertFalse(self.tracker.gesture_done)

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

    def _swipe(self, start, end):
        self.assertIsNone(self.tracker.update(start, 0.0))
        self.assertIsNone(self.tracker.update(end, 0.05))
        return self.tracker.update(None, 0.1)

    def test_a_swipe_drags_the_world_from_the_middle(self):
        self.assertEqual(self._swipe((MID, MID), (MID - 60, MID)), rooms.RIGHT)
        self.assertEqual(self._swipe((MID, MID), (MID + 60, MID)), rooms.LEFT)
        self.assertEqual(self._swipe((MID, MID), (MID, MID - 60)), rooms.DOWN)
        self.assertEqual(self._swipe((MID, MID), (MID, MID + 60)), rooms.UP)

    def test_a_swipe_in_from_an_edge_goes_toward_that_edge(self):
        self.assertEqual(self._swipe((2, MID), (100, MID)), rooms.LEFT)
        self.assertEqual(self._swipe((WIDTH - 2, MID), (WIDTH - 100, MID)), rooms.RIGHT)
        self.assertEqual(self._swipe((MID, 2), (MID, 100)), rooms.UP)
        self.assertEqual(self._swipe((MID, HEIGHT - 2), (MID, HEIGHT - 100)), rooms.DOWN)

    def test_only_the_swipes_direction_counts_not_where_it_started(self):
        self.assertEqual(self._swipe((2, MID), (2, MID + 60)), rooms.UP)
        self.assertEqual(self._swipe((2, 2), (70, 2)), rooms.LEFT)

    def test_margin_boundary(self):
        self.assertEqual(self._tap(MARGIN - 1, MID), rooms.LEFT)
        self.assertIsNone(self._tap(MARGIN, MID))

    def test_consecutive_gestures_each_get_their_own_start(self):
        self.assertEqual(self._tap(2, MID, t=0.0), rooms.LEFT)
        self.assertEqual(self._tap(WIDTH - 2, MID, t=1.0), rooms.RIGHT)


if __name__ == "__main__":
    unittest.main()
