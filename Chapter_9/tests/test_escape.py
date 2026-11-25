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
    """cd-342.49/51: the bolt is a show -- back and forth across the floor, hopping."""

    BOXES = ((40, 160), (72, 152), (104, 164), (136, 152), (168, 160))  # home_view.SLOTS, -8 up
    WAYS = (escape.LEFT, escape.RIGHT, escape.UP, escape.DOWN)
    FLOOR = 162  # the Living Room's plank floor starts here (living_room.bmp at 2x)

    def path(self, start, direction, step=0.02):
        t, out = 0.0, []
        while t <= escape.BOLT_S:
            out.append(escape.bolt_at(start, direction, t))
            t += step
        return out

    def test_it_starts_at_the_box(self):
        for way in self.WAYS:
            x, y, _ux, _uy, leg = escape.bolt_at((40, 160), way, 0.0)
            self.assertEqual((x, y, leg), (40, 160, escape.OUT))

    def test_it_ends_out_of_sight_the_way_it_went(self):
        for start in self.BOXES:
            for way in self.WAYS:
                x, y, _ux, _uy, leg = escape.bolt_at(start, way, escape.BOLT_S)
                with self.subTest(start=start, way=way):
                    self.assertEqual(leg, escape.GONE)
                    cx, cy = x + 16, y + 16
                    self.assertTrue({escape.LEFT: cx < 0, escape.RIGHT: cx > 240,
                                     escape.UP: abs(cx - 120) < 12 and y + 31 <= self.FLOOR,
                                     escape.DOWN: cy > 240}[way])

    def test_it_stays_on_the_floor_but_for_hops(self):
        for start in self.BOXES:
            for way in self.WAYS:
                for x, y, _ux, _uy, leg in self.path(start, way):
                    if leg in (escape.OUT, escape.GONE):
                        continue  # out of the box: one big hop
                    feet = y + 31
                    with self.subTest(start=start, way=way, leg=leg):
                        self.assertGreaterEqual(feet, self.FLOOR - 10)  # a 9px hop at most
                        if not (way == escape.DOWN and leg == escape.DASH):  # forward, off it
                            self.assertLessEqual(feet, 214)

    def test_its_turns_are_on_the_rug_and_on_the_panel(self):
        for start in self.BOXES:
            for way in self.WAYS:
                for x, feet in escape._route(start, way)[1:4]:
                    with self.subTest(start=start, way=way, at=(x, feet)):
                        self.assertGreaterEqual(feet, 190)
                        self.assertLess(math.hypot(x + 16 - 120, feet - 16 - 120), 110)

    def test_it_runs_away_from_its_box_first(self):
        # A box on the side it leaves by still gets a walkabout.
        for way, (sx, sy) in ((escape.LEFT, self.BOXES[0]), (escape.RIGHT, self.BOXES[4])):
            xs = [x for x, _y, _ux, _uy, leg in self.path((sx, sy), way) if leg != escape.GONE]
            with self.subTest(way=way):
                if way == escape.LEFT:
                    self.assertGreater(max(xs), 150)
                else:
                    self.assertLess(min(xs), 60)

    def test_it_goes_back_and_forth(self):
        for start in self.BOXES:
            for way in (escape.LEFT, escape.RIGHT):
                route = escape._route(start, way)
                legs = [route[i + 1][0] - route[i][0] for i in (1, 2, 3)]
                with self.subTest(start=start, way=way):
                    self.assertTrue(legs[0] * legs[1] < 0, route)  # turns round

    def test_it_stands_still_while_it_looks_back(self):
        for way in self.WAYS:
            t0 = sum(leg[0] for leg in escape._LEGS[:escape.PAUSE])
            spots = {escape.bolt_at((104, 164), way, t0 + d)[:2] for d in (0.05, 0.2, 0.4)}
            with self.subTest(way=way):
                self.assertEqual(len(spots), 1)

    def test_its_speed_changes(self):
        path = self.path((72, 152), escape.RIGHT, step=0.05)
        xs = [p[0] for p in path if p[4] not in (escape.PAUSE, escape.GONE)]
        speeds = [abs(b - a) for a, b in zip(xs, xs[1:])]
        moving = [v for v in speeds if v > 0]
        self.assertGreater(max(moving), 3 * min(moving))

    def test_coming_home_is_the_bolt_backwards_ending_on_its_box(self):
        # cd-342.52: in by the way it left, about the rug, up onto its box.
        sit = (72, 136)  # its top-left, sitting on its box
        for way in self.WAYS:
            with self.subTest(way=way):
                self.assertEqual(escape.home_at(sit, way, escape.RUN_S)[:2], sit)
                self.assertEqual(escape.home_at(sit, way, escape.RUN_S + 5)[4], escape.GONE)
                x, y, ux, _uy, leg = escape.home_at(sit, way, 0.05)
                self.assertEqual(leg, escape.DASH)  # coming in fast, by its edge
                # In by the left edge it's heading right, and so on.
                self.assertGreater({escape.LEFT: ux, escape.RIGHT: -ux,
                                    escape.UP: 1, escape.DOWN: 1}[way], 0)
        mid = [escape.home_at(sit, escape.RIGHT, t / 10) for t in range(5, 30)]
        self.assertTrue(all(y + 31 >= self.FLOOR - 10 for _x, y, _ux, _uy, leg in mid
                            if leg != escape.OUT))

    def test_it_is_slow_enough_to_watch(self):
        self.assertGreaterEqual(escape.BOLT_S, 3.0)
        bolt = [b for b in escape.cutscene() if b.shot == escape.BOLT][0]
        self.assertEqual(bolt.duration, escape.BOLT_S)

if __name__ == "__main__":
    unittest.main()
