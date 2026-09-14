"""Procedural terrain tiles (cd-e17.5).

Value-noise + a palette ramp for the base floor/wall/water/stairs set (six
tiles, indices 0-5). Two more things live in this sheet's first 16 slots for
fog-of-war (cd-oht.6): a solid "void" tile at index 6 (drawn for cells the
hero has never seen -- the dungeon reads as solid rock until FOV reveals
it), and a darkened copy of every base tile at index (base + 8) -- the
sheet's second row -- for cells the hero has seen before but can't
currently see (`world.is_explored` true, `is_visible` false). Index 7 is a
reserved/blank spacer so the dim row lands exactly on the sheet's next
8-wide row boundary.

Dim tiles are generated, not hand-drawn: build_palette.py's "fog_dim" ramp
already provides a darkened twin for every colour used here (e.g.
"dirt_dark" -> "dirt_dark_dim"), so each dim tile is just its base tile's
index grid remapped through that pairing -- same pattern, same shape, just
darker. Nudge a base tile's noise/shape and its dim twin follows for free.
"""
from __future__ import annotations

import numpy as np

from tilelib import TILE, Tile

SEED = 1

# Every colour name terrain's base tiles use, in the order build_palette.py
# paired them with a "<name>_dim" twin (its "fog_dim" ramp). Kept here too
# (not imported from build_palette.py, a desktop-only script this module
# doesn't otherwise depend on) since this is the "which pixels get dimmed"
# side of that pairing, a distinct concern from "what the dim colours are".
_DIMMABLE = (
    "dirt_darkest", "dirt_dark", "dirt_mid", "dirt_light",
    "stone_dark", "stone_mid", "stone_light",
    "moss_mid",
    "neutral_dark", "neutral_mid", "neutral_light", "ink_black",
    "water_darkest", "deep_water", "water", "water_light",
    "off_white",
)


def _value_noise(shape, cells, rng):
    """Cheap tileable value noise: random lattice + bilinear, wraps at edges."""
    gh, gw = cells
    lat = rng.random((gh + 1, gw + 1))
    lat[-1, :] = lat[0, :]
    lat[:, -1] = lat[:, 0]
    ys = np.linspace(0, gh, shape[0], endpoint=False)
    xs = np.linspace(0, gw, shape[1], endpoint=False)
    y0 = np.floor(ys).astype(int)
    x0 = np.floor(xs).astype(int)
    fy = (ys - y0)[:, None]
    fx = (xs - x0)[None, :]
    a = lat[y0][:, x0]
    b = lat[y0][:, x0 + 1]
    c = lat[y0 + 1][:, x0]
    d = lat[y0 + 1][:, x0 + 1]
    top = a * (1 - fx) + b * fx
    bot = c * (1 - fx) + d * fx
    return top * (1 - fy) + bot * fy


def _ramp(noise, indices):
    """Map [0,1) noise onto an ordered list of palette indices."""
    edges = np.linspace(0, 1, len(indices) + 1)[1:-1]
    buckets = np.digitize(noise, edges)
    lut = np.array(indices, np.uint8)
    return lut[buckets]


def _dim_lut(pal):
    """index i -> its fog-dim twin's index, identity for anything else."""
    lut = np.arange(pal.capacity, dtype=np.uint8)
    for name in _DIMMABLE:
        lut[pal.index(name)] = pal.index(f"{name}_dim")
    return lut


def build(pal) -> list[Tile]:
    rng = np.random.default_rng(SEED)
    P = pal.index
    base = []

    # dirt floor ------------------------------------------------------------
    n = _value_noise((TILE, TILE), (4, 4), rng)
    n = 0.5 * n + 0.5 * _value_noise((TILE, TILE), (8, 8), rng)
    floor = _ramp(n, [P("dirt_darkest"), P("dirt_dark"), P("dirt_mid"),
                      P("dirt_light")])
    base.append(Tile.from_indices("floor_dirt", floor))

    # mossy flagstone -----------------------------------------------------
    n = _value_noise((TILE, TILE), (2, 2), rng)
    flag = _ramp(n, [P("stone_dark"), P("stone_mid"), P("stone_light")])
    speck = _value_noise((TILE, TILE), (8, 8), rng) > 0.82
    flag[speck] = P("moss_mid")
    base.append(Tile.from_indices("floor_flagstone", flag))

    # wall top ----------------------------------------------------------
    n = _value_noise((TILE, TILE), (3, 3), rng)
    wall = _ramp(n, [P("neutral_dark"), P("neutral_mid"), P("neutral_light")])
    wall[0, :] = P("neutral_light")   # top-lit edge
    wall[-1, :] = P("ink_black")      # bottom shadow
    base.append(Tile.from_indices("wall_top", wall))

    # water ---------------------------------------------------------
    n = _value_noise((TILE, TILE), (2, 4), rng)
    water = _ramp(n, [P("water_darkest"), P("deep_water"), P("water"),
                      P("water_light")])
    base.append(Tile.from_indices("water", water))

    # stairs down (sketch) ----------------------------------------
    g = np.full((TILE, TILE), P("dirt_dark"), np.uint8)
    for i in range(5):
        y0 = 2 + i * 2
        shade = [P("neutral_dark"), P("neutral_mid"), P("stone_mid"),
                 P("stone_light"), P("off_white")][i]
        g[y0:y0 + 2, 2 + i:14] = shade
    base.append(Tile.from_indices("stairs_down", g))

    # stairs up (sketch) ----------------------------------------
    g = np.full((TILE, TILE), P("dirt_dark"), np.uint8)
    for i in range(5):
        y0 = 2 + i * 2
        g[y0:y0 + 2, 2:14 - i] = [P("off_white"), P("stone_light"),
                                  P("stone_mid"), P("neutral_mid"),
                                  P("neutral_dark")][i]
    base.append(Tile.from_indices("stairs_up", g))

    assert len(base) == 6, "world.py/generator.py hardcode base tile indices 0-5"

    # void (index 6) -- never-seen cells, see module docstring -------------
    void = np.full((TILE, TILE), P("ink_black"), np.uint8)
    void_tile = Tile.from_indices("void", void)

    # reserved spacer (index 7) -- keeps the dim row starting at 8 ---------
    blank = np.zeros((TILE, TILE), np.uint8)  # index 0 == transparent
    spacer_tile = Tile.from_indices("_reserved", blank)

    # dim row (indices 8-13) -- see module docstring ------------------------
    lut = _dim_lut(pal)
    dim = [Tile.from_indices(f"{t.name}_dim", lut[t.grid]) for t in base]

    return base + [void_tile, spacer_tile] + dim
