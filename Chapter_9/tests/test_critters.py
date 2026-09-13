# SPDX-License-Identifier: MIT
# Off-device tests for game/critters.py -- pure state logic, no hardware.
#
#   python3 Chapter_9/tests/test_critters.py

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "game"))

import critters as critters_mod  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
