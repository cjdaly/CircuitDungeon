# SPDX-License-Identifier: MIT
# Off-device tests for game/rooms.py -- the room-graph model has no
# displayio/board imports, so it runs under plain desktop Python.
#
#   python3 Chapter_8/tests/test_rooms.py

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


class TestDemoWorld(unittest.TestCase):
    def test_demo_world_starts_in_living_room(self):
        world = rooms_mod.make_demo_world()
        self.assertEqual(world.current, "Living Room")

    def test_demo_world_kitchen_and_entryway_dont_directly_connect(self):
        world = rooms_mod.make_demo_world()
        world.move(rooms_mod.LEFT)  # Living Room -> Kitchen
        self.assertEqual(world.current, "Kitchen")
        self.assertEqual(world.live_exits(), [rooms_mod.RIGHT])

    def test_demo_world_full_loop(self):
        world = rooms_mod.make_demo_world()
        self.assertTrue(world.move(rooms_mod.RIGHT))  # -> Entryway
        self.assertTrue(world.move(rooms_mod.DOWN))  # -> Yard
        self.assertFalse(world.move(rooms_mod.DOWN))  # Yard has no DOWN exit
        self.assertTrue(world.move(rooms_mod.UP))  # -> Entryway
        self.assertTrue(world.move(rooms_mod.LEFT))  # -> Living Room


if __name__ == "__main__":
    unittest.main()
