# SPDX-License-Identifier: MIT
"""Minimal room-graph navigation model -- cd-45v.4 prototype.

Proves the Ch9 "Christmas Critters" navigation feel (project memory
ch9-christmas-critters-design, bead cd-zw2.1) before any real art or room
content exists: a handful of screen-sized rooms connected by up/down/left/
right exits, not every direction live from every room -- Zork-style
connectivity, not a coherent floorplan. DEMO_WORLD below is throwaway
placeholder content for exercising the model, not the real Ch9 room roster
(that's cd-zw2.6).

Pure data + movement logic, no displayio/board imports -- runs under plain
desktop Python, see tests/test_rooms.py.
"""

UP, DOWN, LEFT, RIGHT = "up", "down", "left", "right"
DIRECTIONS = (UP, DOWN, LEFT, RIGHT)


class Room:
    """One screen-sized room. `exits` maps a direction to a destination room name."""

    def __init__(self, name, exits=None):
        self.name = name
        self.exits = dict(exits or {})

    def exit_toward(self, direction):
        return self.exits.get(direction)


class World:
    """A graph of Rooms plus the player's current position."""

    def __init__(self, rooms, start):
        self._rooms = {room.name: room for room in rooms}
        if start not in self._rooms:
            raise ValueError("unknown start room: {}".format(start))
        self.current = start

    @property
    def room(self):
        return self._rooms[self.current]

    def live_exits(self):
        """Directions with a real exit from the current room, in DIRECTIONS order."""
        return [d for d in DIRECTIONS if self.room.exit_toward(d) is not None]

    def move(self, direction):
        """Step through `direction` if it's a live exit.

        Returns True and updates .current on success; returns False (and
        leaves .current unchanged) if that direction has no exit here --
        callers use this to show a "can't go that way" bump instead of
        silently failing.
        """
        dest = self.room.exit_toward(direction)
        if dest is None:
            return False
        self.current = dest
        return True


def make_demo_world():
    """A small throwaway layout: Living Room (start) with three neighbors.

    Not every direction is live from every room, and Kitchen<->Entryway
    doesn't connect directly -- on purpose, to exercise "blocked direction"
    handling and prove the graph doesn't need to be a coherent floorplan.

               [Yard]
                 |down from Entryway
    [Kitchen]--[Living Room]--[Entryway]
    """
    return World(
        rooms=[
            Room("Living Room", {RIGHT: "Entryway", LEFT: "Kitchen"}),
            Room("Kitchen", {RIGHT: "Living Room"}),
            Room("Entryway", {LEFT: "Living Room", DOWN: "Yard"}),
            Room("Yard", {UP: "Entryway"}),
        ],
        start="Living Room",
    )
