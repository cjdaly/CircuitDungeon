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

# Off-device tests for the inventory model -- pick up / use / drop
# (cd-e3p.8) and leveled sword/armor auto-upgrade (cd-dsc.4).
#
#   python3 Chapter_7/tests/test_inventory.py

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "game"))

import ai  # noqa: E402
import modes  # noqa: E402
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


class Pickup(unittest.TestCase):
    def setUp(self):
        ai.WANDER_CHANCE = 0.0
        self.w = room(8, 8)
        self.hero = self.w.add_actor(world_mod.make_hero(3, 3))
        self.sched = world_mod.RoundRobinScheduler(self.w)

    def turn(self, action):
        return world_mod.resolve_turn(self.w, self.sched, action, ai.take_turn)

    def test_walking_onto_an_item_picks_it_up(self):
        item = self.w.add_actor(
            world_mod.make_item(4, 3, world_mod.POTION_RED_TILE, "potion_red", "a red potion")
        )
        self.assertTrue(self.turn(("move", 1, 0)))
        self.assertNotIn(item, self.w.actors)
        self.assertIn(item, self.hero["inventory"])
        self.assertEqual((item["x"], item["y"]), (4, 3))  # dict unchanged, just moved

    def test_pickup_logs_a_message(self):
        self.w.add_actor(world_mod.make_item(4, 3, world_mod.POTION_RED_TILE, "potion_red", "a red potion"))
        self.turn(("move", 1, 0))
        self.assertIn("pick up", self.w.log.latest())

    def test_pickup_bumps_roster_version(self):
        self.w.add_actor(world_mod.make_item(4, 3, world_mod.POTION_RED_TILE, "potion_red", "a red potion"))
        v0 = self.w.roster_version
        self.turn(("move", 1, 0))
        self.assertGreater(self.w.roster_version, v0)

    def test_item_does_not_block_movement_or_trigger_a_bump(self):
        # actor_at() already documents items as non-blocking, same as a
        # corpse -- this just confirms move_actor agrees, not a bump.
        self.w.add_actor(world_mod.make_item(4, 3, world_mod.POTION_RED_TILE, "potion_red", "x"))
        result = self.w.move_actor(self.hero, 1, 0)
        self.assertEqual(result, "moved")

    def test_walking_onto_empty_floor_does_nothing_special(self):
        seq0 = self.w.log.seq
        self.turn(("move", 1, 0))
        self.assertEqual(self.w.log.seq, seq0)
        self.assertEqual(self.hero.get("inventory", []), [])


class Use(unittest.TestCase):
    def setUp(self):
        self.w = room(8, 8)
        self.hero = self.w.add_actor(
            world_mod.make_hero(3, 3, hp=10, max_hp=20, power=4, defense=1)
        )

    def test_heal_potion_restores_hp_capped_at_max(self):
        item = world_mod.make_item(0, 0, world_mod.POTION_RED_TILE, "potion_red", "a red potion")
        self.hero["inventory"] = [item]
        self.assertTrue(world_mod.use_item(self.w, self.hero, item))
        self.assertEqual(self.hero["hp"], 18)  # +8, per ITEM_EFFECTS
        self.assertNotIn(item, self.hero["inventory"])

    def test_heal_potion_caps_at_max_hp(self):
        self.hero["hp"] = 19
        item = world_mod.make_item(0, 0, world_mod.POTION_RED_TILE, "potion_red", "a red potion")
        self.hero["inventory"] = [item]
        world_mod.use_item(self.w, self.hero, item)
        self.assertEqual(self.hero["hp"], 20)

    def test_power_buff_potion_raises_power(self):
        item = world_mod.make_item(0, 0, world_mod.POTION_BLUE_TILE, "potion_blue", "a blue potion")
        self.hero["inventory"] = [item]
        world_mod.use_item(self.w, self.hero, item)
        self.assertEqual(self.hero["power"], 6)  # +2

    def test_defense_buff_scroll_raises_defense(self):
        item = world_mod.make_item(0, 0, world_mod.SCROLL_TILE, "scroll", "a scroll")
        self.hero["inventory"] = [item]
        world_mod.use_item(self.w, self.hero, item)
        self.assertEqual(self.hero["defense"], 2)  # +1

    def test_use_logs_a_message(self):
        item = world_mod.make_item(0, 0, world_mod.POTION_RED_TILE, "potion_red", "a red potion")
        self.hero["inventory"] = [item]
        world_mod.use_item(self.w, self.hero, item)
        self.assertIn("drink", self.w.log.latest())

    def test_use_item_not_in_inventory_is_a_noop(self):
        item = world_mod.make_item(0, 0, world_mod.POTION_RED_TILE, "potion_red", "a red potion")
        self.assertFalse(world_mod.use_item(self.w, self.hero, item))

    def test_using_a_weapon_does_nothing_no_effect_entry(self):
        item = world_mod.make_item(0, 0, world_mod.SWORD_TILE, "weapon", "a sword", level=3)
        self.hero["inventory"] = [item]
        self.assertFalse(world_mod.use_item(self.w, self.hero, item))
        self.assertIn(item, self.hero["inventory"])  # unconsumed

    def test_action_use_picks_the_first_usable_item(self):
        junk = world_mod.make_item(0, 0, world_mod.SWORD_TILE, "weapon", "a sword", level=3)
        potion = world_mod.make_item(0, 0, world_mod.POTION_RED_TILE, "potion_red", "a red potion")
        self.hero["inventory"] = [junk, potion]
        self.assertTrue(world_mod._apply_player_action(self.w, ("use",)))
        self.assertEqual(self.hero["hp"], 18)
        self.assertNotIn(potion, self.hero["inventory"])
        self.assertIn(junk, self.hero["inventory"])  # untouched

    def test_action_use_with_nothing_usable_spends_no_turn(self):
        self.hero["inventory"] = [
            world_mod.make_item(0, 0, world_mod.SWORD_TILE, "weapon", "a sword", level=3)
        ]
        self.assertFalse(world_mod._apply_player_action(self.w, ("use",)))


