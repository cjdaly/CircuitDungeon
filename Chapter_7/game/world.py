# SPDX-FileCopyrightText: 2026 Chris J Daly (github user cjdaly)
#
# SPDX-License-Identifier: MIT

# The pure game-state core: a tile grid, the actors on it, movement, and the
# turn scheduler. No displayio, no board, no timing — so it runs and is
# testable off-device (see test_world.py). engine.py owns everything visual
# and drives this; the generator (cd-dsc) will hand back a World.
#
# Governed by doc/ENGINE.md section 1 (turn model).

import fov as fov_mod
import log as log_mod

# Actors are plain dicts in a list, not class instances: CircuitPython has no
# __slots__, so every instance carries a full __dict__ and a class buys
# nothing over a dict for things that multiply (Ch6 PLAN.md, "State").
# Shape:  {"x": int, "y": int, "sheet": str, "tile": int, "blocks": bool, ...}
# world.actors[0] is the hero by convention; the rest are monsters.


def make_actor(x, y, sheet, tile, blocks=True, **extra):
    a = {"x": x, "y": y, "sheet": sheet, "tile": tile, "blocks": blocks}
    a.update(extra)
    return a


# doc/ENGINE.md §9. Combat stats (hp/power/defense) are plain actor keys —
# any actor that has them can fight and die (cd-e3p.5). Monsters get theirs
# from the spawn tables (LEVELGEN.md §5); the hero starts here.
HERO_DEFAULTS = {
    "hp": 20, "max_hp": 20,
    "power": 4, "defense": 1,
    "gold": 0, "xp": 0, "level": 1,
}


def make_hero(x, y, tile=0, **over):
    h = make_actor(x, y, "heroes", tile, blocks=True)
    h.update(HERO_DEFAULTS)
    h.update(over)
    return h


CORPSE_TILE = 6         # objects.bmp — see game/tiles/tiles.json
WALL_TILE = 2           # terrain.bmp "wall_top" — the one blocking terrain tile v1
STAIRS_DOWN_TILE = 4    # terrain.bmp — walkable; stepping on it descends (cd-e3p.10)
STAIRS_UP_TILE = 5      # terrain.bmp — walkable; stepping on it ascends


def world_from_level(level, start="up"):
    """Build a World from a generator.generate() dict (LEVELGEN.md §7): the
    grid goes in, the hero starts on `level[start]` — "up" for a fresh descent,
    "down" when climbing back up into a level (cd-e3p.10). Monsters and items
    come from the spawn tables in a later step (cd-dsc.4)."""
    world = World(level["grid"], wall_tiles=(WALL_TILE,), depth=level["depth"])
    sx, sy = level[start]
    world.add_actor(make_hero(sx, sy))
    world.refresh_fov()
    return world


class World:
    def __init__(self, grid, wall_tiles, depth=1):
        # grid: list of equal-length rows, each an indexable sequence of tile
        #   indices (list of ints, or a bytes/bytearray row to save RAM).
        # wall_tiles: iterable of tile indices that block movement.
        self.grid = grid
        self.wall_tiles = frozenset(wall_tiles)
        self.depth = depth     # dungeon level number (for the status line, spawns)
        self.actors = []
        self.turn = 0          # completed turns; distinct from engine's cycle pulse
        self.log = log_mod.Log()  # message log (cd-e3p.9)
        self.roster_version = 0  # bumped on any add/remove — PlayMode re-syncs sprites
        self.transition = None   # "up" | "down" set when the hero steps on stairs
        self.height = len(grid)
        self.width = len(grid[0]) if grid else 0

        # Field of view (cd-e3p.6). Two bit-packed masks, width*height bits each
        # — ~288 B apiece for a 48×48 level. `visible` is recomputed every hero
        # move; `explored` only ever gains bits (fog-of-war memory, reset when
        # the level regenerates). refresh_fov() fills them; modes.PlayMode reads
        # is_visible()/is_explored() when painting (dimming is cd-oht.6).
        self._fov_bytes = (self.width * self.height + 7) // 8
        self.visible = bytearray(self._fov_bytes)
        self.explored = bytearray(self._fov_bytes)

    @property
    def hero(self):
        return self.actors[0] if self.actors else None

    def hero_alive(self):
        h = self.hero
        return h is not None and h.get("hp", 1) > 0

    def monsters(self):
        return self.actors[1:]

    def add_actor(self, actor):
        self.actors.append(actor)
        self.roster_version += 1
        return actor

    def remove_actor(self, actor):
        self.actors.remove(actor)
        self.roster_version += 1

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

    # -- field of view (ENGINE.md §8, bead cd-e3p.6) --------------------

    def is_visible(self, x, y):
        """In the hero's current line of sight (from the last refresh_fov())."""
        if not self.in_bounds(x, y):
            return False
        i = y * self.width + x
        return bool(self.visible[i >> 3] & (1 << (i & 7)))

    def is_explored(self, x, y):
        """Seen at least once this level — drawn dim when not also visible."""
        if not self.in_bounds(x, y):
            return False
        i = y * self.width + x
        return bool(self.explored[i >> 3] & (1 << (i & 7)))

    def refresh_fov(self):
        """Recompute `visible` from the hero's position (walls block sight);
        OR the result into `explored`. Cheap enough to call every hero move."""
        h = self.hero
        vis = self.visible
        for k in range(len(vis)):
            vis[k] = 0
        if h is None:
            return
        exp = self.explored
        w = self.width
        grid = self.grid
        walls = self.wall_tiles
        in_bounds = self.in_bounds

        def _blocked(x, y):
            return not in_bounds(x, y) or grid[y][x] in walls

        def _mark(x, y):
            if not in_bounds(x, y):
                return
            i = y * w + x
            bit = 1 << (i & 7)
            vis[i >> 3] |= bit
            exp[i >> 3] |= bit

        fov_mod.compute(h["x"], h["y"], _blocked, _mark)

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


