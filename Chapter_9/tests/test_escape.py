# SPDX-License-Identifier: MIT
# Off-device tests for game/escape.py, the escape cutscene's beats -- cd-342.10.
#
#   python3 Chapter_9/tests/test_escape.py

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "game"))

import escape  # noqa: E402


class TestCutscene(unittest.TestCase):
    def setUp(self):
        self.beats = escape.cutscene()

    def test_it_runs_rattle_to_bolt_in_storyboard_order(self):
        self.assertEqual(
            [beat.shot for beat in self.beats],
            [escape.RATTLE, escape.CLOSEUP, escape.POP, escape.PEEK, escape.NAME, escape.BOLT],
        )

    def test_the_bursts_say_what_happens(self):
        bursts = {beat.shot: beat.burst for beat in self.beats if beat.burst}
        self.assertEqual(bursts, {escape.RATTLE: "Rattle!", escape.POP: "Pop!"})

    def test_it_is_short_and_has_no_words_to_read(self):
        self.assertLess(sum(beat.duration for beat in self.beats), 10.0)
        self.assertFalse(any(beat.caption or beat.speech for beat in self.beats))

    def test_the_close_shots_are_the_cut_in_ones(self):
        self.assertEqual(
            set(escape.CLOSE_SHOTS), {escape.CLOSEUP, escape.POP, escape.PEEK, escape.NAME})

    def test_each_call_makes_fresh_beats(self):
        self.assertIsNot(escape.cutscene()[0], escape.cutscene()[0])


if __name__ == "__main__":
    unittest.main()
