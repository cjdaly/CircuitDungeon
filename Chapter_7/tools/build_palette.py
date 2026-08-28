#!/usr/bin/env python3
"""Chapter 7 master palette - resolves bead cd-e17.3.

One shared indexed palette for every Ch7 art sheet.

  * index 0 is reserved transparent, authored as 0xFF00FF magenta
  * indices 1..15 are the CORE ramps - frozen identity & order.  Hand-authored
    sprites pixel against these slot numbers, so we never renumber or delete
    0..15.  RGB values may still be nudged.
  * indices 16..39 are EXTENDED ramps - append-only while art is in flight.
  * capacity is 64 (indices 40..63 are unallocated, for the polish pass:
    venom, frost, corpse-grey, crystal, lava, cloth dyes...).

Everything is organised as ramps: one material, dark -> highlight.  Coherence
comes from the ramp structure, not from a low colour count.  `off_white`
doubles as the shared brightest-highlight step for most ramps.

The palette is hand-curated for a muted dungeon look, then validated against
the CC0 reference sets: for each colour the script reports the nearest colour
actually present in Project Utumno + 0x72 DungeonTileset v4.

Outputs (desktop-only, Pillow):
    Chapter_7/game/tiles/palette.json   names / rgb / ramp / core flag / capacity
    Chapter_7/game/tiles/palette.py     PAL tuple + IDX name->index map
    Chapter_7/doc/preview/palette.png   swatch sheet, one ramp per row

Run from repo root:  python3 Chapter_7/tools/build_palette.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parents[2]
SRC = REPO / "sourceArt"
TILES = REPO / "Chapter_7" / "game" / "tiles"
PREVIEW = REPO / "Chapter_7" / "doc" / "preview"

UTUMNO = SRC / "DungeonCrawl" / "ProjectUtumno_full.png"
V4 = SRC / "DungeonTileset" / "0x72_16x16DungeonTileset.v4.png"

CAPACITY = 64
CORE_SIZE = 16

# --- the palette, grouped by ramp ------------------------------------------
# (ramp_name, [(colour_name, (r, g, b)), ...])
# The first two groups (indices 0..15) are the frozen core.
RAMPS = [
    ("reserved", [
        ("transparent", (0xFF, 0x00, 0xFF)),
    ]),
    ("neutral", [                       # 1..5   outline + grey ramp
        ("ink_black",     (0x14, 0x0C, 0x1C)),
        ("neutral_dark",  (0x2B, 0x27, 0x33)),
        ("neutral_mid",   (0x4A, 0x46, 0x58)),
        ("neutral_light", (0x8A, 0x86, 0x98)),
        ("off_white",     (0xE8, 0xE0, 0xD0)),
    ]),
    ("stone", [                         # 6..8   cold wet wall-tops
        ("stone_dark",  (0x33, 0x40, 0x4C)),
        ("stone_mid",   (0x5C, 0x71, 0x82)),
        ("stone_light", (0x8A, 0xA0, 0xB0)),
    ]),
    ("dirt", [                          # 9..12  floor / earth
        ("dirt_darkest", (0x2A, 0x1E, 0x16)),
        ("dirt_dark",    (0x3E, 0x2E, 0x20)),
        ("dirt_mid",     (0x5A, 0x43, 0x30)),
        ("dirt_light",   (0x8A, 0x6B, 0x4A)),
    ]),
    ("wood", [                          # 13..15
        ("wood_dark",  (0x45, 0x30, 0x1F)),
        ("wood_mid",   (0x7A, 0x52, 0x30)),
        ("wood_light", (0xA8, 0x7A, 0x45)),
    ]),
    # ---- end of frozen core (indices 0..15) ----
    ("moss", [                          # 16..19  vegetation / damp
        ("moss_darkest", (0x1E, 0x2A, 0x16)),
        ("moss_dark",    (0x2C, 0x3A, 0x1E)),
        ("moss_mid",     (0x4F, 0x6B, 0x2C)),
        ("moss_light",   (0x86, 0xA6, 0x3E)),
    ]),
    ("blood", [                         # 20..23  red / flesh wounds
        ("blood_darkest", (0x3A, 0x14, 0x14)),
        ("blood_dark",    (0x5E, 0x1D, 0x1D)),
        ("blood",         (0xA8, 0x32, 0x2E)),
        ("blood_bright",  (0xD8, 0x50, 0x3A)),
    ]),
    ("gold", [                          # 24..27  brass / coin / treasure
        ("bronze_dark", (0x4A, 0x32, 0x12)),
        ("bronze",      (0x7A, 0x53, 0x20)),
        ("gold",        (0xD8, 0xA9, 0x3C)),
        ("gold_light",  (0xF0, 0xD6, 0x7A)),
    ]),
    ("water", [                         # 28..31  water / mana / ice
        ("water_darkest", (0x16, 0x28, 0x3F)),
        ("deep_water",    (0x1E, 0x3A, 0x5C)),
        ("water",         (0x3E, 0x77, 0xB0)),
        ("water_light",   (0x8F, 0xC8, 0xDE)),
    ]),
    ("arcane", [                        # 32..34  purple magic
        ("arcane_dark",   (0x2A, 0x1E, 0x42)),
        ("arcane",        (0x5E, 0x3A, 0x94)),
        ("arcane_bright", (0x9B, 0x6F, 0xD0)),
    ]),
    ("fire", [                          # 35..37  flame / torch / lava glow
        ("fire_dark",   (0xA8, 0x45, 0x1C)),
        ("fire",        (0xE8, 0x80, 0x2C)),
        ("fire_bright", (0xF4, 0xC2, 0x4A)),
    ]),
    ("flesh", [                         # 38..39  skin
        ("flesh_shadow", (0x9A, 0x6B, 0x4E)),
        ("flesh",        (0xC8, 0x96, 0x6E)),
    ]),
]


def flatten(ramps):
    out = []
    for ramp_name, entries in ramps:
        for cname, rgb in entries:
            out.append((cname, tuple(rgb), ramp_name, len(out) < CORE_SIZE))
    return out


def _ref_colors():
    cols = []
    for path, box in ((UTUMNO, (0, 128, 2048, 2080)), (V4, None)):
        arr = np.array(Image.open(path).convert("RGBA"))
        if box:
            x0, y0, x1, y1 = box
            arr = arr[y0:y1, x0:x1]
        flat = arr.reshape(-1, 4)
        op = flat[flat[:, 3] >= 200][:, :3].astype(np.int16)
        q = (op >> 2) << 2
        cols.append(np.unique(q, axis=0))
    return np.unique(np.concatenate(cols), axis=0)


def validate(full):
    ref = _ref_colors()
    rows = []
    for name, c, ramp, core in full:
        if name == "transparent":
            continue
        d = np.sqrt(((ref - np.array(c)) ** 2).sum(axis=1))
        j = int(d.argmin())
        rows.append((name, c, tuple(int(v) for v in ref[j]), float(d[j])))
    return rows


def write_outputs(full):
    TILES.mkdir(parents=True, exist_ok=True)
    PREVIEW.mkdir(parents=True, exist_ok=True)

    (TILES / "palette.json").write_text(json.dumps({
        "capacity": CAPACITY,
        "core_size": CORE_SIZE,
        "count": len(full),
        "names": [n for n, _, _, _ in full],
        "rgb": [list(c) for _, c, _, _ in full],
        "ramps": [r for _, _, r, _ in full],
        "core": [bool(k) for _, _, _, k in full],
    }, indent=2) + "\n")

    lines = [
        '"""Ch7 master palette - generated by tools/build_palette.py (cd-e17.3).',
        "",
        "Do not edit by hand.  Edit RAMPS in build_palette.py and re-run.",
        f"Capacity {CAPACITY}; indices 0..{CORE_SIZE - 1} are frozen core.",
        '"""',
        "",
        f"CAPACITY = {CAPACITY}",
        f"CORE_SIZE = {CORE_SIZE}",
        "",
        "# index 0 = transparent, authored as 0xFF00FF magenta",
        "PAL = (",
    ]
    for n, c, r, core in full:
        tag = "core" if core else r
        lines.append(f"    ({c[0]:3d}, {c[1]:3d}, {c[2]:3d}),  # {len_prefix(full, n)} {n} [{tag}]")
    lines += [")", "", "IDX = {"]
    for i, (n, _, _, _) in enumerate(full):
        lines.append(f"    {n!r}: {i},")
    lines += ["}", ""]
    (TILES / "palette.py").write_text("\n".join(lines))

    render_swatch_sheet(full, PREVIEW / "palette.png")


