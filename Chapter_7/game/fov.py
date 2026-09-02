# SPDX-FileCopyrightText: 2026 Chris J Daly (github user cjdaly)
#
# SPDX-License-Identifier: MIT

# Player field of view (bead cd-e3p.6). Pure: no displayio, no board, no game
# state — `world.refresh_fov()` drives it and stashes the result in
# `world.visible` / `world.explored`; `modes.PlayMode` reads those when it
# paints the viewport (the dimming itself is cd-oht.6).
#
# Recursive shadowcasting, eight octants (Björn Bergström / RogueBasin). One
# tile is visible if an unobstructed slice of the origin cell can "see" it
# within `RADIUS`. Symmetric enough for a 4-way roguelike: if the hero sees a
# tile, a monster on that tile would see the hero (monster AI still uses the
# cheaper world.los_clear ray — ENGINE.md §6).
#
# Cost: ~radius² per octant, a handful of float divides each — ~1 ms at
# RADIUS 8, run once per hero move. Recursion depth ≤ RADIUS.
#
# Governed by doc/ENGINE.md §8.

RADIUS = 8

# (xx, xy, yx, yy) — the eight (row, col) -> (x, y) transforms, one per octant.
_OCTANTS = (
    (1, 0, 0, 1),
    (0, 1, 1, 0),
    (0, -1, 1, 0),
    (-1, 0, 0, 1),
    (-1, 0, 0, -1),
    (0, -1, -1, 0),
    (0, 1, -1, 0),
    (1, 0, 0, -1),
)


def compute(ox, oy, blocked, mark, radius=RADIUS):
    """Mark every tile visible from (ox, oy).

    blocked(x, y) -> bool   wall, or off the map (must be total)
    mark(x, y)             called once per visible tile, origin included
    """
    mark(ox, oy)
    for xx, xy, yx, yy in _OCTANTS:
        _scan(1, 1.0, 0.0, radius, radius * radius,
              ox, oy, xx, xy, yx, yy, blocked, mark)


def _scan(row, start_slope, end_slope, radius, r2,
          ox, oy, xx, xy, yx, yy, blocked, mark):
    if start_slope < end_slope:
        return
    blocked_run = False
    next_start = start_slope
    for dist in range(row, radius + 1):
        dx, dy = -dist, -dist
        while dx <= 0:
            # slopes of this cell's leading / trailing edge
            l_slope = (dx - 0.5) / (dy + 0.5)
            r_slope = (dx + 0.5) / (dy - 0.5)
            if start_slope < r_slope:
                dx += 1
                continue
            if end_slope > l_slope:
                break

            mx = ox + dx * xx + dy * xy
            my = oy + dx * yx + dy * yy
            if dx * dx + dy * dy <= r2:
                mark(mx, my)

            wall = blocked(mx, my)
            if blocked_run:
                if wall:
                    next_start = r_slope
                else:
                    blocked_run = False
                    start_slope = next_start
            elif wall and dist < radius:
                # a new wall — recurse into the lit span before it, then
                # continue this row past it with a narrowed start slope
                blocked_run = True
                _scan(dist + 1, start_slope, l_slope, radius, r2,
                      ox, oy, xx, xy, yx, yy, blocked, mark)
                next_start = r_slope
            dx += 1
        if blocked_run:
            break
