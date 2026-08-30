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

# Off-device tests for the turn loop (bead cd-e3p.3): world.resolve_turn and
# the modes.py input-event -> action mapping. Both are displayio-free.
#
#   python3 Chapter_7/tests/test_turn.py

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "game"))

import world as world_mod  # noqa: E402
import modes  # noqa: E402
import input as im  # noqa: E402

FLOOR, WALL = 0, 2


def room(w, h):
    grid = []
    for y in range(h):
        row = bytearray(FLOOR for _ in range(w))
        for x in range(w):
            if x in (0, w - 1) or y in (0, h - 1):
                row[x] = WALL
        grid.append(row)
    return world_mod.World(grid, wall_tiles=(WALL,))


class ResolveTurn(unittest.TestCase):
    def setUp(self):
        self.w = room(7, 7)
        self.hero = self.w.add_actor(world_mod.make_actor(3, 3, "heroes", 0))
        self.sched = world_mod.RoundRobinScheduler(self.w)
        self.acted = []
        self.monster_turn = lambda world, a: self.acted.append(a)

    def run_turn(self, action):
        return world_mod.resolve_turn(self.w, self.sched, action, self.monster_turn)

    def test_move_spends_a_turn_and_runs_monsters(self):
        m1 = self.w.add_actor(world_mod.make_actor(5, 5, "creatures", 1))
        m2 = self.w.add_actor(world_mod.make_actor(1, 1, "creatures", 2))
        spent = self.run_turn(("move", 1, 0))
        self.assertTrue(spent)
        self.assertEqual((self.hero["x"], self.hero["y"]), (4, 3))
        self.assertEqual(self.w.turn, 1)
        self.assertEqual(self.acted, [m1, m2])         # both monsters, not the hero

    def test_move_into_wall_is_free(self):
        self.hero["x"], self.hero["y"] = 1, 3
        spent = self.run_turn(("move", -1, 0))
        self.assertFalse(spent)
        self.assertEqual((self.hero["x"], self.hero["y"]), (1, 3))
        self.assertEqual(self.w.turn, 0)
        self.assertEqual(self.acted, [])              # monsters did not move

    def test_bump_actor_is_free_for_now(self):
        self.w.add_actor(world_mod.make_actor(4, 3, "creatures", 1))
        spent = self.run_turn(("move", 1, 0))
        self.assertFalse(spent)                       # TODO cd-e3p.5: attack -> True
        self.assertEqual((self.hero["x"], self.hero["y"]), (3, 3))
        self.assertEqual(self.w.turn, 0)

    def test_none_action_is_free(self):
        self.assertFalse(self.run_turn(None))
        self.assertEqual(self.w.turn, 0)

    def test_wait_spends_a_turn(self):
        self.w.add_actor(world_mod.make_actor(5, 5, "creatures", 1))
        self.assertTrue(self.run_turn(("wait",)))
        self.assertEqual(self.w.turn, 1)
        self.assertEqual(len(self.acted), 1)

    def test_turn_counter_accumulates(self):
        # hero at (3,3) in a 7x7 room; walls at y=6. Two steps down are legal,
        # the third bumps the wall and is free.
        for _ in range(3):
            self.run_turn(("move", 0, 1))
        self.assertEqual((self.hero["x"], self.hero["y"]), (3, 5))
        self.assertEqual(self.w.turn, 2)


class EventToAction(unittest.TestCase):
    def test_move_events_map_to_deltas(self):
        self.assertEqual(modes._first_action([im.MOVE_N]), ("move", 0, -1))
        self.assertEqual(modes._first_action([im.MOVE_S]), ("move", 0, 1))
        self.assertEqual(modes._first_action([im.MOVE_W]), ("move", -1, 0))
        self.assertEqual(modes._first_action([im.MOVE_E]), ("move", 1, 0))

    def test_wait_event_maps_to_wait_action(self):
        self.assertEqual(modes._first_action(["wait"]), ("wait",))

    def test_non_action_events_yield_none(self):
        self.assertIsNone(modes._first_action([im.CONFIRM, im.CANCEL, im.AUX_X]))
        self.assertIsNone(modes._first_action([]))

    def test_first_action_wins_rest_dropped(self):
        self.assertEqual(
            modes._first_action([im.CONFIRM, im.MOVE_E, im.MOVE_N]), ("move", 1, 0)
        )


if __name__ == "__main__":
    unittest.main()