def len_prefix(full, name):
    for i, (n, _, _, _) in enumerate(full):
        if n == name:
            return f"{i:2d}"
    return "??"


def render_swatch_sheet(full, path, scale=60):
    # group consecutively by ramp
    groups = []
    for name, c, ramp, core in full:
        if not groups or groups[-1][0] != ramp:
            groups.append((ramp, []))
        groups[-1][1].append((name, c, core))

    pad = 20
    label_w = 90
    col_w = scale + 34
    row_h = scale + 46
    max_cols = max(len(g[1]) for g in groups)
    W = max(pad * 2 + label_w + max_cols * col_w, 660)
    H = pad * 2 + 34 + len(groups) * row_h
    img = Image.new("RGB", (W, H), (26, 26, 30))
    d = ImageDraw.Draw(img)
    try:
        f = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 11)
        fb = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 14)
    except OSError:
        f = fb = ImageFont.load_default()

    d.text((pad, 6),
           f"Ch7 master palette  -  {len(full)} of {CAPACITY} slots, "
           f"core 0-{CORE_SIZE - 1} frozen, index 0 transparent  (cd-e17.3)",
           fill=(230, 230, 230), font=fb)

    y = pad + 34
    for ramp, entries in groups:
        d.text((pad, y + scale // 2 - 6), ramp, fill=(180, 180, 190), font=fb)
        x = pad + label_w
        for name, c, core in entries:
            if name == "transparent":
                for yy in range(0, scale, 8):
                    for xx in range(0, scale, 8):
                        on = ((xx // 8) + (yy // 8)) % 2 == 0
                        d.rectangle([x + xx, y + yy, x + xx + 8, y + yy + 8],
                                    fill=(96, 96, 100) if on else (56, 56, 60))
            else:
                d.rectangle([x, y, x + scale, y + scale], fill=tuple(c))
            border = (240, 210, 120) if core else (12, 12, 14)
            d.rectangle([x, y, x + scale, y + scale], outline=border,
                        width=2 if core else 1)
            idx = len_prefix(full, name)
            d.text((x, y + scale + 3), f"{idx} {name}", fill=(205, 205, 205), font=f)
            d.text((x, y + scale + 16), "#%02X%02X%02X" % tuple(c),
                   fill=(145, 145, 145), font=f)
            x += col_w
        y += row_h

    d.text((pad, H - 18), "gold border = frozen core slot",
           fill=(200, 175, 110), font=f)
    img.save(path)


if __name__ == "__main__":
    full = flatten(RAMPS)
    assert len(full) <= CAPACITY, f"{len(full)} > capacity {CAPACITY}"
    assert [k for *_, k in full][:CORE_SIZE] == [True] * CORE_SIZE
    assert not any(k for *_, k in full[CORE_SIZE:])
    write_outputs(full)
    print(f"wrote {TILES / 'palette.json'}  ({len(full)}/{CAPACITY} slots)")
    print(f"wrote {TILES / 'palette.py'}")
    print(f"wrote {PREVIEW / 'palette.png'}")
    print()
    print("validation vs reference sets (nearest source colour / RGB distance):")
    worst = 0.0
    for name, c, near, dist in validate(full):
        worst = max(worst, dist)
        flag = "  <-- drift" if dist > 45 else ""
        print(f"  {name:14s} #{c[0]:02X}{c[1]:02X}{c[2]:02X}  "
              f"src #{near[0]:02X}{near[1]:02X}{near[2]:02X}  d={dist:5.1f}{flag}")
    print(f"\nworst drift: d={worst:.1f}")
