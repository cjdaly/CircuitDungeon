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

# Off-device tests for the depth-scaled monster/item spawn tables (cd-dsc.4).
#
#   python3 Chapter_7/tests/test_spawns.py

import os
import random
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "game"))

import spawns  # noqa: E402
import world as world_mod  # noqa: E402

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


def points(n):
    return [(2 + i % 10, 2 + i // 10) for i in range(n)]


class Populate(unittest.TestCase):
    def test_no_spawn_points_places_nothing(self):
        w = room(20, 20)
        spawns.populate(w, [], depth=1, rng=random.Random(1))
        self.assertEqual(w.actors, [])

    def test_places_monsters_up_to_the_depth_scaled_count(self):
        w = room(20, 20)
        spawns.populate(w, points(20), depth=1, rng=random.Random(1))
        monsters = [a for a in w.actors if "hp" in a]
        self.assertEqual(len(monsters), spawns.MONSTER_BASE)  # depth 1 -> base count

    def test_monster_count_scales_with_depth_up_to_the_cap(self):
        w = room(20, 20)
        spawns.populate(w, points(20), depth=10, rng=random.Random(1))
        monsters = [a for a in w.actors if "hp" in a]
        self.assertEqual(len(monsters), spawns.MONSTER_CAP)

    def test_monster_count_is_capped_by_available_points(self):
        w = room(20, 20)
        spawns.populate(w, points(1), depth=10, rng=random.Random(1))
        # 1 point total; monsters take it before the item loop gets a look
        self.assertEqual(len(w.actors), 1)

    def test_places_one_sword_and_one_armor_when_points_allow(self):
        w = room(20, 20)
        spawns.populate(w, points(20), depth=1, rng=random.Random(1))
        weapons = [a for a in w.actors if a.get("kind") == "weapon"]
        armors = [a for a in w.actors if a.get("kind") == "armor"]
        self.assertEqual(len(weapons), 1)
        self.assertEqual(len(armors), 1)

    def test_places_gold_piles_up_to_the_configured_count(self):
        w = room(20, 20)
        spawns.populate(w, points(20), depth=1, rng=random.Random(1))
        piles = [a for a in w.actors if a.get("kind") == "gold"]
        self.assertEqual(len(piles), spawns.GOLD_PILES)

    def test_gold_amount_is_within_the_depth_scaled_range(self):
        w = room(20, 20)
        spawns.populate(w, points(20), depth=3, rng=random.Random(1))
        for a in w.actors:
            if a.get("kind") == "gold":
                self.assertGreaterEqual(a["amount"], spawns.GOLD_MIN * 3)
                self.assertLessEqual(a["amount"], spawns.GOLD_MAX * 3)

    def test_gold_pile_count_is_capped_by_available_points(self):
        w = room(20, 20)
        # depth 1: 2 monsters + 1 sword + 1 armor eat 4 of these 5 points,
        # leaving only 1 for gold even though GOLD_PILES asks for 2.
        spawns.populate(w, points(5), depth=1, rng=random.Random(1))
        piles = [a for a in w.actors if a.get("kind") == "gold"]
        self.assertEqual(len(piles), 1)

    def test_item_levels_are_near_depth(self):
        w = room(20, 20)
        spawns.populate(w, points(20), depth=5, rng=random.Random(1))
        for a in w.actors:
            if a.get("kind") in ("weapon", "armor"):
                self.assertGreaterEqual(a["level"], 1)
                self.assertLessEqual(abs(a["level"] - 5), spawns.ITEM_LEVEL_JITTER)

    def test_item_level_never_drops_below_one(self):
        w = room(20, 20)
        # depth 1 with max-negative jitter would go to -1 without the floor
        spawns.populate(w, points(20), depth=1, rng=random.Random(7))
        for a in w.actors:
            if a.get("kind") in ("weapon", "armor"):
                self.assertGreaterEqual(a["level"], 1)

    def test_no_monster_or_item_placed_on_the_same_point_twice(self):
        w = room(20, 20)
        spawns.populate(w, points(8), depth=10, rng=random.Random(1))
        positions = [(a["x"], a["y"]) for a in w.actors]
        self.assertEqual(len(positions), len(set(positions)))

    def test_deterministic_given_the_same_rng_seed(self):
        w1 = room(20, 20)
        w2 = room(20, 20)
        spawns.populate(w1, points(20), depth=3, rng=random.Random(42))
        spawns.populate(w2, points(20), depth=3, rng=random.Random(42))
        snap = lambda w: [(a["x"], a["y"], a.get("name")) for a in w.actors]
        self.assertEqual(snap(w1), snap(w2))

    def test_only_eligible_monsters_for_the_depth_appear(self):
        w = room(20, 20)
        spawns.populate(w, points(20), depth=1, rng=random.Random(3))
        names = {a["name"] for a in w.actors if "hp" in a}
        eligible = {m[0] for m in spawns._eligible_monsters(1)}
        self.assertTrue(names <= eligible)


if __name__ == "__main__":
    unittest.main()
