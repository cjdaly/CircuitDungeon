# SPDX-License-Identifier: MIT
"""Mixed 16x16 scenery / 32x32 actor rendering -- cd-45v.1 prototype
(relates to Ch9's cd-zw2.2).

Not main.py: run this standalone (rename to main.py or `import
sprite_scale_demo` from a scratch main.py). No hand-authored art exists yet
for Ch9 (that's separate art beads down the line), so every sprite here is
drawn procedurally into a displayio.Bitmap at startup -- the point is to
prove the *technique* (two TileGrids at different tile scales sharing a
screen, actor transparency via Palette.make_transparent(), and staying
clear of the round bezel) works before any real art exists to test it with.

Layout:
  - a 16x16-tile floor/wall/rug grid filling the screen (displayio.TileGrid,
    tile_width=tile_height=16) -- corners get clipped by the round bezel,
    which is fine for background scenery, see doc/HARDWARE.md "Display"
  - two 32x32 actor sprites (hero, critter) as separate TileGrids on top,
    each free-positioned (not grid-locked) and kept _EDGE_MARGIN clear of
    every screen edge so they're never clipped, matching the ~20-30px inset
    doc/HARDWARE.md already calls out for readable content
  - a slow vertical bob on each actor, just to prove animation still reads
    fine layered over the tile grid

STATUS: UNTESTED ON DEVICE as of 2026-09-12 -- written and desk-checked
against hardware.py's APIs and displayio's documented Bitmap/Palette/
TileGrid behavior, not yet run on the board. The actual pixel art (blocky
placeholder shapes) hasn't been eyeballed on the real round panel either.
"""
import math
import time

import displayio

import hardware

TILE = 16
GRID_W = hardware.WIDTH // TILE
GRID_H = hardware.HEIGHT // TILE

ACTOR = 32
_EDGE_MARGIN = 20  # doc/HARDWARE.md "Display" -- round-bezel inset

_FLOOR, _WALL, _RUG = 0, 1, 2
_TRANSPARENT, _HERO_BODY, _HERO_HEAD, _CRITTER_BODY = 0, 1, 2, 3

_BOB_PERIOD = 2.4  # seconds per full bob cycle
_BOB_PX = 4


def _make_tile_sheet():
    """A 3-frame, 16x16 spritesheet: floor, wall (bordered), rug (diamond)."""
    bitmap = displayio.Bitmap(TILE * 3, TILE, 3)
    palette = displayio.Palette(3)
    palette[_FLOOR] = 0x2A2A38
    palette[_WALL] = 0x14141C
    palette[_RUG] = 0x8B2E2E

    for y in range(TILE):
        for x in range(TILE):
            bitmap[x, y] = _FLOOR  # frame 0: floor
            bitmap[TILE + x, y] = _WALL  # frame 1: wall
            bitmap[2 * TILE + x, y] = _FLOOR  # frame 2: rug base

    for x in range(2, TILE - 2):  # wall texture: a lighter inset band
        bitmap[TILE + x, 2] = _FLOOR
        bitmap[TILE + x, TILE - 3] = _FLOOR

    cx = cy = TILE // 2  # rug: a diamond accent
    for y in range(TILE):
        for x in range(TILE):
            if abs(x - cx) + abs(y - cy) <= 5:
                bitmap[2 * TILE + x, y] = _RUG

    return bitmap, palette


def _make_room_grid(bitmap, palette):
    grid = displayio.TileGrid(
        bitmap, pixel_shader=palette, width=GRID_W, height=GRID_H,
        tile_width=TILE, tile_height=TILE,
    )
    for gy in range(GRID_H):
        for gx in range(GRID_W):
            on_border = gx in (0, GRID_W - 1) or gy in (0, GRID_H - 1)
            grid[gx, gy] = 1 if on_border else 0  # wall frame : floor frame
    grid[GRID_W // 2, GRID_H // 2] = 2  # rug in the center
    return grid


def _make_actor_sheet():
    """A 2-frame, 32x32 spritesheet: hero (frame 0), critter (frame 1).

    Background is index 0, made transparent so each actor blends over
    whatever tile is underneath -- same approach as Ch5/Ch6's
    adafruit_imageload + make_transparent() sprites, just hand-drawn here
    instead of loaded from a .bmp.
    """
    bitmap = displayio.Bitmap(ACTOR * 2, ACTOR, 4)
    palette = displayio.Palette(4)
    palette[_TRANSPARENT] = 0x000000
    palette.make_transparent(_TRANSPARENT)
    palette[_HERO_BODY] = 0xC04040
    palette[_HERO_HEAD] = 0xE8C090
    palette[_CRITTER_BODY] = 0x40A0C0

    for y in range(14, 30):  # hero: body block
        for x in range(8, 24):
            bitmap[x, y] = _HERO_BODY
    hx, hy, hr = 16, 9, 7  # hero: head circle
    for y in range(ACTOR):
        for x in range(ACTOR):
            if (x - hx) ** 2 + (y - hy) ** 2 <= hr * hr:
                bitmap[x, y] = _HERO_HEAD

    cx, cy, cr = 16, 20, 10  # critter: round blob, frame 1 (local to its half)
    for y in range(ACTOR):
        for x in range(ACTOR):
            if (x - cx) ** 2 + (y - cy) ** 2 <= cr * cr:
                bitmap[ACTOR + x, y] = _CRITTER_BODY

    return bitmap, palette


def _make_actor(bitmap, palette, frame, x, y):
    grid = displayio.TileGrid(
        bitmap, pixel_shader=palette, width=1, height=1,
        tile_width=ACTOR, tile_height=ACTOR, x=x, y=y,
    )
    grid[0, 0] = frame
    return grid


def main():
    display, _backlight = hardware.init_display()

    group = displayio.Group()
    display.root_group = group

    tile_bitmap, tile_palette = _make_tile_sheet()
    group.append(_make_room_grid(tile_bitmap, tile_palette))

    actor_bitmap, actor_palette = _make_actor_sheet()
    lo = _EDGE_MARGIN
    hi = hardware.WIDTH - _EDGE_MARGIN - ACTOR
    base_y = hardware.HEIGHT // 2 - ACTOR // 2
    hero = _make_actor(actor_bitmap, actor_palette, 0, lo, base_y)
    critter = _make_actor(actor_bitmap, actor_palette, 1, hi, base_y)
    group.append(hero)
    group.append(critter)

    print("Ch8 sprite-scale demo ready")

    while True:
        now = time.monotonic()
        bob = int(_BOB_PX * math.sin(2 * math.pi * now / _BOB_PERIOD))
        hero.y = base_y + bob
        critter.y = base_y - bob
        time.sleep(0.05)


main()
