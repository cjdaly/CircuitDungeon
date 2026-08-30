# SPDX-FileCopyrightText: 2026 Chris J Daly (github user cjdaly)
#
# SPDX-License-Identifier: MIT

import gc

import board
import hardware
import engine
import world as world_mod

# Terrain tile indices — see game/tiles/tiles.json.
FLOOR, FLAGSTONE, WALL, WATER, STAIRS_DOWN, STAIRS_UP = 0, 1, 2, 3, 4, 5

# TODO(cd-dsc): the procedural generator replaces this. Until it exists, a
# walled room bigger than the 13×13 viewport so the camera actually scrolls,
# with an interior cross so the scroll is visible. Roughly a quarter of a real
# 64×64 level.
_W, _H = 28, 28


def _test_room():
    grid = []
    for y in range(_H):
        row = bytearray(FLAGSTONE for _ in range(_W))
        for x in range(_W):
            edge = x in (0, _W - 1) or y in (0, _H - 1)
            cross = x in (_W // 2, _W // 2 + 1) and 4 < y < _H - 5
            cross |= y in (_H // 2, _H // 2 + 1) and 4 < x < _W - 5
            if edge or cross:
                row[x] = WALL
        grid.append(row)
    grid[_H // 2 - 3][_W // 2 - 3] = STAIRS_UP     # under the hero's start
    grid[3][_W - 4] = STAIRS_DOWN
    grid[_H - 4][3] = WATER

    world = world_mod.World(grid, wall_tiles=(WALL,), depth=1)
    world.add_actor(world_mod.make_hero(_W // 2 - 3, _H // 2 - 3))
    # same quadrant as the hero -> line of sight -> wakes and chases (cd-e3p.4)
    world.add_actor(world_mod.make_actor(4, 4, "creatures", 1, name="rat",
                                        ai="sleep", hp=3, power=2, defense=0, xp=2))
    # far bottom-right quadrant, no LoS -> idles / wanders
    world.add_actor(world_mod.make_actor(_W - 4, _H - 4, "creatures", 2, name="bat",
                                        ai="sleep", hp=4, power=2, defense=0, xp=3))
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

game = engine.Game(display, _test_room(), restart=_restart)
gc.collect()
print("Ch7 ready  free=%d  X+Y=diag  A+B=menu" % gc.mem_free())
game.run()
