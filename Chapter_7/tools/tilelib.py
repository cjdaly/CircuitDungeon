#!/usr/bin/env python3
"""Shared tile-authoring + sheet-packing helpers for the Ch7 art pipeline.

Used by build_tiles.py and the per-category art modules (art/*.py).

Authoring model
---------------
A hand-authored tile is an ASCII grid plus a legend:

    LEGEND = {".": None, "o": "off_white", "x": "ink_black"}
    tile("skeleton", '''
        ................
        ......xxxx......
        .....xooooх.....
        ...(16 rows x 16 cols)...
    ''', LEGEND)

`None` (usually ".") -> palette index 0, the transparent slot.  Every other
char maps to a colour *name* from the master palette (game/tiles/palette.json).

A procedural tile just hands back a ready 16x16 numpy array of palette indices
(see art/terrain.py); `Tile.from_indices()` wraps it.

Sheets
------
`pack(tiles, cols)` lays tiles row-major into one index array; `write_bmp()`
emits the palette-indexed 8-bit BMP the device loads with adafruit_imageload
(index 0 made transparent at load time, exactly like Ch6).
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image

REPO = Path(__file__).resolve().parents[2]
TILES_DIR = REPO / "Chapter_7" / "game" / "tiles"
PREVIEW_DIR = REPO / "Chapter_7" / "doc" / "preview"

TILE = 16  # px, uniform for every Ch7 sheet (ART.md sec2)


# --------------------------------------------------------------------------- #
# master palette
# --------------------------------------------------------------------------- #
class Palette:
    def __init__(self, path: Path | None = None):
        data = json.loads((path or (TILES_DIR / "palette.json")).read_text())
        self.names: list[str] = data["names"]
        self.rgb: list[tuple[int, int, int]] = [tuple(c) for c in data["rgb"]]
        self.capacity: int = data.get("capacity", 64)
        self._idx = {n: i for i, n in enumerate(self.names)}

    def index(self, name: str) -> int:
        try:
            return self._idx[name]
        except KeyError:
            raise KeyError(
                f"colour {name!r} not in master palette; "
                f"known: {', '.join(self.names)}"
            ) from None

    def flat_table(self) -> list[int]:
        """Flat RGB triples for the BMP palette table — exactly one entry per
        master-palette colour, no 256-padding.

        PIL writes `biClrUsed` = the number of entries handed here, and
        adafruit_imageload then allocates `displayio.Palette(biClrUsed)`. A
        padded 256-entry table cost a ~2 KB Palette per sheet on the RP2040
        (~8 KB for four sheets) for a 40-colour palette — see
        doc/MEMORY-MAP.md §5 / cd-dsc.6.1. The table stays index-stable
        (slot N is the same colour on every sheet), so tile indices,
        tiles.json, and the engine's `*_TILE` constants are unaffected."""
        flat: list[int] = []
        for r, g, b in self.rgb:
            flat += [r, g, b]
        return flat


# --------------------------------------------------------------------------- #
# a single tile
# --------------------------------------------------------------------------- #
@dataclass
class Tile:
    name: str
    grid: np.ndarray  # (TILE, TILE) uint8 of palette indices

    def __post_init__(self):
        if self.grid.shape != (TILE, TILE):
            raise ValueError(
                f"tile {self.name!r} is {self.grid.shape}, need ({TILE}, {TILE})"
            )
        self.grid = self.grid.astype(np.uint8)

    @classmethod
    def from_ascii(cls, name: str, art: str, legend: dict, pal: Palette) -> "Tile":
        rows = [r for r in (ln.strip() for ln in art.splitlines()) if r]
        if len(rows) != TILE or any(len(r) != TILE for r in rows):
            bad = [(i, len(r)) for i, r in enumerate(rows) if len(r) != TILE]
            raise ValueError(
                f"tile {name!r}: need {TILE}x{TILE}, got {len(rows)} rows; "
                f"wrong-width rows (idx,len): {bad}"
            )
        g = np.zeros((TILE, TILE), np.uint8)
        for y, row in enumerate(rows):
            for x, ch in enumerate(row):
                if ch not in legend:
                    raise KeyError(f"tile {name!r}: char {ch!r} not in legend")
                col = legend[ch]
                g[y, x] = 0 if col is None else pal.index(col)
        return cls(name, g)

    @classmethod
    def from_indices(cls, name: str, grid: np.ndarray) -> "Tile":
        return cls(name, np.asarray(grid, np.uint8))


# --------------------------------------------------------------------------- #
# sheet packing / output
# --------------------------------------------------------------------------- #
@dataclass
class Sheet:
    name: str          # e.g. "terrain"
    tiles: list[Tile]
    cols: int

    @property
    def rows(self) -> int:
        return (len(self.tiles) + self.cols - 1) // self.cols

    def index_array(self) -> np.ndarray:
        a = np.zeros((self.rows * TILE, self.cols * TILE), np.uint8)
        for i, t in enumerate(self.tiles):
            r, c = divmod(i, self.cols)
            a[r * TILE:(r + 1) * TILE, c * TILE:(c + 1) * TILE] = t.grid
        return a

    def manifest(self) -> list[dict]:
        return [{"index": i, "name": t.name,
                 "col": i % self.cols, "row": i // self.cols}
                for i, t in enumerate(self.tiles)]


def write_bmp(sheet: Sheet, pal: Palette, out_dir: Path = TILES_DIR) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    img = Image.fromarray(sheet.index_array(), mode="P")
    img.putpalette(pal.flat_table())
    path = out_dir / f"{sheet.name}.bmp"
    img.save(path)  # 'P' -> 8-bit BMP, 256-entry table, BITMAPINFOHEADER
    return path


def write_manifest(sheets: list[Sheet], out_dir: Path = TILES_DIR) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    doc = {
        s.name: {
            "tile": TILE, "cols": s.cols, "rows": s.rows,
            "count": len(s.tiles), "tiles": s.manifest(),
        }
        for s in sheets
    }
    path = out_dir / "tiles.json"
    path.write_text(json.dumps(doc, indent=2) + "\n")
    return path


# --------------------------------------------------------------------------- #
# rgb rendering (previews)
# --------------------------------------------------------------------------- #
def to_rgba(grid: np.ndarray, pal: Palette) -> np.ndarray:
    lut = np.array(pal.rgb + [(0, 0, 0)] * (256 - len(pal.rgb)), np.uint8)
    rgb = lut[grid]
    a = np.where(grid == 0, 0, 255).astype(np.uint8)
    return np.dstack([rgb, a])
