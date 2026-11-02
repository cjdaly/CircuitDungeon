# SPDX-License-Identifier: MIT
# Off-device tests for ornament.Snow's motion, with vectorio/displayio stubbed.
#
#   python3 Chapter_9/tests/test_ornament.py

import os
import sys
import types
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "game"))

import ornament  # noqa: E402


class _Circle:
    def __init__(self, **kw):
        self.__dict__.update(kw)


class TestSnow(unittest.TestCase):
    def setUp(self):
        vectorio = types.ModuleType("vectorio")
        vectorio.Circle = _Circle
        displayio = types.ModuleType("displayio")
        displayio.Palette = lambda n: {}
        patcher = mock.patch.dict(
            sys.modules, {"vectorio": vectorio, "displayio": displayio}
        )
        patcher.start()
        self.addCleanup(patcher.stop)

        self.flakes = []
        self.snow = ornament.Snow(self.flakes, 240, 240)
        for i, flake in enumerate(self.flakes):
            flake.y = 10 + i * 30  # distinct, known heights

    def _heights(self):
        return [flake.y for flake in self.flakes]

    def test_flakes_fall_at_snow_speed(self):
        start = self._heights()
        self.snow.update(0.0)
        self.snow.update(1.0 / 11)  # 22 px/s for 1/11 s = 2 px
        self.assertEqual(
            self._heights(), [int(y + ornament._SNOW_SPEED / 11) for y in start]
        )

    def test_flake_past_the_bottom_wraps_to_the_top(self):
        self.flakes[0].y = 240
        self.snow.update(0.0)
        self.snow.update(0.1)
        self.assertEqual(self.flakes[0].y, 0)

    def test_long_gap_does_not_collapse_flakes_into_one_row(self):
        # Snow only updates in ornament mode, so returning to that mode after
        # playing looks like a huge time step.
        self.snow.update(0.0)
        self.snow.update(60.0)
        heights = self._heights()
        self.assertEqual(len(set(heights)), len(heights), heights)

    def test_long_gap_moves_flakes_no_further_than_a_short_stall(self):
        start = self._heights()
        self.snow.update(0.0)
        self.snow.update(60.0)
        limit = ornament._SNOW_SPEED * ornament._SNOW_MAX_DT
        for before, after in zip(start, self._heights()):
            self.assertLessEqual(after - before, limit)
            self.assertGreaterEqual(after, before)


class TestOrnamentRandomness(unittest.TestCase):
    def test_positions_stay_inside_the_tree(self):
        apex_x, apex_y = ornament._APEX
        half_base = ornament._BASE_R[0] - apex_x
        height = ornament._BASE_R[1] - apex_y
        for _ in range(200):
            for x, y in ornament._scatter_positions():
                edge = (y - apex_y) * half_base / height
                self.assertLessEqual(abs(x - apex_x) + ornament._ORNAMENT_RADIUS, edge)
                self.assertLessEqual(y + ornament._ORNAMENT_RADIUS, ornament._BASE_R[1])

    def test_ornaments_never_overlap(self):
        touching2 = (2 * ornament._ORNAMENT_RADIUS) ** 2
        for _ in range(500):
            points = ornament._scatter_positions()
            for i, (x1, y1) in enumerate(points):
                for x2, y2 in points[i + 1:]:
                    self.assertGreater((x1 - x2) ** 2 + (y1 - y2) ** 2, touching2)

    def test_layouts_vary(self):
        layouts = {tuple(ornament._scatter_positions()) for _ in range(20)}
        self.assertGreater(len(layouts), 15)

    def test_next_color_always_changes_and_reaches_every_other_color(self):
        count = len(ornament._ORNAMENT_COLORS)
        for current in range(count):
            seen = {ornament._next_color_index(current) for _ in range(200)}
            self.assertEqual(seen, set(range(count)) - {current})


class TestStar(unittest.TestCase):
    def setUp(self):
        self.points = ornament._star_points((120, 58), 13, 5)

    def test_has_five_tips_and_five_notches(self):
        self.assertEqual(len(self.points), 10)
        self.assertEqual(len(set(self.points)), 10)

    def test_first_tip_points_straight_up(self):
        self.assertEqual(self.points[0], (120, 45))

    def test_is_left_right_symmetric(self):
        mirrored = {(240 - x, y) for x, y in self.points}
        self.assertEqual(mirrored, set(self.points))

    def test_tips_are_further_out_than_notches(self):
        def dist(p):
            return ((p[0] - 120) ** 2 + (p[1] - 58) ** 2) ** 0.5

        tips, notches = self.points[0::2], self.points[1::2]
        self.assertGreater(min(dist(p) for p in tips), max(dist(p) for p in notches))

    def test_stays_on_the_round_screen(self):
        for x, y in self.points:
            self.assertLess(((x - 120) ** 2 + (y - 120) ** 2) ** 0.5, 95)


if __name__ == "__main__":
    unittest.main()
