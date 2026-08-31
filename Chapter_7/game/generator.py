# SPDX-FileCopyrightText: 2026 Chris J Daly (github user cjdaly)
#
# SPDX-License-Identifier: MIT

# Procedural level generation (beads cd-dsc.2 + cd-dsc.3). Pure: no displayio,
# no board — runs and is tested off-device. Governed by doc/LEVELGEN.md.
#
# generate(seed, depth) -> a plain level dict (LEVELGEN.md §7). Deterministic:
# the same (seed, depth) always yields the same level. CircuitPython's random
# is module-level only (no random.Random instances), so the whole level is
# generated up front, before any gameplay RNG runs (LEVELGEN.md §6).
#
# Layout goes through one seam only — _rooms_and_corridors(rng) -> (grid,
# rooms). A _bsp_layout(rng) with the same return shape can replace it later
# without touching connectivity, stairs, the spawn pool, or engine integration.
#
# cd-dsc.3: after layout, _connect() floods from rooms[0] (a flat-bytearray
# BFS, _dist_grid — no per-tile dict, it has to fit RP2040 RAM) and carves a
# repair corridor to any room the spine + loops missed, so every room is
# reachable. Down-stairs then go in the room that is the most BFS steps from
# the entry room (_farthest_room_bfs), not just Euclidean-farthest.
#
# What this module does NOT do: fill spawn_points from the spawn tables
# (cd-dsc.4), feed the dict into the engine (cd-dsc.5).

import random

# Terrain tile indices — mirror game/tiles/tiles.json + LEVELGEN.md §2.
DIRT = 0            # corridor floor
FLAGSTONE = 1       # room floor
WALL = 2
STAIRS_DOWN = 4
STAIRS_UP = 5

_FLOOR = (DIRT, FLAGSTONE)     # what the generator treats as walkable-floor

LEVEL_W = 64
LEVEL_H = 64

ROOM_TARGET = 14        # stop rolling rooms once we have this many
ROOM_TRIES = 120        # ... or give up after this many attempts
MIN_ROOMS = 2           # hard floor — fallback rooms guarantee it
ROOM_MIN = 4            # room side length, inclusive
ROOM_MAX = 11
EXTRA_CORRIDORS = 2     # §3.5 "loops": 1..EXTRA_CORRIDORS extra links
SPAWN_POOL = 40         # positions handed to cd-dsc.4; capped by floor count


def generate(seed, depth, rng=None):
    """Build the level for (seed, depth). Returns the dict in LEVELGEN.md §7.

    `rng` is an escape hatch for tests that want a hermetic random.Random;
    on device it is left None and the module RNG is seeded per §6."""
    if rng is None:
        random.seed(seed + depth)
        rng = random

    grid, rooms = _rooms_and_corridors(rng)
    _connect(grid, rooms, rng)          # cd-dsc.3 — BFS reachability + repair

    up = _center(rooms[0])
    down = _center(_farthest_room_bfs(grid, rooms, rooms[0]))
    grid[up[1]][up[0]] = STAIRS_UP
    grid[down[1]][down[0]] = STAIRS_DOWN

    return {
        "grid": grid,
        "rooms": rooms,
        "up": up,
        "down": down,
        "spawn_points": _spawn_pool(rng, grid, rooms[0]),
        "depth": depth,
        "seed": seed,
    }


# -- layout seam (swap _rooms_and_corridors for _bsp_layout later) -----------


def _rooms_and_corridors(rng):
    grid = [bytearray([WALL]) * LEVEL_W for _ in range(LEVEL_H)]
    rooms = []

    tries = 0
    while len(rooms) < ROOM_TARGET and tries < ROOM_TRIES:
        tries += 1
        w = rng.randint(ROOM_MIN, ROOM_MAX)
        h = rng.randint(ROOM_MIN, ROOM_MAX)
        x = rng.randint(1, LEVEL_W - w - 1)
        y = rng.randint(1, LEVEL_H - h - 1)
        rect = (x, y, w, h)
        if any(_overlaps(rect, other, pad=1) for other in rooms):
            continue
        _carve_rect(grid, rect, FLAGSTONE)
        rooms.append(rect)

    # Degenerate seed guard — drop guaranteed-disjoint rooms in opposite
    # corners so rooms[0] and a distinct farthest room always exist.
    for corner in ((2, 2, 8, 8), (LEVEL_W - 10, LEVEL_H - 10, 8, 8)):
        if len(rooms) >= MIN_ROOMS:
            break
        _carve_rect(grid, corner, FLAGSTONE)
        rooms.append(corner)

    # Spine: link each room to the next in list order -> connected chain.
    for a, b in zip(rooms, rooms[1:]):
        _carve_corridor(grid, _center(a), _center(b), rng)

    # Loops: a couple of extra links so the level isn't a single spine.
    if len(rooms) >= 2:
        for _ in range(rng.randint(1, EXTRA_CORRIDORS)):
            a = rng.choice(rooms)
            b = rng.choice(rooms)
            if a is not b:
                _carve_corridor(grid, _center(a), _center(b), rng)

    return grid, rooms


# -- carving ----------------------------------------------------------------


def _carve_rect(grid, rect, tile):
    x, y, w, h = rect
    for row in grid[y:y + h]:
        for xx in range(x, x + w):
            row[xx] = tile


def _carve_corridor(grid, p0, p1, rng):
    """An L-bend of DIRT between two points, H-first or V-first at random.
    Only WALL is overwritten, so a corridor crossing a room leaves the room
    floor intact."""
    (x0, y0), (x1, y1) = p0, p1
    if rng.random() < 0.5:
        _carve_h(grid, y0, x0, x1)
        _carve_v(grid, x1, y0, y1)
    else:
        _carve_v(grid, x0, y0, y1)
        _carve_h(grid, y1, x0, x1)


