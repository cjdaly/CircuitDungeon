# SPDX-License-Identifier: MIT
"""The playable loop: one critter at a time, found and brought home -- cd-342.4.

Runs the episodes in episodes.py against the rooms.World and the
critters.CritterRoster. Starting an episode is the escape trigger (doc/
EPISODES.md sec 1): the critter leaves its box and only that episode's rooms
open. Then the player:

1. finds the lure and taps to take it (one held item, one critter loose)
2. finds the critter and taps it; without the lure, it says what it wants
3. taps it again holding the lure, and it follows them home
4. walks back to the tree, which starts the next episode

Each method returns the messages to show, as plain strings; this module has no
display code, so it runs under plain desktop Python (see tests/test_hunt.py).

v1 is text-only. The comic overlay kit (cd-342.9), escape cutscene (cd-342.10)
and image clues (cd-342.13) replace how these get shown, and the real ending is
cd-342.6.
"""
import episodes
from critters import HOME

HUNTING = "hunting"
GOING_HOME = "going_home"
DONE = "done"

# Stand-in text until cd-342.13 draws image clues.
_IMAGE_CLUE_TEXT = {
    "yarn_strand": "Yarn trail! Tap the top edge",
    "breeze": "You feel a chilly breeze",
}

_BANNER_CHARS = 15  # scale-2 terminalio on the round panel, see nav_view


def wrap(text, width=_BANNER_CHARS):
    """Word-wrap into a list of lines at most `width` characters where possible."""
    lines = []
    line = ""
    for word in text.split(" "):
        if line and len(line) + 1 + len(word) > width:
            lines.append(line)
            line = word
        else:
            line = line + " " + word if line else word
    lines.append(line)
    return lines


def _capitalized(text):
    return text[0].upper() + text[1:]


class Hunt:
    def __init__(self, world, roster, order=None):
        self._world = world
        self._critters = {c.species: c for c in roster.all()}
        species = [c.species for c in roster.all()]
        if order is None:
            order = episodes.make_order(species)
        # Episodes still being written (cd-342.14) are skipped.
        self._order = [s for s in order if s in episodes.EPISODES]
        self._next = 0
        self.stage = None
        self.episode = None
        self.critter = None
        self.held = None

    def start(self):
        """Begin the game. Returns the first escape's messages."""
        return self._start_next_episode()

    def _start_next_episode(self):
        if self._next >= len(self._order):
            self.stage = DONE
            self.episode = None
            self.critter = None
            self._world.set_gate(None)  # the whole map, as the end game will
            return ["All home! More critters soon"]
        species = self._order[self._next]
        self._next += 1
        self.episode = episodes.EPISODES[species]
        self.critter = self._critters[species]
        self.critter.escape(self.episode.hide_room)
        self.episode.open_on(self._world)
        self.stage = HUNTING
        self.held = None
        return ["{} escaped!".format(self.critter.name)] + self._escape_clues()

    def _escape_clues(self):
        return [
            self._clue_text(clue)
            for clue in self.episode.clues_for(episodes.ON_ESCAPE, HOME)
        ]

    def _clue_text(self, clue):
        if clue.form == episodes.IMAGE:
            return _IMAGE_CLUE_TEXT.get(clue.content, clue.content)
        return clue.content.format(name=self.critter.name)

    def entered(self):
        """The player just moved into the current room."""
        room = self._world.current
        if self.stage == GOING_HOME and room == HOME:
            home = self.episode.home_text.format(name=self.critter.name)
            return [home] + self._start_next_episode()

        messages = []
        if self.stage == DONE:
            return messages
        if room == episodes.ODD_CORNER:
            messages.append("Batteries! Just out of reach")
        if self.stage == HUNTING:
            messages.extend(self._room_clues(room))
            if room == self.episode.lure_room and self.held is None:
                messages.append(
                    "{} here! Tap it.".format(_capitalized(self.critter.preferred_item))
                )
            if room == self.episode.hide_room:
                messages.append("Something's here! Tap it.")
        return messages

    def bumped(self, direction):
        """A blocked move: the in-world reason, or None if there's simply no exit."""
        if self.episode is None or direction not in self._world.closed_exits():
            return None
        reason = self.episode.reason_for(self._world.current, direction)
        return reason.format(name=self.critter.name) if reason else None

    def tapped(self):
        """The player tapped the middle of the screen."""
        room = self._world.current
        if self.stage == DONE:
            return ["Merry Christmas!"]
        if self.stage == GOING_HOME:
            return ["{} is with you. Go home!".format(self.critter.name)]
        if room == self.episode.hide_room:
            return self._tapped_critter(room)
        if room == self.episode.lure_room and self.held is None:
            self.held = self.critter.preferred_item
            return ["Got the {}!".format(self.held)]
        if room == HOME:
            return self._escape_clues()
        if room == episodes.ODD_CORNER:
            return ["So close!"]
        clues = [
            self._clue_text(clue) for clue in self.episode.clues_for(episodes.ON_TAP, room)
        ]
        return clues or self._room_clues(room) or ["Nothing here"]

    def _room_clues(self, room):
        """This room's clues, shown on every visit (and tap) so they can't be missed."""
        return [
            self._clue_text(clue)
            for clue in self.episode.clues_for(episodes.ON_ENTER, room)
            if not (clue.lure_trail and self.held is not None)
        ]

    def _tapped_critter(self, room):
        name = self.critter.name
        held = () if self.held is None else (self.held,)
        if self.critter.try_retrieve(room, held):
            self.stage = GOING_HOME
            self.held = None
            return ["{} follows you home!".format(name)]
        return [
            "Found {}!".format(name),
            "{} wants the {}".format(self.critter.subject_pronoun, self.critter.preferred_item),
        ]
