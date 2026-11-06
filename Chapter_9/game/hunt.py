# SPDX-License-Identifier: MIT
"""The playable loop: one critter at a time, found and brought home -- cd-342.4.

Runs the episodes in episodes.py against the rooms.World and the
critters.CritterRoster. Starting an episode is the escape trigger (doc/
EPISODES.md sec 1): the critter leaves its box and only that episode's rooms
open. Then the player:

1. finds the critter and taps it; without the lure, it says what it wants, and
   the episode's unlock lets the lure be reached (episodes.Unlock)
2. finds the lure and taps to take it (one held item, one critter loose)
3. taps the critter again holding the lure, and it follows them home
4. walks back to the tree, which starts the next episode

Each method returns the messages to show, as plain strings; this module has no
display code, so it runs under plain desktop Python (see tests/test_hunt.py).

What's in the room to see and tap -- the critter, the lure, the item in hand --
comes from scene() (cd-342.26), and .event says what a tap just did, so the view
can draw it rather than the text telling you to tap. The escape cutscene
(cd-342.10) and image clues (cd-342.13) are still to come, and the real ending is
cd-342.6.
"""
import episodes
from critters import HOME
from scene_art import HIDING_SPOTS

HUNTING = "hunting"
GOING_HOME = "going_home"
DONE = "done"

# What the last tapped() did, for the view to show it (Hunt.event).
FOUND = "found"
TOOK = "took"
RETRIEVED = "retrieved"

# How the critter looks in the room where it hides (Scene.pose).
HIDING = "hiding"
WAITING = "waiting"  # found, waiting for its lure

# Stand-in text until cd-342.13 draws image clues.
_IMAGE_CLUE_TEXT = {
    "yarn_strand": "Yarn trail! Tap the top edge",
    "breeze": "You feel a chilly breeze",
}

# A caption opens each episode with the hour, tied to its slot and not the critter.
_HOURS = ("9 PM", "10 PM", "11 PM", "Near midnight", "Midnight")

_BANNER_CHARS = 15  # Bangers on the round panel; tests check the real pixel widths


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


class Scene:
    """What the current room shows, as plain data. Every field is None when absent.

    spot: scene_art name of the critter's hiding spot
    critter: its sprite id (critters.Critter.sprite), when it's in this room
    pose: HIDING (peeking out) or WAITING (found)
    lure: scene_art name of what's at the lure spot (the lure, or what hides it)
    follower: sprite id of a critter following you home
    held: the item in hand
    """

    def __init__(self, spot=None, critter=None, pose=None, lure=None, follower=None,
                 held=None):
        self.spot = spot
        self.critter = critter
        self.pose = pose
        self.lure = lure
        self.follower = follower
        self.held = held


class Hunt:
    def __init__(self, world, roster, order=None, player=None):
        self._world = world
        self._critters = {c.species: c for c in roster.all()}
        species = [c.species for c in roster.all()]
        if order is None:
            order = episodes.make_order(species)
        self._order = list(order)
        self._next = 0
        self.stage = None
        self.episode = None
        self.critter = None
        self.held = None
        self._found = False
        self._locked = False
        self._player = player  # who this board is for, if it says
        self.event = None  # FOUND / TOOK / RETRIEVED, set by tapped()

    def start(self):
        """Begin the game. Returns the first escape's messages."""
        return self._start_next_episode()

    def _start_next_episode(self):
        if self._next >= len(self._order):
            self.stage = DONE
            self.episode = None
            self.critter = None
            self._world.set_gate(None)  # the whole map, as the end game will
            return ["All home!"] + self._merry_christmas()
        species = self._order[self._next]
        hour = _HOURS[min(self._next, len(_HOURS) - 1)]
        self._next += 1
        self.episode = episodes.EPISODES[species]
        self.critter = self._critters[species]
        self.critter.escape(self.episode.hide_room)
        self.episode.open_on(self._world)
        self.stage = HUNTING
        self.held = None
        self._found = False
        self._locked = self.episode.unlock is not None
        return [hour, "{} escaped!".format(self.critter.name)] + self._escape_clues()

    def _merry_christmas(self):
        if self._player:
            return ["Merry Christmas,", "{}!".format(self._player)]
        return ["Merry Christmas!"]

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
                lure_text = self._lure_text()
                if lure_text:
                    messages.append(lure_text)
        return messages

    def _lure_text(self):
        """The lure room's own words, if it has any: the lure itself is drawn."""
        unlock = self.episode.unlock
        if self._locked:
            return unlock.locked_text.format(name=self.critter.name)
        if unlock is not None and unlock.ready_text:
            return unlock.ready_text
        return None

    def scene(self):
        """What the current room shows (Scene)."""
        if self.stage == DONE:
            return Scene()
        room = self._world.current
        episode = self.episode
        scene = Scene(held=self.held)
        if room == episodes.ODD_CORNER:
            scene.lure = "batteries"
        if room == episode.hide_room:
            scene.spot = HIDING_SPOTS.get(room)
            if self.stage == HUNTING:
                scene.critter = self.critter.sprite
                scene.pose = WAITING if self._found else HIDING
        if room == episode.lure_room and self.stage == HUNTING and self.held is None:
            scene.lure = episode.unlock.locked_art if self._locked else self.critter.preferred_item
        if self.stage == GOING_HOME:
            scene.follower = self.critter.sprite
        return scene

    def bumped(self, direction):
        """A blocked move: the in-world reason, or None if there's simply no exit."""
        if self.episode is None or direction not in self._world.closed_exits():
            return None
        reason = self.episode.reason_for(self._world.current, direction)
        return reason.format(name=self.critter.name) if reason else None

    def tapped(self):
        """The player tapped the middle of the screen."""
        self.event = None
        room = self._world.current
        if self.stage == DONE:
            return self._merry_christmas()
        if self.stage == GOING_HOME:
            return ["{} is with you. Go home!".format(self.critter.name)]
        if room == self.episode.hide_room:
            return self._tapped_critter(room)
        if room == self.episode.lure_room and self.held is None:
            if self._locked:
                return [self._lure_text()]
            self.held = self.critter.preferred_item
            self.event = TOOK
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
            if not (clue.lure_trail and (self._locked or self.held is not None))
            and not (clue.until_found and self._found)
        ]

    def _tapped_critter(self, room):
        name = self.critter.name
        held = () if self.held is None else (self.held,)
        if self.critter.try_retrieve(room, held):
            self.stage = GOING_HOME
            self.held = None
            self.event = RETRIEVED
            return ["{} follows you home!".format(name)]
        # Finding it: the view shouts FOUND! first (event), then these.
        messages = [
            "{} wants the {}".format(self.critter.subject_pronoun, self.critter.preferred_item),
        ]
        if not self._found:
            self.event = FOUND
        self._found = True
        if self._locked:
            self._locked = False
            self.episode.open_lure_room(self._world)
            messages.append(self.episode.unlock.reveal)
        return messages
