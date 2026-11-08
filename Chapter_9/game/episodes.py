# SPDX-License-Identifier: MIT
"""Per-critter episodes: map gating, hiding/lure rooms, clues -- cd-342.12.

The game is a run of episodes, one escaped critter each (doc/EPISODES.md).
The house is one consistent graph (rooms.make_world()), but an episode
opens only part of it, shaped as a single path from the tree to where the
critter hides (3 moves for episode 1, 4 -- at most one 5 -- for the rest)
with dead-end side branches off it: false paths off the early rooms, one
of which holds the lure, and from the 3rd room (2nd in episode 1) a branch
to the Odd Corner -- batteries in sight, out of reach, until the finale.
No loops, so a dead end is really a dead end. Exits into closed rooms get
an in-world reason when bumped. Every episode holds its lure back until the
critter has been found, each in its own way (see Unlock, and doc/STORY.md).

Episodes are written to be order-independent -- each has its own open set,
nothing one episode uses up is needed by another -- so the order is a
policy, make_order(): cat first (the gentle one), reindeer last (sets up
the finale), the middle shuffled per playthrough (Chris, 2026-10-17).

Clue/reason text uses "{name}" for the critter's rolled name (critters
.make_roster()); it's all-caps on screen, so case here doesn't matter.

Pure data, no displayio/board imports -- runs under plain desktop Python
(see tests/test_episodes.py, which checks every episode's shape against
the real map).
"""

from critters import HOME
from rooms import DOWN, LEFT, RIGHT, UP

ODD_CORNER = "Odd Corner"

FIRST = "cat"
LAST = "reindeer"

# When a clue shows.
ON_ESCAPE = "escape"  # end of the escape cutscene, at HOME
ON_ENTER = "enter"  # entering its room
ON_TAP = "tap"  # tapping something in its room
CLUE_WHENS = (ON_ESCAPE, ON_ENTER, ON_TAP)

# What form it takes: a caption, or an image id from the (future) emanata/
# icon sheet.
TEXT = "text"
IMAGE = "image"
CLUE_FORMS = (TEXT, IMAGE)


class Clue:
    def __init__(self, when, room, form, content, lure_trail=False, until_found=False):
        self.when = when
        self.room = room
        self.form = form
        self.content = content
        # Points at the lure: shows once the lure can be reached, until it's held.
        self.lure_trail = lure_trail
        # Points at the critter: stops once it's been found.
        self.until_found = until_found


class Unlock:
    """What keeps the lure out of reach until the critter is found.

    Either an exit into the lure room is shut (`blocked_exit`, with `blocked_text`
    when bumped), or the room is open but the lure can't be taken yet, and says
    `locked_text`. `reveal` shows when the critter is found. `ready_text`, if any,
    shows on entering the lure room afterwards.

    `locked_art` is what the lure room shows while it's locked (scene_art.NAMES):
    None draws nothing, as in a dark room.
    """

    def __init__(self, reveal, blocked_exit=None, blocked_text=None, locked_text=None,
                 ready_text=None, locked_art=None):
        self.reveal = reveal
        self.blocked_exit = blocked_exit
        self.blocked_text = blocked_text
        self.locked_text = locked_text
        self.ready_text = ready_text
        self.locked_art = locked_art


class Episode:
    """One critter's hunt: which rooms are open, and where things are."""

    def __init__(self, species, open_rooms, hide_room, lure_room, closed_reasons, clues,
                 home_text="{name} is home!", unlock=None):
        self.species = species
        self.home_text = home_text
        self.open_rooms = frozenset(open_rooms)
        self.hide_room = hide_room
        self.lure_room = lure_room
        # {(room, direction): text} for every exit from an open room into a
        # closed one -- shown when the player bumps it.
        self.closed_reasons = dict(closed_reasons)
        self.clues = tuple(clues)
        self.unlock = unlock

    def open_on(self, world):
        """Start of the episode: open its rooms, except behind any blocked exit."""
        if self.unlock is not None and self.unlock.blocked_exit is not None:
            world.set_gate(self.open_rooms - {self.lure_room})
        else:
            world.set_gate(self.open_rooms)

    def open_lure_room(self, world):
        world.set_gate(self.open_rooms)

    def reason_for(self, room, direction):
        if self.unlock is not None and (room, direction) == self.unlock.blocked_exit:
            return self.unlock.blocked_text
        return self.closed_reasons.get((room, direction))

    def clues_for(self, when, room):
        return [c for c in self.clues if c.when == when and c.room == room]


