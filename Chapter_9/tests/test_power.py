# SPDX-License-Identifier: MIT
# Off-device tests for game/power.py -- pure logic, no hardware needed.
#
#   python3 Chapter_9/tests/test_power.py

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "game"))

from power import DeepIdle  # noqa: E402


class TestDeepIdle(unittest.TestCase):
    def test_not_while_lit(self):
        idle = DeepIdle(enter_delay=10.0)
        self.assertFalse(idle.should_enter(True, True, 0.0))
        self.assertFalse(idle.should_enter(True, True, 100.0))

    def test_not_while_handled(self):
        idle = DeepIdle(enter_delay=10.0)
        self.assertFalse(idle.should_enter(False, False, 0.0))
        self.assertFalse(idle.should_enter(False, False, 100.0))

    def test_after_dark_and_still_for_the_delay(self):
        idle = DeepIdle(enter_delay=10.0)
        self.assertFalse(idle.should_enter(False, True, 0.0))
        self.assertFalse(idle.should_enter(False, True, 9.9))
        self.assertTrue(idle.should_enter(False, True, 10.0))

    def test_any_motion_restarts_the_delay(self):
        idle = DeepIdle(enter_delay=10.0)
        idle.should_enter(False, True, 0.0)
        idle.should_enter(False, False, 8.0)
        self.assertFalse(idle.should_enter(False, True, 12.0))
        self.assertTrue(idle.should_enter(False, True, 22.0))

    def test_wakes_only_above_the_jerk_threshold(self):
        idle = DeepIdle(wake_jerk=1.0)
        self.assertFalse(idle.should_wake(0.15))
        self.assertFalse(idle.should_wake(1.0))
        self.assertTrue(idle.should_wake(1.5))

    def test_waking_restarts_the_delay(self):
        idle = DeepIdle(enter_delay=10.0)
        idle.should_enter(False, True, 0.0)
        idle.enter()
        self.assertTrue(idle.asleep)
        idle.wake()
        self.assertFalse(idle.asleep)
        self.assertFalse(idle.should_enter(False, True, 15.0))


if __name__ == "__main__":
    unittest.main()
