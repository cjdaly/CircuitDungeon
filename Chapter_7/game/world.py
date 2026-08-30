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
