# SPDX-License-Identifier: MIT
# Off-device tests for game/screen_blanker.py -- pure logic, no hardware
# needed. Uses a fake backlight (just needs a settable .value).
#
#   python3 Chapter_8/tests/test_screen_blanker.py

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "game"))

from screen_blanker import ScreenBlanker  # noqa: E402


class FakeBacklight:
    def __init__(self):
        self.value = True


class TestScreenBlanker(unittest.TestCase):
    def test_starts_lit(self):
        blanker = ScreenBlanker(FakeBacklight(), timeout=10.0)
        self.assertTrue(blanker.lit)

    def test_stays_lit_before_timeout(self):
        backlight = FakeBacklight()
        blanker = ScreenBlanker(backlight, timeout=10.0)
        blanker.update(False, 0.0)
        blanker.update(False, 9.9)
        self.assertTrue(blanker.lit)
        self.assertTrue(backlight.value)

    def test_blanks_after_timeout_with_no_touch(self):
        backlight = FakeBacklight()
        blanker = ScreenBlanker(backlight, timeout=10.0)
        blanker.update(False, 0.0)
        blanker.update(False, 10.0)
        self.assertFalse(blanker.lit)
        self.assertFalse(backlight.value)

    def test_touch_resets_the_idle_clock(self):
        backlight = FakeBacklight()
        blanker = ScreenBlanker(backlight, timeout=10.0)
        blanker.update(False, 0.0)
        blanker.update(True, 9.0)  # touch just before timeout
        blanker.update(False, 18.0)  # 9s since the touch -- still under 10s
        self.assertTrue(blanker.lit)

    def test_touch_wakes_a_blanked_screen(self):
        backlight = FakeBacklight()
        blanker = ScreenBlanker(backlight, timeout=10.0)
        blanker.update(False, 0.0)
        blanker.update(False, 10.0)
        self.assertFalse(blanker.lit)
        woke = blanker.update(True, 12.0)
        self.assertTrue(woke)
        self.assertTrue(blanker.lit)
        self.assertTrue(backlight.value)

    def test_update_while_lit_does_not_report_a_wake(self):
        backlight = FakeBacklight()
        blanker = ScreenBlanker(backlight, timeout=10.0)
        woke = blanker.update(True, 0.0)
        self.assertFalse(woke)
        woke = blanker.update(False, 1.0)
        self.assertFalse(woke)

    def test_idle_clock_starts_from_first_update_not_construction(self):
        backlight = FakeBacklight()
        blanker = ScreenBlanker(backlight, timeout=10.0)
        # First update happens "late" (e.g. slow startup) -- shouldn't count
        # as having already been idle since t=0.
        blanker.update(False, 100.0)
        blanker.update(False, 105.0)
        self.assertTrue(blanker.lit)


if __name__ == "__main__":
    unittest.main()
