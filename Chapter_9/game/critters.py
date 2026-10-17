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
desktop Python (see tests/test_critters.py).

The real cast (cd-342.3, decided with Chris 2026-10-17, see
doc/CRITTERS.md "Cast") is CAST/WILD + make_roster() at the bottom: five
species escape, one critter each, and which sprite (and so which name)
each species gets is rolled per playthrough. Lures and habits are a
starting point, expected to shift as episodes get written -- same as the
room map.
"""

IN_BOX = "in_box"
HIDING = "hiding"
RETURNED = "returned"


class Critter:
    """One critter's state: where it is, and what it takes to bring it back."""

    def __init__(self, name, preferred_item, home, species=None, sprite=None, habit=None):
        self.name = name
        self.preferred_item = preferred_item
        self.home = home
        self.species = species
        self.sprite = sprite  # critter_candidates id, e.g. "dog_3_0"
        self.habit = habit  # default where-clue text, e.g. "loves the snow"
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


# --------------------------------------------------------------------------- #
# The real cast -- cd-342.3

HOME = "Living Room"  # every box sits under the tree here (rooms.make_world start)

# (species, lure, habit, ((sprite id, name), ...)).  Every sprite has its own
# name, so a playthrough's names follow its sprite roll.  Sprite ids are
# critter_candidates.CANDIDATES ids; tests check the two stay in step.
# Squirrel lure is walnuts, not acorns -- one squirrel is *named* Acorn.
CAST = (
    ("dog", "squeaky ball", "loves the snow",
     (("dog_0_0", "Patch"), ("dog_3_0", "Sparky"), ("dog_4_0", "Woofer"))),
    ("cat", "ball of yarn", "loves warm, high places",
     (("cat_0_1", "Chirpy"), ("cat_0_2", "Tinsel"), ("cat_2_0", "Cinder"))),
    ("squirrel", "walnuts", "loves to climb",
     (("rodent_0_0", "Nutmeg"), ("rodent_1_0", "Acorn"))),
    ("reindeer", "carrot", "wants to fly",
     (("quadraped_0_8", "Vixen"), ("quadraped_1_8", "Blitzen"))),
    ("robot", "oil can", "loves gadgets",
     (("elemental_1_1", "Rivet"), ("elemental_3_1", "Echo"), ("elemental_4_0", "Jingle"))),
)

# Wild animals: scenery/ambience, never escapees.  (sprite id, name).
WILD = (
    ("avian_3_3", "Waddles"),
    ("avian_1_4", "Lolli"),
    ("avian_3_10", "Flurry"),
)


def make_roster(choice=None):
    """The playthrough's five critters, one per CAST species, all IN_BOX at HOME.

    `choice` picks one (sprite, name) pair from a species' tuple; it
    defaults to random.choice (seed `random` for a repeatable run).  Tests
    pass their own picker.
    """
    if choice is None:
        import random
        choice = random.choice
    critters = []
    for species, lure, habit, sprites in CAST:
        sprite, name = choice(sprites)
        critters.append(Critter(name, lure, HOME, species=species, sprite=sprite, habit=habit))
    return CritterRoster(critters)
