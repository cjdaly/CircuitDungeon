# SPDX-FileCopyrightText: 2026 Chris J Daly (github user cjdaly)
#
# SPDX-License-Identifier: MIT

# Depth-scaled monster + leveled-equipment spawn tables (bead cd-dsc.4).
# world.world_from_level() calls populate() once, right after adding the
# hero, using generator.generate()'s spawn_points (up to 32 distinct floor
# tiles, never the entry room, never a stair — see generator.py).
#
# Pure: no displayio/board. Continues the module `random` stream
# generator.generate() left off at (LEVELGEN.md §6, ai.py does the same for
# monster AI) unless a hermetic `rng` is passed in (tests).
#
# Deliberately minimal for v1, per Chris (2026-09-13): monsters, a sword +
# armor pair, and a little gold (added 2026-09-14 — the status line always
# had a Gold counter, cd-oht.3, but nothing dropped any). No potions/scrolls
# yet even though world.py's generic ITEM_EFFECTS/use_item path already
# supports them (cd-e3p.8) — that stays ready for whenever a later pass
# wants to spawn those too.

import random

import world as world_mod

# name, creatures.bmp tile, hp, power, defense, xp, min_depth, max_depth —
# see game/tiles/tiles.json for the tile roster. Roughly: slime/rat are
# depth-1 chaff, bat/skeleton are the depth 3-ish step up, goblin is the
# depth 4+ heavy hitter. Not balanced against real playtesting yet.
MONSTERS = (
    ("slime",    0, 3,  1, 0, 1, 1,  5),
    ("rat",      1, 4,  2, 0, 1, 1,  6),
    ("bat",      3, 3,  2, 0, 2, 1,  7),
    ("skeleton", 2, 8,  3, 1, 3, 3, 10),
    ("goblin",   4, 10, 4, 1, 4, 4, 12),
)

MONSTER_BASE = 2       # monsters at depth 1
MONSTER_PER_DEPTH = 1  # + this many per depth beyond 1
MONSTER_CAP = 8        # never more than this per level, regardless of depth
ITEM_LEVEL_JITTER = 2  # a depth-D level drops gear roughly level D +/- this

GOLD_PILES = 2          # gold piles per level, v1 (flat, not depth-scaled)
GOLD_MIN = 5            # per-pile amount range, scaled by depth below
GOLD_MAX = 15


def _eligible_monsters(depth):
    return [m for m in MONSTERS if m[6] <= depth <= m[7]]


def _make_monster(depth, rng):
    pool = _eligible_monsters(depth) or [MONSTERS[0]]  # slime never runs out
    name, tile, hp, power, defense, xp, _lo, _hi = rng.choice(pool)
    return world_mod.make_actor(0, 0, "creatures", tile, hp=hp, power=power,
                                defense=defense, xp=xp, name=name)


def _item_level(depth, rng):
    return max(1, depth + rng.randint(-ITEM_LEVEL_JITTER, ITEM_LEVEL_JITTER))


def _gold_amount(depth, rng):
    return rng.randint(GOLD_MIN, GOLD_MAX) * depth


def _pop_random(points, rng):
    # CircuitPython's built-in `random` module has no .shuffle() (only
    # choice/randint/randrange/random/uniform/seed/getrandbits — confirmed
    # on-device, cd-dsc.4) unlike a hermetic random.Random() instance, so a
    # shuffle-then-pop that works in tests crashes with AttributeError on
    # the real board. Swap-to-end + pop needs only randint, so it works
    # against both the global module and a test rng alike.
    i = rng.randint(0, len(points) - 1)
    points[i], points[-1] = points[-1], points[i]
    return points.pop()


def populate(world, spawn_points, depth, rng=None):
    """Place monsters + one sword and one armor piece across `spawn_points`,
    scaled by `depth`. Mutates `world` via add_actor(); doesn't touch
    `spawn_points` itself. At most one thing per point, so it's capped by
    however many points generator.py handed over (SPAWN_POOL, currently 32)."""
    if rng is None:
        rng = random
    points = list(spawn_points)

    monster_count = min(len(points),
                        MONSTER_BASE + MONSTER_PER_DEPTH * (depth - 1),
                        MONSTER_CAP)
    for _ in range(monster_count):
        x, y = _pop_random(points, rng)
        m = _make_monster(depth, rng)
        m["x"], m["y"] = x, y
        world.add_actor(m)

    for kind, tile, tag in (("weapon", world_mod.SWORD_TILE, "sword"),
                            ("armor", world_mod.ARMOR_TILE, "armor")):
        if not points:
            break
        x, y = _pop_random(points, rng)
        level = _item_level(depth, rng)
        item = world_mod.make_item(x, y, tile, kind,
                                   "a level %d %s" % (level, tag), level=level)
        world.add_actor(item)

    for _ in range(min(GOLD_PILES, len(points))):
        x, y = _pop_random(points, rng)
        amount = _gold_amount(depth, rng)
        item = world_mod.make_item(x, y, world_mod.COIN_TILE, "gold",
                                   "%d gold" % amount, amount=amount)
        world.add_actor(item)
