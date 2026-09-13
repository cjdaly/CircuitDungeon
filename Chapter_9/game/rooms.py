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
navigation, blocked-move handling). make_world() (cd-zw2.6) is the real Ch9
room roster, filling the slot the Ch8 port deliberately left empty.

Pure data + movement logic, no displayio/board imports -- runs under plain
desktop Python (see tests/test_rooms.py).
"""

UP, DOWN, LEFT, RIGHT = "up", "down", "left", "right"
DIRECTIONS = (UP, DOWN, LEFT, RIGHT)
OPPOSITE = {UP: DOWN, DOWN: UP, LEFT: RIGHT, RIGHT: LEFT}


class Room:
    """One screen-sized room. `exits` maps a direction to a destination room name.

    `description` is a short flavor line for orientation/text overlays;
    `items` is a list of notable objects in the room (e.g. the living
    room's tree/fireplace/cookies/presents) -- content for a future
    rendering/interaction pass, not acted on by this module itself.
    """

    def __init__(self, name, exits=None, description="", items=None):
        self.name = name
        self.exits = dict(exits or {})
        self.description = description
        self.items = list(items or [])

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

    def all_rooms(self):
        """Every Room in this World, in no particular order."""
        return self._rooms.values()

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


def make_world():
    """The real Ch9 room roster -- cd-zw2.6.

    A cozy house on Christmas Eve, plus its yard and what's around/under it.
    Zork-style connectivity (see the module docstring): rooms are placed by
    feel, not to scale, and not every direction works from every room. Every
    exit below has a matching return exit (round-trip navigable both ways).
    10 rooms in three clusters, hung off the start room:

    - **Living Room** (start) <-> Kitchen <-> Basement (down)
    - **Living Room** <-> Entryway <-> Bedroom (up) <-> Kids' Bedroom (right)
    - **Entryway** <-> Yard (down) <-> Pond (left) / Tree House (right) /
      Cave (down)

    Only the living room has detailed `items` content for now (the tree,
    fireplace, cookies/milk, presents) -- the rest are placeholder rooms
    with just a name + description, pending further content/art passes.
    """
    return World(
        rooms=[
            Room(
                "Living Room",
                {RIGHT: "Kitchen", LEFT: "Entryway"},
                description="A cozy living room, decorated for Christmas.",
                items=[
                    "a Christmas tree",
                    "a crackling fireplace",
                    "a tray of cookies and a glass of milk, left out for Santa",
                    "wrapped presents under the tree",
                ],
            ),
            Room(
                "Kitchen",
                {LEFT: "Living Room", DOWN: "Basement"},
                description="The kitchen, still warm from holiday baking.",
            ),
            Room(
                "Basement",
                {UP: "Kitchen"},
                description="A dim basement under the house.",
            ),
            Room(
                "Entryway",
                {RIGHT: "Living Room", UP: "Bedroom", DOWN: "Yard"},
                description="The front entryway, coats and boots by the door.",
            ),
            Room(
                "Bedroom",
                {DOWN: "Entryway", RIGHT: "Kids' Bedroom"},
                description="A quiet bedroom.",
            ),
            Room(
                "Kids' Bedroom",
                {LEFT: "Bedroom"},
                description="A kid's bedroom, stockings hung by the window.",
            ),
            Room(
                "Yard",
                {UP: "Entryway", LEFT: "Pond", RIGHT: "Tree House", DOWN: "Cave"},
                description="The snowy front yard.",
            ),
            Room(
                "Pond",
                {RIGHT: "Yard"},
                description="A small frozen pond at the edge of the yard.",
            ),
            Room(
                "Tree House",
                {LEFT: "Yard"},
                description="A tree house, cold this time of year.",
            ),
            Room(
                "Cave",
                {UP: "Yard"},
                description="A shallow cave mouth, just past the yard.",
            ),
        ],
        start="Living Room",
    )
