# SPDX-License-Identifier: MIT
"""The screens the loop shows -- cd-342.47.2.

The game runs as a sequence -- gift tag, title, game -- with the ornament
taking over whenever the board is set down (modes.py). Each screen has the
same few methods, so the loop (app.Game) doesn't care which is up:

- `group`: its displayio Group;
- `enter(now)`: it's just come on screen (again);
- `handle(point, now)`: this tick's touch point, None when there isn't one
  or the loop is swallowing a wake-up touch. Returns the next screen in the
  sequence, or None to stay;
- `update(now)`: once a tick, after handle.

The gift tag, title and game share one gesture tracker, so a finger that's
down across a change of screen is still one stroke.
"""
import displayio

import edge_gesture
import ornament
from story import News


class TagScreen:
    """FOR <PLAYER>, FROM CHRIS (gift_tag.py), until a tap or its time is up."""

    def __init__(self, tag, tracker, tlog, next_screen):
        self.group = tag.group
        self._tag = tag
        self._tracker = tracker
        self._tlog = tlog
        self._next = next_screen

    def enter(self, now):
        pass

    def handle(self, point, now):
        tracker = self._tracker
        tracker.update(point, now)
        if self._tlog is not None and point is None:
            self._tlog.end(now, "tag" if tracker.gesture_done else "nothing")
        if tracker.gesture_done or self._tag.done(now):
            print("t={:.1f} gift tag -> title ({})".format(
                now, "tapped" if tracker.gesture_done else "time up"))
            return self._next
        return None

    def update(self, now):
        pass


class TitleScreen:
    """CHRISTMAS CRITTERS (title_view.py), until a tap starts the game."""

    def __init__(self, view, tracker, tlog, next_screen):
        self.group = view.group
        self._view = view
        self._tracker = tracker
        self._tlog = tlog
        self._next = next_screen

    def enter(self, now):
        self._view.show()

    def handle(self, point, now):
        tracker = self._tracker
        tracker.update(point, now)
        if self._tlog is not None and point is None:
            self._tlog.end(now, "title" if tracker.gesture_done else "nothing")
        if tracker.gesture_done:  # a tap anywhere starts the game
            print("t={:.1f} title tapped: the game starts".format(now))
            return self._next
        return None

    def update(self, now):
        self._view.update(now)


class GameScreen:
    """The hunt: rooms to walk through, critters to find (nav_view.NavView)."""

    def __init__(self, nav, world, hunt, tracker, tlog, width, height):
        self.group = nav.group
        self.world = world
        self.hunt = hunt
        self._nav = nav
        self._tracker = tracker
        self._tlog = tlog
        self._width = width
        self._height = height
        self._started = False
        self._zone = None  # the edge zone under the finger, for nav's markers

    def enter(self, now):
        self._nav.refresh_backdrop()  # another screen may have had the shared bitmap
        if not self._started:
            self._started = True
            opening = self.hunt.start()  # sets the episode's gate, so before show_room
            self._show_room(now)
            self._tell(opening, now)

    def handle(self, point, now):
        nav, tracker = self._nav, self._tracker
        self._zone = (
            edge_gesture.edge_of(point[0], point[1], self._width, self._height)
            if point is not None and not nav.overlay_up
            else None
        )
        direction = tracker.update(point, now)
        # A move goes through a caption (it would otherwise eat the gesture:
        # cd-342.24); a centre tap moves the caption on, and a cutscene takes
        # every gesture, so the story can't be skipped.
        waits = nav.overlay_up and (direction is None or nav.cutscene_up)
        if self._tlog is not None and point is None and self._tlog.stroke_open:
            self._tlog.end(now, self._outcome(direction, waits))
        if waits:
            # Navigation waits: captions sit in the edge zones.
            if tracker.gesture_done:
                nav.tap_overlay(now)
        elif direction is not None:
            self._move(direction, now)
        elif tracker.center_tapped:
            messages = self.hunt.tapped()
            print("tap in {}: {}".format(self.world.current, messages))
            self._nav.show_scene(self.hunt.scene(), now)
            self._tell(messages, now)
        return None

    def update(self, now):
        self._nav.update(now, self._zone)

    def _move(self, direction, now):
        if self.world.move(direction):
            print("moved {} -> {}".format(direction, self.world.current))
            # May start the next episode, so before show_room reads the gate.
            messages = self.hunt.entered()
            self._show_room(now)
            self._tell(messages, now)
            return
        reason = self.hunt.bumped(direction)
        if reason:
            self._nav.tell(News([reason]), now)
        else:
            self._nav.bonk(now)

    def _show_room(self, now):
        self._nav.show_room(self.world.room.name, self.world.live_exits())
        self._nav.show_scene(self.hunt.scene(), now)

    def _tell(self, messages, now):
        """Show what the hunt just said (storyboard.py draws it)."""
        self._nav.tell(self.hunt.news(messages), now)

    def _outcome(self, direction, waits):
        """What the touch log says a finished stroke did."""
        nav, tracker = self._nav, self._tracker
        if not tracker.gesture_done:
            return "nothing (neither tap nor swipe)"
        if waits:
            return "cutscene advanced" if nav.cutscene_up else "caption advanced"
        if direction is not None:
            return "move " + direction + (
                "" if direction in self.world.live_exits() else " (blocked)") + (
                " through a caption" if nav.overlay_up else "")
        return "centre tap"


class OrnamentScreen:
    """The ornament scenes (ornament.py), shown while the board is set down.
    They borrow the room art's bitmap, so the game redraws its own on return."""

    def __init__(self, backdrop, width, height, power, sensors):
        self.group = displayio.Group()
        self._show = ornament.Show(self.group, backdrop, width, height)
        self._power = power
        self._sensors = sensors

    def enter(self, now):
        self._show.enter(now)

    def handle(self, point, now):
        return None

    def update(self, now):
        if self._power.lit:  # no point animating a dark screen
            self._show.update(now, lit=self._sensors.still)

