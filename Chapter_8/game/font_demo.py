# SPDX-License-Identifier: MIT
"""terminalio.FONT vs. Bangers (comic-book style) side by side -- cd-bp3.11.

Not main.py: run this standalone (rename to main.py or `import font_demo`
from a scratch main.py). Ch9's text overlays (room names, banners) all use
CircuitPython's built-in terminalio.FONT today -- Chris wants a comic-book
look instead. Bangers (an OFL-licensed Google Font built specifically for
superhero-comics-style lettering, https://github.com/googlefonts/bangers)
is the first candidate tried; cd-bp3.12 tracks trying others later.

On-device comparison 2026-09-13 settled on **24px with +45 font-unit extra
advance width per glyph** (fonts/bangers-spaced45-24.bdf): 16px was too
cramped to read; 24px at the font's default (tight) spacing was readable
but felt cramped; +90 extra spacing was tried and felt like too much;
+45 (half of that) was the pick. Bigger sizes (28px/32px) were generated
and tried too, but not compared against the +45-spaced 24px directly --
open question for cd-bp3.12 if 24px+spacing turns out not to be final.
This demo now shows just the settled comparison (terminalio vs. the
winning Bangers variant) rather than every experiment tried along the way;
see doc/FONTS.md for the full history.

fonts/*.bdf were converted from Google Fonts' Bangers-Regular.ttf via
FontForge on arc-1 (the rpi-fleet box already used for Ch8 CAD work, see
../rpi-fleet's INVENTORY.md and doc/FONTS.md) -- FontForge isn't installed
on this Mac. Subsetted to just the characters Ch9's overlays actually need
(space, digits, A-Z, basic punctuation); Bangers renders lowercase input in
the same all-caps style, so there's no real lowercase glyph set to keep.
fonts/bangers-OFL.txt is the required license text (SIL OFL 1.1).

STATUS: confirmed on-device 2026-09-13 (ws-1) -- this is the settled
Bangers configuration, not yet wired into Ch9's actual RoomLabel/RoomBanner
(cd-zw2.5) as a follow-up.
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
_ROW_TERMINALIO = 60
_ROW_BANGERS = 140


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


def main():
    display, _backlight = hardware.init_display()
    group = _make_group(display)

    _add_line(group, terminalio.FONT, "terminalio.FONT (today)", _ROW_TERMINALIO)

    bangers = bitmap_font.load_font("fonts/bangers-spaced45-24.bdf")
    bangers.load_glyphs(_SAMPLE)
    _add_line(group, bangers, _SAMPLE, _ROW_BANGERS)

    print("Ch8 font demo ready")

    while True:
        time.sleep(1.0)  # static scene -- nothing to redraw, just idle


main()
