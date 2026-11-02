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
an in-world reason when bumped.

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
from rooms import DOWN, LEFT

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
    def __init__(self, when, room, form, content, lure_trail=False):
        self.when = when
        self.room = room
        self.form = form
        self.content = content
        self.lure_trail = lure_trail  # points at the lure, so stops once it's held


class Episode:
    """One critter's hunt: which rooms are open, and where things are."""

    def __init__(self, species, open_rooms, hide_room, lure_room, closed_reasons, clues,
                 home_text="{name} is home!"):
        self.species = species
        self.home_text = home_text
        self.open_rooms = frozenset(open_rooms)
        self.hide_room = hide_room
        self.lure_room = lure_room
        # {(room, direction): text} for every exit from an open room into a
        # closed one -- shown when the player bumps it.
        self.closed_reasons = dict(closed_reasons)
        self.clues = tuple(clues)

    def open_on(self, world):
        world.set_gate(self.open_rooms)

    def reason_for(self, room, direction):
        return self.closed_reasons.get((room, direction))

    def clues_for(self, when, room):
        return [c for c in self.clues if c.when == when and c.room == room]


EPISODES = {
    # Episode 1 (always first): Chirpy, the short warm-up -- 3 moves:
    # Living Room -> Dining Room -> Kitchen -> Sun Porch, where she's sniffing
    # the fresh air at an open window. Yarn is up in the Sewing Nook off the
    # Dining Room; the Hallway off the tree is a plain false path; the
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
            ("Living Room", LEFT): "brr! too cold out there",
            ("Kitchen", DOWN): "too dark down there",
        },
        clues=(
            Clue(ON_ESCAPE, HOME, TEXT, "{name} loves fresh air!"),
            # Trailing in from the Sewing Nook, above.
            Clue(ON_ENTER, "Dining Room", IMAGE, "yarn_strand", lure_trail=True),
            Clue(ON_ENTER, "Kitchen", IMAGE, "breeze"),  # from the open window, to the right
        ),
        home_text="{name} curls up on the rug",
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
