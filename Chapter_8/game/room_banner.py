# SPDX-License-Identifier: MIT
"""Room-name banner overlay -- cd-45v.3 prototype (relates to Ch9's cd-zw2.5).

A toast: .show(text, now) draws a message on a solid bar and .update(now)
auto-hides it a few seconds later, rather than a permanent label always
taking up screen space -- the point is to help the player reorient right
after moving, not to overlay every scene. Positioned well inside the round
bezel (see doc/HARDWARE.md "Display", ~20-30px inset) and backed by a solid
bar so it stays legible once there's real room art behind it, not just
today's flat background.

Uses the same bitmap_label/adafruit_display_text approach as the Ch8
diagnostic HUD (game/main.py, cd-bp3.5) and Ch7's HUD text (cd-yl4).

Hiding moves the bar off-screen and blanks the label text, rather than a
`.hidden` toggle -- matching main.py's existing touch-dot idiom
(`dot.x = dot.y = _OFFSCREEN`), not yet confirmed which approach this
port's displayio supports for text/vector shapes.

STATUS: UNTESTED ON DEVICE as of 2026-09-12 -- displayio isn't importable
under plain desktop Python, so unlike rooms.py/edge_gesture.py this can only
be desk-checked, not unit tested; see room_nav_demo.py for where it's used.
"""
import displayio
import terminalio
import vectorio
from adafruit_display_text.bitmap_label import Label

_OFFSCREEN_Y = -1000
_BAR_COLOR = 0x000000
_TEXT_COLOR = 0xFFFFFF


class RoomBanner:
    """Toast-style text banner backed by a solid bar for legibility."""

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
