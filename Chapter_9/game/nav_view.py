# SPDX-License-Identifier: MIT
"""Interactive-mode display group: room label, edge-exit markers, comic overlays
-- cd-342.2.

Lifted from Chapter_8/game/room_nav_demo.py (cd-45v.4's prototype, feel-tested
on real hardware 2026-09-13) and turned into a reusable view instead of a
standalone script. A small circle near the outer end of each direction's tap wedge
shows, live, whether that direction is a real exit from the current room
(pulsing green if so, dim/static if not); touching a zone snaps its dot to
gold (live exit) or red (blocked) immediately, so the margin feel and the
room graph can both be judged by eye. The room's name sits persistently at
the top (room_banner.RoomLabel); the middle is for what's in the room to see
and tap (scene_view.SceneView, cd-342.26). Messages and bump feedback are comic overlays
(comic.py, beats.py); while one is up the app suspends navigation, because a tap
on a caption in an edge zone must not walk you out of the room (doc/STYLE.md sec 9).

This is the navigation chrome only -- room scenery/actor art layers under it
later (sprite_scale.py), which is why the markers/label are appended after
the background rather than owning the whole group.

STATUS: desk-checked only (displayio isn't importable under plain desktop
Python); the underlying pattern is the one already proven on-device in
Chapter 8. tests/test_app_smoke.py drives it through app.run() against
stubbed displayio, which catches wiring bugs but not how it looks.
"""
import math

import displayio
import vectorio

import comic
import comic_fonts
import escape
import rooms
import storyboard
from backdrop import Backdrop
from beats import BeatPlayer
from room_banner import RoomLabel
from scene_view import SceneView

_BG_COLOR = 0x101018

_ROOM_NAME_Y = 50  # top band, under the UP marker; the middle is the scene's

_MARKER_RADIUS = 9
_AVAILABLE_DIM = 0x1A4028
_AVAILABLE_BRIGHT = 0x40FF80
_BLOCKED_IDLE = 0x2A1A1A  # static, not pulsing -- reads as "don't bother"
_ACTIVE_GO_COLOR = 0xFFD040  # gold -- touching a zone that IS a live exit
_ACTIVE_BLOCKED_COLOR = 0xFF4040  # red -- touching a zone that is NOT
_PULSE_PERIOD = 1.4  # seconds per idle pulse cycle, available zones only

# Markers sit near the outer end of each direction's tap wedge
# (edge_gesture.CENTER_RADIUS out to the bezel), clear of the centre text.
_MARGIN_MID = 22


def _blend(color_a, color_b, t):
    """Linear-interpolate two 0xRRGGBB colors; t=0 -> a, t=1 -> b."""
    ar, ag, ab = (color_a >> 16) & 0xFF, (color_a >> 8) & 0xFF, color_a & 0xFF
    br, bg, bb = (color_b >> 16) & 0xFF, (color_b >> 8) & 0xFF, color_b & 0xFF
    r = int(ar + (br - ar) * t)
    g = int(ag + (bg - ag) * t)
    b = int(ab + (bb - ab) * t)
    return (r << 16) | (g << 8) | b


class _Director:
    """What the beat player shows a beat on: the comic stage for its words, and the
    scene for its cutscene shot. Close-up shots hide the room's chrome."""

    def __init__(self, stage, things, chrome, label):
        self._stage, self._things, self._chrome, self._label = stage, things, chrome, label

    def show(self, beat, now):
        self._things.shot(beat.shot, now)
        self._things.update(now)  # the shot's things where they'll be, for keep_clear
        covers = self._stage.show(beat, now, self._things.keep_clear(),
                                  self._things.dancer_rects())
        self._things.avoid(covers, now)
        self._label.make_way(self._stage.caption_band == comic.TOP)
        self._chrome.hidden = beat.shot in escape.CLOSE_SHOTS

    def clear(self):
        self._stage.clear()
        self._things.shot(None, 0.0)
        self._things.avoid(None, 0.0)
        self._label.make_way(False)
        self._chrome.hidden = False


