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

# Off-device tests for world.resolve_attack + the bump→attack wiring (cd-e3p.5).
#
#   python3 Chapter_7/tests/test_combat.py

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "game"))

import world as world_mod  # noqa: E402
import ai  # noqa: E402

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


def mob(w, x, y, **stats):
    s = {"name": "rat", "hp": 5, "power": 2, "defense": 0, "xp": 2}
    s.update(stats)
    return w.add_actor(world_mod.make_actor(x, y, "creatures", 1, **s))


class Attack(unittest.TestCase):
    def setUp(self):
        self.w = room(8, 8)
        self.hero = self.w.add_actor(world_mod.make_hero(3, 3, power=4, defense=1))

    def test_damage_is_power_minus_defense(self):
        m = mob(self.w, 4, 3, hp=10, defense=1)
        world_mod.resolve_attack(self.w, self.hero, m)
        self.assertEqual(m["hp"], 10 - (4 - 1))

    def test_damage_floors_at_one(self):
        m = mob(self.w, 4, 3, hp=10, defense=99)
        world_mod.resolve_attack(self.w, self.hero, m)
        self.assertEqual(m["hp"], 9)

    def test_killing_a_monster_leaves_a_corpse_and_awards_xp(self):
        m = mob(self.w, 4, 3, hp=2, xp=7)
        world_mod.resolve_attack(self.w, self.hero, m)
        self.assertNotIn(m, self.w.actors)
        corpses = [a for a in self.w.actors if a["sheet"] == "objects"]
        self.assertEqual(len(corpses), 1)
        self.assertEqual((corpses[0]["x"], corpses[0]["y"]), (4, 3))
        self.assertFalse(corpses[0]["blocks"])
        self.assertEqual(corpses[0]["tile"], world_mod.CORPSE_TILE)
        self.assertEqual(self.hero["xp"], 7)

    def test_dead_hero_stays_at_actors_zero_no_corpse(self):
        rat = mob(self.w, 4, 3, power=50)
        world_mod.resolve_attack(self.w, rat, self.hero)
        self.assertLessEqual(self.hero["hp"], 0)
        self.assertIs(self.w.actors[0], self.hero)
        self.assertFalse(any(a["sheet"] == "objects" for a in self.w.actors))
        self.assertIn("You die.", self.w.log.all())

    def test_messages(self):
        # hero power 4, defense 1 (from setUp)
        m = mob(self.w, 4, 3, name="rat", hp=2, xp=1)
        world_mod.resolve_attack(self.w, self.hero, m)       # 4-0 = 4, kills it
        world_mod.resolve_attack(self.w, mob(self.w, 2, 3, power=3), self.hero)  # 3-1 = 2
        self.assertIn("You hit the rat for 4.", self.w.log.all())
        self.assertIn("The rat dies.", self.w.log.all())
        self.assertIn("The rat hits you for 2.", self.w.log.all())

    def test_kill_bumps_roster_version_twice(self):
        v0 = self.w.roster_version
        world_mod.resolve_attack(self.w, self.hero, mob(self.w, 4, 3, hp=1))
        # mob() added one (+1), the kill removes it (+1) and adds a corpse (+1)
        self.assertEqual(self.w.roster_version, v0 + 3)


class BumpWiring(unittest.TestCase):
    def setUp(self):
        ai.WANDER_CHANCE = 0.0
        self.w = room(10, 10)
        self.hero = self.w.add_actor(world_mod.make_hero(3, 3, power=4))
        self.sched = world_mod.RoundRobinScheduler(self.w)

    def turn(self, action):
        return world_mod.resolve_turn(self.w, self.sched, action, ai.take_turn)

    def test_monster_adjacent_attacks_the_hero_on_its_turn(self):
        m = mob(self.w, 4, 3, ai="hunt", power=3)
        m["goal"] = (3, 3)
        hp0 = self.hero["hp"]
        self.turn(("wait",))
        self.assertLess(self.hero["hp"], hp0)
        self.assertEqual((m["x"], m["y"]), (4, 3))    # didn't move onto the hero

    def test_hero_dies_mid_turn_and_remaining_monsters_hold(self):
        a = mob(self.w, 4, 3, ai="hunt", power=50)     # one-shots the hero
        b = mob(self.w, 3, 4, ai="hunt", power=3)
        a["goal"] = b["goal"] = (3, 3)
        one_hit = max(1, 50 - self.hero["defense"])
        self.turn(("wait",))
        self.assertFalse(self.w.hero_alive())
        # b comes after a in actors order; resolve_turn broke on the dead hero,
        # so b never swung — the hero took exactly a's one hit
        self.assertEqual(self.hero["hp"], self.hero["max_hp"] - one_hit)

    def test_player_kill_removes_monster_from_the_turn_iteration(self):
        killed = mob(self.w, 4, 3, hp=1, xp=2)
        seen = []
        world_mod.resolve_turn(
            self.w, self.sched, ("move", 1, 0), lambda w, x: seen.append(x)
        )
        self.assertNotIn(killed, seen)                 # corpse-skip in resolve_turn
        self.assertEqual(self.hero["xp"], 2)

    def test_corpse_never_gets_a_turn_and_never_follows_the_hero(self):
        # cd-yl4 sibling: corpses were waking to "hunt" and trailing the hero.
        ai.WANDER_CHANCE = 1.0                         # would move it if it acted
        m = mob(self.w, 4, 3, hp=1)                    # dies to the hero's bump
        self.turn(("move", 1, 0))                      # hero bumps m at (4,3), kills it
        corpse = self.w.actors[-1]
        self.assertTrue(corpse.get("corpse"))
        self.assertEqual((corpse["x"], corpse["y"]), (4, 3))   # left where m fell
        self.assertEqual((self.hero["x"], self.hero["y"]), (3, 3))  # bump, no move

        seen = []
        for _ in range(6):
            world_mod.resolve_turn(
                self.w, self.sched, ("wait",), lambda w, a: seen.append(a)
            )
        self.assertNotIn(corpse, seen)                 # never handed to the AI
        self.assertEqual((corpse["x"], corpse["y"]), (4, 3))   # stayed put
        self.assertIsNone(corpse.get("ai"))            # never woke to "hunt"


class CircuitPythonStr(unittest.TestCase):
    """CircuitPython's `str` is a subset of CPython's — no `.capitalize()`
    or `.title()` (only `.upper()`/`.lower()`). CPython has them, so a unit
    test of the message text can't catch a regression; scan the source of
    every deployed module instead. This is why world._cap exists — the first
    on-device combat hit crashed on `_mob_name(attacker).capitalize()`."""

    def test_no_capitalize_or_title_in_game_source(self):
        import re

        # a value the method is called on ends in a word char, ) or ] — this
        # skips prose mentions in docstrings ("no `.capitalize()`").
        call = re.compile(r"[\w\)\]]\.(?:capitalize|title)\(")
        game_dir = os.path.join(os.path.dirname(__file__), "..", "game")
        offenders = []
        for name in sorted(os.listdir(game_dir)):
            if not name.endswith(".py"):
                continue
            with open(os.path.join(game_dir, name)) as fh:
                for lineno, line in enumerate(fh, 1):
                    if call.search(line):
                        offenders.append("%s:%d %s" % (name, lineno, line.strip()))
        self.assertEqual(offenders, [], "CircuitPython str has no such method")


if __name__ == "__main__":
    unittest.main()
