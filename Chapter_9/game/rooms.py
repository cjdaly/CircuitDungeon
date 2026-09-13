# SPDX-License-Identifier: MIT
"""Room-graph data model -- cd-zw2.1.

Ch9 rooms are Zork/Infocom-style: a bag of connected rooms, not a coherent
floorplan or to-scale map (see project memory
ch9-christmas-critters-design). Each room is one full screen (no
scrolling/camera). Rooms connect via up/down/left/right exits; not every
direction is live from every room -- callers use World.live_exits() /
World.move()'s return value to know (and show) which edges are live in the
current room, e.g. Chapter_8's room_nav_demo.py's color-coded edge markers.

Ported from Chapter_8/game/rooms.py (cd-45v.4's prototype) -- same
Room/World API, already proven on real hardware 2026-09-13 (edge-gesture
navigation, blocked-move handling). No baked-in demo world here; the actual
Ch9 room roster is cd-zw2.6's job, not this module's.

Pure data + movement logic, no displayio/board imports -- runs under plain
desktop Python (see tests/test_rooms.py).
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
