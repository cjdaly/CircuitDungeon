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
import world as world_mod

TILE = 16  # ART.md section 2

# input events that switch modes; consumed by the stack, never seen by a mode
_TOGGLE_EVENTS = ("menu", "diag")

# play-mode input event -> turn action (world.resolve_turn). 4-way only.
_EVENT_ACTION = {
    im.MOVE_N: ("move",) + world_mod.MOVE_DELTAS["n"],
    im.MOVE_S: ("move",) + world_mod.MOVE_DELTAS["s"],
    im.MOVE_W: ("move",) + world_mod.MOVE_DELTAS["w"],
    im.MOVE_E: ("move",) + world_mod.MOVE_DELTAS["e"],
    "wait": ("wait",),   # LEFT+RIGHT / UP+DOWN / DOWN+B chords (cd-e3p.14)
}


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
        # doc/ENGINE.md 1.5: at most one actionable event -> one turn. Extra
        # events this tick are dropped (auto-repeat is already rate-capped in
        # input.py, so >1 move in a single ~50ms tick is nearly impossible).
        self.cycle += 1                        # presentation pulse (ENGINE.md 1.5)
        action = _first_action(events)
        if action is not None:
            world_mod.resolve_turn(
                self.world, self.scheduler, action, self._monster_turn
            )
        return None

    def _monster_turn(self, world, actor):
        pass  # per-monster AI: bead cd-e3p.4

    def render(self):
        # presentation half of ENGINE.md 1.4 — instant snap, no interpolation
        for actor, spr in zip(self.world.actors, self._actor_sprites):
            spr.x = actor["x"] * TILE
            spr.y = actor["y"] * TILE
            spr[0, 0] = actor["tile"]


class _StubOverlay:
    """Placeholder overlay — a centred label so the mode switch is visible and
    testable before the real screen (cd-e3p.13) is built."""

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


class DiagMode:
    """On-device diagnostics. v1 shows the input page only: per-chord
    effectiveness, held state, and the recent input trace — so the wait-chord
    bindings (cd-e3p.14) can be evaluated on real hardware. RAM/flash/timing
    pages and page-switching are cd-89o.6."""

    def __init__(self, display, game_input):
        import displayio
        import terminalio
        import util

        self.display = display
        self.input = game_input
        self.group = displayio.Group()
        self._label = util.init_label(terminalio.FONT, 0x33FF33, x=2, y=6, text="")
        self.group.append(self._label)
        self._every = 3        # refresh the text every N ticks (Label churn is costly)
        self._n = 0

    def tick(self, events, now):
        if im.CANCEL in events:
            return "exit"
        return None

    def render(self):
        self._n += 1
        if self._n % self._every:
            return
        self._label.text = self._text()

    def _text(self):
        inp = self.input
        lines = ["INPUT DIAG   X+Y exits", "chord        fire miss sprd"]
        for row in inp.chord_stats():
            spread = row["last_spread_ms"]
            lines.append(
                "%-12s %4d %4d %4s"
                % (row["combo"], row["fired"], row["missed"],
                   "-" if spread is None else spread)
            )
        snap = inp.snapshot()
        held = " ".join(snap["held"]) or "-"
        lines.append("held: " + held)
        if snap["chord_candidates"]:
            lines.append("forming: " + " ".join(snap["chord_candidates"]))
        lines.append("--- trace (newest last) ---")
        for t_ms, kind, detail in inp.trace()[-6:]:
            lines.append("%7d %-7s %s" % (t_ms, kind, detail if detail else ""))
        return "\n".join(lines)


def _first_action(events):
    """First play-mode action in `events`, or None. Non-action events
    (CONFIRM/CANCEL/AUX_*) belong to future beads (inventory, look) and pass
    no turn."""
    for ev in events:
        action = _EVENT_ACTION.get(ev)
        if action is not None:
            return action
    return None
