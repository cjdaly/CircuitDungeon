#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Build each art set's sprite sheets: objects.bmp and critters.bmp -- cd-342.35, cd-342.38.

    /usr/bin/python3 Chapter_9/tools/build_sprites.py [--png DIR]

Both sheets are 32x32 tiles, 8-bit indexed, index 0 see-through, the rest the
DB16 colours in scene_art.COLORS order; the game reads them from flash
(scene_view.py) and shows them at 2x, the room art's pixel size.

objects.bmp  one tile per scene_art.NAMES entry, in that order; indices 17-19
             are a present's paper/shade/ribbon, swapped per critter.
critters.bmp critter_candidates' layout: candidate i is tiles 2i and 2i+1.

The `drawn` set gets today's hand-drawn art: tools/scene_art_src.py's 16x16
objects doubled to 32x32 (the ball of yarn drawn new at 32x32 here), and the
DawnLike critters (CC-BY; credited in the chapter README) from
game/art/critters_nn.bmp. Any other set with a sprites/ folder gets drawn's
sheets with its own sprites put in: sprites/<object>.png (spaces as
underscores) and sprites/<sprite id>.png + <sprite id>_f1.png (frames 0 and
1), RGBA 32x32, snapped to DB16. EDITS below are hand touches applied on top
of a set's sprites, recorded here so a rebuild gives the same result. A set
without sprites/ inherits drawn's sheets (art_set.py compose).
"""
import argparse
import math
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
CH9 = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(CH9, "game"))
sys.path.insert(0, HERE)
import art_set  # noqa: E402
import critter_candidates  # noqa: E402
import scene_art  # noqa: E402
import scene_art_src  # noqa: E402

TILE = scene_art.TILE  # 32
K = scene_art.KEY
OBJECTS = scene_art.OBJECTS
CRITTERS = scene_art.CRITTERS
SEE_THROUGH = (255, 0, 255)  # index 0's colour in the files, so it's obvious on a desktop


def _palette():
    pal = list(SEE_THROUGH)
    for rgb in scene_art.COLORS[1:]:
        pal += [(rgb >> 16) & 255, (rgb >> 8) & 255, rgb & 255]
    return pal + [0] * (768 - len(pal))


DB16 = [((c >> 16) & 255, (c >> 8) & 255, c & 255) for c in scene_art.COLORS[1:17]]


def snap(rgba):
    """An RGBA image -> index rows: alpha < 128 is 0, else the nearest DB16 index (1-16)."""
    w, h = rgba.size
    px = rgba.convert("RGBA").load()
    rows = []
    for y in range(h):
        row = []
        for x in range(w):
            r, g, b, a = px[x, y]
            if a < 128:
                row.append(0)
            else:
                d = [(r - cr) ** 2 + (g - cg) ** 2 + (b - cb) ** 2 for cr, cg, cb in DB16]
                row.append(1 + d.index(min(d)))
        rows.append(row)
    return rows


class Tile:
    """A 32x32 tile of palette indices, drawn on with scene_art.KEY characters."""

    def __init__(self, rows=None):
        self.px = rows or [[0] * TILE for _ in range(TILE)]

    def put(self, x, y, ch):
        if 0 <= x < TILE and 0 <= y < TILE:
            self.px[y][x] = K[ch]

    def get(self, x, y):
        return self.px[y][x] if 0 <= x < TILE and 0 <= y < TILE else 0

    def outline(self):
        ink = [(x, y) for y in range(TILE) for x in range(TILE)
               if not self.px[y][x] and any(self.get(x + dx, y + dy) not in (0, K["#"])
                                            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
        for x, y in ink:
            self.put(x, y, "#")


def doubled(rows16):
    """16x16 character rows -> a 32x32 tile, each pixel doubled (the look it has today)."""
    t = Tile()
    for y, row in enumerate(rows16):
        for x, ch in enumerate(row):
            if ch != ".":
                for dy in (0, 1):
                    for dx in (0, 1):
                        t.put(2 * x + dx, 2 * y + dy, ch)
    return t


def yarn():
    """The ball of yarn, drawn at 32x32: wound strands, a shine, a loose end, needles."""
    t = Tile()
    cx, cy, r = 14, 17, 11
    for y in range(TILE):
        for x in range(TILE):
            d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
            if d <= r:
                lit = (x - cx) + (y - cy) < 4  # upper left lit, lower right in shade
                t.put(x, y, "r" if lit else "p")
                if not lit and (x + y) % 2 == 0 and d < r - 1:
                    t.put(x, y, "r")  # comic halftone into the shade
    for tilt, ry in ((0.5, 4), (0.5, 8), (-0.7, 6), (-0.7, 10), (1.6, 7)):
        ct, st = math.cos(tilt), math.sin(tilt)
        for i in range(160):  # strands wound round the ball
            a = 2 * math.pi * i / 160
            ex, ey = (r - 1.5) * math.cos(a), ry * math.sin(a)
            x, y = cx + ex * ct - ey * st, cy + ex * st + ey * ct
            if math.hypot(x - cx, y - cy) < r - 1 and math.sin(a) > -0.2:
                t.put(int(x), int(y), "k" if t.get(int(x), int(y)) == K["r"] else "r")
    for x, y in ((8, 11), (9, 10), (10, 10), (8, 12), (11, 9)):  # shine
        t.put(x, y, "w")
    for i in range(26):  # the loose end, curling away to the right
        a = i / 25
        x = cx + 8 + a * 10
        y = cy + 6 + 3 * math.sin(a * 7) - a * 2
        t.put(int(x), int(y), "r")
    for x0, y0, x1, y1 in ((20, 2, 13, 14), (26, 5, 16, 13)):  # knitting needles
        n = max(abs(x1 - x0), abs(y1 - y0))
        for i in range(n + 1):
            t.put(round(x0 + (x1 - x0) * i / n), round(y0 + (y1 - y0) * i / n), "s")
        t.put(x0, y0, "O")
        t.put(x0 + (1 if x1 < x0 else -1), y0, "O")
    t.outline()
    return t


def chirpy_bow(t):
    """A red Christmas bow at Chirpy's neck (the model left it off)."""
    for x, y in ((13, 16), (17, 16), (13, 17), (14, 17), (16, 17), (17, 17), (13, 18), (17, 18),
                 (14, 19), (16, 19)):
        t.put(x, y, "r")
    t.put(15, 17, "p")
    for x, y in ((12, 16), (12, 17), (12, 18), (18, 16), (18, 17), (18, 18), (13, 15), (17, 15)):
        t.put(x, y, "#")


