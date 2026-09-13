# SPDX-License-Identifier: MIT
"""Room-name display + transient move-feedback banner -- cd-zw2.5.

Ported from Chapter_8/game/room_banner.py (cd-45v.3's prototype), with one
important update from what was actually learned on real hardware
2026-09-13: a toast that auto-hides turned out to be a poor way to answer
"what room am I in" -- if you miss the toast, there's no way to find out
without moving again. `RoomLabel` (new here) is the persistent centered
label that Chapter_8's room_nav_demo.py ended up using instead, after that
on-device feedback. `RoomBanner` (the original toast class, unchanged) is
kept for what it's actually good at: a transient "can't go <direction>"
flash on a blocked move, which *should* disappear on its own.

Font: both use terminalio.FONT for now -- see cd-bp3.11 (investigating a
comic-book-style font for Ch9's overlays instead).

STATUS: ported, not yet re-tested on-device in Chapter_9 specifically --
displayio isn't importable under plain desktop Python, so unlike
rooms.py/edge_gesture.py this can only be desk-checked here. The underlying
code and pattern are already proven on Chapter 8 hardware though (RoomBanner
as the blocked-move flash, the RoomLabel pattern as room_nav_demo.py's
persistent center label).
"""
import displayio
import terminalio
import vectorio
from adafruit_display_text.bitmap_label import Label

_OFFSCREEN_Y = -1000
_BAR_COLOR = 0x000000
_TEXT_COLOR = 0xFFFFFF


class RoomLabel:
    """Persistent centered room-name label -- always shows the current room.

    Just a thin wrapper around a Label so "show the room name" is one call
    (`.show(name)`) instead of every caller poking `.text` directly, and so
    it's easy to swap in a different font/style later (cd-bp3.11) in one
    place.
    """

    def __init__(self, group, width, y=100, color=_TEXT_COLOR, scale=2):
        self._label = Label(
            terminalio.FONT,
            text="",
            color=color,
            scale=scale,
            anchor_point=(0.5, 0.5),
            anchored_position=(width // 2, y),
        )
        group.append(self._label)

    def show(self, name):
        self._label.text = name


class RoomBanner:
    """Toast-style text banner backed by a solid bar -- for TRANSIENT
    messages only (e.g. "can't go <direction>" on a blocked move), not the
    room name itself. See RoomLabel for that.

    .show(text, now) draws a message on a solid bar; .update(now) auto-hides
    it a few seconds later.
    """

    def __init__(self, group, width, y=46, bar_height=30, duration=2.5):
        self._y = y
        self._duration = duration

        bar_palette = displayio.Palette(1)
        bar_palette[0] = _BAR_COLOR
        self._bar = vectorio.Rectangle(
            pixel_shader=bar_palette,
            width=width,
            height=bar_height,
            x=0,
            y=_OFFSCREEN_Y,
        )
        self._label = Label(
            terminalio.FONT,
            text="",
            color=_TEXT_COLOR,
            scale=2,
            anchor_point=(0.5, 0.5),
            anchored_position=(width // 2, y),
        )
        group.append(self._bar)
        group.append(self._label)
        self._hide_at = 0.0

    def show(self, text, now, color=_TEXT_COLOR):
        self._label.text = text
        self._label.color = color
        self._bar.y = self._y - self._bar.height // 2
        self._hide_at = now + self._duration

    def update(self, now):
        """Call once per frame; hides the banner once its duration elapses."""
        if self._hide_at and now >= self._hide_at:
            self._label.text = ""
            self._bar.y = _OFFSCREEN_Y
            self._hide_at = 0.0
