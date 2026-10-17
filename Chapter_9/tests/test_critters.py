# SPDX-License-Identifier: MIT
# Off-device tests for game/critters.py -- pure state logic, no hardware.
#
#   python3 Chapter_9/tests/test_critters.py

import os
import random
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "game"))

import critter_candidates  # noqa: E402
import critters as critters_mod  # noqa: E402
import rooms  # noqa: E402


class TestCritter(unittest.TestCase):
    def _critter(self):
        return critters_mod.Critter("Fluffy", preferred_item="stuffed bunny", home="Living Room")

    def test_starts_in_box_at_home(self):
        c = self._critter()
        self.assertEqual(c.state, critters_mod.IN_BOX)
        self.assertEqual(c.location, "Living Room")

    def test_escape_moves_to_hiding_room(self):
        c = self._critter()
        escaped = c.escape("Kitchen")
        self.assertTrue(escaped)
        self.assertEqual(c.state, critters_mod.HIDING)
        self.assertEqual(c.location, "Kitchen")

    def test_cannot_escape_twice(self):
        c = self._critter()
        c.escape("Kitchen")
        escaped_again = c.escape("Yard")
        self.assertFalse(escaped_again)
        self.assertEqual(c.location, "Kitchen")  # unchanged

    def test_retrieve_fails_before_escaping(self):
        c = self._critter()
        found = c.try_retrieve("Living Room", held_items={"stuffed bunny"})
        self.assertFalse(found)
        self.assertEqual(c.state, critters_mod.IN_BOX)

    def test_retrieve_fails_in_wrong_room(self):
        c = self._critter()
        c.escape("Kitchen")
        found = c.try_retrieve("Yard", held_items={"stuffed bunny"})
        self.assertFalse(found)
        self.assertEqual(c.state, critters_mod.HIDING)

    def test_retrieve_fails_with_wrong_item(self):
        c = self._critter()
        c.escape("Kitchen")
        found = c.try_retrieve("Kitchen", held_items={"dog bone"})
        self.assertFalse(found)
        self.assertEqual(c.state, critters_mod.HIDING)

    def test_retrieve_fails_with_right_item_wrong_room(self):
        # Right item, wrong room -- both must hold together, not either/or.
        c = self._critter()
        c.escape("Kitchen")
        found = c.try_retrieve("Yard", held_items={"stuffed bunny"})
        self.assertFalse(found)

    def test_retrieve_succeeds_with_right_room_and_item(self):
        c = self._critter()
        c.escape("Kitchen")
        found = c.try_retrieve("Kitchen", held_items={"stuffed bunny", "dog bone"})
        self.assertTrue(found)
        self.assertEqual(c.state, critters_mod.RETURNED)
        self.assertEqual(c.location, "Living Room")

    def test_returned_is_terminal_not_escapable_again(self):
        # The bead spec lists three distinct states (in-box / hiding /
        # returned) -- RETURNED means this critter's arc is done, it
        # doesn't loop back to IN_BOX for another round.
        c = self._critter()
        c.escape("Kitchen")
        c.try_retrieve("Kitchen", held_items={"stuffed bunny"})
        escaped_again = c.escape("Yard")
        self.assertFalse(escaped_again)
        self.assertEqual(c.location, "Living Room")  # stays home, unchanged


class TestCritterRoster(unittest.TestCase):
    def _roster(self):
        return critters_mod.CritterRoster([
            critters_mod.Critter("Fluffy", "stuffed bunny", "Living Room"),
            critters_mod.Critter("Sparky", "dog bone", "Living Room"),
        ])

    def test_get_by_name(self):
        roster = self._roster()
        self.assertEqual(roster.get("Fluffy").preferred_item, "stuffed bunny")

    def test_get_unknown_name_raises(self):
        roster = self._roster()
        with self.assertRaises(KeyError):
            roster.get("Nobody")

    def test_hiding_in_empty_before_any_escape(self):
        roster = self._roster()
        self.assertEqual(roster.hiding_in("Kitchen"), [])

    def test_hiding_in_reflects_escaped_critters_only(self):
        roster = self._roster()
        roster.get("Fluffy").escape("Kitchen")
        roster.get("Sparky").escape("Yard")
        kitchen = roster.hiding_in("Kitchen")
        self.assertEqual([c.name for c in kitchen], ["Fluffy"])

    def test_hiding_in_excludes_retrieved_critters(self):
        roster = self._roster()
        fluffy = roster.get("Fluffy")
        fluffy.escape("Kitchen")
        fluffy.try_retrieve("Kitchen", held_items={"stuffed bunny"})
        self.assertEqual(roster.hiding_in("Kitchen"), [])

    def test_all_returns_every_critter(self):
        roster = self._roster()
        names = {c.name for c in roster.all()}
        self.assertEqual(names, {"Fluffy", "Sparky"})