def _check_transition(world):
    """Hero just stepped somewhere — flag a level change if it was a stair
    tile. The engine (engine.Game._change_level) reads and clears this after
    the turn resolves. Only a *move* onto stairs triggers it, never spawning
    there (world_from_level adds the hero without going through here)."""
    h = world.hero
    tile = world.grid[h["y"]][h["x"]]
    if tile == STAIRS_DOWN_TILE:
        world.transition = "down"
    elif tile == STAIRS_UP_TILE:
        world.transition = "up"


def _apply_player_action(world, action):
    """Apply the hero's action. Returns True if it spends a turn."""
    if action is None:
        return False
    kind = action[0]
    if kind == "move":
        result = world.move_actor(world.hero, action[1], action[2])
        if result == "moved":
            _check_transition(world)
            return True
        if isinstance(result, tuple) and result[0] == "bump":
            other = result[1]
            if "hp" in other:              # bump a fightable actor -> attack
                resolve_attack(world, world.hero, other)
                return True                # ENGINE.md 1.2 — spends the turn
            return False                   # bumped a non-combatant
        return False  # "blocked" — wall or edge
    if kind == "wait":
        return True
    return False


def resolve_turn(world, scheduler, action, monster_turn):
    """One turn: hero acts, then every monster acts once, then upkeep
    (ENGINE.md 1.1). `monster_turn(world, actor)` is the per-monster AI.
    Returns True if a turn actually passed."""
    # Snapshot the actor order BEFORE anyone moves (ENGINE.md 1.1). A monster
    # the hero kills this turn is dropped by the `not in world.actors` check
    # below; a corpse created this turn is simply not in the snapshot, so it
    # never gets an AI turn — corpses are scenery, not actors that act.
    roster = scheduler.actors_for_turn()
    if not _apply_player_action(world, action):
        return False
    for actor in roster:
        if actor is world.hero:
            continue
        if actor not in world.actors:
            continue                       # died earlier this turn (corpse)
        if actor.get("corpse"):
            continue                       # scenery, not something that acts
        if not world.hero_alive():
            break                          # nothing swings at a dead hero
        monster_turn(world, actor)
    _upkeep(world)
    world.refresh_fov()        # the hero may have moved (cd-e3p.6)
    world.turn += 1
    return True


def _upkeep(world):
    """End-of-turn bookkeeping — status-effect ticks, regen, etc.
    Empty until cd-e3p.7 (player model) / cd-e3p.4 add state that needs it."""
    pass


# -- combat (ENGINE.md §7, bead cd-e3p.5) ----------------------------
# v1 is hero <-> monster only. Damage = max(1, power - defense). A dead
# monster is replaced by a non-blocking corpse; a dead hero stays at
# actors[0] and engine.Game handles the game-over screen (§9.2).


def _mob_name(actor):
    return "the " + actor.get("name", "creature")


def _cap(s):
    """Capitalize the first letter. CircuitPython's str has no .capitalize()
    (nor .title()) — only .upper()/.lower() — so do it by hand."""
    return s[:1].upper() + s[1:] if s else s


def resolve_attack(world, attacker, defender):
    dmg = max(1, attacker.get("power", 1) - defender.get("defense", 0))
    defender["hp"] = defender.get("hp", 0) - dmg

    if attacker is world.hero:
        world.log.add("You hit %s for %d." % (_mob_name(defender), dmg))
    else:
        world.log.add("%s hits you for %d." % (_cap(_mob_name(attacker)), dmg))

    if defender["hp"] > 0:
        return
    if defender is world.hero:
        world.log.add("You die.")
        return
    world.log.add("%s dies." % _cap(_mob_name(defender)))
    world.remove_actor(defender)
    # A corpse is scenery: non-blocking, and `corpse` keeps resolve_turn from
    # ever handing it an AI turn (it was waking up and trailing the hero —
    # cd-yl4 sibling bug).
    world.add_actor(
        make_actor(defender["x"], defender["y"], "objects", CORPSE_TILE,
                   blocks=False, corpse=True)
    )
    if attacker is world.hero:
        world.hero["xp"] = world.hero.get("xp", 0) + defender.get("xp", 0)


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
