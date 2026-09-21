#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Build the animated critter-candidate sheets for the on-device look-test
(cd-342.3).  Desktop only -- needs Pillow + numpy (`/usr/bin/python3` here).

    /usr/bin/python3 Chapter_9/tools/build_critter_candidates.py

Reads 16x16, 2-frame animated creatures from DawnLike (sourceArt/DawnLike/
Characters/, CC-BY 4.0 -- see Chapter_9/README.md credits; frame 0 lives in
`<Sheet>0.png`, frame 1 in `<Sheet>1.png`) and expands each to 32x32, since
Ch9 draws critters/heroes at 32x32 over 16x16 scenery. Two expansion methods
are built so the device test can compare them:

  nn   nearest-neighbor pixel doubling (chunky, faithful to the source)
  epx  Scale2x/EPX edge smoothing (rounder diagonals; never invents a colour,
       so the 16-colour DawnBringer palette is preserved)

Outputs:
  game/art/critters_nn.bmp, critters_epx.bmp   8-bit indexed, index 0 =
      transparent, candidates packed row-major, 2 consecutive 32x32 tiles
      (frame 0, frame 1) each -> candidate i is tile frames 2i and 2i+1
  game/critter_candidates.py                   GENERATED id/group/source list
      the on-device demo (critter_demo.py) reads
  doc/critter-candidates-{nn,epx}.png          labeled desktop previews

Edit CANDIDATES below to add/drop entries, then re-run.
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent.parent          # Chapter_9/
SRC = HERE.parent / "sourceArt" / "DawnLike" / "Characters"

TILE_SRC = 16
TILE = 32
SHEET_TILES_WIDE = 12          # 6 candidates per row of the output sheet

# (group, source sheet, col, row).  Groups are just for browsing on the
# device; the id is derived from the source cell, so it's stable and lets
# anyone find the original.  Chris re-labels the winners later.
CANDIDATES = [
    ("dog", "Dog", 0, 0), ("dog", "Dog", 3, 0), ("dog", "Dog", 4, 0), ("dog", "Dog", 0, 2),
    ("cat", "Cat", 0, 0), ("cat", "Cat", 0, 1), ("cat", "Cat", 0, 2),
    ("cat", "Cat", 0, 3), ("cat", "Cat", 2, 0),
    ("rodent", "Rodent", 0, 0), ("rodent", "Rodent", 1, 0), ("rodent", "Rodent", 4, 0),
    ("bunny", "Misc", 0, 2), ("bunny", "Misc", 1, 2), ("bunny", "Misc", 2, 2),
    ("bunny", "Misc", 3, 2),
    ("bird", "Avian", 1, 3), ("bird", "Avian", 3, 3), ("bird", "Avian", 1, 4),
    ("bird", "Avian", 0, 3), ("bird", "Avian", 2, 3),
    ("owl", "Avian", 2, 10), ("owl", "Avian", 3, 10), ("owl", "Avian", 0, 10),
    ("owl", "Avian", 1, 10),
    ("bat", "Avian", 0, 11), ("bat", "Avian", 2, 11), ("bat", "Avian", 3, 11),
    ("reindeer", "Quadraped", 0, 8), ("reindeer", "Quadraped", 1, 8),
    ("sheep", "Quadraped", 0, 3),
    ("robot", "Elemental", 0, 1), ("robot", "Elemental", 1, 1),
    ("robot", "Elemental", 3, 1), ("robot", "Elemental", 4, 0),
    ("robot", "Misc", 2, 5), ("robot", "Misc", 3, 5),
    ("snow", "Elemental", 4, 1), ("snow", "Elemental", 0, 7),
]


def cand_id(sheet, col, row):
    return "{}_{}_{}".format(sheet.lower(), col, row)


# --------------------------------------------------------------------------- #
# loading + palette
# --------------------------------------------------------------------------- #
_sheet_cache = {}


def load_sheet(name, frame):
    key = (name, frame)
    if key not in _sheet_cache:
        _sheet_cache[key] = Image.open(SRC / "{}{}.png".format(name, frame)).convert("RGBA")
    return _sheet_cache[key]


def cell(name, frame, col, row):
    box = (col * TILE_SRC, row * TILE_SRC, (col + 1) * TILE_SRC, (row + 1) * TILE_SRC)
    return load_sheet(name, frame).crop(box)


def build_palette():
    """Index 0 = transparent; then every opaque colour used by any candidate."""
    colors = set()
    for _group, sheet, col, row in CANDIDATES:
        for frame in (0, 1):
            for r, g, b, a in cell(sheet, frame, col, row).getdata():
                if a:
                    colors.add((r, g, b))
    ordered = sorted(colors)
    if len(ordered) > 255:
        raise SystemExit("too many colours ({}) for an 8-bit palette".format(len(ordered)))
    return [(255, 0, 255)] + ordered  # index 0 is the (unused) transparent key


def to_indices(img, lookup):
    out = np.zeros((img.height, img.width), dtype=np.uint8)
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = img.getpixel((x, y))
            out[y, x] = lookup[(r, g, b)] if a else 0
    return out


# --------------------------------------------------------------------------- #
# 16 -> 32 expansion
# --------------------------------------------------------------------------- #
def scale_nn(a):
    return np.repeat(np.repeat(a, 2, axis=0), 2, axis=1)


