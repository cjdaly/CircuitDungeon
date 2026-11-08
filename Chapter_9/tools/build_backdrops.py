#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Build the room backdrops into game/art/rooms/*.bmp -- cd-342.35.

    /usr/bin/python3 Chapter_9/tools/build_backdrops.py [--png DIR]

Each backdrop is 120x120 in DB16 (backdrop.COLORS), shown at 2x behind the
room's scene (doc/STYLE.md sec 6: a tableau of the room's iconic objects).
The game copies the room's file into its one shared backdrop bitmap on
entering the room (game/backdrop.py), so they stay in flash and RAM holds
only the room on screen. Keep the middle quiet: that's where the hiding
spots, lures and critters sit and where taps land, and the room name sits
at the top (art y ~20-30).

--png also writes a 4x preview of each, cut to the round panel, for review.
Needs Pillow.
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = os.path.join(HERE, "..", "game")
sys.path.insert(0, GAME)
import backdrop  # noqa: E402
import scene_art  # noqa: E402

SIZE = backdrop.SIZE
K = scene_art.KEY  # character -> scene_art palette index; the BMP stores index - 1


class Canvas:
    def __init__(self, fill):
        self.px = [[K[fill]] * SIZE for _ in range(SIZE)]

    def put(self, x, y, c):
        if 0 <= x < SIZE and 0 <= y < SIZE:
            self.px[y][x] = K[c]

    def rect(self, x0, y0, x1, y1, c):
        """Filled, inclusive corners."""
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.put(x, y, c)

    def box(self, x0, y0, x1, y1, fill, ink="#"):
        """Filled with a 1px ink outline."""
        self.rect(x0, y0, x1, y1, ink)
        self.rect(x0 + 1, y0 + 1, x1 - 1, y1 - 1, fill)

    def hline(self, x0, x1, y, c):
        self.rect(x0, y, x1, y, c)

    def vline(self, x, y0, y1, c):
        self.rect(x, y0, x, y1, c)

    def ellipse(self, cx, cy, rx, ry, fill, ink="#"):
        for y in range(cy - ry - 1, cy + ry + 2):
            for x in range(cx - rx - 1, cx + rx + 2):
                d = ((x - cx) / (rx + 0.5)) ** 2 + ((y - cy) / (ry + 0.5)) ** 2
                if d <= 1.0:
                    self.put(x, y, fill)
                elif d <= 1.0 + 2.2 / min(rx, ry):
                    self.put(x, y, ink)

    def sprite(self, x0, y0, rows):
        for dy, row in enumerate(rows):
            for dx, ch in enumerate(row):
                if ch != ".":
                    self.put(x0 + dx, y0 + dy, ch)


