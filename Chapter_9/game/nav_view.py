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
import hunt
import rooms
from backdrop import Backdrop
from beats import Beat, BeatPlayer
from hunt import wrap
from room_banner import RoomLabel
from scene_view import SceneView

_BG_COLOR = 0x101018

_ROOM_NAME_Y = 50  # top band, under the UP marker; the middle is the scene's
_FOUND_BURST = "Found!"
# Hearts either side of a critter that's coming home with you (screen px).
_HEARTS = (("heart", 56, 92), ("heart", 152, 92))

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

    def __init__(self, stage, things, chrome):
        self._stage, self._things, self._chrome = stage, things, chrome

    def show(self, beat, now):
        self._stage.show(beat, now)
        self._things.shot(beat.shot, now)
        self._chrome.hidden = beat.shot in escape.CLOSE_SHOTS

    def clear(self):
        self._stage.clear()
        self._things.shot(None, 0.0)
        self._chrome.hidden = False


class NavView:
    """Owns the interactive-mode displayio Group (`.group`)."""

    def __init__(self, width, height, backdrop_root="/art/rooms"):
        self.group = displayio.Group()

        bg_bitmap = displayio.Bitmap(width, height, 1)
        bg_palette = displayio.Palette(1)
        bg_palette[0] = _BG_COLOR
        self.group.append(displayio.TileGrid(bg_bitmap, pixel_shader=bg_palette))
        self._backdrop = Backdrop(backdrop_root)  # the room's art, if it has some
        self.art_set = self._backdrop.art_set  # which room-art set is deployed
        self.backdrop = self._backdrop  # shared with the ornament screen (ornament.Show)
        self.group.append(self._backdrop.group)
        self._scene = displayio.Group()  # what a shake moves
        self.group.append(self._scene)
        self._things = SceneView()
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
        self._player = BeatPlayer(_Director(self._stage, self._things, self._chrome))
        self._live_exits = set()

    def refresh_backdrop(self):
        """Put the room's art back after another screen used the shared bitmap."""
        if getattr(self, "_room_name", None) is not None:
            self._backdrop.show(self._room_name)

    def show_room(self, name, live_exits):
        """Call on entering a room (and once at startup)."""
        self._backdrop.show(name)
        self._room_name = name
        self._label.show(name)
        self._live_exits = set(live_exits)

    def show_scene(self, scene, now):
        """Draw what's in the room (a hunt.Scene). Call after anything changes it."""
        self._things.show(scene, now)

    @property
    def overlay_up(self):
        return self._player.active

    def tap_overlay(self, now):
        """A tap while an overlay is up: on to the next beat."""
        self._player.tap(now)

    def say(self, messages, now, event=None, want=None, escaped=None, escape_at=0):
        """Show `messages` as captions, one after another.

        `event` is what just happened (hunt.Hunt.event): finding a critter
        shouts FOUND! first and puts `want`, the scene_art name of its lure, in a
        thought bubble over the first caption; bringing one home adds hearts. An
        escape (`escaped`, a hunt.Escape) plays the cutscene before message
        `escape_at`, with the box still shut under the messages before it.
        """
        beats = []
        for index, text in enumerate(messages):
            if event == hunt.ESCAPED and index == escape_at:
                self._things.set_escape(escaped)
                beats.extend(escape.cutscene())
            lines = wrap(text)
            # A caption holds two lines; anything longer runs on into the next.
            for i in range(0, len(lines), 2):
                shot = escape.CALM if event == hunt.ESCAPED and index < escape_at else None
                beats.append(Beat(caption="\n".join(lines[i:i + 2]), shot=shot))
        if event == hunt.FOUND:
            if beats and want is not None:
                beats[0].thought = self._things.icon(want)
            beats.insert(0, Beat(burst=_FOUND_BURST))
        elif event == hunt.RETRIEVED and beats:
            beats[0].emanata = _HEARTS
        self._player.play(beats, now)

    def bonk(self, now):
        """A move onto an edge with no exit at all."""
        self._player.play([Beat(burst="Bonk!", shake=True)], now)

    def update(self, now, active_zone):
        """Call once per frame. `active_zone` = edge_gesture.edge_of() of the
        current touch point, or None."""
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
