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

# Off-device tests for game/world.py — the pure turn-model core has no
# displayio/board imports, so it runs under plain desktop Python.
#
#   python3 Chapter_7/tests/test_world.py

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "game"))

import world as world_mod  # noqa: E402

FLOOR, WALL = 0, 2


def room(w, h):
    """A w x h room: wall border, floor interior."""
    grid = []
    for y in range(h):
        row = bytearray(FLOOR for _ in range(w))
        for x in range(w):
            if x in (0, w - 1) or y in (0, h - 1):
                row[x] = WALL
        grid.append(row)
    return world_mod.World(grid, wall_tiles=(WALL,))


class WorldQueries(unittest.TestCase):
    def setUp(self):
        self.w = room(5, 5)

    def test_dimensions(self):
        self.assertEqual((self.w.width, self.w.height), (5, 5))

    def test_in_bounds(self):
        self.assertTrue(self.w.in_bounds(0, 0))
        self.assertTrue(self.w.in_bounds(4, 4))
        self.assertFalse(self.w.in_bounds(-1, 0))
        self.assertFalse(self.w.in_bounds(5, 0))

    def test_is_wall_border_and_interior(self):
        self.assertTrue(self.w.is_wall(0, 2))
        self.assertTrue(self.w.is_wall(2, 0))
        self.assertFalse(self.w.is_wall(2, 2))

    def test_out_of_bounds_is_wall(self):
        self.assertTrue(self.w.is_wall(-1, 2))
        self.assertTrue(self.w.is_wall(99, 2))

    def test_actor_at_and_blocking(self):
        mob = self.w.add_actor(world_mod.make_actor(2, 2, "creatures", 1))
        item = self.w.add_actor(world_mod.make_actor(3, 2, "objects", 2, blocks=False))
        self.assertIs(self.w.actor_at(2, 2), mob)
        self.assertIsNone(self.w.actor_at(3, 2))  # non-blocking actor ignored
        self.assertTrue(self.w.blocked(2, 2))
        self.assertFalse(self.w.blocked(3, 2))

    def test_hero_is_actor_zero(self):
        hero = self.w.add_actor(world_mod.make_actor(1, 1, "heroes", 0))
        self.w.add_actor(world_mod.make_actor(2, 2, "creatures", 1))
        self.assertIs(self.w.hero, hero)
        self.assertEqual(len(self.w.monsters()), 1)


class Movement(unittest.TestCase):
    def setUp(self):
        self.w = room(5, 5)
        self.hero = self.w.add_actor(world_mod.make_actor(2, 2, "heroes", 0))

    def test_move_into_floor(self):
        self.assertEqual(self.w.move_actor(self.hero, 1, 0), "moved")
        self.assertEqual((self.hero["x"], self.hero["y"]), (3, 2))

    def test_move_into_wall_is_blocked_and_no_op(self):
        self.hero["x"], self.hero["y"] = 1, 2
        self.assertEqual(self.w.move_actor(self.hero, -1, 0), "blocked")
        self.assertEqual((self.hero["x"], self.hero["y"]), (1, 2))

    def test_move_into_actor_is_bump(self):
        mob = self.w.add_actor(world_mod.make_actor(3, 2, "creatures", 1))
        result = self.w.move_actor(self.hero, 1, 0)
        self.assertEqual(result[0], "bump")
        self.assertIs(result[1], mob)
        self.assertEqual((self.hero["x"], self.hero["y"]), (2, 2))  # didn't move

    def test_diagonal_and_multistep_rejected(self):
        for bad in ((1, 1), (0, 0), (2, 0), (0, -2)):
            with self.assertRaises(ValueError):
                self.w.move_actor(self.hero, *bad)


class Scheduler(unittest.TestCase):
    def test_round_robin_order_is_hero_then_monsters(self):
        w = room(6, 6)
        hero = w.add_actor(world_mod.make_actor(1, 1, "heroes", 0))
        m1 = w.add_actor(world_mod.make_actor(2, 2, "creatures", 1))
        m2 = w.add_actor(world_mod.make_actor(3, 3, "creatures", 2))
        sched = world_mod.RoundRobinScheduler(w)
        self.assertEqual(sched.actors_for_turn(), [hero, m1, m2])

    def test_turn_order_is_a_snapshot(self):
        w = room(6, 6)
        w.add_actor(world_mod.make_actor(1, 1, "heroes", 0))
        doomed = w.add_actor(world_mod.make_actor(2, 2, "creatures", 1))
        sched = world_mod.RoundRobinScheduler(w)
        order = sched.actors_for_turn()
        w.remove_actor(doomed)  # dies mid-turn
        self.assertIn(doomed, order)  # snapshot unaffected
        self.assertEqual(len(w.actors), 1)


if __name__ == "__main__":
    unittest.main()