def scale_epx(a):
    """Scale2x/EPX. Out-of-bounds counts as transparent (index 0)."""
    p = np.pad(a, 1, constant_values=0)
    out = np.zeros((a.shape[0] * 2, a.shape[1] * 2), dtype=a.dtype)
    for y in range(a.shape[0]):
        for x in range(a.shape[1]):
            P = p[y + 1, x + 1]
            A, B, C, D = p[y, x + 1], p[y + 1, x + 2], p[y + 1, x], p[y + 2, x + 1]
            e0 = A if (C == A and C != D and A != B) else P
            e1 = B if (A == B and A != C and B != D) else P
            e2 = C if (D == C and D != B and C != A) else P
            e3 = D if (B == D and B != A and D != C) else P
            out[2 * y, 2 * x], out[2 * y, 2 * x + 1] = e0, e1
            out[2 * y + 1, 2 * x], out[2 * y + 1, 2 * x + 1] = e2, e3
    return out


METHODS = {"nn": scale_nn, "epx": scale_epx}


# --------------------------------------------------------------------------- #
# sheet + outputs
# --------------------------------------------------------------------------- #
def build_sheet(method, lookup):
    """(sheet index array, list of per-candidate [frame0, frame1] arrays)."""
    scale = METHODS[method]
    tiles, per_cand = [], []
    for _group, sheet, col, row in CANDIDATES:
        frames = [scale(to_indices(cell(sheet, f, col, row), lookup)) for f in (0, 1)]
        per_cand.append(frames)
        tiles.extend(frames)
    n_rows = -(-len(tiles) // SHEET_TILES_WIDE)
    arr = np.zeros((n_rows * TILE, SHEET_TILES_WIDE * TILE), dtype=np.uint8)
    for i, t in enumerate(tiles):
        ty, tx = divmod(i, SHEET_TILES_WIDE)
        arr[ty * TILE:(ty + 1) * TILE, tx * TILE:(tx + 1) * TILE] = t
    return arr, per_cand


def write_bmp(arr, palette, path):
    img = Image.fromarray(arr, mode="P")
    flat = []
    for r, g, b in palette:
        flat += [r, g, b]
    img.putpalette(flat + [0] * (768 - len(flat)))
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)  # 'P' -> 8-bit indexed BMP


def render_preview(per_cand, palette, path, zoom=2, per_row=4):
    """Both animation frames of every candidate at the real 32x32 size x zoom."""
    fw = TILE * zoom
    cell_w, cell_h = 2 * fw + 12, fw + 34
    rows = -(-len(CANDIDATES) // per_row)
    img = Image.new("RGB", (per_row * cell_w + 8, rows * cell_h + 8), (40, 44, 60))
    d = ImageDraw.Draw(img)
    lut = np.array(palette, dtype=np.uint8)
    for i, ((group, sheet, col, row), frames) in enumerate(zip(CANDIDATES, per_cand)):
        ry, rx = divmod(i, per_row)
        ox, oy = 8 + rx * cell_w, 8 + ry * cell_h
        d.text((ox, oy), "{:2d} {}".format(i + 1, group), fill=(255, 220, 120))
        d.text((ox, oy + 11), "{} {},{}".format(sheet, col, row), fill=(160, 170, 200))
        for fi, frame in enumerate(frames):
            rgb = lut[frame]
            mask = frame != 0
            tile = Image.fromarray(rgb, "RGB").resize((fw, fw), Image.NEAREST)
            m = Image.fromarray((mask * 255).astype(np.uint8)).resize((fw, fw), Image.NEAREST)
            img.paste(tile, (ox + fi * (fw + 4), oy + 26), m)
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)


def write_manifest(path):
    lines = [
        "# SPDX-License-Identifier: MIT",
        '"""GENERATED by tools/build_critter_candidates.py -- do not edit by hand.',
        "",
        "One entry per animated critter candidate, in sheet order: candidate i",
        "is tile frames 2*i and 2*i+1 of art/critters_<method>.bmp (32x32 tiles).",
        'Fields: (id, group, source).  id is the DawnLike sheet + column + row."""',
        "",
        "TILE = {}".format(TILE),
        "TILES_WIDE = {}".format(SHEET_TILES_WIDE),
        "CANDIDATES = (",
    ]
    for group, sheet, col, row in CANDIDATES:
        lines.append("    ({!r}, {!r}, {!r}),".format(
            cand_id(sheet, col, row), group, "{} {},{}".format(sheet, col, row)))
    lines.append(")")
    path.write_text("\n".join(lines) + "\n")


def main():
    palette = build_palette()
    lookup = {c: i for i, c in enumerate(palette) if i}
    print("palette: {} colours + transparent".format(len(palette) - 1))
    for method in METHODS:
        arr, per_cand = build_sheet(method, lookup)
        bmp = HERE / "game" / "art" / "critters_{}.bmp".format(method)
        write_bmp(arr, palette, bmp)
        render_preview(per_cand, palette, HERE / "doc" / "critter-candidates-{}.png".format(method))
        print("wrote {} ({}x{}), {} candidates".format(
            bmp.relative_to(HERE), arr.shape[1], arr.shape[0], len(per_cand)))
    write_manifest(HERE / "game" / "critter_candidates.py")
    print("wrote game/critter_candidates.py")


if __name__ == "__main__":
    main()
