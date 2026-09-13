# SPDX-License-Identifier: MIT
"""terminalio.FONT vs. two comic-book-style fonts side by side -- cd-bp3.11,
cd-bp3.12.

Not main.py: run this standalone (rename to main.py or `import font_demo`
from a scratch main.py). Ch9's text overlays (room names, banners) all use
CircuitPython's built-in terminalio.FONT today -- Chris wants a comic-book
look instead. Two candidates compared here, both at 24px with +45 font-unit
extra advance width per glyph (the spacing amount cd-bp3.11 settled on for
Bangers -- reused as-is for Luckiest Guy rather than re-deriving from
scratch, since both are similarly bold/dense comic-style faces):

- **Bangers** (https://github.com/googlefonts/bangers, SIL OFL 1.1) --
  built specifically for superhero-comics cover lettering. cd-bp3.11's
  pick after trying 16px (too cramped), 24px tight (readable but cramped),
  and +90 spacing (too much) -- +45 was the winner.
- **Luckiest Guy** (Google Fonts) -- rounder, more a 1950s-advertisement
  look than comics lettering specifically. **License correction**:
  cd-bp3.11's desk research assumed OFL like Bangers; Google's own download
  manifest (`fonts.google.com/download/list?family=Luckiest+Guy`) says
  **Apache License 2.0** -- still fully free/permissive, just a different
  license text to ship (`fonts/LuckiestGuy-LICENSE.txt`), not OFL. Worth
  remembering not every Google Font is OFL.

fonts/*.bdf were converted from the respective TTFs via FontForge on arc-1
(the rpi-fleet box, see ../rpi-fleet's INVENTORY.md and doc/FONTS.md) --
FontForge isn't installed on this Mac. Subsetted to just the characters
these overlays need (space, digits, A-Z, basic punctuation); both fonts
render lowercase input in the same caps style, so there's no lowercase
glyph set worth keeping for either.

STATUS: both confirmed on-device 2026-09-13 (ws-1). Verdict: a role split,
not a single winner -- Luckiest Guy (bolder, upright) for titles/room
names, Bangers (slanted, more compact) for in-character dialogue (once
that mechanic exists). See doc/FONTS.md "On-device verdict".
"""
import time

import displayio
import terminalio
from adafruit_bitmap_font import bitmap_font
from adafruit_display_text.bitmap_label import Label

import hardware

_BG_COLOR = 0x101018
_TEXT_COLOR = 0xE0E0E0

_SAMPLE = "LIVING ROOM"

# Rows kept inside the round bezel's ~20-30px inset, see doc/HARDWARE.md
# "Display".
_ROW_TERMINALIO = 35
_ROW_BANGERS = 100
_ROW_LUCKIEST = 165


def _make_group(display):
    group = displayio.Group()
    display.root_group = group

    bg_bitmap = displayio.Bitmap(hardware.WIDTH, hardware.HEIGHT, 1)
    bg_palette = displayio.Palette(1)
    bg_palette[0] = _BG_COLOR
    group.append(displayio.TileGrid(bg_bitmap, pixel_shader=bg_palette))
    return group


def _add_line(group, font, text, y, scale=1):
    label = Label(
        font,
        text=text,
        color=_TEXT_COLOR,
        scale=scale,
        anchor_point=(0.5, 0.5),
        anchored_position=(hardware.WIDTH // 2, y),
    )
    group.append(label)
    return label


def _load(group, path, y):
    font = bitmap_font.load_font(path)
    font.load_glyphs(_SAMPLE)
    _add_line(group, font, _SAMPLE, y)


def main():
    display, _backlight = hardware.init_display()
    group = _make_group(display)

    _add_line(group, terminalio.FONT, "terminalio (today)", _ROW_TERMINALIO)
    _load(group, "fonts/bangers-spaced45-24.bdf", _ROW_BANGERS)
    _load(group, "fonts/luckiestguy-spaced45-24.bdf", _ROW_LUCKIEST)

    print("Ch8 font demo ready")

    while True:
        time.sleep(1.0)  # static scene -- nothing to redraw, just idle


main()
