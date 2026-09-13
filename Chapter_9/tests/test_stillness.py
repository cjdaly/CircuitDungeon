# SPDX-License-Identifier: MIT
# Off-device tests for game/stillness.py -- pure logic, no hardware needed.
#
#   python3 Chapter_9/tests/test_stillness.py

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "game"))

from stillness import StillnessDetector  # noqa: E402


class TestStillnessDetector(unittest.TestCase):
    def test_starts_not_still(self):
        detector = StillnessDetector()
        self.assertFalse(detector.is_still)

    def test_stays_handled_below_hold_time(self):
        detector = StillnessDetector(jerk_max=2.0, hold=3.0)
        detector.update(0.5, 0.0)
        result = detector.update(0.5, 2.9)
        self.assertFalse(result)
        self.assertFalse(detector.is_still)

    def test_becomes_still_after_continuous_quiet(self):
        detector = StillnessDetector(jerk_max=2.0, hold=3.0)
        detector.update(0.5, 0.0)
        result = detector.update(0.5, 3.0)
        self.assertTrue(result)
        self.assertTrue(detector.is_still)

    def test_a_jerk_spike_resets_the_quiet_clock(self):
        detector = StillnessDetector(jerk_max=2.0, hold=3.0)
        detector.update(0.5, 0.0)
        detector.update(5.0, 2.0)  # spike -- resets
        result = detector.update(0.5, 2.5)  # only 0.5s quiet since the spike
        self.assertFalse(result)

    def test_still_flips_back_to_handled_on_a_spike(self):
        detector = StillnessDetector(jerk_max=2.0, hold=3.0)
        detector.update(0.5, 0.0)
        detector.update(0.5, 3.0)
        self.assertTrue(detector.is_still)
        result = detector.update(5.0, 3.1)
        self.assertFalse(result)
        self.assertFalse(detector.is_still)

    def test_jerk_exactly_at_max_counts_as_quiet(self):
        detector = StillnessDetector(jerk_max=2.0, hold=3.0)
        detector.update(2.0, 0.0)
        result = detector.update(2.0, 3.0)
        self.assertTrue(result)

    def test_hold_boundary_is_inclusive(self):
        detector = StillnessDetector(jerk_max=2.0, hold=3.0)
        detector.update(0.5, 0.0)
        self.assertTrue(detector.update(0.5, 3.0))


if __name__ == "__main__":
    unittest.main()
