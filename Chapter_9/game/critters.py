# SPDX-License-Identifier: MIT
"""Critter mechanic: escape, hide, per-critter item preference, retrieval --
cd-zw2.3.

Critters are robot pets that start in their box (per the design, under the
Living Room tree -- see project memory ch9-christmas-critters-design).
At some point they escape and hide in another room. Bringing one back is a
two-part fetch, not a locate-and-touch: the player has to (1) find the
critter in whatever room it's hiding in, AND (2) be holding the specific
item that critter likes. Getting the room right but the item wrong (or vice
versa) doesn't work.

Escape TRIGGER is deliberately not decided here -- the design notes flag
the trigger condition itself as unspecified (time-based? player-action-
based?). Critter.escape() is a plain method a future game loop calls
whenever it decides to; this module only owns the state machine and the
retrieval rule, not the policy for when an escape happens.

"Holding an item" is likewise not this module's concern -- try_retrieve()
takes `held_items` (any collection supporting `in`), so a caller can back
it with a real inventory, a set of picked-up item names, or anything else,
without critters.py depending on rooms.py's Room.items or any particular
inventory design.

Pure data + state logic, no displayio/board imports -- runs under plain
desktop Python (see tests/test_critters.py). No real critter roster/content
(names, preferred items) here either -- placeholder critters only exist in
tests; naming actual critters and their preferences is a content decision
for later, same way cd-zw2.6 authored the real room roster once the room
*model* existed.
"""

IN_BOX = "in_box"
HIDING = "hiding"
RETURNED = "returned"


class Critter:
    """One critter's state: where it is, and what it takes to bring it back."""

    def __init__(self, name, preferred_item, home):
        self.name = name
        self.preferred_item = preferred_item
        self.home = home
        self.state = IN_BOX
        self.location = home

    def escape(self, hide_in):
        """Leave the box and hide in room `hide_in`.

        Returns True on success; False (no-op) if not currently IN_BOX.
        RETURNED is terminal, not a path back to IN_BOX -- once retrieved,
        a critter's arc is done and it doesn't escape again.
        """
        if self.state != IN_BOX:
            return False
        self.state = HIDING
        self.location = hide_in
        return True

    def try_retrieve(self, room_name, held_items):
        """Attempt to retrieve this critter from the player's current room.

        Succeeds only if the critter is HIDING in exactly `room_name` AND
        `held_items` contains its preferred_item -- both conditions,
        checked together, not two separate steps a caller could get half
        right. On success the critter returns to its home. Returns True/
        False; no partial state change on failure.
        """
        if self.state != HIDING:
            return False
        if room_name != self.location or self.preferred_item not in held_items:
            return False
        self.state = RETURNED
        self.location = self.home
        return True


class CritterRoster:
    """A named collection of Critters -- lookup by name, or by current room."""

    def __init__(self, critters):
        self._critters = {c.name: c for c in critters}

    def get(self, name):
        return self._critters[name]

    def all(self):
        return self._critters.values()

    def hiding_in(self, room_name):
        """Critters currently HIDING in `room_name`, e.g. for a room's text
        overlay to hint "something's rustling in here"."""
        return [
            c for c in self._critters.values()
            if c.state == HIDING and c.location == room_name
        ]
