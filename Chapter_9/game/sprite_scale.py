# SPDX-License-Identifier: MIT
"""Mixed-scale rendering: 32x32 actors over a 16x16 scenery grid -- cd-zw2.2.

The technique here -- two TileGrids at different tile scales sharing the
round screen, free-positioned actor sprites kept clear of the bezel, actor
transparency via Palette.make_transparent() -- is already proven on real
hardware: Chapter_8's cd-45v.1 prototype (sprite_scale_demo.py) confirmed
the round-bezel clipping assumption and actor-over-scenery layering both
work as expected, 2026-09-13.

This module is the *mechanism* only, generalized from that prototype's
hardcoded demo scene into reusable helpers -- no actual room content or
hero/critter art lives here. Real bitmaps and room layouts are separate
content/art work (cd-zw2.6 for rooms, whichever art beads eventually cover
Ch9's sprites) that calls into these helpers.

STATUS: ported/generalized, not yet re-tested on-device in Chapter_9 --
displayio isn't importable under plain desktop Python. make_scenery_grid()/
make_actor() can only be desk-checked (the underlying technique is already
proven on Chapter 8 hardware); displayio is imported lazily inside them
(same trick as touch.py's adafruit_cst8xx import) so clamp_actor_position()
-- pure arithmetic, no hardware -- stays unit-testable, see
tests/test_sprite_scale.py.
"""

ACTOR_SIZE = 32
SCENERY_TILE_SIZE = 16
EDGE_MARGIN = 20  # px -- round-bezel inset for actor placement, matches
                  # Chapter_8/doc/HARDWARE.md "Display" guidance and the
                  # value cd-45v.1 confirmed looked right on real hardware.


def make_scenery_grid(bitmap, palette, layout, tile_size=SCENERY_TILE_SIZE):
    """A TileGrid from a tile sheet (`bitmap`/`palette`), laid out by `layout`.

    `layout` is a 2D sequence of tile-frame indices: `layout[y][x]` ->
    the frame (column) of `bitmap` to show at grid position (x, y). All
    rows must be the same length. Ragged/empty layouts aren't handled here
    -- validate real room content before calling this.
    """
    import displayio

    height = len(layout)
    width = len(layout[0]) if height else 0
    grid = displayio.TileGrid(
        bitmap, pixel_shader=palette, width=width, height=height,
        tile_width=tile_size, tile_height=tile_size,
    )
    for gy, row in enumerate(layout):
        for gx, frame in enumerate(row):
            grid[gx, gy] = frame
    return grid


def make_actor(bitmap, palette, frame, x, y, size=ACTOR_SIZE):
    """A free-positioned actor TileGrid at (x, y) showing `frame` from `bitmap`.

    `palette` should already have its background index made transparent
    (`palette.make_transparent(idx)`) if the actor is meant to blend over
    whatever scenery is underneath -- this function doesn't do that itself,
    since a caller might want an opaque actor instead.
    """
    import displayio

    grid = displayio.TileGrid(
        bitmap, pixel_shader=palette, width=1, height=1,
        tile_width=size, tile_height=size, x=x, y=y,
    )
    grid[0, 0] = frame
    return grid


def clamp_actor_position(x, y, screen_width, screen_height, size=ACTOR_SIZE, margin=EDGE_MARGIN):
    """Clamp a proposed actor position so it stays >= margin from every edge.

    Generalizes the fixed left/right positions cd-45v.1's demo hardcoded --
    Ch9 will need to place actors dynamically (per room, per critter), not
    just two fixed spots.
    """
    lo_x, hi_x = margin, screen_width - margin - size
    lo_y, hi_y = margin, screen_height - margin - size
    return max(lo_x, min(x, hi_x)), max(lo_y, min(y, hi_y))
