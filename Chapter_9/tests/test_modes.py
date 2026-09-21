# SPDX-License-Identifier: MIT
# Off-device tests for game/modes.py -- pure logic, no hardware needed.
#
#   python3 Chapter_9/tests/test_modes.py

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "game"))

from modes import INTERACTIVE, ORNAMENT, ModeController  # noqa: E402


class TestModeController(unittest.TestCase):
    def test_starts_interactive(self):
        mc = ModeController()
        self.assertEqual(mc.mode, INTERACTIVE)
        self.assertFalse(mc.just_switched)

    def test_stays_interactive_before_timeout(self):
        mc = ModeController(idle_timeout=30.0)
        mc.update(False, True, 0.0)
        self.assertEqual(mc.update(False, True, 29.9), INTERACTIVE)
        self.assertFalse(mc.just_switched)

    def test_goes_ornament_after_idle_and_still(self):
        mc = ModeController(idle_timeout=30.0)
        mc.update(False, True, 0.0)
        self.assertEqual(mc.update(False, True, 30.0), ORNAMENT)
        self.assertTrue(mc.just_switched)

    def test_idle_but_handled_stays_interactive(self):
        # Carried/held but untouched -- must not drop into ornament mode.
        mc = ModeController(idle_timeout=30.0)
        mc.update(False, False, 0.0)
        self.assertEqual(mc.update(False, False, 300.0), INTERACTIVE)

    def test_touch_resets_idle_clock(self):
        mc = ModeController(idle_timeout=30.0)
        mc.update(False, True, 0.0)
        mc.update(True, True, 25.0)
        self.assertEqual(mc.update(False, True, 50.0), INTERACTIVE)
        self.assertEqual(mc.update(False, True, 55.0), ORNAMENT)

    def test_touch_returns_from_ornament_and_flags_switch(self):
        mc = ModeController(idle_timeout=30.0)
        mc.update(False, True, 0.0)
        mc.update(False, True, 30.0)
        self.assertEqual(mc.mode, ORNAMENT)
        self.assertEqual(mc.update(True, True, 31.0), INTERACTIVE)
        self.assertTrue(mc.just_switched)

    def test_just_switched_only_lasts_one_tick(self):
        mc = ModeController(idle_timeout=30.0)
        mc.update(False, True, 0.0)
        mc.update(False, True, 30.0)
        self.assertTrue(mc.just_switched)
        mc.update(False, True, 30.05)
        self.assertFalse(mc.just_switched)

    def test_ornament_ignores_handling(self):
        # Being picked up alone doesn't leave ornament mode -- only touch.
        mc = ModeController(idle_timeout=30.0)
        mc.update(False, True, 0.0)
        mc.update(False, True, 30.0)
        self.assertEqual(mc.update(False, False, 40.0), ORNAMENT)

    def test_ordinary_touch_in_interactive_never_flags_switch(self):
        mc = ModeController()
        mc.update(True, False, 0.0)
        self.assertFalse(mc.just_switched)

    def test_idle_clock_counts_from_first_update_not_construction(self):
        mc = ModeController(idle_timeout=30.0)
        self.assertEqual(mc.update(False, True, 1000.0), INTERACTIVE)
        self.assertEqual(mc.update(False, True, 1029.0), INTERACTIVE)
        self.assertEqual(mc.update(False, True, 1030.0), ORNAMENT)


if __name__ == "__main__":
    unittest.main()
