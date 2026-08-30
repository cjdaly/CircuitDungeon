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

import hardware
import engine
import world as world_mod

# Terrain tile indices — see game/tiles/tiles.json.
FLOOR = 0
WALL = 2

# TODO(cd-dsc): the procedural generator replaces this. Until it exists, a
# plain walled room so the forked engine has something to draw and cd-e3p.3
# has a board to move on. 15x15 fills the 240x240 PicoSystem screen.
_ROOM_W, _ROOM_H = 15, 15


def _test_room():
    grid = []
    for y in range(_ROOM_H):
        row = bytearray(FLOOR for _ in range(_ROOM_W))
        for x in range(_ROOM_W):
            if x == 0 or x == _ROOM_W - 1 or y == 0 or y == _ROOM_H - 1:
                row[x] = WALL
        grid.append(row)
    world = world_mod.World(grid, wall_tiles=(WALL,))
    world.add_actor(world_mod.make_actor(_ROOM_W // 2, _ROOM_H // 2, "heroes", 0))
    world.add_actor(world_mod.make_actor(3, 3, "creatures", 1))  # a rat, to prove the sprite path
    return world


display = hardware.detect()
if display.neopixel is not None:
    display.neopixel.fill((0, 3, 5))

game = engine.Game(display, _test_room())
game.run()
