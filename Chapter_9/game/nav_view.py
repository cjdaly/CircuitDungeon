# SPDX-License-Identifier: MIT
"""Interactive-mode display group: room label, edge-exit markers, blocked-move
banner -- cd-342.2.

Lifted from Chapter_8/game/room_nav_demo.py (cd-45v.4's prototype, feel-tested
on real hardware 2026-09-13) and turned into a reusable view instead of a
standalone script. A small circle at the midpoint of each edge's margin band
shows, live, whether that direction is a real exit from the current room
(pulsing green if so, dim/static if not); touching a zone snaps its dot to
gold (live exit) or red (blocked) immediately, so the margin feel and the
room graph can both be judged by eye. The room's name sits persistently in
the center (room_banner.RoomLabel); room_banner.RoomBanner is only the
transient "can't go <direction>" flash.

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

import edge_gesture
import rooms
from room_banner import RoomBanner, RoomLabel

_BG_COLOR = 0x101018
_BLOCKED_FLASH_COLOR = 0xE04040

_ROOM_NAME_Y = 100  # center-ish; clear of the edge markers' row/column
_BANNER_Y = 172  # below the room name, above the DOWN marker

_MARKER_RADIUS = 9
_AVAILABLE_DIM = 0x1A4028
_AVAILABLE_BRIGHT = 0x40FF80
_BLOCKED_IDLE = 0x2A1A1A  # static, not pulsing -- reads as "don't bother"
_ACTIVE_GO_COLOR = 0xFFD040  # gold -- touching a zone that IS a live exit
_ACTIVE_BLOCKED_COLOR = 0xFF4040  # red -- touching a zone that is NOT
_PULSE_PERIOD = 1.4  # seconds per idle pulse cycle, available zones only

# Markers sit at each edge's margin-band midpoint -- literally where a
# gesture needs to start, matching edge_gesture.EDGE_MARGIN.
_MARGIN_MID = edge_gesture.EDGE_MARGIN // 2


def _blend(color_a, color_b, t):
    """Linear-interpolate two 0xRRGGBB colors; t=0 -> a, t=1 -> b."""
    ar, ag, ab = (color_a >> 16) & 0xFF, (color_a >> 8) & 0xFF, color_a & 0xFF
    br, bg, bb = (color_b >> 16) & 0xFF, (color_b >> 8) & 0xFF, color_b & 0xFF
    r = int(ar + (br - ar) * t)
    g = int(ag + (bg - ag) * t)
    b = int(ab + (bb - ab) * t)
    return (r << 16) | (g << 8) | b


class NavView:
    """Owns the interactive-mode displayio Group (`.group`)."""

    def __init__(self, width, height):
        self.group = displayio.Group()

        bg_bitmap = displayio.Bitmap(width, height, 1)
        bg_palette = displayio.Palette(1)
        bg_palette[0] = _BG_COLOR
        self.group.append(displayio.TileGrid(bg_bitmap, pixel_shader=bg_palette))

        positions = {
            rooms.UP: (width // 2, _MARGIN_MID),
            rooms.DOWN: (width // 2, height - _MARGIN_MID),
            rooms.LEFT: (_MARGIN_MID, height // 2),
            rooms.RIGHT: (width - _MARGIN_MID, height // 2),
        }
        self._markers = {}
        for direction, (x, y) in positions.items():
            palette = displayio.Palette(1)
            palette[0] = _BLOCKED_IDLE
            self.group.append(
                vectorio.Circle(pixel_shader=palette, x=x, y=y, radius=_MARKER_RADIUS)
            )
            self._markers[direction] = palette

        self._label = RoomLabel(self.group, width, y=_ROOM_NAME_Y)
        self._banner = RoomBanner(self.group, width, y=_BANNER_Y)
        self._live_exits = set()

    def show_room(self, name, live_exits):
        """Call on entering a room (and once at startup)."""
        self._label.show(name)
        self._live_exits = set(live_exits)

    def blocked(self, direction, now):
        """Flash "can't go <direction>" after a move onto a dead edge."""
        self._banner.show(
            "can't go {}".format(direction), now, color=_BLOCKED_FLASH_COLOR
        )

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
        self._banner.update(now)