def _carve_h(grid, y, x0, x1):
    row = grid[y]
    for x in range(min(x0, x1), max(x0, x1) + 1):
        if row[x] == WALL:
            row[x] = DIRT


def _carve_v(grid, x, y0, y1):
    for y in range(min(y0, y1), max(y0, y1) + 1):
        if grid[y][x] == WALL:
            grid[y][x] = DIRT


# -- connectivity (cd-dsc.3) ---------------------------------------------

_UNREACHED = 255       # sentinel in the flat distance grid (max real path ~128)


def _dist_grid(grid, start):
    """A flat bytearray[LEVEL_W*LEVEL_H] of BFS step counts from `start` over
    non-wall tiles, `_UNREACHED` where you can't get to.

    Deliberately not a {(x, y): steps} dict — on the RP2040 that dict would be
    ~1500 tuple keys and blow the heap. This is 4 KB flat + an int queue that
    drains. Steps are clamped at 254 (irrelevant for a 64×64 level)."""
    w, h = LEVEL_W, LEVEL_H
    dist = bytearray([_UNREACHED]) * (w * h)
    s = start[1] * w + start[0]
    dist[s] = 0
    queue = [s]
    head = 0
    while head < len(queue):
        i = queue[head]
        head += 1
        nd = dist[i] + 1
        if nd > 254:
            nd = 254
        x = i % w
        y = i // w
        if x + 1 < w and grid[y][x + 1] != WALL and dist[i + 1] == _UNREACHED:
            dist[i + 1] = nd
            queue.append(i + 1)
        if x > 0 and grid[y][x - 1] != WALL and dist[i - 1] == _UNREACHED:
            dist[i - 1] = nd
            queue.append(i - 1)
        if y + 1 < h and grid[y + 1][x] != WALL and dist[i + w] == _UNREACHED:
            dist[i + w] = nd
            queue.append(i + w)
        if y > 0 and grid[y - 1][x] != WALL and dist[i - w] == _UNREACHED:
            dist[i - w] = nd
            queue.append(i - w)
    return dist


def _dist_at(dist, pos):
    return dist[pos[1] * LEVEL_W + pos[0]]


def _connect(grid, rooms, rng):
    """Guarantee every room centre is reachable from rooms[0]. The spine +
    loops usually already do this; where they don't, carve a repair corridor
    from the stranded room to the nearest connected room and re-check."""
    if not rooms:
        return
    origin = _center(rooms[0])
    dist = _dist_grid(grid, origin)
    guard = 0
    while guard < len(rooms) * 2:
        guard += 1
        stranded = [r for r in rooms if _dist_at(dist, _center(r)) == _UNREACHED]
        if not stranded:
            return
        r = stranded[0]
        _carve_corridor(grid, _center(r),
                        _nearest_reached_center(_center(r), rooms, dist), rng)
        dist = _dist_grid(grid, origin)


def _nearest_reached_center(pos, rooms, dist):
    px, py = pos
    best, best_d2 = None, None
    for r in rooms:
        c = _center(r)
        if _dist_at(dist, c) == _UNREACHED:
            continue
        d2 = (c[0] - px) ** 2 + (c[1] - py) ** 2
        if best_d2 is None or d2 < best_d2:
            best, best_d2 = c, d2
    return best


# -- stairs + spawn pool ---------------------------------------------------


def _farthest_room(rooms, origin):
    """Euclidean-farthest room by centre distance — the pre-BFS fallback."""
    ox, oy = _center(origin)
    best, best_d2 = origin, -1
    for r in rooms:
        cx, cy = _center(r)
        d2 = (cx - ox) ** 2 + (cy - oy) ** 2
        if d2 > best_d2:
            best, best_d2 = r, d2
    return best


def _farthest_room_bfs(grid, rooms, origin):
    """The room whose centre is the most BFS steps from `origin` over floor
    (cd-dsc.3). `_connect` runs first, so every room centre has a real
    distance; the Euclidean fallback covers a pathological miss."""
    dist = _dist_grid(grid, _center(origin))
    best, best_d = origin, -1
    for r in rooms:
        d = _dist_at(dist, _center(r))
        if d != _UNREACHED and d > best_d:
            best, best_d = r, d
    if best is origin and len(rooms) > 1:
        return _farthest_room(rooms, origin)
    return best


def _spawn_pool(rng, grid, entry_room):
    """~SPAWN_POOL distinct floor tiles, never in the entry room, never a
    stair tile (stairs aren't in _FLOOR). cd-dsc.4 assigns entities to these."""
    candidates = []
    for y in range(LEVEL_H):
        row = grid[y]
        for x in range(LEVEL_W):
            if row[x] in _FLOOR and not _in_room((x, y), entry_room):
                candidates.append((x, y))

    want = min(SPAWN_POOL, len(candidates))
    pool, seen = [], set()
    guard = 0
    while len(pool) < want and guard < want * 20:
        guard += 1
        i = rng.randrange(len(candidates))
        if i not in seen:
            seen.add(i)
            pool.append(candidates[i])
    return pool


# -- rectangle helpers ---------------------------------------------------


def _center(rect):
    x, y, w, h = rect
    return (x + w // 2, y + h // 2)


def _overlaps(a, b, pad=0):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return (
        ax - pad < bx + bw and ax + aw + pad > bx
        and ay - pad < by + bh and ay + ah + pad > by
    )


def _in_room(pos, rect):
    x, y = pos
    rx, ry, rw, rh = rect
    return rx <= x < rx + rw and ry <= y < ry + rh
