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

# Off-device tests for game/ai.py (cd-e3p.4) and world.los_clear — pure.
#
#   python3 Chapter_7/tests/test_ai.py

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "game"))

import world as world_mod  # noqa: E402
import ai  # noqa: E402

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


class LineOfSight(unittest.TestCase):
    def test_clear_line(self):
        w = room(10, 10)
        self.assertTrue(world_mod.los_clear(w, 1, 1, 8, 1))
        self.assertTrue(world_mod.los_clear(w, 1, 1, 8, 8))

    def test_wall_blocks(self):
        w = room(10, 10, walls=[(4, 1)])
        self.assertFalse(world_mod.los_clear(w, 1, 1, 8, 1))

    def test_adjacent_always_visible(self):
        w = room(10, 10, walls=[(5, 5)])
        self.assertTrue(world_mod.los_clear(w, 4, 5, 5, 5))  # endpoint wall ignored

    def test_endpoints_excluded(self):
        # a wall on the monster's OWN tile doesn't blind it
        w = room(10, 10, walls=[(1, 1)])
        self.assertTrue(world_mod.los_clear(w, 1, 1, 5, 1))


class Wake(unittest.TestCase):
    def setUp(self):
        ai.WANDER_CHANCE = 0.0
        self.w = room(30, 10)
        self.hero = self.w.add_actor(world_mod.make_actor(3, 3, "heroes", 0))

    def mob(self, x, y):
        return self.w.add_actor(world_mod.make_actor(x, y, "creatures", 1, ai="sleep"))

    def test_wakes_on_line_of_sight_in_range(self):
        m = self.mob(9, 3)  # 6 tiles away, clear
        ai.take_turn(self.w, m)
        self.assertEqual(m["ai"], "hunt")
        self.assertEqual(m["goal"], (3, 3))

    def test_stays_asleep_beyond_sight(self):
        m = self.mob(3 + ai.SIGHT + 2, 3)
        ai.take_turn(self.w, m)
        self.assertEqual(m["ai"], "sleep")

    def test_stays_asleep_behind_a_wall(self):
        self.w.grid[3][6] = WALL
        m = self.mob(9, 3)
        ai.take_turn(self.w, m)
        self.assertEqual(m["ai"], "sleep")

    def test_idle_monster_holds_position_with_wander_off(self):
        m = self.mob(20, 3)          # out of sight
        for _ in range(10):
            ai.take_turn(self.w, m)
        self.assertEqual((m["x"], m["y"]), (20, 3))


class Hunt(unittest.TestCase):
    def setUp(self):
        ai.WANDER_CHANCE = 0.0
        self.w = room(30, 12)
        self.hero = self.w.add_actor(world_mod.make_actor(3, 5, "heroes", 0))

    def hunter(self, x, y, goal=None):
        m = self.w.add_actor(world_mod.make_actor(x, y, "creatures", 1, ai="hunt"))
        m["goal"] = goal if goal is not None else (self.hero["x"], self.hero["y"])
        return m

    def _dist(self, a):
        return abs(a["x"] - self.hero["x"]) + abs(a["y"] - self.hero["y"])

    def test_steps_closer_each_turn(self):
        m = self.hunter(12, 9)
        d0 = self._dist(m)
        for _ in range(3):
            ai.take_turn(self.w, m)
            d1 = self._dist(m)
            self.assertLess(d1, d0)
            d0 = d1

    def test_refreshes_goal_while_it_can_see_the_hero(self):
        m = self.hunter(9, 5)
        self.hero["x"] = 5           # hero moved; monster still has LoS
        ai.take_turn(self.w, m)
        self.assertEqual(m["goal"], (5, 5))

    def test_gives_up_at_last_known_tile(self):
        # goal is a spot with no hero and no LoS to the real hero
        self.w.grid[5][15] = WALL    # blocks LoS from (16,5) back to the hero
        m = self.hunter(16, 5, goal=(16, 5))
        ai.take_turn(self.w, m)
        self.assertEqual(m["ai"], "sleep")
        self.assertIsNone(m["goal"])

    def test_does_not_step_onto_the_hero(self):
        m = self.hunter(4, 5)        # directly east-adjacent to hero at (3,5)
        ai.take_turn(self.w, m)
        self.assertEqual((m["x"], m["y"]), (4, 5))   # bump, no move
        self.assertEqual(self.hero["x"], 3)          # hero untouched

    def test_falls_back_to_the_other_axis_when_blocked(self):
        # hero at (3,5); hunter at (6,7). prefers x (dx=3 > dy=2); wall due west
        self.w.grid[7][5] = WALL
        m = self.hunter(6, 7)
        ai.take_turn(self.w, m)
        self.assertEqual((m["x"], m["y"]), (6, 6))   # stepped north instead


if __name__ == "__main__":
    unittest.main()
