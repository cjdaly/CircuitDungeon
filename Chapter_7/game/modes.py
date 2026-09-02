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
#   diag  - on-device diagnostics: INPUT + SYSTEM pages (cd-e3p.14, cd-89o.6)
#
# The two chord events from input.py, "menu" and "diag", toggle their overlay
# over play. ModeStack imports nothing hardware-side (displayio et al. are
# imported lazily inside the mode classes), so its routing is tested
# off-device in tests/test_modes.py.
#
# Governed by doc/ENGINE.md section 4.

import gc

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
    viewport with an actor layer, a status band (HP/depth/turn/gold —
    cd-oht.3), an icon rail (cd-oht.5, empty), and a message band (cd-e3p.9;
    scroll is cd-oht.4). doc/LAYOUT.md §1."""

    VOID_TILE = 2  # shown for viewport cells outside the level (wall-top)

    def __init__(self, display, world):
        import displayio
        import terminalio
        import util

        self.display = display
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
        # Load every sprite sheet up front, while the heap is clean and
        # unfragmented — the alternative (lazy-load in _sheet()) put the first
        # `objects.bmp` load in the middle of a fight and it OOM'd (cd-yl4).
        self._actor_sheets = {
            name: util.load_bitmap(name)
            for name in ("heroes", "creatures", "objects")
        }
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

        self.load_world(world)

    def load_world(self, world):
        """Point the scene at a World and (re)paint everything. Called once
        from __init__ and again on each level change (cd-e3p.10) — the
        displayio scene (viewport size, HUD groups) is reused, only the
        contents change."""
        self.world = world
        self.scheduler = world_mod.RoundRobinScheduler(world)
        self._msg_seq = -1          # last world.log.seq shown on the message line
        self._status_sig = None     # last (hp, max_hp, depth, turn, gold) painted
        self._recenter()
        self._sync_actor_sprites()
        self._paint_terrain()
        self._paint_status()
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
        """Match the sprite list to world.actors after a spawn/death. Rebuilds
        every sprite TileGrid, so defrag first — it runs only on a roster
        change, never per frame (cd-yl4)."""
        gc.collect()
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

    # -- status line (cd-oht.3) — HP / depth / turn / gold (LAYOUT.md §4) --

    _STATUS_CHARS = 39   # ~ (240 - 4) / 6 for terminalio

    def _paint_status(self):
        """Repaint the top band only when a shown value changed — Label text
        assignment rebuilds the glyph bitmap, so it's not free."""
        h = self.world.hero
        sig = (h.get("hp", 0), h.get("max_hp", 0), self.world.depth,
               self.world.turn, h.get("gold", 0))
        if sig == self._status_sig:
            return
        self._status_sig = sig
        self._status_label.text = (
            "HP %s/%s   Depth %s   Turn %s   Gold %s" % sig
        )[: self._STATUS_CHARS]

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
            self._paint_status()               # HP / turn / gold moved (cd-oht.3)
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


def _kib(n):
    """Bytes -> a short 'NNNk' string; '-' for None."""
    return "-" if n is None else "%dk" % (n // 1024)


def _round10(x):
    return int(x + 5) // 10 * 10


class DiagMode:
    """On-device diagnostics (bead cd-89o.6). Two pages; `CONFIRM` (A) cycles,
    `CANCEL` (B) or the X+Y chord exits:

      INPUT   per-chord effectiveness, held state, recent input trace
              (cd-e3p.14 — evaluate the wait-chord bindings on real hardware)
      SYSTEM  RAM (free / low-water / heap), flash, frame time, board + CP
              version, actor / turn / depth counts

    The always-on diagnostic event-log ring buffer is a follow-up (cd-89o.10).

    Assigning `Label.text` rebuilds the whole glyph bitmap and needs a ~2 KB
    contiguous block — which OOM'd mid-game (cd-yl4). So the label is rebuilt
    only when the rendered text actually changes (and at most every Nth
    render), with a gc.collect() right before the allocation."""

    PAGES = ("INPUT", "SYSTEM")

    def __init__(self, display, game_input, metrics=None, world=None):
        import displayio
        import terminalio
        import util

        self.display = display
        self.input = game_input
        self.metrics = metrics
        self.world = world
        self.group = displayio.Group()
        self._label = util.init_label(terminalio.FONT, 0x33FF33, x=2, y=6, text="")
        self.group.append(self._label)
        self._every = 4        # lower bound on renders between label rebuilds
        self._n = 0
        self._shown = None     # last text pushed to the label
        self._page = 0

    def tick(self, events, now):
        if im.CANCEL in events:
            return "exit"
        if im.CONFIRM in events:
            self._page = (self._page + 1) % len(self.PAGES)
            self._repaint()                       # page flip — new content now
        return None

    def render(self):
        self._n += 1
        if self._n % self._every == 0:
            self._repaint()

    def _repaint(self):
        txt = self._text()
        if txt == self._shown:
            return
        gc.collect()                              # defrag before the ~2 KB alloc
        self._label.text = txt
        self._shown = txt

    def _text(self):
        if self.PAGES[self._page] == "SYSTEM":
            return self._text_system()
        return self._text_input()

    def _text_input(self):
        inp = self.input
        lines = ["INPUT DIAG   A:page B:exit", "chord        fire miss sprd"]
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

    def _text_system(self):
        lines = ["SYSTEM DIAG  A:page B:exit"]
        m = self.metrics
        if m is None:
            lines.append("(no metrics)")
        else:
            lines.append("ram  free %-6s low %s" % (_kib(m.free), _kib(m.free_low)))
            lines.append("ram  used %-6s heap %s" % (_kib(m.alloc), _kib(m.heap)))
            lines.append("gc.collect %d ms  (n=%d)" % (m.collect_ms, m.ram_samples))
            ff, ft = m.flash()
            lines.append("flash free %s / %s" % (_kib(ff), _kib(ft)))
            ver, osname = m.environment()
            lines.append("cpy  %s  %s" % (ver, osname))
            # round to 10 ms so a jittering frame time doesn't force a rebuild
            lines.append("frame %d ms  max %d ms"
                         % (_round10(m.frame_ms), _round10(m.frame_ms_max)))
        lines.append("board  %s" % _board_id())
        w = self.world
        if w is not None:
            lines.append("actors %d  turn %d  depth %d"
                         % (len(w.actors), w.turn, w.depth))
        return "\n".join(lines)


def _board_id():
    try:
        import board
        return getattr(board, "board_id", "?")
    except ImportError:
        return "?"


def _first_action(events):
    """First play-mode action in `events`, or None. Non-action events
    (CONFIRM/CANCEL/AUX_*) belong to future beads (inventory, look) and pass
    no turn."""
    for ev in events:
        action = _EVENT_ACTION.get(ev)
        if action is not None:
            return action
    return None
