# SPDX-License-Identifier: MIT
# Off-device tests for game/stillness.py -- pure logic, no hardware imports.
#
#   python3 Chapter_8/tests/test_stillness.py

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "game"))

import stillness  # noqa: E402

JERK_MAX = stillness.STILL_JERK_MAX
HOLD = stillness.STILL_HOLD
QUIET = JERK_MAX / 2
LOUD = JERK_MAX * 5


class TestStillnessDetector(unittest.TestCase):
    def setUp(self):
        self.detector = stillness.StillnessDetector()

    def test_starts_not_still(self):
        self.assertFalse(self.detector.is_still)

    def test_stays_not_still_before_hold_elapses(self):
        self.detector.update(QUIET, 0.0)
        result = self.detector.update(QUIET, HOLD - 0.01)
        self.assertFalse(result)
        self.assertFalse(self.detector.is_still)

    def test_becomes_still_once_hold_elapses(self):
        self.detector.update(QUIET, 0.0)
        result = self.detector.update(QUIET, HOLD)
        self.assertTrue(result)
        self.assertTrue(self.detector.is_still)

    def test_loud_jerk_resets_the_quiet_window(self):
        self.detector.update(QUIET, 0.0)
        self.detector.update(LOUD, HOLD - 0.01)  # loud right before it would settle
        self.assertFalse(self.detector.is_still)
        # still needs a fresh full hold from here, not just the original window
        result = self.detector.update(QUIET, HOLD + 0.01)
        self.assertFalse(result)

    def test_loud_jerk_ends_an_established_stillness(self):
        self.detector.update(QUIET, 0.0)
        self.detector.update(QUIET, HOLD)
        self.assertTrue(self.detector.is_still)
        self.detector.update(LOUD, HOLD + 0.1)
        self.assertFalse(self.detector.is_still)

    def test_jerk_exactly_at_max_counts_as_quiet(self):
        self.detector.update(JERK_MAX, 0.0)
        result = self.detector.update(JERK_MAX, HOLD)
        self.assertTrue(result)

    def test_custom_thresholds(self):
        detector = stillness.StillnessDetector(jerk_max=1.0, hold=10.0)
        detector.update(0.5, 0.0)
        self.assertFalse(detector.update(0.5, 9.9))
        self.assertTrue(detector.update(0.5, 10.0))


if __name__ == "__main__":
    unittest.main()
