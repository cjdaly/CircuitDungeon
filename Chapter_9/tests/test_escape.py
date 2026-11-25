# SPDX-License-Identifier: MIT
# Off-device tests for game/escape.py, the escape cutscene's beats -- cd-342.10.
#
#   python3 Chapter_9/tests/test_escape.py

import math
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
        # The bolt is a show now (cd-342.49), but every beat can be tapped past.
        self.assertLess(sum(beat.duration for beat in self.beats), 12.0)
        self.assertFalse(any(beat.caption or beat.speech for beat in self.beats))

    def test_the_close_shots_are_the_cut_in_ones(self):
        self.assertEqual(
            set(escape.CLOSE_SHOTS), {escape.CLOSEUP, escape.POP, escape.PEEK, escape.NAME})

    def test_each_call_makes_fresh_beats(self):
        self.assertIsNot(escape.cutscene()[0], escape.cutscene()[0])


class TestBolt(unittest.TestCase):
    """cd-342.49: the bolt is a show -- a Z around the room, not a straight dash."""

    BOXES = ((40, 160), (72, 152), (104, 164), (136, 152), (168, 160))  # home_view.SLOTS, -8 up
    WAYS = (escape.LEFT, escape.RIGHT, escape.UP, escape.DOWN)

    def path(self, start, direction, step=0.05):
        t, out = 0.0, []
        while t <= escape.BOLT_S:
            out.append(escape.bolt_at(start, direction, t))
            t += step
        return out

    def test_it_starts_at_the_box(self):
        for way in self.WAYS:
            x, y, _ux, _uy, leg = escape.bolt_at((40, 160), way, 0.0)
            self.assertEqual((x, y, leg), (40, 160, 0))

    def test_it_ends_off_the_panel_past_its_exit(self):
        for way in self.WAYS:
            x, y, _ux, _uy, leg = escape.bolt_at((104, 164), way, escape.BOLT_S)
            with self.subTest(way=way):
                self.assertEqual(leg, escape.DASH)
                cx, cy = x + 16, y + 16
                self.assertGreater(abs(cx - 120) + abs(cy - 120), 150)
                self.assertTrue({escape.LEFT: cx < 0, escape.RIGHT: cx > 240,
                                 escape.UP: cy < 0, escape.DOWN: cy > 240}[way])

    def test_its_turns_are_on_the_panel(self):
        for way, route in escape._ROUTES.items():
            for x, y in route[:-1]:
                with self.subTest(way=way, at=(x, y)):
                    self.assertLess(math.hypot(x + 16 - 120, y + 16 - 120), 100)

    def test_it_runs_away_from_its_exit_first(self):
        # A box on the side it leaves by still gets a walkabout.
        for way, (sx, sy) in ((escape.LEFT, self.BOXES[0]), (escape.RIGHT, self.BOXES[4])):
            xs = [x for x, _y, _ux, _uy, _leg in self.path((sx, sy), way)]
            with self.subTest(way=way):
                if way == escape.LEFT:
                    self.assertGreater(max(xs), 150)
                else:
                    self.assertLess(min(xs), 60)

    def test_it_stays_on_screen_while_it_looks_back(self):
        for way in self.WAYS:
            t = sum(seconds for seconds, _e in escape._LEGS[:escape.PAUSE]) + 0.2
            x, y, ux, _uy, leg = escape.bolt_at((104, 164), way, t)
            with self.subTest(way=way):
                self.assertEqual(leg, escape.PAUSE)
                self.assertEqual((x, y), escape._ROUTES[way][2])

    def test_its_speed_changes(self):
        path = self.path((104, 164), escape.RIGHT, step=0.05)
        speeds = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(path, path[1:])
                  if b[4] != escape.DASH or a[4] != escape.DASH or b[0] < 240]
        moving = [v for v in speeds if v > 0]
        self.assertGreater(max(moving), 3 * min(moving))
        self.assertIn(0.0, speeds)  # it stops to look back

    def test_it_is_slow_enough_to_watch(self):
        self.assertGreaterEqual(escape.BOLT_S, 3.0)
        bolt = [b for b in escape.cutscene() if b.shot == escape.BOLT][0]
        self.assertEqual(bolt.duration, escape.BOLT_S)


if __name__ == "__main__":
    unittest.main()
