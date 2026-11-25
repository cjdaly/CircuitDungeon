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

Each method returns the messages to show, as plain strings, and news() wraps
them with what else the screen needs (a story.News): .event says what a tap
just did, so the view can draw it rather than the text telling you to tap, and
.cutscenes says which cutscene plays before which message (the escape,
cd-342.10; the finale's, finale.py). What's in the room to see and tap -- the
critter, the lure, the item in hand -- comes from scene() (cd-342.26). Both are
story.py's plain data; storyboard.py turns News into comic beats. This module
has no display code, so it runs under plain desktop Python (see
tests/test_hunt.py).

After the last episode comes the finale (cd-342.6, doc/EPISODES.md sec 6):
every critter bursts out again (PARADE), you lead them to the Odd Corner where
they stack up and get the batteries (CARRYING), and bringing them home ends the
game (DONE).
"""
import episodes
import finale
from critters import CAST, HIDING as CRITTER_HIDING, HOME, IN_BOX, LOOSE, RETURNED
from scene_art import HIDING_SPOTS
# What the hunt reports (story.py), named here too for the hunt's tests.
from story import (BOX_CLOSED, BOX_EMPTY, BOX_HOME, BURST, CHARGED, ESCAPE_SCENE,  # noqa: F401
                   ESCAPED, FOUND, HIDING, RETRIEVED, SHELF, TOOK, TOWER, WAITING, Escape,
                   News, Scene)

HUNTING = "hunting"
GOING_HOME = "going_home"
PARADE = "parade"  # the finale: everyone loose, following you to the Odd Corner
CARRYING = "carrying"  # ...and back to the tree with the batteries
DONE = "done"

# The tower, bottom to top: the biggest critters underneath.
TOWER_ORDER = ("reindeer", "dog", "robot", "cat", "squirrel")

# Stand-in text until cd-342.13 draws image clues.
_IMAGE_CLUE_TEXT = {
    "yarn_strand": "Yarn trail! Tap the top edge",
    "breeze": "You feel a chilly breeze",
}

# A caption opens each episode with the hour, tied to its slot and not the critter.
_HOURS = ("9 PM", "10 PM", "11 PM", "Near midnight", "Midnight")

# Short names for the "<critter> wants the <item>" line, so it fits two lines;
# the thought bubble beside it shows the item itself.
_SHORT_ITEM = {"ball of yarn": "yarn", "squeaky ball": "ball"}

class Hunt:
    def __init__(self, world, roster, order=None, player=None,
                 difficulty=episodes.DEFAULT_DIFFICULTY):
        self._world = world
        self.difficulty = difficulty  # episodes.EASY / MEDIUM / HARD: how the clues help
        self._here = world.current  # the room before this move
        self._came_by = None  # the edge the last move came in by, for a follower
        self._homecoming = None  # (species, edge): who you just brought home, and how
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
        self.event = None  # FOUND / TOOK / RETRIEVED / ESCAPED
        self.escape = None  # Escape, the last critter to get out
        self.call = None  # (word, direction): MEDIUM's critter, heard through that exit
        self.cutscenes = ()  # ((message index, cutscene name), ...) for the last messages

    def start(self):
        """Begin the game. Returns the first escape's messages."""
        self._quiet()
        return self._start_next_episode(lead=0)

    def _quiet(self):
        self.event = None
        self.cutscenes = ()
        self.call = None

    def news(self, messages):
        """`messages`, just returned by start(), entered() or tapped(), with
        what else the screen needs to show them (story.News)."""
        escaping = any(name == ESCAPE_SCENE for _index, name in self.cutscenes)
        return News(messages, self.event, self.cutscenes,
                    escape=self.escape if escaping else None,
                    want=self.critter.preferred_item if self.critter else None,
                    parade=len(self._parade()), call=self.call)

    def _start_next_episode(self, lead):
        """`lead`: how many messages the caller puts ahead of these."""
        if self._next >= len(self._order):
            self.episode = None
            self.critter = None
            self._world.set_gate(None)  # the whole map, for the finale and after
            if any(c.state == RETURNED for c in self._critters.values()):
                return self._begin_finale(lead)
            self.stage = DONE  # nobody to burst out (a game with no episodes)
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
        self.event = ESCAPED
        self.escape = Escape(self.critter.species, self.critter.sprite, self.critter.name,
                             self._first_step())
        self.cutscenes = ((lead + 1, ESCAPE_SCENE),)  # after the hour
        return [hour, "{} escaped!".format(self.critter.name)] + self._escape_clues()

    def _first_step(self):
        path = episodes.spine(self._world, self.episode)
        if not path or len(path) < 2:
            return None
        for direction, dest in self._world.get(HOME).exits.items():
            if dest == path[1]:
                return direction
        return None

    def skip_to_finale(self):
        """Review switch (settings.toml FINALE_NOW): every critter already
        found and home, so start() goes straight to the finale."""
        for critter in self._critters.values():
            if critter.escape(HOME):
                critter.try_retrieve(HOME, (critter.preferred_item,))
        self._next = len(self._order)

    def _begin_finale(self, lead):
        for critter in self._critters.values():
            critter.burst()
        self.stage = PARADE
        self.held = None
        self._came_by = None  # they burst out of their boxes: nobody walks in
        self.event = BURST
        self.cutscenes = ((lead + 1, finale.BURST_SCENE),)  # after "All home!"
        return ["All home!", "Uh oh! They're running flat!",
                "They need fresh batteries!", "Lead them to the Odd Corner!"]

    def _parade(self):
        loose = [(species, c.sprite) for species, c in self._critters.items() if c.state == LOOSE]
        loose.sort(key=lambda pair: TOWER_ORDER.index(pair[0])
                   if pair[0] in TOWER_ORDER else len(TOWER_ORDER))
        return tuple(loose)

    def _reached_batteries(self):
        self.stage = CARRYING
        self.held = "batteries"
        self.event = TOWER
        self.cutscenes = ((1, finale.TOWER_SCENE),)
        return ["The batteries! Everybody up!", "Got them!", "Now, everyone home!"]

    def _ending(self):
        flier = self._critters.get("reindeer")
        for critter in self._critters.values():
            critter.recharge()
        self.stage = DONE
        self.held = None
        self.event = CHARGED
        messages = ["Fresh batteries all round!"]
        self.cutscenes = ((0, finale.HOP_SCENE),)
        if flier is not None:
            self.cutscenes += ((2, finale.LIFTOFF_SCENE),)
            messages += ["And look...", "{} can fly!".format(flier.name)]
        messages += ["Only crumbs on Santa's plate!", "And a note...", "THANKS! NICE ROBOTS!"]
        return messages + self._merry_christmas()

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
        self._quiet()
        room = self._world.current
        came_from, self._here = self._here, room
        self._came_by = self._homecoming = None
        for direction, dest in self._world.get(room).exits.items():
            if dest == came_from:
                self._came_by = direction
        if self.stage == PARADE:
            return self._reached_batteries() if room == episodes.ODD_CORNER else []
        if self.stage == CARRYING:
            return self._ending() if room == HOME else []
        if self.stage == GOING_HOME and room == HOME:
            self._homecoming = (self.critter.species, self._came_by)
            home = self.episode.home_text.format(name=self.critter.name)
            return [home] + self._start_next_episode(lead=1)

        messages = []
        if self.stage == DONE:
            return messages
        if room == episodes.ODD_CORNER:
            messages.append("Batteries! Just out of reach")
        if self.stage == HUNTING:
            messages.extend(self._room_clues(room))
            self.call = self._earshot(room)
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
        room = self._world.current
        boxes = self._boxes() if room == HOME else None
        if self.stage == DONE:
            return Scene(boxes=boxes)
        homecoming = self._homecoming if room == HOME else None
        if self.stage in (PARADE, CARRYING):
            scene = Scene(held=self.held, boxes=boxes, parade=self._parade(),
                          follower_from=self._came_by, homecoming=homecoming)
            if room == episodes.ODD_CORNER and self.stage == PARADE:
                scene.lure, scene.lure_at = "batteries", SHELF
            return scene
        episode = self.episode
        scene = Scene(held=self.held, boxes=boxes, homecoming=homecoming)
        if room == episodes.ODD_CORNER:
            scene.lure = "batteries"
            scene.lure_at = SHELF
        if room == episode.hide_room:
            scene.spot = HIDING_SPOTS.get(room)
            if self.stage == HUNTING:
                scene.critter = self.critter.sprite
                scene.pose = WAITING if self._found else HIDING
        if room == episode.lure_room and self.stage == HUNTING and self.held is None:
            scene.lure = episode.unlock.locked_art if self._locked else self.critter.preferred_item
        if self.stage == GOING_HOME:
            scene.follower = self.critter.sprite
            scene.follower_from = self._came_by
        return scene

    def _short_item(self):
        item = self.critter.preferred_item
        return _SHORT_ITEM.get(item, item)

    def _boxes(self):
        boxes = []
        for species, _lure, _habit, _sprites in CAST:
            critter = self._critters.get(species)
            if critter is None:
                continue
            if critter.state == IN_BOX:
                state = BOX_CLOSED
            elif critter.state in (CRITTER_HIDING, LOOSE) or (
                    critter is self.critter and self.stage == GOING_HOME):
                state = BOX_EMPTY
            else:
                state = BOX_HOME
            boxes.append((species, state, critter.sprite))
        return tuple(boxes)

    def bumped(self, direction):
        """A blocked move: the in-world reason, or None if there's simply no exit."""
        if self.episode is None or direction not in self._world.closed_exits():
            return None
        reason = self.episode.reason_for(self._world.current, direction)
        return reason.format(name=self.critter.name) if reason else None

    def tapped(self):
        """The player tapped the middle of the screen."""
        self._quiet()
        self._came_by = self._homecoming = None  # anyone following is already in the room
        room = self._world.current
        if self.stage == DONE:
            return self._merry_christmas()
        if self.stage == PARADE:
            return ["To the Odd Corner!"]
        if self.stage == CARRYING:
            return ["Back to the tree!"]
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
        self.call = self._earshot(room)  # listening again
        if self.call is not None:
            return clues
        return clues or self._room_clues(room) or ["Nothing here"]

    def _earshot(self, room):
        """MEDIUM's clue (cd-342.48): from a room next to the critter's, you
        hear it -- its call and the exit it's through. None from anywhere
        else, or at other levels."""
        episode = self.episode
        if self.difficulty != episodes.MEDIUM or not episode.call:
            return None
        if self.stage != HUNTING or room == episode.hide_room:
            return None
        for direction, dest in self._world.get(room).exits.items():
            if dest == episode.hide_room and self._world.is_open(dest):
                return (episode.call, direction)
        return None

    def _room_clues(self, room):
        """This room's clues, shown on every visit (and tap) so they can't be missed.
        EASY only: they say which edge to tap (cd-342.40)."""
        if self.difficulty != episodes.EASY:
            return []
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
            "{} wants the {}".format(self.critter.name, self._short_item()),
        ]
        if not self._found:
            self.event = FOUND
        self._found = True
        if self._locked:
            self._locked = False
            self.episode.open_lure_room(self._world)
            messages.append(self.episode.unlock.reveal)
        return messages
