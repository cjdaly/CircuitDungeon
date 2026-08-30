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

# Screen/mode dispatch (bead cd-e3p.12). The main loop owns one ModeStack; the
# stack decides which mode is on top, routes per-tick input events to it, and
# swaps `screen.root_group` when the top changes.
#
# v1 modes:
#   play  - the roguelike (PlayMode here; the turn loop is cd-e3p.3)
#   menu  - main menu / settings (stub; cd-e3p.13)
#   diag  - on-device diagnostics (stub; cd-89o.6)
#
# The two chord events from input.py, "menu" and "diag", toggle their overlay
# over play. ModeStack imports nothing hardware-side (displayio et al. are
# imported lazily inside the mode classes), so its routing is tested
# off-device in tests/test_modes.py.
#
# Governed by doc/ENGINE.md section 4.

import input as im

TILE = 16  # ART.md section 2

# input events that switch modes; consumed by the stack, never seen by a mode
_TOGGLE_EVENTS = ("menu", "diag")


class ModeStack:
    def __init__(self, base, overlays):
        # base: the always-present bottom mode (play)
        # overlays: {event_name: mode} for the toggle events ("menu", "diag")
        self._base = base
        self._overlays = overlays
        self._stack = [base]
        self._last_group = None

    @property
    def top(self):
        return self._stack[-1]

    @property
    def depth(self):
        return len(self._stack)

    def overlay_active(self):
        return self.top is not self._base

    def toggle(self, mode):
        """Chord pressed: if `mode` is already on top, drop back to base;
        otherwise show `mode` as the sole overlay over base (never stack two)."""
        if self.top is mode:
            self._stack = [self._base]
        else:
            self._stack = [self._base, mode]

    def handle(self, events, now):
        """Route this tick's input events. Toggle events ("menu"/"diag") switch
        modes and are consumed; everything else goes to the top mode's tick().
        A mode returning "exit" drops back to base — that's how a stub overlay
        leaves on CANCEL. Entering/leaving an overlay never ticks `play`, so no
        game turn passes (ENGINE.md 1.1)."""
        passthrough = []
        for ev in events:
            if ev in _TOGGLE_EVENTS and ev in self._overlays:
                self.toggle(self._overlays[ev])
            else:
                passthrough.append(ev)
        if self.top.tick(passthrough, now) == "exit":
            self._stack = [self._base]

    def render(self, screen):
        self.top.render()
        group = self.top.group
        if group is not self._last_group:
            screen.root_group = group
            self._last_group = group


# --------------------------------------------------------------------------


class PlayMode:
    """The roguelike itself: the terrain grid + actor sprites + (eventually,
    cd-e3p.3) the turn loop. Owns the world-scene displayio group."""

    def __init__(self, display, world):
        import displayio
        import util
        import world as world_mod

        self.display = display
        self.world = world
        self.scheduler = world_mod.RoundRobinScheduler(world)
        self.cycle = 0  # presentation pulse (wall-clock); NOT world.turn

        self.group = displayio.Group()
        # TODO(cd-oht.2): partition into status / map / inventory bands
        # (geometry from cd-oht.1). For now the world fills the screen.
        world_group = displayio.Group()
        self.group.append(world_group)
        self._world_group = world_group
        display.groups["world"] = world_group
        display.groups["root"] = self.group

        self._terrain_bmp, self._terrain_pal = util.load_bitmap("terrain")
        terrain = util.tilegrid(
            self._terrain_bmp, self._terrain_pal,
            world.width, world.height, TILE, TILE,
        )
        display.grids["terrain"] = terrain
        world_group.append(terrain)
        self._paint_terrain()

        self._util = util
        self._actor_sheets = {}
        self._actor_sprites = []
        self._sync_actor_sprites()

    # -- scene ------------------------------------------------------

    def _paint_terrain(self):
        terrain = self.display.grids["terrain"]
        grid = self.world.grid
        for y in range(self.world.height):
            row = grid[y]
            for x in range(self.world.width):
                terrain[x, y] = row[x]

    def _sheet(self, name):
        pair = self._actor_sheets.get(name)
        if pair is None:
            pair = self._util.load_bitmap(name)
            self._actor_sheets[name] = pair
        return pair

    def _sync_actor_sprites(self):
        """Match the sprite list to world.actors after a spawn/death."""
        for spr in self._actor_sprites:
            self._world_group.remove(spr)
        self._actor_sprites = []
        for actor in self.world.actors:
            bmp, pal = self._sheet(actor["sheet"])
            spr = self._util.tilegrid(bmp, pal, 1, 1, TILE, TILE, transparent=0)
            spr[0, 0] = actor["tile"]
            self._world_group.append(spr)
            self._actor_sprites.append(spr)
        self.display.sprites["actors"] = self._actor_sprites

    # -- per-tick -------------------------------------------------

    def tick(self, events, now):
        # TODO(cd-e3p.3): consume one actionable event -> self._resolve_turn().
        # Until the turn loop exists, movement events are ignored and the world
        # is static. The pulse still advances so idle animation has a clock
        # (ENGINE.md 1.5).
        self.cycle += 1
        return None

    def render(self):
        for actor, spr in zip(self.world.actors, self._actor_sprites):
            spr.x = actor["x"] * TILE
            spr.y = actor["y"] * TILE
            spr[0, 0] = actor["tile"]

    def _resolve_turn(self, action):
        """One turn per ENGINE.md 1.1 — the turn loop is bead cd-e3p.3."""
        raise NotImplementedError("turn loop: cd-e3p.3")


class _StubOverlay:
    """Placeholder for MenuMode / DiagMode — a centred label so the mode
    switch is visible and testable before cd-e3p.13 / cd-89o.6 build them."""

    def __init__(self, display, title):
        import displayio
        import terminalio
        import util

        self.display = display
        self.group = displayio.Group()
        screen = display.screen
        lbl = util.init_label(
            terminalio.FONT, 0xFFFFFF, text=title + "\n(CANCEL / chord to exit)"
        )
        lbl.anchor_point = (0.5, 0.5)
        lbl.anchored_position = (screen.width // 2, screen.height // 2)
        self.group.append(lbl)

    def tick(self, events, now):
        if im.CANCEL in events:
            return "exit"
        return None

    def render(self):
        pass


def MenuMode(display):
    return _StubOverlay(display, "MENU")   # cd-e3p.13


def DiagMode(display):
    return _StubOverlay(display, "DIAG")   # cd-89o.6