class NavView:
    """Owns the interactive-mode displayio Group (`.group`)."""

    def __init__(self, width, height, backdrop_root="/art/rooms"):
        self.group = displayio.Group()

        bg_palette = displayio.Palette(1)
        bg_palette[0] = _BG_COLOR
        # A shape, not a bitmap: a 240x240 bitmap costs ~7.7 KB even in one colour.
        self.group.append(vectorio.Rectangle(pixel_shader=bg_palette, width=width, height=height,
                                             x=0, y=0))
        self._backdrop = Backdrop(backdrop_root)  # the room's art, if it has some
        self.art_set = self._backdrop.art_set  # which room-art set is deployed
        self.backdrop = self._backdrop  # shared with the ornament screen (ornament.Show)
        self.group.append(self._backdrop.group)
        self._scene = displayio.Group()  # what a shake moves
        self.group.append(self._scene)
        self._things = SceneView(backdrop_root)
        self._scene.append(self._things.group)

        positions = {
            rooms.UP: (width // 2, _MARGIN_MID),
            rooms.DOWN: (width // 2, height - _MARGIN_MID),
            rooms.LEFT: (_MARGIN_MID, height // 2),
            rooms.RIGHT: (width - _MARGIN_MID, height // 2),
        }
        self._chrome = displayio.Group()  # edge markers + room name
        self._scene.append(self._chrome)
        self._markers = {}
        for direction, (x, y) in positions.items():
            palette = displayio.Palette(1)
            palette[0] = _BLOCKED_IDLE
            self._chrome.append(
                vectorio.Circle(pixel_shader=palette, x=x, y=y, radius=_MARKER_RADIUS)
            )
            self._markers[direction] = palette

        self._label = RoomLabel(self._chrome, width, comic_fonts.caption(), y=_ROOM_NAME_Y)
        self._stage = comic.Stage(width, height, shake_target=self._scene)
        self.group.append(self._stage.group)
        self._player = BeatPlayer(_Director(self._stage, self._things, self._chrome, self._label))
        self._live_exits = set()
        # What update() is to draw next (cd-342.47.3): the calls below only say
        # what's changed, so nothing is drawn under input handling.
        self._room_name = None
        self._new_room = False
        self._new_backdrop = False
        self._new_scene = None
        self._scene_at = 0.0

    def sprite_sheets(self):
        """The props and critter sheets and palettes, for the title screen to share."""
        return self._things.sheets()

    def refresh_backdrop(self):
        """Put the room's art back after another screen used the shared bitmap."""
        self._new_backdrop = self._room_name is not None

    def show_room(self, name, live_exits):
        """Call on entering a room (and once at startup)."""
        self._room_name = name
        self._live_exits = set(live_exits)
        self._new_room = True

    def show_scene(self, scene, now):
        """Draw what's in the room (a story.Scene). Call after anything changes it."""
        self._new_scene = scene
        self._scene_at = now

    @property
    def overlay_up(self):
        return self._player.active

    @property
    def cutscene_up(self):
        """A cutscene beat is on (it draws a shot): taps advance it, moves wait."""
        beat = self._player.current
        return beat is not None and beat.shot is not None

    def tap_overlay(self, now):
        """A tap while an overlay is up: on to the next beat, at update()."""
        self._player.tap(now)

    def tell(self, news, now):
        """Show `news` (a story.News: what the hunt just said, or a bump's
        reason) as storyboard.py's beats, from update()."""
        if news.escape is not None:
            self._things.set_escape(news.escape)  # who the escape cutscene is about
        self._player.play(storyboard.beats(news, self._things.icon), now)

    def bonk(self, now):
        """A move onto an edge with no exit at all."""
        self._player.play(storyboard.bonk(), now)

    def update(self, now, active_zone):
        """Call once per frame: the only place this screen draws. `active_zone` =
        edge_gesture.edge_of() of the current touch point, or None."""
        if self._new_room:
            self._backdrop.show(self._room_name)
            self._label.show(self._room_name)
        elif self._new_backdrop:
            self._backdrop.show(self._room_name)
        self._new_room = self._new_backdrop = False
        if self._new_scene is not None:
            self._things.show(self._new_scene, self._scene_at)
            self._new_scene = None
        phase = (now % _PULSE_PERIOD) / _PULSE_PERIOD
        pulse = 0.5 + 0.5 * math.sin(2 * math.pi * phase)
        available_idle = _blend(_AVAILABLE_DIM, _AVAILABLE_BRIGHT, pulse)
        for direction, palette in self._markers.items():
            available = direction in self._live_exits
            if direction == active_zone:
                palette[0] = _ACTIVE_GO_COLOR if available else _ACTIVE_BLOCKED_COLOR
            elif available:
                palette[0] = available_idle
            else:
                palette[0] = _BLOCKED_IDLE
        self._things.update(now)
        self._player.update(now)
        self._stage.update(now)