EDITS = {  # (set, sprite file stem) -> hand touch
    ("sdxl-repaint", "cat_0_1"): chirpy_bow,
    ("sdxl-repaint", "cat_0_1_f1"): chirpy_bow,
}


def bob(t):
    """A second frame: everything above the feet 1px lower (a breath)."""
    rows = [i for i, row in enumerate(t.px) if any(row)]
    out = Tile([row[:] for row in t.px])
    if len(rows) < 6:
        return out
    top, feet = rows[0], rows[-1] - 3
    for y in range(feet, top, -1):
        out.px[y] = t.px[y - 1][:]
    out.px[top] = [0] * TILE
    return out


def drawn_objects():
    return [yarn() if name == "ball of yarn" else doubled(scene_art_src.ART[name])
            for name in scene_art.NAMES]


def drawn_critters():
    """critters_nn.bmp's tiles, re-indexed into this palette."""
    src = Image.open(os.path.join(CH9, "game", "art", "critters_nn.bmp"))
    old = src.getpalette()
    to_new = {0: 0}  # its colours are DB16 give or take a step: map to the nearest
    for i in range(1, 256):
        r, g, b = old[3 * i:3 * i + 3]
        d = [(r - cr) ** 2 + (g - cg) ** 2 + (b - cb) ** 2 for cr, cg, cb in DB16]
        to_new[i] = 1 + d.index(min(d))
    data = list(src.getdata())
    w = src.size[0]
    tiles = []
    n = 2 * len(critter_candidates.CANDIDATES)
    for f in range(n):
        tx = (f % critter_candidates.TILES_WIDE) * TILE
        ty = (f // critter_candidates.TILES_WIDE) * TILE
        tiles.append(Tile([[to_new.get(data[(ty + y) * w + tx + x], 0) for x in range(TILE)]
                           for y in range(TILE)]))
    return tiles


def sheet_image(tiles, wide):
    rows = (len(tiles) + wide - 1) // wide
    img = Image.new("P", (wide * TILE, rows * TILE))
    img.putpalette(_palette())
    flat = [0] * (wide * TILE * rows * TILE)
    for i, t in enumerate(tiles):
        tx, ty = (i % wide) * TILE, (i // wide) * TILE
        for y in range(TILE):
            for x in range(TILE):
                flat[(ty + y) * wide * TILE + tx + x] = t.px[y][x]
    img.putdata(flat)
    return img


def load_sprite(path):
    return Tile(snap(Image.open(path).convert("RGBA").resize((TILE, TILE), Image.NEAREST)))


def build(name, objects, critters):
    """Put a set's own sprites into copies of drawn's tiles; write its two sheets."""
    sprites = os.path.join(art_set.SETS_DIR, name, "sprites")
    if name != "drawn":
        if not os.path.isdir(sprites):
            return None
        objects = [Tile([r[:] for r in t.px]) for t in objects]
        critters = [Tile([r[:] for r in t.px]) for t in critters]
        ids = [c[0] for c in critter_candidates.CANDIDATES]
        for f in sorted(os.listdir(sprites)):
            if not f.endswith(".png"):
                continue
            stem = f[:-4]
            tile = load_sprite(os.path.join(sprites, f))
            edit = EDITS.get((name, stem))
            if edit:
                edit(tile)
            obj = stem.replace("_", " ")
            base = stem[:-3] if stem.endswith("_f1") else stem
            if obj in scene_art.NAMES:
                objects[scene_art.NAMES.index(obj)] = tile
            elif base in ids:
                frame = 2 * ids.index(base) + (1 if stem.endswith("_f1") else 0)
                critters[frame] = tile
                if not stem.endswith("_f1") and not os.path.exists(
                        os.path.join(sprites, base + "_f1.png")):
                    critters[frame + 1] = bob(tile)
            else:
                sys.exit("{}: {} is neither an object nor a critter sprite id".format(name, f))
    out = art_set.rooms_dir(name)
    os.makedirs(out, exist_ok=True)
    sheet_image(objects, len(objects)).save(os.path.join(out, OBJECTS))
    sheet_image(critters, critter_candidates.TILES_WIDE).save(os.path.join(out, CRITTERS))
    return objects, critters


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--png", help="also write 4x previews of each set's sheets here")
    args = ap.parse_args()
    objects, critters = drawn_objects(), drawn_critters()
    for name in art_set.names():
        built = build(name, objects, critters)
        if built is None:
            continue
        print("{}: {} and {}".format(name, OBJECTS, CRITTERS))
        if args.png:
            os.makedirs(args.png, exist_ok=True)
            for fname in (OBJECTS, CRITTERS):
                img = Image.open(os.path.join(art_set.rooms_dir(name), fname)).convert("RGB")
                img.resize((img.size[0] * 4, img.size[1] * 4), Image.NEAREST).save(
                    os.path.join(args.png, "{}_{}.png".format(name, fname[:-4])))


if __name__ == "__main__":
    main()