# Bump text shared by the episodes. It says something true: the critter is elsewhere.
_NOT_THAT_WAY = "{name} isn't that way"
_BOXES = "Too many boxes that way"  # the Odd Corner's other sides
_TOO_COLD = "brr! too cold out there"


EPISODES = {
    # Episode 1 (always first): Chirpy, the short warm-up -- 3 moves:
    # Living Room -> Dining Room -> Kitchen -> Sun Porch, where she's sniffing
    # the fresh air at an open window. Yarn is up in the Sewing Nook off the
    # Dining Room, whose door is stuck until she's found; the Hallway off the tree is a plain false path; the
    # Kitchen (room 2 here) has the branch up to the Odd Corner. Home, she
    # curls up on the Living Room rug.
    "cat": Episode(
        species="cat",
        open_rooms=(
            "Living Room", "Hallway", "Dining Room", "Sewing Nook",
            "Kitchen", ODD_CORNER, "Sun Porch",
        ),
        hide_room="Sun Porch",
        lure_room="Sewing Nook",
        closed_reasons={
            ("Living Room", LEFT): _TOO_COLD,
            ("Kitchen", DOWN): "too dark down there",
            ("Hallway", LEFT): _TOO_COLD,
            ("Hallway", RIGHT): _NOT_THAT_WAY,
            (ODD_CORNER, LEFT): _BOXES,
            (ODD_CORNER, RIGHT): _BOXES,
            (ODD_CORNER, UP): _BOXES,
        },
        clues=(
            Clue(ON_ESCAPE, HOME, TEXT, "{name} loves fresh air!"),
            # Trailing in from the Sewing Nook, above.
            Clue(ON_ENTER, "Dining Room", IMAGE, "yarn_strand", lure_trail=True),
            Clue(ON_ENTER, "Kitchen", IMAGE, "breeze"),  # from the open window, to the right
        ),
        home_text="{name} curls up on the rug",
        unlock=Unlock(
            "The stuck door creaks open!",
            blocked_exit=("Dining Room", UP), blocked_text="The door's stuck",
        ),
    ),
    # The dog digs: a drift off the Front Porch hides the Snow Fort and its ball,
    # until the dog, found out in the Yard, tunnels through.
    "dog": Episode(
        species="dog",
        open_rooms=(
            "Living Room", "Entryway", "Bedroom", "Front Porch", "Snow Fort",
            "Front Walk", ODD_CORNER, "Yard",
        ),
        hide_room="Yard",
        lure_room="Snow Fort",
        closed_reasons={
            ("Living Room", RIGHT): _NOT_THAT_WAY,
            ("Living Room", UP): _NOT_THAT_WAY,
            ("Bedroom", LEFT): _NOT_THAT_WAY,
            ("Bedroom", RIGHT): _NOT_THAT_WAY,
            ("Bedroom", UP): _NOT_THAT_WAY,
            ("Front Walk", RIGHT): _NOT_THAT_WAY,
            ("Yard", LEFT): _TOO_COLD,
            ("Yard", RIGHT): _NOT_THAT_WAY,
            ("Yard", DOWN): _TOO_COLD,
            (ODD_CORNER, DOWN): _BOXES,
            (ODD_CORNER, LEFT): _BOXES,
            (ODD_CORNER, UP): _BOXES,
        },
        clues=(
            Clue(ON_ESCAPE, HOME, TEXT, "{name} loves the snow!"),
            Clue(ON_ENTER, "Entryway", TEXT, "Paw prints! Tap the bottom edge", until_found=True),
            Clue(ON_ENTER, "Front Porch", TEXT, "Woof! Tap the bottom edge", until_found=True),
            Clue(ON_ENTER, "Front Walk", TEXT, "Woof woof! Tap the bottom edge", until_found=True),
            Clue(ON_ENTER, "Front Porch", TEXT, "Tunnel! Tap the right edge", lure_trail=True),
        ),
        unlock=Unlock(
            "Dig dig dig! A path opens!",
            blocked_exit=("Front Porch", RIGHT), blocked_text="The snow's too deep",
        ),
    ),
    # The robot has been at the fuse box, so the Garage is pitch black until it's
    # found. Nothing is blocked: the room is open, you just can't find anything.
    "robot": Episode(
        species="robot",
        open_rooms=(
            "Living Room", "Hallway", "Bedroom", "Back Door", "Garage",
            "Cellar Door", ODD_CORNER, "Basement",
        ),
        hide_room="Basement",
        lure_room="Garage",
        closed_reasons={
            ("Living Room", LEFT): _NOT_THAT_WAY,
            ("Living Room", RIGHT): _NOT_THAT_WAY,
            ("Bedroom", DOWN): _NOT_THAT_WAY,
            ("Bedroom", RIGHT): _NOT_THAT_WAY,
            ("Bedroom", UP): _NOT_THAT_WAY,
            ("Back Door", LEFT): _TOO_COLD,
            ("Basement", UP): _NOT_THAT_WAY,
            ("Basement", RIGHT): _NOT_THAT_WAY,
            (ODD_CORNER, DOWN): _BOXES,
            (ODD_CORNER, LEFT): _BOXES,
            (ODD_CORNER, RIGHT): _BOXES,
        },
        clues=(
            Clue(ON_ESCAPE, HOME, TEXT, "{name} loves gadgets!"),
            Clue(ON_ENTER, "Hallway", TEXT, "Beep! Tap the left edge", until_found=True),
            Clue(ON_ENTER, "Back Door", TEXT, "Beep! Tap the bottom edge", until_found=True),
            Clue(ON_ENTER, "Cellar Door", TEXT, "Beep beep! Tap the right edge", until_found=True),
            Clue(ON_ENTER, "Back Door", TEXT, "Oil drips! Tap the top edge", lure_trail=True),
        ),
        unlock=Unlock(
            "Zap! The lights come on!",
            locked_text="Too dark to find anything",
        ),
    ),
    # You walk past the walnuts on the dining table with no reason to take them.
    # Flurry the owl, wild, points the way near the end.
    "squirrel": Episode(
        species="squirrel",
        open_rooms=(
            "Living Room", "Dining Room", "Entryway", "Bedroom", "Front Porch",
            "Snow Fort", "Front Walk", ODD_CORNER, "Tree House",
        ),
        hide_room="Tree House",
        lure_room="Dining Room",
        closed_reasons={
            ("Living Room", UP): _NOT_THAT_WAY,
            ("Dining Room", UP): _NOT_THAT_WAY,
            ("Dining Room", RIGHT): _NOT_THAT_WAY,
            ("Bedroom", LEFT): _NOT_THAT_WAY,
            ("Bedroom", RIGHT): _NOT_THAT_WAY,
            ("Bedroom", UP): _NOT_THAT_WAY,
            ("Front Walk", DOWN): _TOO_COLD,
            (ODD_CORNER, DOWN): _BOXES,
            (ODD_CORNER, LEFT): _BOXES,
            (ODD_CORNER, UP): _BOXES,
        },
        clues=(
            Clue(ON_ESCAPE, HOME, TEXT, "{name} loves to climb!"),
            Clue(ON_ENTER, "Entryway", TEXT, "Nut shells! Tap the bottom edge", until_found=True),
            Clue(ON_ENTER, "Front Porch", TEXT, "Nut shells! Tap the bottom edge", until_found=True),
            Clue(ON_ENTER, "Front Walk", TEXT, "Whoo! Tap the right edge", until_found=True),
        ),
        unlock=Unlock(
            "Walnuts on the dining table!",
            locked_text="Walnuts. You're not hungry",
            locked_art="walnuts",  # in plain sight, you just don't want them yet
        ),
    ),
    # Always last. Its failed takeoff from the Roof brings the snow down on the
    # snowman in the Yard, which frees his carrot nose. Nothing later needs him.
    "reindeer": Episode(
        species="reindeer",
        open_rooms=(
            "Living Room", "Hallway", "Back Door", "Yard", "Bedroom", "Kids' Bedroom",
            "Attic", ODD_CORNER, "Roof",
        ),
        hide_room="Roof",
        lure_room="Yard",
        closed_reasons={
            ("Living Room", LEFT): _NOT_THAT_WAY,
            ("Living Room", RIGHT): _NOT_THAT_WAY,
            ("Back Door", DOWN): _NOT_THAT_WAY,
            ("Back Door", UP): _NOT_THAT_WAY,
            ("Yard", UP): _NOT_THAT_WAY,
            ("Yard", LEFT): _TOO_COLD,
            ("Yard", DOWN): _TOO_COLD,
            ("Bedroom", DOWN): _NOT_THAT_WAY,
            (ODD_CORNER, DOWN): _BOXES,
            (ODD_CORNER, RIGHT): _BOXES,
            (ODD_CORNER, UP): _BOXES,
        },
        clues=(
            Clue(ON_ESCAPE, HOME, TEXT, "{name} wants to fly!"),
            Clue(ON_ENTER, "Hallway", TEXT, "Hoofprints! Tap the right edge", until_found=True),
            Clue(ON_ENTER, "Bedroom", TEXT, "Clomp! Tap the top edge", until_found=True),
            Clue(ON_ENTER, "Attic", TEXT, "Clomp! Tap the top edge", until_found=True),
            Clue(ON_ENTER, "Hallway", TEXT, "Cold air! Tap the left edge", lure_trail=True),
            Clue(ON_ENTER, "Back Door", TEXT, "Snow crash! Tap the left edge", lure_trail=True),
        ),
        unlock=Unlock(
            "Whump! Snow slides off!",
            locked_text="He needs that nose",
            ready_text="The snowman's flat!",
            locked_art="snowman",
        ),
    ),
}


def spine(world, episode):
    """The open path from HOME to the hiding room, as a list of room names.

    Episodes have no loops (tested), so this is the one way there; walks
    open rooms only. None if the hiding room can't be reached.
    """
    came_from = {HOME: None}
    frontier = [HOME]
    while frontier:
        name = frontier.pop(0)
        if name == episode.hide_room:
            path = []
            while name is not None:
                path.append(name)
                name = came_from[name]
            return path[::-1]
        for dest in world.get(name).exits.values():
            if dest in episode.open_rooms and dest not in came_from:
                came_from[dest] = name
                frontier.append(dest)
    return None


def make_order(species, randrange=None):
    """Episode order for one playthrough: FIRST, the rest shuffled, LAST.

    `species` is every escaping species (critters.CAST order). `randrange`
    defaults to random.randrange (CircuitPython's random has no shuffle,
    so this is a plain Fisher-Yates); tests pass their own.
    """
    if randrange is None:
        import random
        randrange = random.randrange
    middle = [s for s in species if s not in (FIRST, LAST)]
    for i in range(len(middle) - 1, 0, -1):
        j = randrange(i + 1)
        middle[i], middle[j] = middle[j], middle[i]
    return [FIRST] + middle + [LAST]
