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

# Chapter 7 engine — forked from Chapter_6/game/engine.py and stripped to a
# turn-based skeleton (bead cd-e3p.2). Gone from the Ch6 version: the 2px
# real-time movement, the fixed-rate frame loop with time.sleep pacing tied
# to movement speed, explosion pool + chain reactions, HUD scroll animation,
# the .lvl exit/event trigger system, and pixel-scroll camera.
#
# What this file owns: the displayio scene (terrain grid + actor sprites) and
# the non-blocking main loop. All game state and rules live in world.py.
# The turn loop itself is the next bead (cd-e3p.3); see _resolve_turn().
#
# Governed by doc/ENGINE.md.

import time

import displayio

import util
import world as world_mod

TILE = 16  # ART.md section 2: one 16x16 grid for terrain, objects, creatures, heroes

# doc/ENGINE.md section 1.5: the loop runs at a modest fixed tick so idle
# animation and button auto-repeat have a clock while we wait for input. This
# is an upper bound on tick rate, not a guarantee — a slow refresh() just
# runs at its own pace. It does NOT pace movement (that's one tile per turn,
# turns only advance on input), unlike Ch6's TARGET_TICK_SECONDS.
TICK_SECONDS = 1 / 20


class Game:
    def __init__(self, display, world):
        self.display = display          # a hardware.GameDisplay
        self.world = world              # a world.World
        self.scheduler = world_mod.RoundRobinScheduler(world)
        self.cycle = 0                  # presentation pulse (wall-clock); NOT world.turn

        screen = display.screen

        # TODO(cd-oht.2): partition the screen into status / map viewport /
        # inventory bands per cd-oht.1. For now the world group fills the
        # screen and the map shows from (0,0).
        world_group = displayio.Group()
        root = displayio.Group()
        root.append(world_group)
        display.groups["world"] = world_group
        display.groups["root"] = root

        # terrain grid, one TileGrid sized to the whole world
        self._terrain_bmp, self._terrain_pal = util.load_bitmap("terrain")
        terrain = util.tilegrid(
            self._terrain_bmp, self._terrain_pal,
            world.width, world.height, TILE, TILE,
        )
        display.grids["terrain"] = terrain
        world_group.append(terrain)
        self._paint_terrain()

        # actor sprites: one 1x1 TileGrid per actor, index-aligned with
        # world.actors. Rebuilt by _sync_actor_sprites() when the roster
        # changes (monsters spawned by the generator / dying in combat).
        self._actor_sheets = {}         # sheet name -> (bmp, pal)
        self._actor_sprites = []        # parallel to world.actors
        self._sync_actor_sprites()

        screen.root_group = display.groups["root"]
        screen.auto_refresh = False

    # -- terrain --------------------------------------------------------

    def _paint_terrain(self):
        terrain = self.display.grids["terrain"]
        grid = self.world.grid
        for y in range(self.world.height):
            row = grid[y]
            for x in range(self.world.width):
                terrain[x, y] = row[x]

    # -- actor sprites (the presentation half of ENGINE.md 1.4) --------

    def _sheet(self, name):
        pair = self._actor_sheets.get(name)
        if pair is None:
            pair = util.load_bitmap(name)
            self._actor_sheets[name] = pair
        return pair

    def _sync_actor_sprites(self):
        """Make the sprite list match world.actors. Cheap to call after a
        spawn or death; a no-op cost when the roster is unchanged."""
        world_group = self.display.groups["world"]
        for spr in self._actor_sprites:
            world_group.remove(spr)
        self._actor_sprites = []
        for actor in self.world.actors:
            bmp, pal = self._sheet(actor["sheet"])
            spr = util.tilegrid(bmp, pal, 1, 1, TILE, TILE, transparent=0)
            spr[0, 0] = actor["tile"]
            world_group.append(spr)
            self._actor_sprites.append(spr)
        self.display.sprites["actors"] = self._actor_sprites
        self._render_actors()

    def _render_actors(self):
        for actor, spr in zip(self.world.actors, self._actor_sprites):
            spr.x = actor["x"] * TILE
            spr.y = actor["y"] * TILE
            spr[0, 0] = actor["tile"]

    # -- animation pulse ----------------------------------------------

    def _pulse(self):
        """Advance presentation-only animation (idle wobble, torch flicker,
        HUD scroll). Runs every tick, independent of turns (ENGINE.md 1.5).
        Nothing animates yet — the placeholder sheets are one frame each."""
        self.cycle += 1

    # -- turn resolution (cd-e3p.3) ----------------------------------

    def _resolve_turn(self, action):
        """One turn, per ENGINE.md 1.1:

            applied = apply `action` to self.world.hero
            if not applied:
                return                       # free / failed action, no turn
            for actor in self.scheduler.actors_for_turn():
                if actor is self.world.hero:
                    continue
                monster_take_turn(self.world, actor)   # cd-e3p.4
            self._upkeep()                              # status ticks, regen
            self.world.turn += 1

        Left unimplemented here on purpose — the turn loop is bead cd-e3p.3,
        which also needs the button input model (cd-e3p.11) to turn a button
        event into an `action`.
        """
        raise NotImplementedError("turn loop: cd-e3p.3")

    # -- main loop (ENGINE.md 1.5) ----------------------------------

    def run(self):
        screen = self.display.screen
        while True:
            t0 = time.monotonic()

            # TODO(cd-e3p.11 + cd-e3p.3): read the input model for at most one
            # actionable event, and if there is one:
            #     self._resolve_turn(event.action)
            #     self._render_actors()
            # Until then the skeleton just renders a static world and pulses.

            self._pulse()
            self._render_actors()
            screen.refresh()

            slack = TICK_SECONDS - (time.monotonic() - t0)
            if slack > 0:
                time.sleep(slack)
