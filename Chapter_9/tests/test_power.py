# SPDX-License-Identifier: MIT
# Off-device tests for game/power.py -- pure logic, no hardware needed.
#
#   python3 Chapter_9/tests/test_power.py

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "game"))

from power import DeepIdle  # noqa: E402

REST = (0.0, -0.3, -10.2)
TILTED = (3.0, -0.3, -10.2)


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

    def test_wakes_after_reads_in_a_row_away_from_rest(self):
        idle = DeepIdle(wake_shift=2.0, wake_reads=2)
        idle.enter()
        self.assertFalse(idle.should_wake(REST))  # the resting reading
        self.assertFalse(idle.should_wake((0.1, -0.3, -10.3)))  # noise
        self.assertFalse(idle.should_wake(TILTED))
        self.assertTrue(idle.should_wake(TILTED))

    def test_a_single_bump_does_not_wake_it(self):
        idle = DeepIdle(wake_shift=2.0, wake_reads=2)
        idle.enter()
        idle.should_wake(REST)
        for _ in range(20):
            self.assertFalse(idle.should_wake((3.0, 4.0, -6.0)))  # one odd read
            self.assertFalse(idle.should_wake(REST))

    def test_rest_is_taken_fresh_each_sleep(self):
        idle = DeepIdle(wake_shift=2.0, wake_reads=2)
        idle.enter()
        idle.should_wake(REST)
        idle.wake()
        idle.enter()  # set down tilted this time
        self.assertFalse(idle.should_wake(TILTED))
        self.assertFalse(idle.should_wake(TILTED))
        self.assertFalse(idle.should_wake(TILTED))

    def test_shift_reports_the_move_from_rest(self):
        idle = DeepIdle()
        idle.enter()
        idle.should_wake(REST)
        idle.should_wake(TILTED)
        self.assertAlmostEqual(idle.shift, 3.0)

    def test_waking_restarts_the_delay(self):
        idle = DeepIdle(enter_delay=10.0)
        idle.should_enter(False, True, 0.0)
        idle.enter()
        self.assertTrue(idle.asleep)
        idle.wake()
        self.assertFalse(idle.asleep)
        self.assertFalse(idle.should_enter(False, True, 15.0))



class TestGlance(unittest.TestCase):
    def test_a_motion_wake_starts_a_glance(self):
        idle = DeepIdle()
        self.assertFalse(idle.glance)
        idle.enter()
        idle.wake()
        self.assertTrue(idle.glancing(True, False, 0.05))

    def test_a_bump_that_settles_stays_a_glance(self):
        idle = DeepIdle(glance_handled=6.0)
        idle.wake()
        for _ in range(60):  # 3 s handled, then still
            idle.glancing(False, False, 0.05)
        for _ in range(200):
            self.assertTrue(idle.glancing(True, False, 0.05))

    def test_handling_it_ends_the_glance(self):
        idle = DeepIdle(glance_handled=6.0)
        idle.wake()
        for _ in range(119):
            self.assertTrue(idle.glancing(False, False, 0.05))
        self.assertFalse(idle.glancing(False, False, 0.06))

    def test_a_touch_ends_the_glance(self):
        idle = DeepIdle()
        idle.wake()
        self.assertFalse(idle.glancing(True, True, 0.05))

    def test_a_non_motion_wake_is_no_glance(self):
        idle = DeepIdle()
        idle.wake(glance=False)
        self.assertFalse(idle.glancing(True, False, 0.05))


if __name__ == "__main__":
    unittest.main()