class LeveledEquipment(unittest.TestCase):
    """Sword/armor auto-upgrade on pickup (cd-dsc.4) -- no carry list, no
    manual equip step; see world.EQUIP_SLOTS / _try_equip_leveled."""

    def setUp(self):
        self.w = room(8, 8)
        self.hero = self.w.add_actor(world_mod.make_hero(3, 3, power=4, defense=1))

    def _sword(self, level):
        return world_mod.make_item(4, 3, world_mod.SWORD_TILE, "weapon",
                                   "a level %d sword" % level, level=level)

    def _armor(self, level):
        return world_mod.make_item(4, 3, world_mod.ARMOR_TILE, "armor",
                                   "level %d armor" % level, level=level)

    def test_first_sword_found_is_equipped(self):
        self.assertTrue(world_mod._try_equip_leveled(self.w, self.hero, self._sword(2)))
        self.assertEqual(self.hero["weapon_level"], 2)
        self.assertEqual(self.hero["power"], 6)  # 4 base + 2

    def test_first_armor_found_is_equipped(self):
        self.assertTrue(world_mod._try_equip_leveled(self.w, self.hero, self._armor(3)))
        self.assertEqual(self.hero["armor_level"], 3)
        self.assertEqual(self.hero["defense"], 4)  # 1 base + 3

    def test_better_sword_replaces_and_unwinds_the_old_bonus(self):
        world_mod._try_equip_leveled(self.w, self.hero, self._sword(2))
        self.assertTrue(world_mod._try_equip_leveled(self.w, self.hero, self._sword(5)))
        self.assertEqual(self.hero["weapon_level"], 5)
        self.assertEqual(self.hero["power"], 9)  # 4 base + 5, not 4+2+5

    def test_worse_sword_is_rejected_not_carried(self):
        world_mod._try_equip_leveled(self.w, self.hero, self._sword(3))
        self.assertFalse(world_mod._try_equip_leveled(self.w, self.hero, self._sword(2)))
        self.assertEqual(self.hero["weapon_level"], 3)  # unchanged
        self.assertEqual(self.hero["power"], 7)
        self.assertEqual(self.hero.get("inventory", []), [])  # never carried

    def test_equal_level_sword_is_rejected(self):
        world_mod._try_equip_leveled(self.w, self.hero, self._sword(3))
        self.assertFalse(world_mod._try_equip_leveled(self.w, self.hero, self._sword(3)))

    def test_upgrade_logs_a_message(self):
        world_mod._try_equip_leveled(self.w, self.hero, self._sword(4))
        self.assertIn("better sword", self.w.log.latest())

    def test_rejection_logs_a_message(self):
        world_mod._try_equip_leveled(self.w, self.hero, self._sword(4))
        world_mod._try_equip_leveled(self.w, self.hero, self._sword(1))
        self.assertIn("is better!", self.w.log.latest())

    def test_walking_onto_a_sword_auto_equips_not_carries(self):
        item = self.w.add_actor(self._sword(2))
        moved = self.w.move_actor(self.hero, 1, 0)
        self.assertEqual(moved, "moved")  # non-blocking, no bump
        world_mod._check_pickup(self.w)
        self.assertNotIn(item, self.w.actors)
        self.assertEqual(self.hero.get("inventory", []), [])  # not in the bag
        self.assertEqual(self.hero["weapon_level"], 2)


class Drop(unittest.TestCase):
    def setUp(self):
        self.w = room(8, 8)
        self.hero = self.w.add_actor(world_mod.make_hero(3, 3))

    def test_drop_places_the_item_at_the_actors_position_on_the_map(self):
        item = world_mod.make_item(0, 0, world_mod.POTION_RED_TILE, "potion_red", "a red potion")
        self.hero["inventory"] = [item]
        self.assertTrue(world_mod.drop_item(self.w, self.hero, item))
        self.assertIn(item, self.w.actors)
        self.assertEqual((item["x"], item["y"]), (3, 3))
        self.assertNotIn(item, self.hero["inventory"])

    def test_drop_item_not_carried_is_a_noop(self):
        item = world_mod.make_item(0, 0, world_mod.POTION_RED_TILE, "potion_red", "a red potion")
        self.assertFalse(world_mod.drop_item(self.w, self.hero, item))
        self.assertNotIn(item, self.w.actors)


class EventWiring(unittest.TestCase):
    def test_aux_x_maps_to_use(self):
        import input as im
        self.assertEqual(modes._first_action([im.AUX_X]), ("use",))

    def test_aux_y_is_unbound(self):
        # weapon/armor auto-equip on pickup (cd-dsc.4) -- no "equip" action
        # left to trigger, so Y alone is currently a no-op in play mode.
        import input as im
        self.assertIsNone(modes._first_action([im.AUX_Y]))


if __name__ == "__main__":
    unittest.main()
