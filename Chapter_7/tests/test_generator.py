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

# Off-device tests for game/generator.py (cd-dsc.2). Pure module — plain
# desktop Python. Exercises a spread of seeds so seed-specific breakage shows.
#
#   python3 Chapter_7/tests/test_generator.py

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "game"))

import generator as gen  # noqa: E402

SEEDS = list(range(40))


def _flood(grid, start):
    """Set of tiles reachable from `start` over non-wall tiles, 4-connected."""
    seen = {start}
    stack = [start]
    while stack:
        x, y = stack.pop()
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if (nx, ny) in seen:
                continue
            if 0 <= nx < gen.LEVEL_W and 0 <= ny < gen.LEVEL_H \
                    and grid[ny][nx] != gen.WALL:
                seen.add((nx, ny))
                stack.append((nx, ny))
    return seen


class Shape(unittest.TestCase):
    def test_grid_is_64x64_bytearrays(self):
        grid = gen.generate(1, 1)["grid"]
        self.assertEqual(len(grid), 64)
        for row in grid:
            self.assertIsInstance(row, bytearray)
            self.assertEqual(len(row), 64)

    def test_output_dict_keys_and_types(self):
        lvl = gen.generate(7, 3)
        self.assertEqual(
            set(lvl),
            {"grid", "rooms", "up", "down", "spawn_points", "depth", "seed"},
        )
        self.assertEqual(lvl["depth"], 3)
        self.assertEqual(lvl["seed"], 7)
        self.assertIsInstance(lvl["rooms"], list)
        self.assertEqual(len(lvl["up"]), 2)
        self.assertEqual(len(lvl["down"]), 2)

    def test_border_stays_wall(self):
        for s in SEEDS:
            grid = gen.generate(s, 1)["grid"]
            for x in range(64):
                self.assertEqual(grid[0][x], gen.WALL, (s, "top", x))
                self.assertEqual(grid[63][x], gen.WALL, (s, "bottom", x))
            for y in range(64):
                self.assertEqual(grid[y][0], gen.WALL, (s, "left", y))
                self.assertEqual(grid[y][63], gen.WALL, (s, "right", y))

    def test_only_known_tiles_appear(self):
        allowed = {gen.DIRT, gen.FLAGSTONE, gen.WALL,
                   gen.STAIRS_DOWN, gen.STAIRS_UP}
        grid = gen.generate(3, 1)["grid"]
        seen = {t for row in grid for t in row}
        self.assertTrue(seen <= allowed, seen - allowed)


class Determinism(unittest.TestCase):
    def test_same_seed_and_depth_replays_identically(self):
        a = gen.generate(123, 2)
        b = gen.generate(123, 2)
        self.assertEqual([bytes(r) for r in a["grid"]],
                         [bytes(r) for r in b["grid"]])
        self.assertEqual(a["rooms"], b["rooms"])
        self.assertEqual((a["up"], a["down"]), (b["up"], b["down"]))
        self.assertEqual(a["spawn_points"], b["spawn_points"])

    def test_depth_changes_the_level(self):
        a = gen.generate(123, 1)
        b = gen.generate(123, 2)
        self.assertNotEqual([bytes(r) for r in a["grid"]],
                            [bytes(r) for r in b["grid"]])

    def test_module_rng_path_matches_injected_rng(self):
        import random
        injected = gen.generate(50, 1, rng=random.Random(50 + 1))
        gen.random.seed(999)               # perturb module RNG first
        seeded = gen.generate(50, 1)       # re-seeds to 50+1 internally
        self.assertEqual(injected["rooms"], seeded["rooms"])
        self.assertEqual(injected["spawn_points"], seeded["spawn_points"])


