# SPDX-License-Identifier: MIT
"""Persistent room-name display -- cd-zw2.5, cd-bp3.13.

Ported from Chapter_8/game/room_banner.py (cd-45v.3's prototype), with one
important update from what was actually learned on real hardware
2026-09-13: a toast that auto-hides turned out to be a poor way to answer
"what room am I in" -- if you miss the toast, there's no way to find out
without moving again. `RoomLabel` (new here) is the persistent centered
label that Chapter_8's room_nav_demo.py ended up using instead, after that
on-device feedback. Messages that *should* disappear on their own are the comic
overlay kit's job now (comic.py).

Callers pass the font (see comic_fonts.py). Those fonts have no lower case, so
the text is upper-cased.
"""
from adafruit_display_text.bitmap_label import Label

_TEXT_COLOR = 0xFFFFFF


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
