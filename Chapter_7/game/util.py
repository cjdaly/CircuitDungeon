# The MIT License (MIT)
#
# Copyright (c) 2026 Chris J Daly (github user cjdaly)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

# displayio helpers shared by every board. No hardware-specific code and no
# game state here — callers position and group what these functions return.

import displayio
import adafruit_imageload
from adafruit_display_text import label

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


def init_label(font, color, x=0, y=0, text=""):
    lbl = label.Label(font, color=color, text=text)
    lbl.x = x
    lbl.y = y
    return lbl
