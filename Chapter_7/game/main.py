# SPDX-FileCopyrightText: 2026 Chris J Daly (github user cjdaly)
#
# SPDX-License-Identifier: MIT

import gc

import board
import hardware
import engine
import generator
import world as world_mod

# Fixed for now so a crash reproduces. Seed selection (menu / RTC / entropy)
# and depth progression belong to cd-89o.1 / cd-e3p.10.
RUN_SEED = 1

# Placeholder foes until cd-dsc.4 populates level["spawn_points"] from the
# spawn tables. (creatures.bmp tile, name, stats)
_PLACEHOLDER_MOBS = (
    (1, "rat", {"hp": 3, "power": 2, "defense": 0, "xp": 2}),
    (3, "bat", {"hp": 4, "power": 2, "defense": 0, "xp": 3}),
    (0, "slime", {"hp": 5, "power": 1, "defense": 0, "xp": 2}),
)


def _new_game(depth=1, start="up"):
    level = generator.generate(RUN_SEED, depth)
    world = world_mod.world_from_level(level, start=start)
    spawns = level["spawn_points"]
    for i, (tile, name, stats) in enumerate(_PLACEHOLDER_MOBS):
        if i >= len(spawns):
            break
        sx, sy = spawns[i]
        world.add_actor(world_mod.make_actor(
            sx, sy, "creatures", tile, name=name, ai="sleep", **stats))
    return world


def _restart():
    import supervisor
    supervisor.reload()


# --- smoke-test boot log (cd-89o.8): watch over serial `screen /dev/tty.usbmodem*`
gc.collect()
print("Ch7 boot   board=%s  free=%d" % (getattr(board, "board_id", "?"), gc.mem_free()))

display = hardware.detect()
if display.neopixel is not None:
    display.neopixel.fill((0, 3, 5))

world = _new_game(depth=1)
gc.collect()
print("Ch7 level  seed=%d depth=%d  free=%d" % (RUN_SEED, world.depth, gc.mem_free()))

game = engine.Game(display, world, restart=_restart, new_level=_new_game)
gc.collect()
print("Ch7 ready  free=%d  X+Y=diag  A+B=menu" % gc.mem_free())
game.run()
