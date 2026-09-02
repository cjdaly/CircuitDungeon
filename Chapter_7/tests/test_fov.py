# The MIT License (MIT)
#
# Copyright (c) 2026 Chris J Daly (github user cjdaly)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

# Off-device tests for game/fov.py (cd-e3p.6) and world FOV state — pure.
#
#   python3 Chapter_7/tests/test_fov.py

import math
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "game"))

import fov  # noqa: E402
import world as world_mod  # noqa: E402

FLOOR, WALL = 0, 2


def room(w, h, walls=()):
    grid = []
    for y in range(h):
        row = bytearray(FLOOR for _ in range(w))
        for x in range(w):
            if x in (0, w - 1) or y in (0, h - 1) or (x, y) in walls:
                row[x] = WALL
        grid.append(row)
    return world_mod.World(grid, wall_tiles=(WALL,))


def lit_from(ox, oy, blocked, radius=fov.RADIUS):
    seen = set()
    fov.compute(ox, oy, blocked, lambda x, y: seen.add((x, y)), radius=radius)
    return seen


OPEN = lambda x, y: False   # noqa: E731 — infinite empty plane


class OpenField(unittest.TestCase):
    def test_origin_always_lit(self):
        self.assertIn((0, 0), lit_from(0, 0, OPEN))

    def test_disc_shape(self):
        seen = lit_from(0, 0, OPEN, radius=6)
        # everything inside the radius circle is lit, nothing outside it
        for (x, y) in seen:
            self.assertLessEqual(x * x + y * y, 6 * 6 + 6)   # small slop
        self.assertIn((6, 0), seen)
        self.assertIn((0, -6), seen)
        self.assertNotIn((7, 0), seen)
        self.assertNotIn((5, 5), seen)          # 50 > 36

    def test_radius_scales(self):
        self.assertLess(len(lit_from(0, 0, OPEN, radius=3)),
                        len(lit_from(0, 0, OPEN, radius=8)))

    def test_symmetric_in_the_open(self):
        a = lit_from(0, 0, OPEN)
        for (x, y) in a:
            back = lit_from(x, y, OPEN)
            self.assertIn((0, 0), back, "%r sees origin but not vice versa" % ((x, y),))


class Walls(unittest.TestCase):
    def test_wall_casts_a_shadow(self):
        # a 3-tall wall segment at x=2; origin at (0,0) looking +x
        wall = {(2, -1), (2, 0), (2, 1)}
        seen = lit_from(0, 0, lambda x, y: (x, y) in wall)
        self.assertIn((2, 0), seen)             # you see the wall face
        self.assertNotIn((4, 0), seen)          # not the floor behind it
        self.assertNotIn((6, 0), seen)
        self.assertIn((2, 3), seen)             # around the end of the segment

    def test_single_pillar_shadow(self):
        seen = lit_from(0, 0, lambda x, y: (x, y) == (3, 0))
        self.assertIn((3, 0), seen)             # the pillar itself
        self.assertNotIn((6, 0), seen)          # directly behind, in shadow
        self.assertIn((3, 3), seen)             # off to the side, still lit

    def test_a_room_wall_hides_the_next_room(self):
        # a solid vertical wall at x=4 with a one-tile doorway at y=0
        wall = lambda x, y: x == 4 and y != 0   # noqa: E731
        seen = lit_from(0, 0, wall)
        self.assertIn((4, 3), seen)             # wall face is lit
        self.assertNotIn((6, 3), seen)          # the room beyond, behind wall
        self.assertIn((6, 0), seen)             # but straight through the doorway


class WorldFov(unittest.TestCase):
    def _world(self, w=12, h=12, hero=(2, 2), walls=()):
        wd = room(w, h, walls)
        wd.add_actor(world_mod.make_hero(*hero))
        wd.refresh_fov()
        return wd

    def test_hero_tile_is_visible_and_explored(self):
        wd = self._world(hero=(3, 3))
        self.assertTrue(wd.is_visible(3, 3))
        self.assertTrue(wd.is_explored(3, 3))

    def test_out_of_bounds_is_never_visible(self):
        wd = self._world()
        self.assertFalse(wd.is_visible(-1, 5))
        self.assertFalse(wd.is_visible(999, 999))
        self.assertFalse(wd.is_explored(-1, -1))

    def test_a_wall_blocks_sight_of_the_floor_behind_it(self):
        # hero at (2,2); a wall pillar at (2,4) hides (2,6)
        wd = self._world(w=14, h=14, hero=(2, 2), walls={(2, 4)})
        self.assertTrue(wd.is_visible(2, 3))
        self.assertTrue(wd.is_visible(2, 4))        # the wall face
        self.assertFalse(wd.is_visible(2, 6))       # shadowed floor

    def test_bounding_walls_are_lit(self):
        wd = self._world(w=10, h=10, hero=(2, 2))
        self.assertTrue(wd.is_visible(0, 2))        # west wall, in line
        self.assertTrue(wd.is_visible(2, 0))        # north wall

    def test_explored_is_sticky_but_visible_is_not(self):
        wd = self._world(w=40, h=8, hero=(2, 4))
        self.assertTrue(wd.is_visible(2, 4))
        near = (5, 4)
        self.assertTrue(wd.is_visible(*near))

        wd.hero["x"] = 34                            # teleport far away
        wd.refresh_fov()
        self.assertFalse(wd.is_visible(*near))       # out of sight now
        self.assertTrue(wd.is_explored(*near))       # but still remembered
        self.assertTrue(wd.is_visible(34, 4))

    def test_refresh_is_driven_by_a_resolved_turn(self):
        wd = self._world(w=24, h=8, hero=(2, 4))
        sched = world_mod.RoundRobinScheduler(wd)
        far = (15, 4)                                # dx 13 > RADIUS at the start
        self.assertFalse(wd.is_visible(*far))
        for _ in range(6):
            world_mod.resolve_turn(wd, sched, ("move", 1, 0), lambda w, a: None)
        self.assertEqual((wd.hero["x"], wd.hero["y"]), (8, 4))
        self.assertTrue(wd.is_visible(*far))         # dx 7 — walked into view


class Packing(unittest.TestCase):
    def test_mask_size_matches_the_grid(self):
        wd = room(64, 64)
        self.assertEqual(len(wd.visible), (64 * 64 + 7) // 8)   # 512 bytes
        self.assertEqual(len(wd.explored), 512)


if __name__ == "__main__":
    unittest.main()