class TestCast(unittest.TestCase):
    """The real cast (cd-342.3) -- content checks, not just mechanics."""

    def _all_named(self):
        named = [pair for _sp, _lure, _habit, sprites in critters_mod.CAST for pair in sprites]
        return named + list(critters_mod.WILD)

    def test_every_candidate_sprite_is_cast_or_wild_exactly_once(self):
        # Catches drift when tools/build_critter_candidates.py's list changes.
        ids = [sprite for sprite, _name in self._all_named()]
        self.assertEqual(sorted(ids), sorted(c[0] for c in critter_candidates.CANDIDATES))

    def test_cast_sprites_match_their_species_group(self):
        groups = {cid: group for cid, group, _src in critter_candidates.CANDIDATES}
        for species, _lure, _habit, sprites in critters_mod.CAST:
            for sprite, _name in sprites:
                self.assertEqual(groups[sprite], species, sprite)

    def test_names_are_unique(self):
        names = [name for _sprite, name in self._all_named()]
        self.assertEqual(len(names), len(set(names)))

    def test_escapees_of_different_species_never_share_an_initial(self):
        # Any one name per species can be rolled together, so initials must
        # differ across species to keep all-caps captions easy to tell apart.
        seen = {}
        for species, _lure, _habit, sprites in critters_mod.CAST:
            for _sprite, name in sprites:
                other = seen.setdefault(name[0], species)
                self.assertEqual(other, species, name)

    def test_names_fit_one_caption_line(self):
        # "<NAME> ESCAPED!" must stay one Bangers line (~170px band, see
        # doc/STYLE.md); 7 letters measured at <=165px.
        for _sprite, name in self._all_named():
            self.assertLessEqual(len(name), 7, name)

    def test_lures_are_distinct_and_none_is_a_battery(self):
        # Batteries belong to the finale (doc/EPISODES.md sec 6).
        lures = [lure for _sp, lure, _habit, _sprites in critters_mod.CAST]
        self.assertEqual(len(lures), len(set(lures)))
        for lure in lures:
            self.assertNotIn("batter", lure)

    def test_home_is_the_start_room(self):
        self.assertEqual(critters_mod.HOME, rooms.make_world().current)

    def test_make_roster_has_one_critter_per_species_in_box(self):
        roster = critters_mod.make_roster(choice=lambda seq: seq[0])
        self.assertEqual([c.species for c in roster.all()], [sp[0] for sp in critters_mod.CAST])
        for c in roster.all():
            self.assertEqual(c.state, critters_mod.IN_BOX)
            self.assertEqual(c.location, critters_mod.HOME)

    def test_make_roster_name_follows_the_sprite_roll(self):
        last = critters_mod.make_roster(choice=lambda seq: seq[-1])
        self.assertEqual(last.get("Woofer").sprite, "dog_4_0")
        self.assertEqual(last.get("Jingle").preferred_item, "oil can")
        first = critters_mod.make_roster(choice=lambda seq: seq[0])
        self.assertEqual(first.get("Patch").sprite, "dog_0_0")
        with self.assertRaises(KeyError):
            first.get("Woofer")

    def test_make_roster_default_is_random_and_seedable(self):
        random.seed(7)
        a = [c.name for c in critters_mod.make_roster().all()]
        random.seed(7)
        b = [c.name for c in critters_mod.make_roster().all()]
        self.assertEqual(a, b)
        self.assertEqual(len(a), len(critters_mod.CAST))


if __name__ == "__main__":
    unittest.main()