def kitchen():
    """Still warm from holiday baking: fridge left, window + oven + cookie jar right."""
    c = Canvas("k")  # warm tan wall
    # Wallpaper: a faint dot pattern, so the wall isn't a flat slab.
    for x in range(2, SIZE, 12):
        for y in range(4, 77, 8):
            c.put(x, y, "O")
    # Floor: quiet grey-and-white checks below a baseboard, so the hiding
    # spots standing on it still read.
    c.rect(0, 78, SIZE - 1, 80, "o")
    c.hline(0, SIZE - 1, 78, "#")
    for y in range(81, SIZE, 7):
        for x in range(0, SIZE, 7):
            c.rect(x, y, x + 6, y + 6, "w" if (x // 7 + y // 7) % 2 else "s")

    # Fridge, left: tall, white, two doors, a magnet or two.
    c.box(10, 22, 34, 80, "w")
    c.vline(33, 23, 79, "s")  # side shade
    c.hline(11, 32, 44, "#")  # freezer / fridge split
    c.rect(29, 30, 30, 39, "s")  # handles
    c.rect(29, 50, 30, 64, "s")
    c.rect(15, 28, 17, 30, "r")  # magnets
    c.rect(20, 52, 22, 54, "y")
    c.rect(14, 56, 16, 58, "b")
    c.box(14, 33, 22, 41, "w")  # a kid's drawing of a tree
    c.rect(18, 35, 18, 35, "G")
    c.rect(17, 36, 19, 37, "G")
    c.rect(16, 38, 20, 39, "G")

    # Window, right, night outside with snow; red curtains.
    c.box(80, 18, 108, 46, "n")
    c.vline(94, 19, 45, "#")
    c.hline(81, 107, 32, "#")
    for x, y in ((84, 22), (89, 27), (98, 21), (103, 26), (86, 37), (100, 38), (91, 42), (105, 41)):
        c.put(x, y, "w")
    c.rect(81, 43, 107, 45, "w")  # snow on the sill outside
    c.rect(76, 16, 112, 17, "o")  # curtain rod
    c.rect(77, 18, 81, 50, "r")  # curtains
    c.rect(107, 18, 111, 50, "r")
    c.vline(79, 18, 50, "p")
    c.vline(109, 18, 50, "p")

    # Counter under the window, oven in it, cookie jar on top.
    c.box(72, 56, 119, 60, "s")  # counter top
    c.box(72, 60, 119, 80, "o")  # cabinets
    c.box(78, 61, 102, 80, "d")  # oven
    c.rect(80, 63, 100, 64, "g")  # knobs strip
    for x in (82, 87, 92, 97):
        c.put(x, 63, "y")
    c.box(81, 67, 99, 77, "#")
    c.rect(83, 69, 97, 75, "O")  # warm glow through the door
    c.rect(85, 71, 95, 73, "y")
    c.hline(82, 98, 66, "s")  # door handle
    c.vline(110, 62, 79, "#")  # cabinet door seam
    c.rect(106, 68, 107, 70, "y")
    c.rect(113, 68, 114, 70, "y")
    # Cookie jar
    c.ellipse(112, 51, 5, 4, "c")
    c.rect(109, 45, 115, 47, "c")
    c.hline(109, 115, 44, "#")
    c.rect(111, 42, 113, 43, "#")
    c.put(110, 51, "o")
    c.put(113, 50, "o")
    c.put(114, 53, "o")
    # A tray of cookies cooling on the counter, left of the oven.
    c.box(73, 52, 79, 55, "s")
    c.put(74, 53, "o")
    c.put(77, 53, "o")

    # Shelf above the fridge: a pot and a pan, low on detail.
    c.ellipse(22, 17, 6, 3, "s")
    c.rect(28, 16, 31, 17, "#")
    # Gingerbread men in the oven, its glow on the floor; shade beside the fridge.
    for x in (87, 93):
        c.put(x, 70, "o")
        c.rect(x - 1, 71, x + 1, 73, "o")
        c.put(x - 2, 71, "o")
        c.put(x + 2, 71, "o")
        c.put(x - 1, 74, "o")
        c.put(x + 1, 74, "o")
    glow(c, 90, 82, 18, "O", "ws")
    shade(c, 35, 22, 40, 77, "o", "kO")
    return c


# ---- shared pieces ---------------------------------------------------------- #

FLOOR_Y = 78  # baseboard line: hiding spots (art y ~56-88) stand on the floor


def baseboard(c, y=FLOOR_Y, color="o"):
    c.rect(0, y, SIZE - 1, y + 2, color)
    c.hline(0, SIZE - 1, y, "#")


def planks(c, y0, base="O", seam="o", width=10):
    """Wood floor boards running left-right, staggered seams."""
    c.rect(0, y0, SIZE - 1, SIZE - 1, base)
    for i, y in enumerate(range(y0, SIZE, 5)):
        c.hline(0, SIZE - 1, y, seam)
        for x in range((i % 2) * width // 2, SIZE, width * 2):
            c.vline(x, y, y + 4, seam)


def night_window(c, x0, y0, x1, y1, frame="w", snow=True):
    """A night window, cross bars, a few snowflakes and snow on the sill."""
    c.box(x0, y0, x1, y1, "n")
    c.rect(x0 + 1, y0 + 1, x1 - 1, y0 + 1, frame)
    c.rect(x0 + 1, y1 - 1, x1 - 1, y1 - 1, frame)
    c.rect(x0 + 1, y0 + 1, x0 + 1, y1 - 1, frame)
    c.rect(x1 - 1, y0 + 1, x1 - 1, y1 - 1, frame)
    mx, my = (x0 + x1) // 2, (y0 + y1) // 2
    c.vline(mx, y0, y1, frame)
    c.hline(x0, x1, my, frame)
    if snow:
        w, h = x1 - x0, y1 - y0
        for fx, fy in ((0.2, 0.2), (0.7, 0.15), (0.35, 0.65), (0.8, 0.7), (0.15, 0.8), (0.6, 0.4)):
            c.put(x0 + int(w * fx), y0 + int(h * fy), "w")
        c.rect(x0 + 2, y1 - 3, x1 - 2, y1 - 2, "w")


def dots(c, color, y1, step_x=12, step_y=8, x0=2, y0=4):
    for x in range(x0, SIZE, step_x):
        for y in range(y0, y1, step_y):
            c.put(x, y, color)


def halftone(c, x0, y0, x1, y1, color, step=2):
    """Comic-book shading: a checker of dots over whatever is there."""
    for y in range(y0, y1 + 1, step):
        for x in range(x0 + (y // step) % 2, x1 + 1, step):
            c.put(x, y, color)



def _lit_pixels(c, x0, y0, x1, y1, only, step=2):
    """The halftone checker positions in a box whose pixel is one of `only`."""
    keys = {K[ch] for ch in only}
    for y in range(max(0, y0), min(SIZE - 1, y1) + 1):
        if y % step:
            continue
        for x in range(max(0, x0), min(SIZE - 1, x1) + 1):
            if (x + (y // step) % 2) % step == 0 and c.px[y][x] in keys:
                yield x, y


def glow(c, cx, cy, r, color, only):
    """Light falling on the walls/floor (`only` those colours) within r of a source."""
    for x, y in list(_lit_pixels(c, cx - r, cy - r, cx + r, cy + r, only)):
        if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
            c.put(x, y, color)


def dusk(c, cx, cy, r, color, only):
    """The dark beyond r of the room's light: halftone `color` over `only`."""
    for x, y in list(_lit_pixels(c, 0, 0, SIZE - 1, SIZE - 1, only)):
        if (x - cx) ** 2 + (y - cy) ** 2 > r * r:
            c.put(x, y, color)


def shade(c, x0, y0, x1, y1, color, only):
    """A comic shadow: halftone `color` over `only` in a box."""
    for x, y in list(_lit_pixels(c, x0, y0, x1, y1, only)):
        c.put(x, y, color)


def paw(c, x, y, col="s"):
    c.rect(x, y, x + 1, y + 1, col)
    c.put(x - 1, y - 2, col)
    c.put(x + 1, y - 3, col)
    c.put(x + 3, y - 2, col)


def candy_cane(c, x, y, h=8):
    c.vline(x - 1, y - h, y, "#")
    c.vline(x + 1, y - h + 2, y, "#")
    for j in range(h + 1):
        c.put(x, y - j, "r" if j % 2 == 0 else "w")
    c.put(x + 1, y - h, "w")
    c.put(x + 2, y - h + 1, "r")
    c.put(x + 2, y - h, "#")
    c.put(x + 3, y - h + 1, "#")


def candle(c, x, y, h=6, color="r"):
    c.rect(x, y - h, x + 1, y, color)
    c.put(x, y - h - 1, "y")
    c.put(x + 1, y - h - 1, "O")


# ---- rooms ------------------------------------------------------------------ #


def dining_room():
    """Table set for tomorrow: hutch left, painting right, chandelier, the table's edge."""
    c = Canvas("k")
    for x in range(4, SIZE, 10):  # festive pinstripe wallpaper
        c.vline(x, 0, 55, "O")
    c.rect(0, 56, SIZE - 1, FLOOR_Y, "o")  # wainscot
    c.hline(0, SIZE - 1, 56, "#")
    c.hline(0, SIZE - 1, 57, "O")
    for x in range(6, SIZE, 16):
        c.box(x, 60, x + 11, 75, "o", ink="p")
    baseboard(c, color="p")
    planks(c, FLOOR_Y + 3)

    # China hutch, left: glass doors over plates, drawers below.
    c.box(6, 20, 34, 80, "o")
    c.rect(4, 18, 36, 20, "o")
    c.hline(4, 36, 18, "#")
    c.box(9, 24, 31, 52, "c")
    c.vline(20, 24, 52, "#")
    for y in (31, 41):
        c.hline(10, 30, y + 5, "o")
        for x in (11, 16, 22, 27):
            c.ellipse(x + 1, y + 2, 2, 2, "w")
    c.box(9, 56, 31, 66, "O")
    c.box(9, 68, 31, 78, "O")
    c.rect(19, 60, 21, 61, "y")
    c.rect(19, 72, 21, 73, "y")

    # Painting, right: a snowy hill and a tiny pine, in a gold frame.
    c.box(82, 22, 112, 46, "y")
    c.box(84, 24, 110, 44, "b")
    c.rect(85, 37, 109, 43, "w")
    c.ellipse(92, 38, 7, 3, "w", ink="w")
    c.rect(102, 30, 103, 37, "G")
    c.rect(100, 33, 105, 36, "G")
    c.put(87, 27, "w")
    c.put(95, 29, "w")
    c.put(107, 26, "w")
    # A sideboard under it with a poinsettia.
    c.box(80, 62, 116, 80, "o")
    c.hline(80, 116, 62, "#")
    c.vline(98, 63, 79, "#")
    c.box(92, 55, 98, 62, "r")
    c.ellipse(95, 51, 5, 3, "r")
    c.put(93, 50, "G")
    c.put(97, 52, "G")
    c.put(95, 51, "y")

    # Chandelier at the top, above the room name.
    c.vline(60, 0, 6, "#")
    c.rect(48, 9, 72, 10, "y")
    c.hline(48, 72, 11, "O")
    for x in (49, 55, 65, 71):
        candle(c, x, 8, h=3, color="w")

    # The table's near edge, set for tomorrow: cloth, plates, candles.
    c.box(0, 96, SIZE - 1, SIZE - 1, "w")
    c.hline(1, SIZE - 2, 102, "s")
    for x in (24, 60, 96):
        c.ellipse(x, 99, 7, 2, "w")
        c.ellipse(x, 99, 4, 1, "s", ink="s")
    candle(c, 41, 99, h=7)
    candle(c, 78, 99, h=7)
    # Candlelight from the chandelier; garland on the hutch; a wreath centrepiece.
    glow(c, 60, 10, 30, "y", "kO")
    for x in range(4, 37):
        c.put(x, 21 + (x % 8 > 3), "G")
        if x % 6 == 1:
            c.put(x, 22, "r")
    shade(c, 4, 81, 38, 85, "p", "Oo")
    shade(c, 78, 81, 118, 85, "p", "Oo")
    c.ellipse(60, 99, 8, 2, "G")
    for x in (54, 59, 64, 67):
        c.put(x, 99 + (x % 2), "r")
    candle(c, 59, 98, h=5)
    return c


def sun_porch():
    """Windows all round, one open a crack with the curtain blowing; plants, a wicker chair."""
    c = Canvas("w")
    for y in range(2, FLOOR_Y, 6):  # painted board walls
        c.hline(0, SIZE - 1, y, "s")
    baseboard(c, color="s")
    planks(c, FLOOR_Y + 3, base="O", seam="o", width=14)
    # A woven rug in the middle of the floor.
    c.box(30, 88, 90, 108, "c", ink="b")
    for y in range(91, 107, 4):
        c.hline(33, 87, y, "b")

    # Left window, shut.
    night_window(c, 6, 14, 36, 52)
    # Right window, open a crack: the lower sash raised, a gap of cold air,
    # the curtain blowing in.
    night_window(c, 84, 14, 114, 52)
    c.rect(85, 46, 113, 49, "#")  # the gap
    c.rect(85, 45, 113, 45, "w")
    for x, y in ((88, 47), (95, 48), (104, 47), (110, 48)):
        c.put(x, y, "c")
    c.rect(78, 10, 84, 54, "r")  # curtain, billowing into the room
    c.rect(74, 30, 77, 50, "r")
    c.rect(71, 40, 73, 48, "r")
    c.vline(80, 10, 54, "p")
    c.vline(75, 31, 50, "p")
    c.rect(78, 8, 116, 9, "o")  # rod
    # Breeze lines.
    for x, y in ((64, 38), (60, 44), (66, 47)):
        c.hline(x, x + 4, y, "c")

    # Plants on a stand, left.
    c.box(8, 62, 30, 66, "o")
    c.vline(10, 66, 80, "o")
    c.vline(28, 66, 80, "o")
    for x in (10, 20):
        c.box(x, 54, x + 7, 61, "O")
        c.ellipse(x + 3, 51, 5, 4, "l")
        c.put(x + 2, 49, "G")
        c.put(x + 5, 52, "G")
    # Wicker chair, right.
    c.box(88, 58, 114, 82, "y")
    c.box(90, 70, 112, 76, "O")
    for x in range(91, 113, 3):
        c.vline(x, 59, 69, "O")
    c.rect(90, 82, 92, 90, "O")
    c.rect(110, 82, 112, 90, "O")
    c.box(91, 67, 111, 71, "r")  # cushion
    # Moon in the shut window, its light on the floor; snow blowing in.
    c.ellipse(13, 22, 3, 3, "w", ink="s")
    for y in range(84, 104):
        k = (y - 84) // 2
        shade(c, 6 + k, y, 30 + k, y, "c", "Oo")
    for x, y in ((70, 34), (64, 44), (58, 36), (67, 26), (60, 50), (73, 52)):
        c.put(x, y, "c")
    shade(c, 86, 91, 116, 95, "p", "Oo")
    return c


def odd_corner():
    """A cluttered corner where two walls meet; batteries on a shelf, too high to reach."""
    c = Canvas("g")
    # Two walls meeting in a corner at the middle, lit a little from the left.
    c.rect(60, 0, SIZE - 1, FLOOR_Y, "s")
    c.vline(60, 0, FLOOR_Y, "d")
    for x in range(0, 60, 9):
        c.vline(x, 0, FLOOR_Y, "d")
    baseboard(c, color="d")
    planks(c, FLOOR_Y + 3, base="o", seam="p")

    # A high shelf, top right. (The batteries are the scene's own lure,
    # drawn by scene_view in the middle, so not here too.)
    c.box(70, 24, 118, 27, "o")
    c.rect(74, 28, 75, 32, "#")
    c.rect(112, 28, 113, 32, "#")
    c.box(78, 16, 86, 23, "c")  # an old jar
    c.rect(77, 14, 87, 15, "s")
    c.box(93, 12, 108, 23, "O")  # an old box beside it
    c.hline(93, 108, 16, "o")

    # Boxes stacked up the left, the "too many boxes" way.
    c.box(4, 50, 32, 80, "O")
    c.hline(4, 32, 56, "o")
    c.box(8, 30, 30, 50, "k")
    c.vline(19, 31, 49, "o")
    c.box(12, 16, 26, 30, "O")
    c.hline(12, 26, 21, "o")
    # More boxes, bottom right, and a broom leaning on them.
    c.box(88, 56, 118, 80, "k")
    c.hline(88, 118, 62, "o")
    c.box(94, 40, 114, 56, "O")
    for i in range(36):
        c.put(84 - i // 3, 44 + i, "o")
    c.box(68, 78, 76, 88, "y")
    for x in range(69, 76, 2):
        c.vline(x, 84, 88, "O")
    # A lamp with no shade, and a picture frame leaning against the wall.
    c.box(40, 66, 54, 80, "o")
    c.box(42, 68, 52, 78, "b")
    # One bare bulb on a chain; dark in the corner; a mouse hole; a cobweb.
    c.vline(40, 0, 7, "#")
    c.ellipse(40, 10, 2, 2, "y", ink="O")
    c.vline(42, 12, 18, "s")
    glow(c, 40, 10, 18, "y", "gd")
    shade(c, 61, 0, 70, 78, "g", "s")
    shade(c, 52, 0, 59, 78, "d", "g")
    dusk(c, 40, 10, 72, "p", "sgdo")
    c.rect(37, 75, 41, 80, "#")
    c.hline(38, 40, 74, "#")
    for i in range(7):
        c.put(60 - i, i, "w")
        c.put(60 + i, i, "w")
    for i in range(3, 9, 3):
        c.hline(60 - i, 60 + i, i, "s")
    return c


def sewing_nook():
    """Christmas sewing at 9 PM: an old black machine under its lamp with a
    stocking half-sewn, a Santa dress pinned on the dress form, a braided rug."""
    c = Canvas("c")
    for i, y in enumerate(range(6, FLOOR_Y - 2, 11)):  # sprig wallpaper
        for x in range(4 + (i % 2) * 7, SIZE, 14):
            c.put(x, y, "y")
            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                c.put(x + dx, y + dy, "w")
            c.put(x + 1, y + 2, "l")
    baseboard(c, color="w")
    planks(c, FLOOR_Y + 3, base="o", seam="p")
    # A braided rag rug, red and green rings.
    for i, (rx, ry) in enumerate(((42, 11), (34, 9), (26, 7), (18, 5), (10, 3))):
        col = "rGrGr"[i]
        c.ellipse(60, 101, rx, ry, col, ink="#" if i == 0 else col)
    for x in range(22, 99, 4):  # the braid
        c.put(x, 101 - 7 + (x // 4) % 2, "k")
    halftone(c, 0, FLOOR_Y + 3, SIZE - 1, FLOOR_Y + 6, "p")  # dark along the wall

    # A clock by the caption: nine o'clock.
    c.ellipse(20, 28, 5, 5, "w")
    c.vline(20, 24, 28, "#")
    c.hline(16, 20, 28, "#")
    c.put(20, 21, "o")

    # The dress form, left, wearing the Santa dress in progress.
    rows = [(36, 1), (37, 2), (38, 2), (39, 1), (40, 6), (41, 8), (42, 8), (43, 9),
            (44, 9), (45, 9), (46, 8), (47, 7), (48, 6), (49, 6), (50, 6), (51, 7)]
    cx = 20
    for y, half in rows:
        c.hline(cx - half - 1, cx + half + 1, y, "#")
    for y, half in rows:
        c.hline(cx - half, cx + half, y, "k" if y < 44 else "r")
    for j in range(13):  # the skirt flares out, pinned up unfinished
        half = 7 + j * 5 // 12
        y = 52 + j
        c.hline(cx - half - 1, cx + half + 1, y, "#")
        c.hline(cx - half, cx + half, y, "r")
    c.rect(cx - 12, 62, cx + 1, 64, "w")  # white fur at the hem, half done
    for x in range(cx + 2, cx + 13, 2):
        c.put(x, 64, "k")  # still only chalked on
        c.put(x, 63, "r")
    c.hline(cx - 8, cx + 8, 44, "w")  # fur trim along the neckline
    c.rect(cx - 1, 46, cx + 1, 50, "#")  # a belt and buckle
    c.hline(cx - 6, cx + 6, 49, "#")
    c.rect(cx - 1, 48, cx + 1, 50, "y")
    for x, y in ((cx - 4, 41), (cx + 5, 42), (cx + 3, 56), (cx - 6, 59)):
        c.put(x, y, "s")  # pins
    c.vline(cx, 66, 77, "#")  # stand and feet
    c.vline(cx + 1, 66, 77, "d")
    c.hline(cx - 8, cx + 8, 78, "#")
    c.put(cx - 9, 79, "#")
    c.put(cx + 9, 79, "#")
    c.ellipse(cx + 1, 81, 11, 1, "p", ink="p")  # shadow

    # The hero: an old black sewing machine with gold scrollwork on a wooden
    # table, its lamp on, a stocking half-sewn under the needle.
    d = 5  # everything below sits this much lower than first drawn
    halftone(c, 104, 30 + d, 116, 56 + d, "b")  # its comic shadow on the wall
    c.box(66, 57 + d, 114, 61 + d, "O", ink="#")  # table top
    c.hline(67, 113, 60 + d, "o")
    c.box(68, 67, 112, 71, "o")  # apron, a drawer in it
    halftone(c, 69, 68, 111, 70, "p")
    c.box(84, 67, 96, 71, "O", ink="#")
    c.put(90, 69, "y")
    for x in (70, 108):  # legs
        c.box(x, 72, x + 3, 82, "o")
    c.ellipse(90, 84, 24, 2, "p", ink="p")  # shadow under the table
    parts = ((70, 52, 108, 56), (96, 30, 106, 51), (74, 30, 106, 38), (72, 30, 82, 46))
    for x0, y0, x1, y1 in parts:  # one ink outline round the whole machine
        c.rect(x0 - 1, y0 - 1 + d, x1 + 1, y1 + 1 + d, "#")
    for x0, y0, x1, y1 in parts:
        c.rect(x0, y0 + d, x1, y1 + d, "p")
    c.hline(75, 105, 30 + d, "d")  # light along the top
    c.vline(72, 31 + d, 45 + d, "d")
    c.hline(71, 107, 52 + d, "d")
    for x in range(84, 95, 2):  # gold scrollwork
        c.put(x, 34 + d + (x // 2) % 2, "y")
    for y in range(41, 50, 2):
        c.put(100 + (y // 2) % 2, y + d, "O")
    c.hline(73, 105, 55 + d, "O")  # gold line round the bed
    c.ellipse(109, 38 + d, 4, 4, "s")  # handwheel
    c.put(109, 38 + d, "d")
    c.put(109, 35 + d, "w")
    c.ellipse(77, 36 + d, 1, 1, "s", ink="#")  # tension knob
    c.vline(100, 24 + d, 29 + d, "s")  # spool pin, red thread
    c.box(97, 25 + d, 103, 29 + d, "r")
    c.hline(97, 103, 25 + d, "O")
    c.hline(97, 103, 29 + d, "O")
    for x in range(80, 97, 2):  # the thread, over to the needle
        c.put(x, 28 + d, "r")
    c.vline(79, 28 + d, 31 + d, "r")
    c.rect(75, 47 + d, 76, 50 + d, "s")  # needle bar, needle, presser foot
    c.put(75, 51 + d, "w")
    c.hline(72, 79, 51 + d, "s")
    c.rect(79, 47 + d, 81, 47 + d, "y")  # the little lamp under the head...
    halftone(c, 73, 48 + d, 86, 51 + d, "y")  # ...and its pool of light
    # The stocking: cuff under the needle, the leg hanging over the table.
    c.box(73, 49 + d, 87, 52 + d, "w", ink="s")
    c.rect(76, 58, 86, 74, "#")
    c.rect(76, 70, 94, 78, "#")
    c.rect(77, 58, 85, 73, "r")
    c.rect(77, 71, 93, 77, "r")
    c.rect(90, 71, 93, 77, "w")  # toe
    for y in range(58, 65, 2):  # sewn so far: stitches; then chalk marks
        c.put(78, y, "w")
    for y in range(66, 76, 3):
        c.put(78, y, "k")
    for x in range(80, 90, 3):
        c.put(x, 76, "k")
    # Basket of yarn under the table, behind the stocking's toe.
    c.box(96, 74, 112, 83, "O")
    for x in range(98, 111, 3):
        c.vline(x, 75, 82, "o")
    for x, col in ((100, "l"), (106, "b")):
        c.ellipse(x, 72, 3, 2, col)
    return c


def basement():
    """Dim: stone walls, a furnace glowing on the left, stairs going up on the right."""
    c = Canvas("g")
    # Stone block wall.
    for i, y in enumerate(range(0, FLOOR_Y, 8)):
        c.hline(0, SIZE - 1, y, "d")
        for x in range((i % 2) * 8, SIZE, 16):
            c.vline(x, y, y + 7, "d")
    c.rect(0, FLOOR_Y, SIZE - 1, SIZE - 1, "d")  # concrete floor
    c.hline(0, SIZE - 1, FLOOR_Y, "#")
    for x, y, n in ((30, 96, 9), (78, 104, 7), (52, 112, 6)):
        for i in range(n):
            c.put(x + i, y + (i % 3) // 2, "#")

    # A bare bulb on a wire, top middle, and its pool of light.
    c.vline(60, 0, 5, "#")
    c.rect(59, 6, 61, 7, "s")
    c.ellipse(60, 10, 2, 2, "y", ink="O")

    # Furnace, left, with its grate glowing.
    c.box(6, 30, 34, 80, "s")
    c.vline(33, 31, 79, "d")
    c.rect(12, 6, 16, 30, "s")  # the duct up
    c.vline(16, 6, 30, "d")
    c.box(12, 56, 28, 70, "#")
    c.rect(14, 58, 26, 68, "r")
    c.rect(16, 61, 24, 66, "O")
    for x in range(14, 27, 3):
        c.vline(x, 58, 68, "#")
    c.box(12, 38, 28, 44, "d")

    # Wooden stairs climbing up to the kitchen, right.
    for i in range(9):
        x = 84 + i * 4
        y = 78 - i * 7
        c.rect(x, y, SIZE - 1, y + 2, "O")
        c.hline(x, SIZE - 1, y, "#")
        c.rect(x, y + 3, SIZE - 1, y + 6, "o")
    c.rect(80, 78, 83, 80, "o")
    for i in range(10):  # a handrail
        c.put(82 + i * 4, 62 - i * 7, "#")
        c.put(83 + i * 4, 61 - i * 7, "#")
        c.put(84 + i * 4, 60 - i * 7, "#")
        c.put(85 + i * 4, 58 - i * 7, "#")
    # A paint can and a jar shelf.
    c.box(42, 72, 50, 80, "b")
    c.hline(42, 50, 74, "w")
    # The furnace as an old octopus: round shoulders, ducts reaching up, rivets,
    # its fire lighting the stone; the bulb is the only other light.
    c.ellipse(20, 31, 14, 4, "s")
    c.box(24, 10, 29, 28, "s")
    c.box(24, 8, 46, 13, "s")
    c.vline(28, 11, 28, "d")
    for y in range(36, 79, 6):
        c.put(8, y, "d")
        c.put(31, y, "d")
    glow(c, 20, 63, 30, "O", "gd")
    glow(c, 60, 10, 18, "y", "gd")
    dusk(c, 60, 10, 58, "p", "gd")
    return c


# ---- more shared pieces (batch 2) ------------------------------------------- #


def scatter(n, x0, y0, x1, y1, seed):
    """n fixed pseudo-random points in a box (same every build)."""
    pts = []
    v = seed
    for _ in range(n):
        v = (v * 1103515245 + 12345) & 0x7FFFFFFF
        x = x0 + v % (x1 - x0 + 1)
        v = (v * 1103515245 + 12345) & 0x7FFFFFFF
        y = y0 + v % (y1 - y0 + 1)
        pts.append((x, y))
    return pts


def night_sky(c, y1, seed=7, stars=22):
    c.rect(0, 0, SIZE - 1, y1, "n")
    for i, (x, y) in enumerate(scatter(stars, 0, 0, SIZE - 1, y1 - 2, seed)):
        c.put(x, y, "w" if i % 3 else "y")


def moon(c, cx, cy, r):
    c.ellipse(cx, cy, r, r, "w", ink="s")
    c.put(cx - r // 3, cy - r // 3, "s")
    c.put(cx + r // 3, cy + 1, "s")


def snow_ground(c, y0, seed=3):
    c.rect(0, y0, SIZE - 1, SIZE - 1, "w")
    for x, y in scatter(30, 0, y0 + 2, SIZE - 1, SIZE - 1, seed):
        c.hline(x, x + 2, y, "c" if x % 2 else "s")


def pine(c, cx, base, h, snowy=True):
    """A snowy pine: three tiers on a stub of trunk, `h` tall, standing on `base`."""
    c.rect(cx - 1, base - 3, cx + 1, base, "o")
    top = base - h
    tier = (h - 3) // 3
    for k in range(3):
        y0 = top + k * tier
        for j in range(tier + 3):
            half = j * 2 // 3 + k * 2 + 1
            y = y0 + j
            if y > base - 4:
                break
            c.hline(cx - half, cx + half, y, "G")
            c.put(cx - half - 1, y, "#")
            c.put(cx + half + 1, y, "#")
        if snowy:
            c.hline(cx - k - 1, cx + k + 1, y0 + 1, "w")
            c.hline(cx - half + 1, cx - half + 3, y, "w")
            c.hline(cx + half - 3, cx + half - 1, y, "w")
    c.put(cx, top - 1, "#")


def checks(c, y0, a, b, n=7):
    for y in range(y0, SIZE, n):
        for x in range(0, SIZE, n):
            c.rect(x, y, x + n - 1, y + n - 1, a if (x // n + y // n) % 2 else b)


def portrait(c, x0, y0, x1, y1, frame, bg, shirt, skin="k"):
    """A framed family photo: a head and shoulders."""
    c.box(x0, y0, x1, y1, frame)
    c.box(x0 + 2, y0 + 2, x1 - 2, y1 - 2, bg)
    cx = (x0 + x1) // 2
    r = max(2, (x1 - x0) // 6)
    c.ellipse(cx, y0 + 3 + r + 1, r, r, skin)
    c.rect(cx - r - 2, y1 - 3 - r, cx + r + 2, y1 - 3, shirt)


def string_lights(c, points, colors="ryblc"):
    for i, (x, y) in enumerate(points):
        c.put(x, y, "#")
        if i % 3 == 0:
            c.put(x, y + 1, colors[(i // 3) % len(colors)])


def wavy_line(c, x0, x1, y, sag):
    """A rope or wire hung from x0 to x1, sagging `sag` px in the middle."""
    pts = []
    for x in range(x0, x1 + 1):
        t = (x - x0) / max(1, x1 - x0)
        yy = y + int(sag * 4 * t * (1 - t))
        c.put(x, yy, "#")
        pts.append((x, yy))
    return pts


def stocking(c, x, y, col, cuff="w"):
    c.rect(x, y, x + 3, y + 2, cuff)
    c.rect(x, y + 3, x + 3, y + 8, col)
    c.rect(x - 2, y + 7, x + 3, y + 9, col)


# ---- rooms, batch 2 --------------------------------------------------------- #


def hallway():
    """A long hallway lined with family photos; a hall table, a red runner."""
    c = Canvas("s")
    for x in range(3, SIZE, 8):  # soft striped wallpaper
        c.vline(x, 12, 55, "w")
    c.rect(0, 0, SIZE - 1, 11, "w")  # ceiling, a lamp
    c.hline(0, SIZE - 1, 11, "o")
    c.ellipse(60, 6, 6, 3, "y", ink="O")
    c.rect(0, 56, SIZE - 1, FLOOR_Y, "o")  # wainscot
    c.hline(0, SIZE - 1, 56, "#")
    for x in range(4, SIZE, 14):
        c.box(x, 60, x + 9, 75, "o", ink="p")
    baseboard(c, color="p")
    planks(c, FLOOR_Y + 3)
    c.rect(0, 90, SIZE - 1, 106, "r")  # the runner
    c.hline(0, SIZE - 1, 89, "#")
    c.hline(0, SIZE - 1, 107, "#")
    c.hline(0, SIZE - 1, 92, "y")
    c.hline(0, SIZE - 1, 104, "y")
    for x in range(4, SIZE, 10):
        c.put(x, 98, "O")
        c.put(x + 5, 97, "p")
        c.put(x + 5, 99, "p")

    # Family photos, left and right, at all sorts of heights.
    portrait(c, 6, 18, 22, 38, "o", "c", "r")
    portrait(c, 26, 26, 36, 40, "y", "l", "b")
    portrait(c, 10, 42, 20, 53, "p", "k", "G", skin="O")
    portrait(c, 84, 20, 100, 40, "y", "b", "l")
    portrait(c, 104, 16, 116, 32, "o", "r", "w")
    portrait(c, 102, 36, 114, 52, "p", "c", "O")
    c.ellipse(91, 48, 4, 4, "k", ink="o")  # a round one
    c.put(91, 47, "o")
    # A hall table with a vase of holly, against the wainscot.
    c.box(4, 64, 34, 67, "O")
    c.vline(7, 68, 80, "o")
    c.vline(31, 68, 80, "o")
    c.box(16, 56, 22, 63, "b")
    c.ellipse(19, 53, 4, 2, "G")
    c.put(17, 52, "r")
    c.put(20, 51, "r")
    c.put(21, 54, "r")
    # Mistletoe under the lamp; shadow under the table; the ends of the hall dim.
    c.put(60, 12, "r")
    for x, y in ((58, 14), (59, 13), (61, 13), (62, 14), (60, 14)):
        c.put(x, y, "G")
    for x, y in ((59, 15), (61, 15)):
        c.put(x, y, "w")
    shade(c, 4, 81, 36, 85, "p", "Oo")
    dusk(c, 60, 6, 58, "g", "sw")
    return c


def laundry_room():
    """Washer and a still-warm dryer, socks on a line, a basket of clothes."""
    c = Canvas("c")
    for y in range(4, FLOOR_Y, 8):  # tiled walls
        c.hline(0, SIZE - 1, y, "w")
    for x in range(4, SIZE, 8):
        c.vline(x, 0, FLOOR_Y, "w")
    baseboard(c, color="s")
    checks(c, FLOOR_Y + 3, "w", "b")

    # A clothesline across the top, socks and a stocking pegged on it.
    line = wavy_line(c, 0, SIZE - 1, 6, 6)
    for x, col in ((10, "r"), (22, "l"), (88, "b"), (100, "w"), (110, "r")):
        y = line[x][1]
        c.put(x + 1, y, "O")  # peg
        c.rect(x, y + 1, x + 2, y + 6, col)
        c.rect(x, y + 5, x + 4, y + 7, col)
    stocking(c, 32, line[32][1] + 1, "r")

    # Shelf of detergent above the machines.
    c.box(2, 34, 40, 36, "o")
    for x, col in ((4, "b"), (12, "O"), (20, "r"), (30, "l")):
        c.box(x, 25, x + 6, 33, col)
        c.rect(x + 2, 23, x + 4, 24, "w")
    # Washer (left) and dryer, side by side.
    for x0, door in ((2, "c"), (21, "#")):
        c.box(x0, 44, x0 + 18, 80, "w")
        c.box(x0, 44, x0 + 18, 50, "w")
        c.put(x0 + 3, 47, "r")
        c.put(x0 + 6, 47, "l")
        c.ellipse(x0 + 9, 63, 6, 6, "s")
        c.ellipse(x0 + 9, 63, 4, 4, door, ink="d")
    c.rect(28, 61, 32, 65, "O")  # the dryer's warm load inside
    for x in (25, 30, 35):  # still warm: heat wavering up
        for i, y in enumerate(range(37, 43)):
            c.put(x + (i % 2), y, "O")

    # Laundry basket, right, heaped with clothes; an ironing board leaning.
    c.box(110, 14, 116, 82, "s")
    c.vline(113, 15, 81, "w")
    c.box(82, 66, 108, 82, "O")
    for x in range(84, 107, 3):
        c.vline(x, 67, 81, "o")
    c.ellipse(88, 64, 5, 3, "r")
    c.ellipse(97, 63, 5, 3, "l")
    c.ellipse(104, 64, 4, 3, "b")
    # The dryer's warmth on the tiles; shadows; a lost sock on the floor.
    glow(c, 30, 63, 22, "O", "c")
    dusk(c, 30, 63, 80, "b", "c")
    shade(c, 2, 81, 40, 85, "n", "wb")
    shade(c, 82, 83, 108, 87, "n", "wb")
    c.rect(100, 96, 102, 100, "#")
    c.rect(100, 99, 106, 102, "#")
    c.rect(101, 96, 101, 100, "r")
    c.rect(101, 100, 105, 101, "r")
    return c


def entryway():
    """The front door with a wreath, coats on hooks, boots on the mat."""
    c = Canvas("r")
    dots(c, "p", 56, step_x=10, step_y=10, x0=5, y0=5)
    c.rect(0, 56, SIZE - 1, FLOOR_Y, "w")  # white wainscot
    c.hline(0, SIZE - 1, 56, "#")
    for x in range(4, SIZE, 14):
        c.box(x, 60, x + 9, 75, "w", ink="s")
    baseboard(c, color="s")
    planks(c, FLOOR_Y + 3, base="o", seam="p")

    # Coat hooks, left: two coats and a striped scarf, a hat on top.
    c.box(2, 18, 38, 21, "o")
    for x in (8, 20, 32):
        c.rect(x, 22, x + 1, 23, "y")
    c.box(3, 24, 15, 54, "b")  # coat
    c.vline(9, 26, 53, "n")
    c.box(16, 24, 26, 50, "G")  # coat
    c.vline(21, 26, 49, "#")
    for y in range(24, 56, 4):  # scarf
        c.rect(30, y, 33, y + 1, "y")
        c.rect(30, y + 2, 33, y + 3, "r")
    c.ellipse(8, 14, 5, 3, "r")  # bobble hat on the rail
    c.put(8, 9, "w")
    # Boots on a mat below them.
    c.box(2, 84, 38, 90, "O")
    for x, col in ((4, "#"), (12, "#"), (22, "r"), (29, "r")):
        c.rect(x, 74, x + 3, 84, col)
        c.rect(x, 82, x + 6, 85, col)

    # The front door, right, a wreath on it and a window at the top.
    c.box(82, 12, 114, 80, "o")
    c.box(86, 16, 110, 30, "n")
    c.vline(98, 17, 29, "o")
    c.put(90, 20, "w")
    c.put(104, 22, "w")
    c.put(94, 26, "w")
    c.rect(87, 28, 109, 29, "w")
    c.box(86, 36, 96, 74, "o", ink="p")
    c.box(100, 36, 110, 74, "o", ink="p")
    c.ellipse(98, 48, 8, 8, "G")  # wreath
    c.ellipse(98, 48, 3, 3, "o")
    for x, y in ((92, 44), (103, 45), (95, 54), (102, 53)):
        c.put(x, y, "r")
    c.rect(96, 55, 100, 58, "r")  # bow
    c.rect(79, 52, 81, 54, "y")  # knob (on the latch side)
    c.box(84, 82, 112, 87, "g")  # mat
    # Garland and lights round the door, jingle bells on the knob, wet boots.
    for x in range(80, 117):
        c.put(x, 10 + (x % 6 > 2), "G")
        if x % 4 == 0:
            c.put(x, 12, "yrb"[(x // 4) % 3])
    for y in range(10, 60):
        c.put(80 + (y % 6 > 2), y, "G")
        if y % 4 == 0:
            c.put(82, y, "yrb"[(y // 4) % 3])
    c.put(80, 56, "y")
    c.put(81, 58, "y")
    for x, y in ((6, 92), (22, 93), (30, 91)):
        c.hline(x, x + 6, y, "c")
    shade(c, 2, 91, 38, 93, "p", "op")
    return c


def bedroom():
    """A quiet bedroom: moonlit window, nightstand lamp, a patchwork quilt."""
    c = Canvas("b")
    dots(c, "c", FLOOR_Y, step_x=8, step_y=8)
    baseboard(c, color="w")
    planks(c, FLOOR_Y + 3, base="O", seam="o")
    c.ellipse(60, 102, 38, 9, "c", ink="n")  # an oval rug

    # Window, left, with the moon in it and white curtains.
    night_window(c, 6, 14, 34, 44)
    c.ellipse(13, 21, 3, 3, "y", ink="y")
    c.rect(3, 12, 37, 13, "o")
    c.rect(3, 14, 7, 48, "w")
    c.rect(33, 14, 37, 48, "w")
    # Nightstand with a lamp and a little clock.
    c.box(8, 60, 30, 80, "o")
    c.hline(9, 29, 68, "#")
    c.rect(18, 64, 20, 65, "y")
    c.rect(18, 73, 20, 74, "y")
    c.vline(14, 50, 59, "#")
    for i in range(6):  # lampshade
        c.hline(10 - i // 2, 18 + i // 2, 44 + i, "y")
    c.ellipse(25, 56, 3, 3, "w")
    c.put(25, 55, "#")
    c.put(26, 56, "#")

    # Bed, right: headboard, pillow, patchwork quilt.
    c.box(84, 38, 119, 80, "o")
    c.box(88, 42, 119, 50, "O", ink="o")
    c.box(88, 52, 114, 59, "w")
    c.box(80, 60, 119, 84, "w")
    for i, x in enumerate(range(81, 119, 6)):
        for j, y in enumerate(range(61, 83, 6)):
            c.rect(x, y, x + 4, y + 4, "rlcy"[(i + j) % 4])
    # A picture of a sailboat above the bed.
    c.box(94, 18, 112, 32, "y")
    c.box(96, 20, 110, 30, "c")
    c.rect(97, 28, 109, 29, "b")
    c.rect(100, 26, 106, 27, "o")
    c.vline(103, 21, 25, "#")
    c.rect(104, 22, 106, 25, "w")
    # Lamplight, dark beyond; a present hidden under the bed for tomorrow.
    glow(c, 14, 47, 22, "O", "bc")
    dusk(c, 14, 47, 60, "n", "bc")
    shade(c, 80, 85, 119, 89, "p", "Oo")
    c.box(88, 84, 100, 91, "r")
    c.vline(94, 85, 90, "y")
    c.rect(92, 83, 96, 84, "y")
    return c


def kids_bedroom():
    """Star stickers, a little bed with a teddy, stockings hung by the window, blocks."""
    c = Canvas("l")
    for x, y in scatter(16, 4, 4, SIZE - 5, 70, 11):  # star stickers
        c.put(x, y, "y")
        c.put(x - 1, y, "y")
        c.put(x + 1, y, "y")
        c.put(x, y - 1, "y")
        c.put(x, y + 1, "y")
    baseboard(c, color="w")
    planks(c, FLOOR_Y + 3, base="O", seam="o")

    # Window, right, with stockings hung on a string under it.
    night_window(c, 80, 18, 106, 40)
    wavy_line(c, 76, 110, 44, 2)
    for x, col in ((81, "r"), (90, "G"), (99, "b")):
        stocking(c, x, 45, col)
    # A toy shelf under that.
    c.box(84, 66, 114, 68, "o")
    c.box(86, 60, 92, 65, "r")
    c.box(94, 58, 98, 65, "b")
    c.ellipse(106, 62, 3, 3, "y")
    # Blocks on the floor.
    for x, y, col in ((90, 90, "r"), (98, 90, "b"), (94, 84, "y"), (106, 92, "l")):
        c.box(x, y, x + 6, y + 6, col)
        c.put(x + 3, y + 3, "w")

    # A little bed, left, red blanket, teddy on the pillow.
    c.box(2, 46, 8, 80, "b")
    c.box(2, 46, 36, 50, "b")
    c.box(8, 56, 24, 62, "w")
    c.box(2, 62, 38, 80, "r")
    for y in (66, 72):
        c.hline(3, 37, y, "w")
    c.ellipse(28, 56, 4, 4, "O")  # teddy
    c.ellipse(28, 50, 3, 3, "O")
    c.put(25, 47, "O")
    c.put(31, 47, "O")
    c.put(27, 50, "#")
    c.put(29, 50, "#")
    # A rocket poster above the bed.
    c.box(8, 14, 30, 38, "n")
    c.rect(18, 20, 20, 30, "w")
    c.put(19, 19, "r")
    c.rect(16, 28, 17, 31, "r")
    c.rect(21, 28, 22, 31, "r")
    c.rect(18, 32, 20, 34, "O")
    c.put(11, 17, "w")
    c.put(26, 22, "w")
    # A star night-light, dark corners, a letter to Santa on the floor.
    c.box(72, 69, 77, 75, "y")
    c.put(74, 71, "O")
    glow(c, 74, 72, 18, "y", "l")
    dusk(c, 74, 72, 62, "G", "l")
    c.box(44, 98, 53, 106, "w", ink="s")
    for y in (100, 102, 104):
        c.hline(46, 51, y, "s")
    c.put(47, 100, "r")
    c.rect(55, 103, 59, 104, "r")
    return c


def garage():
    """Pegboard of tools over a workbench, shelves crammed with cans, a sled."""
    c = Canvas("s")
    for i, y in enumerate(range(0, FLOOR_Y, 6)):  # block wall
        c.hline(0, SIZE - 1, y, "g")
        for x in range((i % 2) * 6, SIZE, 12):
            c.vline(x, y, y + 5, "g")
    c.rect(0, FLOOR_Y, SIZE - 1, SIZE - 1, "g")  # concrete floor
    c.hline(0, SIZE - 1, FLOOR_Y, "#")
    c.ellipse(64, 104, 10, 3, "d", ink="d")  # an oil stain
    c.rect(48, 0, 72, 3, "w")  # strip light
    c.hline(48, 72, 4, "#")

    # Pegboard and tools, left.
    c.box(2, 16, 38, 50, "O")
    for x in range(5, 37, 4):
        for y in range(19, 49, 4):
            c.put(x, y, "o")
    c.rect(6, 20, 7, 34, "o")  # hammer
    c.rect(4, 20, 9, 23, "d")
    c.rect(13, 22, 14, 38, "s")  # wrench
    c.rect(12, 20, 15, 22, "s")
    c.rect(19, 21, 31, 27, "s")  # saw
    c.rect(19, 21, 22, 30, "o")
    c.rect(25, 34, 27, 46, "r")  # screwdriver
    c.rect(26, 40, 26, 46, "s")
    c.ellipse(33, 40, 3, 3, "y", ink="#")  # a coil of tape
    # Workbench with a red toolbox.
    c.box(2, 56, 40, 60, "o")
    c.vline(5, 61, 80, "o")
    c.vline(37, 61, 80, "o")
    c.box(10, 72, 26, 79, "r")  # the toolbox, under the bench
    c.rect(15, 70, 21, 71, "#")
    # On the bench, a wooden toy train being painted for under the tree.
    c.box(6, 47, 16, 55, "r")
    c.box(12, 43, 16, 55, "r")
    c.put(14, 45, "c")
    c.rect(8, 44, 9, 46, "#")
    c.box(18, 49, 28, 55, "k")  # its car, not painted yet
    for x in (8, 14, 20, 26):
        c.put(x, 55, "#")
    c.box(31, 50, 36, 55, "l")  # a paint pot, brush in it
    c.vline(34, 45, 49, "o")
    c.put(30, 55, "r")

    # Shelves, right, crammed.
    for y in (26, 46):
        c.box(80, y, 118, y + 2, "o")
    for x, h, col in ((82, 8, "b"), (88, 6, "r"), (93, 9, "y"), (100, 7, "l"), (106, 8, "w"), (112, 6, "O")):
        c.box(x, 26 - h, x + 5, 25, col)
    for x, h, col in ((82, 10, "k"), (92, 7, "d"), (99, 9, "k"), (110, 6, "r")):
        c.box(x, 46 - h, x + 8, 45, col)
    c.vline(81, 29, 80, "o")
    c.vline(117, 29, 80, "o")
    # A red sled leaning against the shelves, and a snow shovel.
    for i in range(24):
        c.rect(96 + i // 6, 56 + i, 108 + i // 6, 56 + i, "r")
    c.rect(94, 54, 108, 55, "#")
    c.vline(112, 50, 80, "o")
    c.rect(109, 78, 116, 84, "s")
    # Dark beyond the strip light; shadow under the bench.
    dusk(c, 60, 4, 68, "g", "s")
    shade(c, 2, 79, 40, 83, "d", "g")
    return c


def attic():
    """Under the rafters: a round window, a trunk, a box of ornaments, old lights."""
    c = Canvas("o")
    for x in range(0, SIZE, 7):  # board walls
        c.vline(x, 0, FLOOR_Y, "p")
    for x, y in scatter(10, 2, 40, SIZE - 3, 75, 5):
        c.put(x, y, "O")  # knots
    # The roof's underside: rafters slope down from the peak to either side.
    for y in range(52):
        x = 60 - (52 - y) * 60 // 52
        c.rect(0, y, max(0, x - 1), y, "p")
        c.rect(min(SIZE - 1, 120 - x), y, SIZE - 1, y, "p")
        c.rect(max(0, x - 3), y, x, y, "O")
        c.rect(120 - x - 1, y, min(SIZE - 1, 120 - x + 2), y, "O")
        c.put(max(0, x - 4), y, "#")
        c.put(min(SIZE - 1, 120 - x + 3), y, "#")
    # Old lights draped along both rafters.
    pts = [(60 - (52 - y) * 60 // 52 + 1, y + 3) for y in range(0, 52, 2)]
    pts += [(120 - (60 - (52 - y) * 60 // 52) - 1, y + 3) for y in range(0, 52, 2)]
    string_lights(c, [(x, y) for x, y in pts if 0 <= x < SIZE])
    # A round window in the peak.
    c.ellipse(60, 9, 6, 6, "n", ink="#")
    c.vline(60, 3, 15, "o")
    c.hline(54, 66, 9, "o")
    c.put(57, 6, "w")
    baseboard(c, color="p")
    planks(c, FLOOR_Y + 3, base="O", seam="o")

    # A trunk, left, with a box of ornaments open on it.
    c.box(2, 62, 34, 82, "O")
    c.hline(2, 34, 68, "#")
    for x in (8, 28):
        c.vline(x, 63, 81, "o")
    c.rect(17, 66, 19, 70, "y")
    c.box(6, 50, 30, 61, "k")
    for x, col in ((10, "r"), (16, "b"), (22, "y"), (27, "l")):
        c.ellipse(x, 50, 2, 2, col)
    # Boxes, right, one spilling tinsel; a cobweb or two.
    c.box(86, 58, 118, 82, "k")
    c.hline(86, 118, 64, "o")
    c.box(92, 42, 114, 58, "k")
    c.hline(92, 114, 47, "o")
    for x in range(93, 114, 2):
        c.put(x, 41 - (x % 4) // 2, "y")
    c.rect(97, 52, 108, 54, "r")  # a label
    for i in range(6):
        c.put(SIZE - 1 - i, 52 + i, "s")
        c.put(SIZE - 7 + i // 2, 58, "s")
    # Moonlight down from the round window, dust in it.
    for y in range(15, 93):
        half = 5 + (y - 15) * 15 // 78
        shade(c, 60 - half, y, 60 + half, y, "s", "opO")
    for x, y in ((56, 40), (64, 52), (58, 64), (66, 34), (62, 74), (55, 58)):
        c.put(x, y, "w")
    return c


def yard():
    """The snowy yard at night: a fence, pines, the moon, footprints."""
    c = Canvas("w")
    night_sky(c, 56, seed=21)
    moon(c, 98, 14, 6)
    snow_ground(c, 56, seed=4)
    # A picket fence along the back, capped with snow.
    c.rect(0, 50, SIZE - 1, 51, "o")
    c.rect(0, 60, SIZE - 1, 61, "o")
    for x in range(1, SIZE, 6):
        c.box(x, 44, x + 3, 66, "O", ink="o")
        c.rect(x, 43, x + 3, 44, "w")
    c.rect(0, 64, SIZE - 1, 68, "w")  # drifted snow along its foot
    # Pines either side.
    pine(c, 14, 86, 56)
    pine(c, 106, 84, 50)
    pine(c, 30, 70, 26)
    # Footprints across the snow.
    for i, x in enumerate(range(20, 100, 7)):
        y = 108 - i % 2 * 3 - i // 3
        c.rect(x, y, x + 1, y + 1, "s")
    # A sled in the snow, bottom right.
    c.box(84, 96, 106, 100, "r")
    c.hline(82, 108, 102, "#")
    c.put(81, 101, "#")
    # A snow angel; pines' shadows on the snow.
    c.ellipse(60, 99, 10, 4, "w", ink="s")
    for j in range(8):
        c.hline(60 - 2 - j // 2, 60 + 2 + j // 2, 100 + j, "w")
        c.put(60 - 3 - j // 2, 100 + j, "s")
        c.put(60 + 3 + j // 2, 100 + j, "s")
    c.ellipse(60, 93, 2, 2, "w", ink="s")
    shade(c, 16, 85, 34, 89, "c", "w")
    shade(c, 108, 83, 119, 87, "c", "w")
    return c


def front_porch():
    """Icicles on the eave, a glowing porch light and window, a railing, deep drifts."""
    c = Canvas("s")
    for y in range(14, 60, 5):  # siding
        c.hline(0, SIZE - 1, y, "g")
    c.rect(0, 0, SIZE - 1, 7, "o")  # the eave, hung with icicles
    c.hline(0, SIZE - 1, 7, "#")
    c.rect(0, 5, SIZE - 1, 6, "w")
    for x in range(2, SIZE, 5):
        h = 3 + (x * 7) % 6
        c.vline(x, 8, 8 + h, "c")
        c.vline(x + 1, 8, 8 + h // 2, "w")
    string_lights(c, [(x, 10 + (x % 10 > 4)) for x in range(0, SIZE, 2)])
    # A window with warm light and a candle in it.
    c.box(4, 20, 34, 48, "O")
    c.vline(19, 21, 47, "w")
    c.hline(5, 33, 34, "w")
    c.rect(5, 21, 33, 21, "w")
    candle(c, 11, 46, h=6, color="w")
    candle(c, 26, 46, h=6, color="w")
    # Porch light by the door's edge.
    c.box(84, 26, 90, 34, "y")
    c.rect(86, 24, 88, 25, "#")
    for x, y in ((82, 30), (92, 30), (87, 22), (87, 37), (83, 25), (91, 35)):
        c.put(x, y, "y")
    # Porch floor and railing.
    planks(c, 60, base="o", seam="p")
    c.rect(0, 52, SIZE - 1, 54, "w")
    c.hline(0, SIZE - 1, 55, "#")
    for x in range(2, SIZE, 7):
        c.rect(x, 56, x + 2, 76, "w")
        c.vline(x + 3, 56, 76, "s")
    c.rect(0, 74, SIZE - 1, 77, "w")
    c.hline(0, SIZE - 1, 78, "#")
    snow_ground(c, 79, seed=8)
    # Deep drifts, piled up the right side and over the rail.
    c.ellipse(112, 74, 22, 18, "w", ink="s")
    c.ellipse(100, 92, 26, 14, "w", ink="s")
    c.ellipse(8, 96, 16, 8, "w", ink="s")
    c.rect(0, 100, SIZE - 1, SIZE - 1, "w")
    for x, y in scatter(12, 0, 100, SIZE - 1, SIZE - 1, 9):
        c.hline(x, x + 2, y, "c")
    # The porch light's glow; a wreath; a shovel stuck in the drift.
    glow(c, 87, 30, 20, "y", "sg")
    c.ellipse(42, 40, 5, 5, "G")
    c.ellipse(42, 40, 1, 1, "s", ink="#")
    for x, y in ((38, 37), (45, 38), (40, 44), (46, 42)):
        c.put(x, y, "r")
    c.rect(40, 45, 44, 47, "r")
    c.vline(98, 56, 72, "o")
    c.hline(96, 100, 55, "#")
    c.box(94, 72, 102, 78, "s")
    for x, y in ((30, 92), (38, 96), (46, 92), (54, 96)):
        c.rect(x, y, x + 2, y + 1, "s")
    return c


def snow_fort():
    """Snow-block walls, a flag on the tower, a pyramid of snowballs, a toy bucket."""
    c = Canvas("w")
    night_sky(c, 46, seed=33)
    snow_ground(c, 46, seed=13)

    def blocks(x0, y0, x1, y1):
        c.box(x0, y0, x1, y1, "w", ink="s")
        for i, y in enumerate(range(y0, y1, 6)):
            c.hline(x0, x1, y, "s")
            for x in range(x0 + (i % 2) * 5, x1, 10):
                c.vline(x, y, y + 5, "s")
        for x in range(x0, x1 - 3, 8):  # crenellations
            c.box(x, y0 - 5, x + 4, y0, "w", ink="s")

    blocks(0, 26, 34, 86)  # left tower
    blocks(86, 32, 119, 86)  # right wall
    blocks(34, 58, 86, 76)  # low back wall behind the middle
    # A flag on the tower.
    c.vline(18, 6, 20, "o")
    c.rect(19, 6, 27, 11, "r")
    c.rect(19, 12, 23, 12, "r")
    c.put(22, 8, "y")
    # Toys stashed on top of the right wall: a toy truck.
    c.box(88, 20, 102, 26, "r")
    c.box(98, 16, 104, 26, "r")
    c.rect(100, 18, 102, 20, "c")
    c.ellipse(91, 27, 2, 2, "#", ink="#")
    c.ellipse(100, 27, 2, 2, "#", ink="#")
    # Snowball pyramid, bottom right; a bucket and spade, bottom left.
    for row, n in enumerate((4, 3, 2, 1)):
        for i in range(n):
            c.ellipse(78 + row * 3 + i * 6, 100 - row * 5, 2, 2, "w", ink="s")
    c.box(18, 90, 30, 102, "b")
    c.hline(18, 30, 93, "c")
    wavy_line(c, 19, 29, 86, -3)
    c.vline(36, 84, 100, "o")
    c.rect(34, 100, 38, 104, "y")
    # The moon, and the fort's walls shaded away from it.
    moon(c, 46, 12, 4)
    shade(c, 28, 22, 34, 86, "c", "w")
    shade(c, 112, 28, 119, 86, "c", "w")
    shade(c, 34, 70, 86, 76, "c", "w")
    shade(c, 0, 87, 36, 91, "c", "w")
    shade(c, 84, 87, 119, 91, "c", "w")
    return c


def front_walk():
    """The shoveled walk: a path between snowbanks, a lamppost, the mailbox."""
    c = Canvas("w")
    night_sky(c, 44, seed=41)
    moon(c, 22, 14, 5)
    snow_ground(c, 44, seed=17)
    # A row of distant snowy pines along the horizon.
    for x in range(4, SIZE, 13):
        pine(c, x, 46, 14 + (x * 5) % 7)
    # The path, widening toward us, stones in it.
    for y in range(46, SIZE):
        half = 8 + (y - 46) * 30 // (SIZE - 46)
        c.hline(60 - half, 60 + half, y, "g")
        c.put(60 - half - 1, y, "s")
        c.put(60 + half + 1, y, "s")
    for i, y in enumerate(range(50, SIZE, 7)):
        half = 8 + (y - 46) * 30 // (SIZE - 46)
        c.hline(60 - half, 60 + half, y, "d")
        for x in range(60 - half + (i % 2) * 5, 60 + half, 10):
            c.vline(x, y, y + 6, "d")
    # Snowbanks along both edges.
    for x, y in ((14, 96), (106, 96), (24, 66), (96, 66)):
        c.ellipse(x, y, 16, 6, "w", ink="s")
    # Lamppost, left, its light glowing.
    c.rect(22, 30, 24, 90, "#")
    c.rect(19, 88, 27, 91, "#")
    c.box(18, 18, 28, 29, "y")
    c.rect(17, 16, 29, 17, "#")
    for x, y in ((15, 22), (31, 24), (23, 13), (14, 28), (32, 18)):
        c.put(x, y, "y")
    # Mailbox, right, flag up; a shovel stuck in the bank.
    c.vline(99, 64, 92, "o")
    c.vline(100, 64, 92, "o")
    c.box(90, 54, 108, 64, "b")
    c.rect(90, 52, 108, 53, "w")
    c.rect(106, 46, 107, 56, "r")
    c.rect(104, 46, 105, 48, "r")
    c.vline(86, 72, 92, "o")
    c.box(82, 90, 90, 100, "s")
    # Candy canes along the path, a wreath on the lamppost, its glow.
    for y in (60, 74, 88, 102):
        half = 8 + (y - 46) * 30 // (SIZE - 46)
        candy_cane(c, 60 - half - 5, y, h=7)
        candy_cane(c, 60 + half + 4, y, h=7)
    glow(c, 23, 24, 16, "y", "n")
    c.ellipse(23, 42, 3, 3, "G")
    c.put(23, 42, "#")
    c.rect(22, 45, 24, 46, "r")
    return c


def back_door():
    """The mudroom: back door with a snowy window, boots in a tray, a shovel, coats."""
    c = Canvas("g")
    c.rect(0, 50, SIZE - 1, FLOOR_Y, "w")  # beadboard
    for x in range(0, SIZE, 4):
        c.vline(x, 51, FLOOR_Y, "s")
    c.hline(0, SIZE - 1, 50, "#")
    c.rect(0, 48, SIZE - 1, 49, "o")
    baseboard(c, color="o")
    checks(c, FLOOR_Y + 3, "d", "g", n=8)

    # The back door, left, with a snowy window.
    c.box(4, 10, 34, 80, "c")
    night_window(c, 9, 14, 29, 36, frame="w")
    c.box(9, 42, 29, 74, "c", ink="b")
    c.rect(30, 46, 32, 48, "y")
    c.box(2, 82, 38, 90, "o")  # mat
    for x in range(5, 37, 4):
        c.vline(x, 83, 89, "O")
    for x, y in ((6, 94), (30, 96), (20, 100)):  # melted snow
        c.hline(x, x + 4, y, "c")
    # Boot tray, right of the door.
    c.box(78, 82, 118, 86, "#", ink="#")
    for x, col in ((80, "r"), (88, "r"), (98, "b"), (106, "b")):
        c.rect(x, 70, x + 3, 82, col)
        c.rect(x, 79, x + 6, 82, col)
        c.rect(x, 69, x + 3, 70, "w")
    # Coat hooks with a coat and a scarf; the snow shovel leaning.
    c.box(80, 18, 118, 21, "o")
    c.box(82, 22, 96, 50, "r")
    c.vline(89, 24, 49, "p")
    for y in range(22, 46, 4):
        c.rect(100, y, 103, y + 1, "w")
        c.rect(100, y + 2, 103, y + 3, "b")
    c.vline(112, 22, 70, "o")
    c.box(107, 70, 117, 82, "s")
    c.rect(110, 20, 114, 21, "#")
    # Moonlight through the door's window onto the floor; dim far wall; snowy boots.
    for y in range(91, 104):
        k = (y - 91) // 2
        shade(c, 10 + k, y, 30 + k, y, "s", "dg")
    dusk(c, 19, 25, 70, "p", "g")
    for x in (80, 88, 98, 106):
        c.rect(x + 4, 79, x + 6, 79, "w")
    return c


def cellar_door():
    """Outside, against the house: a slanted red cellar door in the snow."""
    c = Canvas("s")
    for y in range(4, 58, 5):  # siding
        c.hline(0, SIZE - 1, y, "g")
    # Stone foundation.
    c.rect(0, 58, SIZE - 1, 80, "g")
    for i, y in enumerate(range(58, 80, 5)):
        c.hline(0, SIZE - 1, y, "d")
        for x in range((i % 2) * 6, SIZE, 12):
            c.vline(x, y, y + 4, "d")
    c.hline(0, SIZE - 1, 58, "#")
    snow_ground(c, 80, seed=23)
    # A basement window low in the wall, a little warm light.
    c.box(10, 62, 30, 74, "O")
    c.vline(20, 63, 73, "w")
    c.rect(11, 72, 29, 73, "w")
    # A kitchen window above, and the downspout.
    night_window(c, 84, 12, 110, 40, snow=False)
    c.rect(85, 13, 109, 39, "O")
    c.vline(97, 13, 39, "w")
    c.hline(85, 109, 26, "w")
    c.rect(82, 41, 112, 43, "w")
    c.rect(114, 0, 116, 80, "w")
    c.vline(116, 0, 80, "s")
    # The slanted cellar door, in the snow below the middle.
    for y in range(82, 112):
        t = (y - 82) / 30
        half = int(30 + 12 * t)
        c.hline(60 - half - 3, 60 + half + 3, y, "g")
        c.hline(60 - half, 60 + half, y, "r")
        for x in range(60 - half, 60 + half, 6):
            c.put(x + int(t * (x - 60) // 6), y, "p")
        c.put(60, y, "#")
        c.put(59, y, "#")
    c.hline(27, 93, 81, "#")
    c.rect(27, 82, 93, 83, "w")  # snow along its top
    c.rect(52, 94, 54, 98, "s")  # handles
    c.rect(66, 94, 68, 98, "s")
    c.hline(15, 105, 112, "#")
    c.ellipse(10, 100, 12, 6, "w", ink="s")
    c.ellipse(110, 100, 12, 6, "w", ink="s")
    # Warm light from the windows; paw prints in the snow, to the cellar door.
    glow(c, 97, 26, 20, "O", "sg")
    glow(c, 20, 76, 14, "O", "w")
    for x, y in ((6, 114), (14, 110), (10, 104), (18, 100), (16, 94), (24, 90)):
        paw(c, x, y)
    return c


def roof():
    """Up on the snowy roof: moon and stars, the neighbours' roofs, an antenna."""
    c = Canvas("n")
    night_sky(c, SIZE - 1, seed=55, stars=30)
    moon(c, 22, 40, 10)
    # Neighbours' rooftops in the distance, windows lit.
    for x0, x1, top in ((0, 34, 54), (30, 70, 60), (66, 96, 52), (92, 119, 58)):
        c.rect(x0, top, x1, 80, "p")
        mid = (x0 + x1) // 2
        for y in range(top - 8, top):
            half = (y - (top - 8)) * (x1 - x0) // 16
            c.hline(mid - half, mid + half, y, "p")
        c.hline(mid - (x1 - x0) // 2, mid + (x1 - x0) // 2, top, "w")
        c.box(mid - 4, top + 6, mid + 2, top + 12, "y")
    # Our roof: shingles under a thick layer of snow, lights along the gutter.
    c.rect(0, 82, SIZE - 1, SIZE - 1, "r")
    for i, y in enumerate(range(84, SIZE, 5)):
        c.hline(0, SIZE - 1, y, "p")
        for x in range((i % 2) * 4, SIZE, 8):
            c.vline(x, y, y + 4, "p")
    c.rect(0, 74, SIZE - 1, 84, "w")
    for x in range(0, SIZE, 9):
        c.ellipse(x + 4, 74, 6, 2, "w", ink="w")
        c.hline(x + 1, x + 7, 72, "s")
    c.hline(0, SIZE - 1, 85, "s")
    string_lights(c, [(x, 112 + (x % 12 > 5)) for x in range(0, SIZE, 2)])
    # A TV antenna, right.
    c.vline(108, 30, 76, "d")
    for y, half in ((34, 8), (42, 6), (50, 4)):
        c.hline(108 - half, 108 + half, y, "d")
    c.put(108, 29, "w")
    # Santa's sleigh across the moon, and the shingles shaded below the snow.
    c.rect(14, 39, 19, 41, "#")
    c.rect(14, 37, 15, 38, "#")
    c.put(17, 38, "#")
    c.hline(13, 20, 43, "#")
    c.put(21, 42, "#")
    c.hline(20, 23, 39, "#")
    for rx in (24, 29):
        c.rect(rx, 38, rx + 2, 39, "#")
        c.put(rx, 40, "#")
        c.put(rx + 2, 40, "#")
        c.put(rx + 3, 37, "#")
        c.put(rx + 3, 36, "#")
        c.put(rx + 4, 35, "#")
    shade(c, 0, 100, SIZE - 1, SIZE - 1, "p", "r")
    return c


def pond():
    """A frozen pond: ice with glints, reeds and cattails, a snowy log."""
    c = Canvas("w")
    night_sky(c, 42, seed=61)
    snow_ground(c, 42, seed=19)
    moon(c, 22, 22, 3)
    for x in range(0, SIZE, 9):  # pines along the far bank
        pine(c, x + 3, 48, 16 + (x * 3) % 9)
    # The ice.
    c.ellipse(60, 84, 50, 18, "c", ink="s")
    c.ellipse(60, 84, 40, 13, "c", ink="c")
    for x, y, n in ((30, 78, 6), (70, 74, 8), (52, 92, 5), (86, 88, 6), (40, 86, 3)):
        c.hline(x, x + n, y, "w")
        c.put(x + n + 1, y - 1, "w")
    for x, y in ((24, 84), (96, 80), (64, 96)):
        c.put(x, y, "b")
        c.put(x + 1, y + 1, "b")
    # Reeds and cattails, left and right.
    for x0 in (4, 104):
        for i, x in enumerate(range(x0, x0 + 14, 3)):
            top = 58 + (i * 5) % 9
            c.vline(x, top, 84, "G" if i % 2 else "l")
            if i % 2 == 0:
                c.rect(x - 1, top, x + 1, top + 5, "o")
                c.put(x, top - 1, "w")
    # A log in the snow, front left, snow on top.
    c.box(14, 98, 46, 106, "o")
    for x in range(18, 44, 6):
        c.hline(x, x + 3, 102, "p")
    c.ellipse(46, 102, 3, 4, "O", ink="#")
    c.put(46, 102, "o")
    c.rect(15, 96, 45, 98, "w")
    # The moon's light on the ice; somebody's skates left on the log.
    shade(c, 19, 72, 25, 96, "w", "c")
    for x in (26, 35):
        c.rect(x, 90, x + 3, 94, "r")
        c.rect(x, 93, x + 6, 94, "r")
        c.hline(x - 1, x + 7, 95, "s")
    return c


def tree_house():
    """Inside the tree house: plank walls, a window onto bare snowy branches,
    a lantern, pennants, a blanket, the trapdoor."""
    c = Canvas("o")
    for x in range(0, SIZE, 8):
        c.vline(x, 0, FLOOR_Y, "p")
    for x, y in scatter(9, 3, 30, SIZE - 4, 74, 2):
        c.ellipse(x, y, 1, 1, "O", ink="p")
    # Pennants on a string across the top.
    pts = wavy_line(c, 0, SIZE - 1, 4, 8)
    for i, x in enumerate(range(3, SIZE - 6, 9)):
        y = pts[x][1] + 1
        col = "rybl"[i % 4]
        for j in range(5):
            c.hline(x + j // 2, x + 5 - j // 2, y + j, col)
    # The window, left: night, bare branches with snow on them.
    c.box(4, 18, 34, 48, "n")
    c.rect(3, 17, 35, 17, "O")
    c.rect(3, 49, 35, 50, "O")
    for i in range(24):
        c.put(5 + i, 40 - i // 2, "o")
        c.put(5 + i, 39 - i // 2, "w" if i % 3 == 0 else "o")
    for i in range(10):
        c.put(20 + i, 28 + i // 3, "o")
    c.put(10, 22, "w")
    c.put(28, 22, "w")
    c.put(16, 44, "w")
    # A lantern on a nail, right.
    c.vline(94, 14, 18, "#")
    c.box(90, 19, 98, 30, "y")
    c.rect(92, 22, 96, 27, "O")
    c.hline(89, 99, 19, "#")
    c.hline(89, 99, 30, "#")
    for x, y in ((86, 24), (102, 24), (94, 34), (88, 32), (100, 16)):
        c.put(x, y, "y")
    baseboard(c, color="p")
    planks(c, FLOOR_Y + 3, base="O", seam="o")
    # A checked blanket heaped in the corner, left.
    c.box(2, 70, 32, 88, "r")
    for x in range(4, 32, 6):
        c.vline(x, 71, 87, "w")
    for y in (75, 81):
        c.hline(3, 31, y, "w")
    # The trapdoor, open, the rope ladder going down.
    c.box(86, 92, 114, 108, "#")
    c.vline(94, 93, 107, "O")
    c.vline(106, 93, 107, "O")
    for y in range(95, 108, 4):
        c.hline(94, 106, y, "O")
    c.box(84, 82, 116, 90, "o")  # the lid, flipped up
    # A few dry leaves blown in.
    for x, y in ((40, 96), (76, 104), (50, 112), (20, 100)):
        c.rect(x, y, x + 2, y + 1, "O")
        c.put(x + 1, y + 2, "r")
    # The lantern's glow; comics on the blanket; a tin-can phone out the window.
    glow(c, 94, 25, 24, "O", "op")
    c.rect(10, 64, 22, 65, "r")
    c.rect(11, 66, 21, 67, "y")
    c.rect(10, 68, 22, 69, "b")
    c.hline(10, 22, 63, "#")
    for t in range(39):
        c.put(40 - t * 6 // 38, 84 - t, "k")
    c.box(37, 84, 42, 90, "s")
    return c


def cave():
    """A shallow cave: the snowy yard through the mouth, drips, glowing eyes in the dark."""
    c = Canvas("d")
    for x, y in scatter(40, 0, 0, SIZE - 1, FLOOR_Y, 77):  # rough rock
        c.rect(x, y, x + 2, y + 1, "g" if x % 3 else "p")
    # Floor.
    c.rect(0, FLOOR_Y, SIZE - 1, SIZE - 1, "g")
    c.hline(0, SIZE - 1, FLOOR_Y, "#")
    for x, y in scatter(14, 0, FLOOR_Y + 4, SIZE - 1, SIZE - 1, 31):
        c.ellipse(x, y, 2, 1, "s", ink="d")
    # The mouth, left: the night yard outside, snow drifting in.
    c.ellipse(16, 46, 18, 30, "n", ink="#")
    for x, y in scatter(8, 2, 18, 30, 50, 12):
        c.put(x, y, "w")
    c.rect(0, 56, 33, 77, "w")
    c.ellipse(14, 80, 22, 6, "w", ink="s")
    pine(c, 12, 64, 22)
    # Stalactites along the ceiling, dripping.
    for x, h in ((40, 10), (50, 6), (62, 14), (72, 8), (84, 11), (96, 7), (106, 9)):
        for j in range(h):
            half = (h - j) // 3
            c.hline(x - half, x + half, j, "g")
        c.put(x, h, "#")
        c.put(x, h + 4, "c")
        c.put(x, h + 9, "c")
    c.ellipse(62, 98, 9, 2, "c", ink="b")  # a drip puddle
    # A dark recess, right, and two glowing eyes in it.
    c.ellipse(104, 54, 14, 20, "p", ink="#")
    c.ellipse(104, 54, 10, 15, "#", ink="#")
    for x in (99, 107):
        c.rect(x, 50, x + 2, 51, "y")
        c.put(x + 1, 50, "w")
    # Moonlight through the mouth; dark deeper in; snowy paw prints walking in.
    glow(c, 20, 60, 34, "s", "gd")
    dusk(c, 20, 60, 50, "#", "dgp")
    for x, y in ((36, 90), (44, 94), (52, 90), (60, 95), (68, 91)):
        paw(c, x, y, "w")
    return c


# The Living Room tree, 40 x 52 in scene_art.KEY characters ('.' = wall shows
# through). It was a sprite in home_view; now it's part of the room's backdrop.
TREE = (
        "....................#...................",
        "...................#y#..................",
        "................####y####...............",
        "................#yyyyyyy#...............",
        ".................#yyyyy#................",
        "..................#yyy#.................",
        ".................#yy#yy#................",
        ".................##lll##................",
        ".................#llll#.................",
        "................#llllGl#................",
        "................#lllllG#................",
        "...............#lllllGGG#...............",
        "...............#llwrllGG#...............",
        "..............#lllrrllGGG#..............",
        ".............#llllGGGGlGGG#.............",
        ".............#llllGGGGGGGG#.............",
        "............#llllGGGGGGGGGG#............",
        "............#llOyGGGGGwbGGG#............",
        "...........#llllGyOGGGbbGGGG#...........",
        "...........#lllGGGGyyGGGGGGG#...........",
        "..........#lllGGGGGGGOyGGGGGG#..........",
        "...........###GGGGGGGGGyOG###...........",
        "............#GGGGGGGGGGGGGG#............",
        "...........#llllllllllGGGGGG#...........",
        "...........#llwrlllllGlGGGGG#...........",
        "..........#lllrrllGGGGGGGGGGG#..........",
        ".........#llllllllGGGGGGwcGGGG#.........",
        "........#llllllllGGGGGGGccGGGGG#........",
        "........#lllllllGGGGGGGGGGGGGGG#........",
        ".......#llllOylGGGGGGGGGGGGGGGGG#.......",
        "......#lllllllyOGGGGGGGGGGGGGGGGG#......",
        "......#llllllGGGyyGwbGGGGGGGGGGGG#......",
        ".....#llllllGGGGGGObbGGGGGGwyGGGGG#.....",
        "......#####GGGGGGGGGGOyGGGGyy#####......",
        "..........wrGGGGGGGGGGGyOGGGG#..........",
        ".........#rrllllllllllGGGyyGGG#.........",
        "........#llllllllllllGGGGGGOyGG#........",
        ".......#lllllllllllllwrGGGGGGGGG#.......",
        "......#llllllllllllllrrGGGGGyOyyO#......",
        ".....#lllllllllllllllyyOyyOyGGGGGG#.....",
        "....#lllllllyyOyyOyyOlGGGGGGGGGGGGG#....",
        "...#llllOyyOlwcllllllGGGGGGGGGGGGGGG#...",
        "...#lllllllllcclllllllGGGGGGwbGGGGGG#...",
        "..#lllllllllllllllllllwyGGGGbbGGGGGGG#..",
        ".#lllllllllllllllllllGyyGGGGGGGGGGGGGG#.",
        "#lllllllllllllllllllllGGGGGGGGGGGGGGGGG#",
        ".################oooopp################.",
        "................#oooopp#................",
        "................#oooopp#................",
        "................#oooopp#................",
        "................#oooopp#................",
        ".................######.................",
)

TREE_AT = (40, 31)  # art px; screen (80, 62) at 2x, where the presents expect it


def living_room():
    """Home: the tree, fireplace with stockings,
    a snowy window, cookies and milk for Santa. The presents are not here: they
    change with the game, so home_view draws them on the tree skirt."""
    c = Canvas("r")
    for x in range(5, SIZE, 10):  # damask stripes
        c.vline(x, 0, FLOOR_Y, "p")
    for x, y in scatter(14, 0, 2, SIZE - 1, 70, 29):
        c.put(x, y, "O")
    baseboard(c, color="w")
    planks(c, FLOOR_Y + 3, base="o", seam="p")
    c.ellipse(60, 92, 44, 12, "w", ink="s")  # tree skirt, under the presents
    for x in range(20, 101, 8):
        c.put(x, 92 + (x % 16 > 7), "c")
    # Garland swags along the top of the wall.
    for x0 in range(0, SIZE, 20):
        pts = wavy_line(c, x0, x0 + 20, 3, 5)
        for x, y in pts[::4]:
            c.put(x, y + 1, "G")
        c.put(x0, 3, "r")

    # Fireplace, left: stone surround, the fire, stockings off the mantel.
    c.box(2, 38, 36, 80, "s")
    for i, y in enumerate(range(42, 80, 5)):
        c.hline(3, 35, y, "g")
        for x in range(3 + (i % 2) * 4, 35, 8):
            c.vline(x, y, y + 4, "g")
    c.box(8, 54, 30, 80, "#")
    c.ellipse(19, 74, 8, 4, "r", ink="#")  # the fire
    c.ellipse(19, 72, 5, 4, "O", ink="r")
    c.ellipse(19, 72, 2, 2, "y", ink="O")
    c.rect(11, 77, 27, 79, "o")  # logs
    c.box(0, 34, 38, 38, "o")  # mantel
    for x, col in ((6, "r"), (16, "G"), (26, "b")):
        stocking(c, x, 39, col)
    c.ellipse(10, 31, 3, 2, "G")  # holly and a candle on the mantel
    c.put(9, 30, "r")
    c.put(11, 31, "r")
    candle(c, 28, 33, h=5, color="w")

    # Window, right, snow falling; cookies and milk on a little table below.
    night_window(c, 84, 22, 110, 48)
    c.rect(81, 20, 113, 21, "o")
    c.rect(82, 22, 85, 52, "G")  # green curtains
    c.rect(109, 22, 112, 52, "G")
    c.box(86, 64, 112, 67, "O")
    c.vline(89, 68, 80, "o")
    c.vline(109, 68, 80, "o")
    c.ellipse(94, 62, 6, 1, "w")  # plate of cookies
    for x in (91, 94, 97):
        c.ellipse(x, 60, 1, 1, "O", ink="o")
    c.box(104, 54, 109, 63, "w", ink="s")  # glass of milk
    c.hline(105, 108, 56, "s")

    # The tree last, so it stands in front of everything.
    tx, ty = TREE_AT
    c.sprite(tx, ty, TREE)
    # The fire lights the room.
    glow(c, 19, 70, 30, "O", "rpo")
    return c


ROOMS = {
    "Living Room": living_room,
    "Kitchen": kitchen,
    "Dining Room": dining_room,
    "Sun Porch": sun_porch,
    "Odd Corner": odd_corner,
    "Sewing Nook": sewing_nook,
    "Basement": basement,
    "Hallway": hallway,
    "Laundry Room": laundry_room,
    "Entryway": entryway,
    "Bedroom": bedroom,
    "Kids' Bedroom": kids_bedroom,
    "Garage": garage,
    "Attic": attic,
    "Yard": yard,
    "Front Porch": front_porch,
    "Snow Fort": snow_fort,
    "Front Walk": front_walk,
    "Back Door": back_door,
    "Cellar Door": cellar_door,
    "Roof": roof,
    "Pond": pond,
    "Tree House": tree_house,
    "Cave": cave,
}


def _palette_bytes():
    pal = []
    for rgb in backdrop.COLORS:
        pal += [(rgb >> 16) & 0xFF, (rgb >> 8) & 0xFF, rgb & 0xFF]
    return pal + [0] * (768 - len(pal))


def to_image(canvas):
    from PIL import Image

    img = Image.new("P", (SIZE, SIZE))
    img.putpalette(_palette_bytes())
    img.putdata([v - 1 for row in canvas.px for v in row])
    return img


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--png", help="also write 4x round previews here")
    ap.add_argument("--only", help="build just this room")
    args = ap.parse_args()
    out_dir = os.path.join(GAME, "art", "rooms")
    os.makedirs(out_dir, exist_ok=True)
    for room, draw in ROOMS.items():
        if args.only and room != args.only:
            continue
        img = to_image(draw())
        path = os.path.join(out_dir, backdrop.file_name(room))
        img.save(path)
        print(path, os.path.getsize(path), "bytes")
        if args.png:
            from PIL import Image, ImageDraw

            os.makedirs(args.png, exist_ok=True)
            big = img.convert("RGB").resize((SIZE * 4, SIZE * 4), Image.NEAREST)
            mask = Image.new("L", big.size, 0)
            ImageDraw.Draw(mask).ellipse((0, 0, big.size[0] - 1, big.size[1] - 1), fill=255)
            round_img = Image.new("RGB", big.size, (40, 40, 40))
            round_img.paste(big, mask=mask)
            png = os.path.join(args.png, backdrop.file_name(room)[:-4] + ".png")
            round_img.save(png)
            print(png)


if __name__ == "__main__":
    main()
