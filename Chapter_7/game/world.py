# The MIT License (MIT)
#
# Copyright (c) 2026 Chris J Daly (github user cjdaly)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

# The pure game-state core: a tile grid, the actors on it, movement, and the
# turn scheduler. No displayio, no board, no timing — so it runs and is
# testable off-device (see test_world.py). engine.py owns everything visual
# and drives this; the generator (cd-dsc) will hand back a World.
#
# Governed by doc/ENGINE.md section 1 (turn model).

# Actors are plain dicts in a list, not class instances: CircuitPython has no
# __slots__, so every instance carries a full __dict__ and a class buys
# nothing over a dict for things that multiply (Ch6 PLAN.md, "State").
# Shape:  {"x": int, "y": int, "sheet": str, "tile": int, "blocks": bool, ...}
# world.actors[0] is the hero by convention; the rest are monsters.


def make_actor(x, y, sheet, tile, blocks=True, **extra):
    a = {"x": x, "y": y, "sheet": sheet, "tile": tile, "blocks": blocks}
    a.update(extra)
    return a


class World:
    def __init__(self, grid, wall_tiles):
        # grid: list of equal-length rows, each an indexable sequence of tile
        #   indices (list of ints, or a bytes/bytearray row to save RAM).
        # wall_tiles: iterable of tile indices that block movement.
        self.grid = grid
        self.wall_tiles = frozenset(wall_tiles)
        self.actors = []
        self.turn = 0          # completed turns; distinct from engine's cycle pulse
        self.height = len(grid)
        self.width = len(grid[0]) if grid else 0

    @property
    def hero(self):
        return self.actors[0] if self.actors else None

    def monsters(self):
        return self.actors[1:]

    def add_actor(self, actor):
        self.actors.append(actor)
        return actor

    def remove_actor(self, actor):
        self.actors.remove(actor)

    # -- queries ----------------------------------------------------------

    def in_bounds(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height

    def tile_at(self, x, y):
        return self.grid[y][x]

    def is_wall(self, x, y):
        """Terrain-only blocking. Out of bounds counts as wall."""
        if not self.in_bounds(x, y):
            return True
        return self.grid[y][x] in self.wall_tiles

    def actor_at(self, x, y):
        """The blocking actor on (x, y), or None. Non-blocking actors (items,
        a corpse) don't count."""
        for a in self.actors:
            if a["x"] == x and a["y"] == y and a["blocks"]:
                return a
        return None

    def blocked(self, x, y):
        return self.is_wall(x, y) or self.actor_at(x, y) is not None

    # -- movement (the logical half of ENGINE.md 1.4) --------------------

    def move_actor(self, actor, dx, dy):
        """Try to step `actor` by (dx, dy). 4-way only: exactly one of dx/dy
        is non-zero and +/-1 (ENGINE.md 1.3).

        Returns one of:
          "moved"   - actor position changed
          "blocked" - wall or map edge; caller treats as a no-op, NO turn passes
          "bump:<a>" - a blocking actor is there; returns the actor in a tuple
                       ("bump", other). Combat (cd-e3p.5) decides what a bump
                       does and whether it spends the turn.
        """
        if (dx, dy) not in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            raise ValueError("move_actor is 4-way, single-step: %r" % ((dx, dy),))
        nx, ny = actor["x"] + dx, actor["y"] + dy
        if self.is_wall(nx, ny):
            return "blocked"
        other = self.actor_at(nx, ny)
        if other is not None and other is not actor:
            return ("bump", other)
        actor["x"], actor["y"] = nx, ny
        return "moved"


class RoundRobinScheduler:
    """v1 turn scheduler (ENGINE.md 1.1): every actor acts once per turn, in
    world.actors order — hero first, then monsters.

    This is the seam a speed/energy scheduler replaces later (stretch goal):
    swap this class for one whose actors_for_turn() yields fast actors more
    often, and nothing in the turn loop / AI / combat has to change.
    """

    def __init__(self, world):
        self.world = world

    def actors_for_turn(self):
        # snapshot: a monster dying mid-turn must not reshuffle the iteration
        return list(self.world.actors)


# -- the turn loop (ENGINE.md 1.1, bead cd-e3p.3) -----------------------
#
# Pure: no displayio. modes.PlayMode maps input events to an `action` and
# calls resolve_turn(); its render() then reflects the new positions
# (instant snap in v1 — ENGINE.md 1.4).
#
# An action is a tuple:  ("move", dx, dy) | ("wait",) | None
# None / a free action / a failed move spends no turn.

MOVE_DELTAS = {"n": (0, -1), "s": (0, 1), "w": (-1, 0), "e": (1, 0)}


def _apply_player_action(world, action):
    """Apply the hero's action. Returns True if it spends a turn."""
    if action is None:
        return False
    kind = action[0]
    if kind == "move":
        result = world.move_actor(world.hero, action[1], action[2])
        if result == "moved":
            return True
        if isinstance(result, tuple) and result[0] == "bump":
            # TODO(cd-e3p.5): a bump onto a hostile is an attack and DOES spend
            # the turn (ENGINE.md 1.2). No combat yet, so treat it as inert.
            return False
        return False  # "blocked" — wall or edge
    if kind == "wait":
        return True
    return False


def resolve_turn(world, scheduler, action, monster_turn):
    """One turn: hero acts, then every monster acts once, then upkeep
    (ENGINE.md 1.1). `monster_turn(world, actor)` is the per-monster AI
    (a no-op until cd-e3p.4). Returns True if a turn actually passed."""
    if not _apply_player_action(world, action):
        return False
    for actor in scheduler.actors_for_turn():
        if actor is world.hero:
            continue
        monster_turn(world, actor)
    _upkeep(world)
    world.turn += 1
    return True


def _upkeep(world):
    """End-of-turn bookkeeping — status-effect ticks, regen, etc.
    Empty until cd-e3p.7 (player model) / cd-e3p.4 add state that needs it."""
    pass


# -- viewport / camera (LAYOUT.md §3) ---------------------------------
# Pure: modes.PlayMode calls this to pick which view_tiles-square window of
# the level to paint into its terrain TileGrid.


def camera_for(hero_x, hero_y, view_tiles, level_w, level_h):
    """Top-left level tile of a `view_tiles`-square viewport centred on the
    hero, clamped so the window never leaves the level. Near an edge the hero
    drifts off-centre rather than showing out-of-bounds (standard roguelike)."""
    half = view_tiles // 2
    max_x = level_w - view_tiles
    max_y = level_h - view_tiles
    cx = min(max(hero_x - half, 0), max_x) if max_x > 0 else 0
    cy = min(max(hero_y - half, 0), max_y) if max_y > 0 else 0
    return cx, cy


# -- line of sight (for monster AI, cd-e3p.4) ------------------------
# A monster→hero visibility ray. Simpler than the player FOV (cd-e3p.6):
# one straight line, walls only.


def los_clear(world, x0, y0, x1, y1):
    """True if no wall tile lies strictly between (x0,y0) and (x1,y1) — a
    Bresenham walk, endpoints excluded."""
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy
    x, y = x0, y0
    while (x, y) != (x1, y1):
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x += sx
        if e2 < dx:
            err += dx
            y += sy
        if (x, y) != (x1, y1) and world.is_wall(x, y):
            return False
    return True
