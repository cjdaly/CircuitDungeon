# SPDX-License-Identifier: MIT
# Off-device tests for game/rooms.py -- the room-graph model has no
# displayio/board imports, so it runs under plain desktop Python.
#
#   python3 Chapter_9/tests/test_rooms.py

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "game"))

import rooms as rooms_mod  # noqa: E402


class TestRoom(unittest.TestCase):
    def test_exit_toward_known_direction(self):
        room = rooms_mod.Room("A", {rooms_mod.UP: "B"})
        self.assertEqual(room.exit_toward(rooms_mod.UP), "B")

    def test_exit_toward_missing_direction(self):
        room = rooms_mod.Room("A", {rooms_mod.UP: "B"})
        self.assertIsNone(room.exit_toward(rooms_mod.DOWN))

    def test_no_exits_by_default(self):
        room = rooms_mod.Room("A")
        for direction in rooms_mod.DIRECTIONS:
            self.assertIsNone(room.exit_toward(direction))

    def test_description_and_items_default_empty(self):
        room = rooms_mod.Room("A")
        self.assertEqual(room.description, "")
        self.assertEqual(room.items, [])

    def test_description_and_items_stored(self):
        room = rooms_mod.Room("A", description="A room.", items=["a lamp"])
        self.assertEqual(room.description, "A room.")
        self.assertEqual(room.items, ["a lamp"])


class TestWorld(unittest.TestCase):
    def _linear_world(self):
        return rooms_mod.World(
            rooms=[
                rooms_mod.Room("A", {rooms_mod.RIGHT: "B"}),
                rooms_mod.Room("B", {rooms_mod.LEFT: "A", rooms_mod.UP: "C"}),
                rooms_mod.Room("C", {rooms_mod.DOWN: "B"}),
            ],
            start="A",
        )

    def test_starts_at_start_room(self):
        world = self._linear_world()
        self.assertEqual(world.current, "A")
        self.assertEqual(world.room.name, "A")

    def test_unknown_start_room_raises(self):
        with self.assertRaises(ValueError):
            rooms_mod.World(rooms=[rooms_mod.Room("A")], start="nope")

    def test_live_exits_reflects_current_room(self):
        world = self._linear_world()
        self.assertEqual(world.live_exits(), [rooms_mod.RIGHT])
        world.move(rooms_mod.RIGHT)
        self.assertEqual(
            world.live_exits(), [rooms_mod.UP, rooms_mod.LEFT]
        )

    def test_move_through_live_exit_updates_current(self):
        world = self._linear_world()
        moved = world.move(rooms_mod.RIGHT)
        self.assertTrue(moved)
        self.assertEqual(world.current, "B")

    def test_move_through_blocked_direction_is_a_noop(self):
        world = self._linear_world()
        moved = world.move(rooms_mod.UP)  # no UP exit from A
        self.assertFalse(moved)
        self.assertEqual(world.current, "A")

    def test_round_trip_move(self):
        world = self._linear_world()
        world.move(rooms_mod.RIGHT)
        world.move(rooms_mod.UP)
        self.assertEqual(world.current, "C")
        world.move(rooms_mod.DOWN)
        self.assertEqual(world.current, "B")


class TestMakeWorld(unittest.TestCase):
    def test_starts_in_living_room(self):
        world = rooms_mod.make_world()
        self.assertEqual(world.current, "Living Room")

    def test_living_room_has_expected_items(self):
        world = rooms_mod.make_world()
        items = world.room.items
        self.assertIn("a Christmas tree", items)
        self.assertIn("wrapped presents under the tree", items)

    def test_every_exit_has_a_matching_return_exit(self):
        # Every room in this roster is meant to round-trip both ways --
        # catches a typo'd/one-way exit if the roster is ever edited.
        world = rooms_mod.make_world()
        by_name = {room.name: room for room in world.all_rooms()}
        for room in world.all_rooms():
            for direction, dest_name in room.exits.items():
                dest = by_name[dest_name]
                back = rooms_mod.OPPOSITE[direction]
                self.assertEqual(
                    dest.exit_toward(back), room.name,
                    "{} --{}--> {} has no return exit".format(room.name, direction, dest_name),
                )

    def test_every_room_reachable_from_start(self):
        world = rooms_mod.make_world()
        by_name = {room.name: room for room in world.all_rooms()}
        seen = {world.current}
        frontier = [world.current]
        while frontier:
            name = frontier.pop()
            for direction in rooms_mod.DIRECTIONS:
                dest = by_name[name].exit_toward(direction)
                if dest is not None and dest not in seen:
                    seen.add(dest)
                    frontier.append(dest)
        self.assertEqual(seen, set(by_name))


if __name__ == "__main__":
    unittest.main()
