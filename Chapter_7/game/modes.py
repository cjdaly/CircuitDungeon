# SPDX-FileCopyrightText: 2026 Chris J Daly (github user cjdaly)
#
# SPDX-License-Identifier: MIT

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

import ai
import input as im
import world as world_mod

# doc/LAYOUT.md — Option G, 240×240 PicoSystem
TILE = 16
MAP_TILES = 13                 # odd → hero on the exact centre tile
MAP_PX = MAP_TILES * TILE       # 208 — map viewport is 208×208
BAND_H = TILE                   # 16 — one terminalio line, top and bottom

# input events that switch modes; consumed by the stack, never seen by a mode
_TOGGLE_EVENTS = ("menu", "diag")

# play-mode input event -> turn action (world.resolve_turn). 4-way only.
_EVENT_ACTION = {
    im.MOVE_N: ("move",) + world_mod.MOVE_DELTAS["n"],
    im.MOVE_S: ("move",) + world_mod.MOVE_DELTAS["s"],
    im.MOVE_W: ("move",) + world_mod.MOVE_DELTAS["w"],
    im.MOVE_E: ("move",) + world_mod.MOVE_DELTAS["e"],
    "wait": ("wait",),   # the DOWN+B chord (cd-e3p.15)
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

    def show(self, mode):
        """Force `mode` over base — for game-over and other non-chord overlays.
        Not dismissed by chords or a tick() "exit"; the mode itself decides
        when to leave (e.g. calling a restart)."""
        if self.top is not mode:
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
    """The roguelike itself. Owns the Option-G scene: a 13×13 terrain
    viewport with an actor layer, a status band, an icon rail, and a message
    band (doc/LAYOUT.md §1). Child beads render into the HUD groups:
    cd-oht.3 status, cd-oht.4 message, cd-oht.5 rail, cd-oht.6 map polish."""

    VOID_TILE = 2  # shown for viewport cells outside the level (wall-top)

    def __init__(self, display, world):
        import displayio
        import terminalio
        import util

        self.display = display
        self.world = world
        self.scheduler = world_mod.RoundRobinScheduler(world)
        self.cycle = 0            # presentation pulse (wall-clock); NOT world.turn
        self.cam_x = 0
        self.cam_y = 0
        self._util = util

        screen = display.screen
        rail_w = screen.width - MAP_PX          # 32 on a 240-wide screen
        msg_y = BAND_H + MAP_PX                 # 224

        self.group = displayio.Group()

        # --- map viewport: a MAP_TILES-square terrain grid + actor layer ---
        self._map_group = displayio.Group(x=0, y=BAND_H)
        self._terrain_bmp, self._terrain_pal = util.load_bitmap("terrain")
        self._terrain = util.tilegrid(
            self._terrain_bmp, self._terrain_pal,
            MAP_TILES, MAP_TILES, TILE, TILE,
        )
        self._map_group.append(self._terrain)
        self._actor_sheets = {}
        self._actor_sprites = []                # parallel to world.actors
        self.group.append(self._map_group)

        # --- HUD region groups — content is the child beads' job ---
        self.status_group = displayio.Group(x=0, y=0)
        self.rail_group = displayio.Group(x=MAP_PX, y=BAND_H)
        self.message_group = displayio.Group(x=0, y=msg_y)
        self._status_label = util.init_label(terminalio.FONT, 0xC8E0FF, x=2, text="")
        self._message_label = util.init_label(terminalio.FONT, 0xC8E0FF, x=2, text="")
        for lbl in (self._status_label, self._message_label):
            lbl.anchor_point = (0.0, 0.5)
            lbl.anchored_position = (2, BAND_H // 2)
        self.status_group.append(self._status_label)
        self.message_group.append(self._message_label)
        self.group.append(self.status_group)
        self.group.append(self.rail_group)
        self.group.append(self.message_group)

        # for the child beads / debugging
        display.groups["root"] = self.group
        display.grids["terrain"] = self._terrain
        self._rail_w = rail_w
        self._msg_seq = -1          # last world.log.seq shown on the message line

        self._recenter()
        self._sync_actor_sprites()
        self._paint_terrain()
        self._paint_message()
        self._render()

    # -- camera + terrain viewport (LAYOUT.md §3) ------------------

    def _recenter(self):
        hero = self.world.hero
        self.cam_x, self.cam_y = world_mod.camera_for(
            hero["x"], hero["y"], MAP_TILES, self.world.width, self.world.height
        )

    def _paint_terrain(self):
        g = self.world.grid
        w, h = self.world.width, self.world.height
        for row in range(MAP_TILES):
            wy = self.cam_y + row
            in_y = 0 <= wy < h
            for col in range(MAP_TILES):
                wx = self.cam_x + col
                if in_y and 0 <= wx < w:
                    self._terrain[col, row] = g[wy][wx]
                else:
                    self._terrain[col, row] = self.VOID_TILE

    # -- actor sprites (presentation half of ENGINE.md 1.4) --------

    def _sheet(self, name):
        pair = self._actor_sheets.get(name)
        if pair is None:
            pair = self._util.load_bitmap(name)
            self._actor_sheets[name] = pair
        return pair

    def _sync_actor_sprites(self):
        """Match the sprite list to world.actors after a spawn/death."""
        for spr in self._actor_sprites:
            self._map_group.remove(spr)
        self._actor_sprites = []
        for actor in self.world.actors:
            bmp, pal = self._sheet(actor["sheet"])
            spr = self._util.tilegrid(bmp, pal, 1, 1, TILE, TILE, transparent=0)
            spr[0, 0] = actor["tile"]
            self._map_group.append(spr)
            self._actor_sprites.append(spr)
        self.display.sprites["actors"] = self._actor_sprites
        self._synced_roster = self.world.roster_version

    def _render(self):
        for actor, spr in zip(self.world.actors, self._actor_sprites):
            vx = actor["x"] - self.cam_x
            vy = actor["y"] - self.cam_y
            if 0 <= vx < MAP_TILES and 0 <= vy < MAP_TILES:
                spr.hidden = False
                spr.x = vx * TILE
                spr.y = vy * TILE
                spr[0, 0] = actor["tile"]
            else:
                spr.hidden = True

    # -- message line (cd-e3p.9; cd-oht.4 adds scroll / a longer history) --

    _MSG_CHARS = 39   # ~ (240 - 4) / 6 for terminalio

    def _paint_message(self):
        if self.world.log.seq != self._msg_seq:
            self._message_label.text = self.world.log.latest()[: self._MSG_CHARS]
            self._msg_seq = self.world.log.seq

    # -- mode interface -------------------------------------------

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
            if self.world.roster_version != self._synced_roster:
                self._sync_actor_sprites()     # a monster died / spawned (cd-e3p.5)
            self._paint_message()              # combat / event text (cd-e3p.9)
        cam = (self.cam_x, self.cam_y)
        self._recenter()
        if (self.cam_x, self.cam_y) != cam:
            self._paint_terrain()
        return None

    def _monster_turn(self, world, actor):
        ai.take_turn(world, actor)

    def render(self):
        self._render()


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


class GameOverMode:
    """Shown by ModeStack.show() when the hero dies (ENGINE.md §9). CONFIRM
    calls `restart` — `supervisor.reload()` on device, a test hook off it."""

    def __init__(self, display, restart):
        import displayio
        import terminalio
        import util

        self.display = display
        self._restart = restart
        self.group = displayio.Group()
        screen = display.screen
        lbl = util.init_label(
            terminalio.FONT, 0xFF5555, text="YOU DIED\n\npress A to try again"
        )
        lbl.anchor_point = (0.5, 0.5)
        lbl.anchored_position = (screen.width // 2, screen.height // 2)
        self.group.append(lbl)

    def tick(self, events, now):
        if im.CONFIRM in events:
            self._restart()
        return None

    def render(self):
        pass


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
