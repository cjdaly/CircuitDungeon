# SPDX-License-Identifier: MIT
"""settings.toml, read in one place -- cd-342.47.2 (game/settings.py)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "game"))

import episodes  # noqa: E402
from settings import Settings  # noqa: E402


def _settings(**values):
    return Settings(getenv=values.get)


class TestSettings(unittest.TestCase):
    def test_nothing_set_means_the_defaults(self):
        s = _settings()
        self.assertIsNone(s.player)
        self.assertEqual(s.difficulty, episodes.DEFAULT_DIFFICULTY)
        self.assertIsNone(s.tag_seconds)
        self.assertFalse(s.open_all_rooms or s.finale_now or s.touch_log)

    def test_values_are_read(self):
        s = _settings(PLAYER="Sam", DEVICE_ID="ws-03", DIFFICULTY="hard", TAG_SECONDS="5",
                      OPEN_ALL_ROOMS="1", FINALE_NOW="yes", TOUCH_LOG="true")
        self.assertEqual((s.player, s.device_id), ("Sam", "ws-03"))
        self.assertEqual(s.difficulty, episodes.HARD)
        self.assertEqual(s.tag_seconds, 5.0)
        self.assertTrue(s.open_all_rooms and s.finale_now and s.touch_log)

    def test_a_bad_tag_time_falls_back_and_zero_is_kept(self):
        self.assertIsNone(_settings(TAG_SECONDS="soon").tag_seconds)
        self.assertEqual(_settings(TAG_SECONDS="0").tag_seconds, 0.0)

    def test_a_switch_needs_a_yes(self):
        self.assertFalse(_settings(OPEN_ALL_ROOMS="0").open_all_rooms)


if __name__ == "__main__":
    unittest.main()
