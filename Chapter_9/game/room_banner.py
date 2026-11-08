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
import displayio
import vectorio
from adafruit_display_text.bitmap_label import Label

_TEXT_COLOR = 0x140C1C  # DB16 ink, on...
_BOX_COLOR = 0xDAD45E  # ...a yellow comic location caption (doc/STYLE.md sec 6)
_INK = 0x140C1C
_PAD_X, _PAD_Y = 5, 2
_BORDER = 2


class RoomLabel:
    """Persistent centered room name in a comic caption box: a yellow box with an
    ink border, so it reads on any room backdrop (cd-342.35). `.show(name)` sets it."""

    def __init__(self, group, width, font, y=100, color=_TEXT_COLOR, box=_BOX_COLOR):
        self._center = (width // 2, y)
        ink, fill = displayio.Palette(1), displayio.Palette(1)
        ink[0], fill[0] = _INK, box
        self._border = vectorio.Rectangle(pixel_shader=ink, width=1, height=1, x=0, y=0)
        self._fill = vectorio.Rectangle(pixel_shader=fill, width=1, height=1, x=0, y=0)
        self._label = Label(
            font,
            text="",
            color=color,
            anchor_point=(0.5, 0.5),
            anchored_position=self._center,
        )
        self._box = displayio.Group()
        self._box.append(self._border)
        self._box.append(self._fill)
        self._box.hidden = True
        group.append(self._box)
        group.append(self._label)

    def show(self, name):
        self._label.text = name.upper()
        _, _, w, h = self._label.bounding_box
        self._box.hidden = not w
        if not w:
            return
        cx, cy = self._center
        w, h = w + 2 * _PAD_X, h + 2 * _PAD_Y
        self._fill.width, self._fill.height = w, h
        self._fill.x, self._fill.y = cx - w // 2, cy - h // 2
        b = 2 * _BORDER
        self._border.width, self._border.height = w + b, h + b
        self._border.x, self._border.y = cx - w // 2 - _BORDER, cy - h // 2 - _BORDER
