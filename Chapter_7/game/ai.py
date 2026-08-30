# SPDX-FileCopyrightText: 2026 Chris J Daly (github user cjdaly)
#
# SPDX-License-Identifier: MIT

# Per-monster AI for the turn loop (bead cd-e3p.4). Pure: `world.resolve_turn`
# calls take_turn(world, actor) for each monster once per turn. Monsters are
# plain dicts (world.py); take_turn adds and reads:
#   actor["ai"]   - "sleep" | "hunt"      (defaults to "sleep")
#   actor["goal"] - (x, y) last-known hero tile, while hunting
#
# Two behaviours, 4-way (ENGINE.md §1.3):
#   sleep - idle; a small chance to wander one tile; wakes to "hunt" on
#           line-of-sight to the hero within SIGHT
#   hunt  - step greedily toward the last-known hero tile; drop back to
#           "sleep" on reaching it without seeing the hero
#
# RNG: the module `random` stream, continuing after level generation
# (LEVELGEN.md §6) — deterministic given the run seed + call order.
#
# Governed by doc/ENGINE.md §6.

import random

import world as world_mod

SIGHT = 8              # Chebyshev tiles a monster can spot the hero at
WANDER_CHANCE = 0.12   # per idle turn; set to 0 in tests for determinism

_STEPS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def take_turn(world, actor):
    hero = world.hero
    if hero is None:
        return
    seen = _can_see(world, actor, hero)

    if actor.get("ai", "sleep") == "sleep":
        if seen:
            actor["ai"] = "hunt"
            actor["goal"] = (hero["x"], hero["y"])
        elif random.random() < WANDER_CHANCE:
            _wander(world, actor)
        return

    # hunting
    if seen:
        actor["goal"] = (hero["x"], hero["y"])
    goal = actor.get("goal")
    if goal is None or (actor["x"], actor["y"]) == goal:
        actor["ai"] = "sleep"          # lost the trail at the last-known tile
        actor["goal"] = None
        return
    _step_toward(world, actor, goal[0], goal[1])


# -- perception -----------------------------------------------------


def _can_see(world, actor, hero):
    dx = hero["x"] - actor["x"]
    dy = hero["y"] - actor["y"]
    if max(abs(dx), abs(dy)) > SIGHT:
        return False
    return world_mod.los_clear(world, actor["x"], actor["y"], hero["x"], hero["y"])


# -- movement -----------------------------------------------------


def _step_toward(world, actor, gx, gy):
    """One greedy 4-way step toward (gx, gy): the axis with the larger
    remaining delta first, the other axis as a fallback if blocked. Bumping
    the hero is an attack (cd-e3p.5)."""
    dx = gx - actor["x"]
    dy = gy - actor["y"]
    prefer_x = abs(dx) >= abs(dy)
    tries = []
    if dx:
        tries.append((1 if dx > 0 else -1, 0))
    if dy:
        tries.append((0, 1 if dy > 0 else -1))
    if not prefer_x:
        tries.reverse()
    for step in tries:
        result = world.move_actor(actor, step[0], step[1])
        if result == "moved":
            return
        if isinstance(result, tuple) and result[0] == "bump" and result[1] is world.hero:
            world_mod.resolve_attack(world, actor, world.hero)
            return
        # "blocked" or bumped another actor -> try the other axis


def _shuffled(seq):
    """Fisher-Yates. CircuitPython's `random` has no shuffle()/sample() —
    only random / randint / randrange / uniform / choice / getrandbits / seed."""
    out = list(seq)
    for i in range(len(out) - 1, 0, -1):
        j = random.randint(0, i)
        out[i], out[j] = out[j], out[i]
    return out


def _wander(world, actor):
    for dx, dy in _shuffled(_STEPS):
        if world.move_actor(actor, dx, dy) == "moved":
            return
