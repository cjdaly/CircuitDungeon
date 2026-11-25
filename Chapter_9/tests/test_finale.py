# SPDX-License-Identifier: MIT
# Off-device tests for game/finale.py: the finale's beats and where the
# critters are while they're loose -- cd-342.6, cd-342.52.
#
#   python3 Chapter_9/tests/test_finale.py

import math
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "game"))

import comic_shapes  # noqa: E402
import finale  # noqa: E402

_FLOOR = 162  # every room's floor or ground starts at or above this (cd-342.51)
_HOP_MAX = 20


def _feet(y):
    return y + 31


class TestOnTheGround(unittest.TestCase):
    """cd-342.52: hopping on the floor, never flying -- that's the reindeer's lap."""

    def test_the_chaos_stays_on_the_floor_but_for_hops(self):
        for i in range(finale.MAX_TOWER):
            for k in range(200):
                x, y, _right = finale.chaos_place(i, k * 0.05)
                with self.subTest(i=i, t=k * 0.05):
                    self.assertGreaterEqual(_feet(y), _FLOOR + 20 - _HOP_MAX)
                    self.assertLessEqual(_feet(y), 212)
                    self.assertTrue(0 <= x + 16 <= 240)

    def test_the_chaos_goes_back_and_forth_hopping(self):
        xs = [finale.chaos_place(0, k * 0.05)[0] for k in range(100)]
        self.assertGreater(max(xs) - min(xs), 120)
        feet = [_feet(finale.chaos_place(0, k * 0.02)[1]) for k in range(100)]
        self.assertGreater(max(feet) - min(feet), 8)  # hops

    def test_the_parade_stands_on_the_floor_clear_of_the_item_in_hand(self):
        for i in range(finale.MAX_TOWER):
            x, y = finale.parade_place(i)
            with self.subTest(i=i):
                self.assertGreaterEqual(_feet(y), 186)
                self.assertGreaterEqual(x, 88)  # the held item is bottom left, to x 84
                self.assertLess(math.hypot(x + 16 - 120, y + 16 - 120), 104)

    def test_the_parade_wanders_and_hops(self):
        for i in range(finale.MAX_TOWER):
            path = [finale.parade_at(i, k * 0.05) for k in range(120)]
            xs = [p[0] for p in path]
            feet = [_feet(p[1]) for p in path]
            home = _feet(finale.parade_place(i)[1])
            with self.subTest(i=i):
                self.assertGreater(max(xs) - min(xs), 20)
                self.assertGreaterEqual(min(xs), 88)
                self.assertEqual(max(feet), home)  # back down on the floor between hops
                self.assertGreater(home - min(feet), 4)
                self.assertLessEqual(home - min(feet), 10)


class TestHup(unittest.TestCase):
    def test_hup_is_beside_the_tower_not_over_it(self):
        sys.path.insert(0, os.path.dirname(__file__))
        import test_hunt  # the title font's real widths
        width = test_hunt._px("HUP!", test_hunt._TITLE)
        hups = [b for b in finale.tower(3) if b.burst]
        self.assertEqual(len(hups), 3)
        for beat in hups:
            x, y = beat.burst_at
            self.assertLess(x + width // 2, 104)  # the word clears the tower (x 104 on)
            rx, ry = comic_shapes.burst_radii(width)
            points = comic_shapes.burst_points(x, y, rx, ry, grow=3)
            self.assertLessEqual(max(px for px, _py in points), 104 + 16)  # spike tips only
            self.assertTrue(all(math.hypot(px - 120, py - 120) <= 120 for px, py in points))


if __name__ == "__main__":
    unittest.main()