class Rooms(unittest.TestCase):
    def test_at_least_two_rooms(self):
        for s in SEEDS:
            self.assertGreaterEqual(len(gen.generate(s, 1)["rooms"]), 2, s)

    def test_rooms_are_inside_the_border(self):
        for s in SEEDS:
            for (x, y, w, h) in gen.generate(s, 1)["rooms"]:
                self.assertGreaterEqual(x, 1, s)
                self.assertGreaterEqual(y, 1, s)
                self.assertLessEqual(x + w, 63, s)
                self.assertLessEqual(y + h, 63, s)

    def test_sampled_rooms_do_not_touch(self):
        # fallback corner rooms only fire on degenerate seeds; the SEEDS range
        # here always samples enough, so every pair must respect the 1-tile gap
        for s in SEEDS:
            rooms = gen.generate(s, 1)["rooms"]
            for i in range(len(rooms)):
                for j in range(i + 1, len(rooms)):
                    self.assertFalse(
                        gen._overlaps(rooms[i], rooms[j], pad=1),
                        (s, rooms[i], rooms[j]),
                    )


class StairsAndSpawns(unittest.TestCase):
    def test_stairs_on_the_right_tiles_and_distinct(self):
        for s in SEEDS:
            lvl = gen.generate(s, 1)
            ux, uy = lvl["up"]
            dx, dy = lvl["down"]
            self.assertEqual(lvl["grid"][uy][ux], gen.STAIRS_UP, s)
            self.assertEqual(lvl["grid"][dy][dx], gen.STAIRS_DOWN, s)
            self.assertNotEqual(lvl["up"], lvl["down"], s)

    def test_up_stairs_are_in_the_entry_room(self):
        for s in SEEDS:
            lvl = gen.generate(s, 1)
            self.assertTrue(gen._in_room(lvl["up"], lvl["rooms"][0]), s)

    def test_spawn_points_valid(self):
        for s in SEEDS:
            lvl = gen.generate(s, 1)
            grid, entry = lvl["grid"], lvl["rooms"][0]
            self.assertLessEqual(len(lvl["spawn_points"]), gen.SPAWN_POOL)
            self.assertEqual(len(lvl["spawn_points"]), len(set(lvl["spawn_points"])))
            for (x, y) in lvl["spawn_points"]:
                self.assertIn(grid[y][x], (gen.DIRT, gen.FLAGSTONE), (s, x, y))
                self.assertFalse(gen._in_room((x, y), entry), (s, x, y))
                self.assertNotEqual((x, y), lvl["up"])
                self.assertNotEqual((x, y), lvl["down"])

    def test_spawn_pool_is_non_trivial(self):
        # a normal level has plenty of floor outside the entry room
        self.assertGreater(len(gen.generate(11, 1)["spawn_points"]), 10)


class Connectivity(unittest.TestCase):
    def test_every_room_center_reachable_from_the_up_stairs(self):
        # cd-dsc.3: _connect() BFS-repairs any gap the spine + loops left
        for s in SEEDS:
            lvl = gen.generate(s, 1)
            reach = _flood(lvl["grid"], lvl["up"])
            for r in lvl["rooms"]:
                self.assertIn(gen._center(r), reach, (s, r))
            self.assertIn(lvl["down"], reach, s)

    def test_every_floor_tile_is_one_connected_region(self):
        for s in (0, 5, 13, 27, 39):
            grid = gen.generate(s, 1)["grid"]
            floor = [(x, y) for y in range(64) for x in range(64)
                     if grid[y][x] != gen.WALL]
            reach = _flood(grid, floor[0])
            self.assertEqual(len(reach), len(floor), s)

    def test_connect_joins_a_stranded_room(self):
        # two rooms, no corridor between them -> _connect must carve one
        grid = [bytearray([gen.WALL]) * 64 for _ in range(64)]
        rooms = [(3, 3, 6, 6), (50, 50, 6, 6)]
        for r in rooms:
            gen._carve_rect(grid, r, gen.FLAGSTONE)
        import random
        self.assertNotIn(gen._center(rooms[1]),
                         _flood(grid, gen._center(rooms[0])))
        gen._connect(grid, rooms, random.Random(0))
        self.assertIn(gen._center(rooms[1]),
                      _flood(grid, gen._center(rooms[0])))

    def test_down_stairs_sits_at_the_bfs_farthest_room(self):
        for s in SEEDS:
            lvl = gen.generate(s, 1)
            dist = gen._dist_grid(lvl["grid"], lvl["up"])
            room_dists = [gen._dist_at(dist, gen._center(r)) for r in lvl["rooms"]]
            self.assertEqual(gen._dist_at(dist, lvl["down"]), max(room_dists), s)


if __name__ == "__main__":
    unittest.main()
