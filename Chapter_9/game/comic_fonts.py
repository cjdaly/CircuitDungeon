# SPDX-License-Identifier: MIT
"""The two comic fonts -- cd-bp3.13, doc/STYLE.md sec 3.

Luckiest Guy (Apache 2.0) is for titles and room names; Bangers (SIL OFL) is for
captions and messages. Both are subset BDFs from Chapter_8 (doc/FONTS.md there),
so text must be upper case: a character missing from GLYPHS draws as nothing.

Each font loads once and preloads every glyph, so play never reads the BDF file
(tests/test_hunt.py checks the game's text against these files).
"""
from adafruit_bitmap_font import bitmap_font

GLYPHS = " !',.0123456789?ABCDEFGHIJKLMNOPQRSTUVWXYZ"

TITLE_PATH = "fonts/luckiestguy-spaced45-24.bdf"
CAPTION_PATH = "fonts/bangers-spaced45-24.bdf"

_loaded = {}


def _load(path):
    font = _loaded.get(path)
    if font is None:
        font = bitmap_font.load_font(path)
        font.load_glyphs(GLYPHS)
        _loaded[path] = font
    return font


def title():
    return _load(TITLE_PATH)


def caption():
    return _load(CAPTION_PATH)
