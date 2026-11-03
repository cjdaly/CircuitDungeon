# SPDX-License-Identifier: MIT
"""Room-name display + transient message banner -- cd-zw2.5, cd-bp3.13.

Ported from Chapter_8/game/room_banner.py (cd-45v.3's prototype), with one
important update from what was actually learned on real hardware
2026-09-13: a toast that auto-hides turned out to be a poor way to answer
"what room am I in" -- if you miss the toast, there's no way to find out
without moving again. `RoomLabel` (new here) is the persistent centered
label that Chapter_8's room_nav_demo.py ended up using instead, after that
on-device feedback. `RoomBanner` (the original toast class) is kept for what
it's actually good at: messages that *should* disappear on their own.

Callers pass the font (see comic_fonts.py). Those fonts have no lower case, so
both classes upper-case their text.
"""
from adafruit_display_text.bitmap_label import Label

_TEXT_COLOR = 0xFFFFFF
_LINE_OFFSET = 13  # a two-line banner's lines sit this far above/below its middle


class RoomLabel:
    """Persistent centered label -- thin wrapper so "show the room name" is one
    call (`.show(name)`) instead of every caller poking `.text` directly."""

    def __init__(self, group, width, font, y=100, color=_TEXT_COLOR):
        self._label = Label(
            font,
            text="",
            color=color,
            anchor_point=(0.5, 0.5),
            anchored_position=(width // 2, y),
        )
        group.append(self._label)

    def show(self, name):
        self._label.text = name.upper()


class RoomBanner:
    """Toast-style text banner -- for TRANSIENT messages only, not the room
    name itself. See RoomLabel for that.

    .show(text, now) draws one line, or two split by a newline; .update(now)
    auto-hides it a few seconds later. Each line is its own label
    because bitmap_label can't center the lines of a proportional font.
    """

    def __init__(self, group, width, font, y=46, duration=2.5):
        self._x = width // 2
        self._y = y
        self._duration = duration
        self._lines = []
        for _ in range(2):
            label = Label(
                font,
                text="",
                color=_TEXT_COLOR,
                anchor_point=(0.5, 0.5),
                anchored_position=(self._x, y),
            )
            group.append(label)
            self._lines.append(label)
        self._hide_at = 0.0

    @property
    def showing(self):
        return bool(self._hide_at)

    def show(self, text, now, color=_TEXT_COLOR, duration=None):
        lines = text.upper().split("\n")
        two = len(lines) > 1
        first, second = self._lines
        first.anchored_position = (self._x, self._y - _LINE_OFFSET if two else self._y)
        second.anchored_position = (self._x, self._y + _LINE_OFFSET)
        first.text = lines[0]
        second.text = lines[1] if two else ""
        first.color = color
        second.color = color
        self._hide_at = now + (self._duration if duration is None else duration)

    def update(self, now):
        """Call once per frame; hides the banner once its duration elapses."""
        if self._hide_at and now >= self._hide_at:
            for label in self._lines:
                label.text = ""
            self._hide_at = 0.0
