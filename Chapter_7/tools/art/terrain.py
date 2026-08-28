"""Procedural terrain tiles (cd-e17.5).

PLACEHOLDER generator: value-noise + a palette ramp, just enough to prove the
pipeline and give the preview something real to show.  cd-e17.5 expands this
into the full tileable floor/wall/rubble/water/door/stairs set.
"""
from __future__ import annotations

import numpy as np

from tilelib import TILE, Tile

SEED = 1


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


def build(pal) -> list[Tile]:
    rng = np.random.default_rng(SEED)
    P = pal.index
    out = []

    # dirt floor ------------------------------------------------------------
    n = _value_noise((TILE, TILE), (4, 4), rng)
    n = 0.5 * n + 0.5 * _value_noise((TILE, TILE), (8, 8), rng)
    floor = _ramp(n, [P("dirt_darkest"), P("dirt_dark"), P("dirt_mid"),
                      P("dirt_light")])
    out.append(Tile.from_indices("floor_dirt", floor))

    # mossy flagstone -----------------------------------------------------
    n = _value_noise((TILE, TILE), (2, 2), rng)
    flag = _ramp(n, [P("stone_dark"), P("stone_mid"), P("stone_light")])
    speck = _value_noise((TILE, TILE), (8, 8), rng) > 0.82
    flag[speck] = P("moss_mid")
    out.append(Tile.from_indices("floor_flagstone", flag))

    # wall top ----------------------------------------------------------
    n = _value_noise((TILE, TILE), (3, 3), rng)
    wall = _ramp(n, [P("neutral_dark"), P("neutral_mid"), P("neutral_light")])
    wall[0, :] = P("neutral_light")   # top-lit edge
    wall[-1, :] = P("ink_black")      # bottom shadow
    out.append(Tile.from_indices("wall_top", wall))

    # water ---------------------------------------------------------
    n = _value_noise((TILE, TILE), (2, 4), rng)
    water = _ramp(n, [P("water_darkest"), P("deep_water"), P("water"),
                      P("water_light")])
    out.append(Tile.from_indices("water", water))

    # stairs down (sketch) ----------------------------------------
    g = np.full((TILE, TILE), P("dirt_dark"), np.uint8)
    for i in range(5):
        y0 = 2 + i * 2
        shade = [P("neutral_dark"), P("neutral_mid"), P("stone_mid"),
                 P("stone_light"), P("off_white")][i]
        g[y0:y0 + 2, 2 + i:14] = shade
    out.append(Tile.from_indices("stairs_down", g))

    # stairs up (sketch) ----------------------------------------
    g = np.full((TILE, TILE), P("dirt_dark"), np.uint8)
    for i in range(5):
        y0 = 2 + i * 2
        g[y0:y0 + 2, 2:14 - i] = [P("off_white"), P("stone_light"),
                                  P("stone_mid"), P("neutral_mid"),
                                  P("neutral_dark")][i]
    out.append(Tile.from_indices("stairs_up", g))

    return out
