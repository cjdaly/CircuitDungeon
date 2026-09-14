# SPDX-FileCopyrightText: 2026 Chris J Daly (github user cjdaly)
#
# SPDX-License-Identifier: MIT

# displayio helpers shared by every board. No hardware-specific code and no
# game state here — callers position and group what these functions return.

import displayio
import adafruit_imageload
# bitmap_label, NOT label: label.Label is a Group with one TileGrid per glyph,
# and re-assigning `.text` frees + reallocates all of them. The status line
# rebuilds every turn (the turn counter is in it), so ~1000 turns shredded the
# heap and a later 84-byte alloc in DiagMode OOM'd (cd-yl4). bitmap_label
# renders into a single Bitmap it reuses when the text fits.
from adafruit_display_text import bitmap_label

_TILES_DIR = "/tiles/"


def load_bitmap(filename):
    """Load a bitmap+palette pair once, to share across many sprites via `tilegrid()`."""
    return adafruit_imageload.load(
        _TILES_DIR + filename + ".bmp",
        bitmap=displayio.Bitmap,
        palette=displayio.Palette,
    )


def tilegrid(bmp, pal, w, h, tw, th, x=0, y=0, transparent=None):
    """Build a TileGrid from an already-loaded bitmap/palette — cheap enough to call
    many times against the same bmp/pal (e.g. a pool of same-sprite-sheet instances)."""
    if transparent is not None:
        pal.make_transparent(transparent)
    tg = displayio.TileGrid(bmp, pixel_shader=pal, width=w, height=h, tile_width=tw, tile_height=th)
    tg.x = x
    tg.y = y
    return tg


def load_tilegrid(filename, w, h, tw, th, x=0, y=0):
    """Opaque tile grid (terrain) — no transparency."""
    bmp, pal = load_bitmap(filename)
    return tilegrid(bmp, pal, w, h, tw, th, x=x, y=y)


def load_sprite(filename, w, h, tw, th, x=0, y=0, transparent=0):
    """Overlaid tile grid (hero, explosion, ...) — palette index `transparent` is see-through."""
    bmp, pal = load_bitmap(filename)
    return tilegrid(bmp, pal, w, h, tw, th, x=x, y=y, transparent=transparent)


def solid_rect(w, h, color, x=0, y=0):
    """A single solid-color TileGrid, no bitmap file involved — every pixel
    in a fresh Bitmap defaults to palette index 0, so no per-pixel fill
    loop is needed. Used for the icon-rail grouping boxes (cd-oht.5)."""
    bmp = displayio.Bitmap(w, h, 1)
    pal = displayio.Palette(1)
    pal[0] = color
    tg = displayio.TileGrid(bmp, pixel_shader=pal, width=1, height=1, tile_width=w, tile_height=h)
    tg.x = x
    tg.y = y
    return tg


def init_label(font, color, x=0, y=0, text=""):
    lbl = bitmap_label.Label(font, color=color, text=text)
    lbl.x = x
    lbl.y = y
    return lbl
