# SPDX-FileCopyrightText: 2026 Chris J Daly (github user cjdaly)
#
# SPDX-License-Identifier: MIT

# Screen/mode dispatch (bead cd-e3p.12). The main loop owns one ModeStack; the
# stack decides which mode is on top, routes per-tick input events to it, and
# swaps `screen.root_group` when the top changes.
#
# v1 modes:
#   play  - the roguelike (PlayMode here; the turn loop is cd-e3p.3)
#   diag  - on-device diagnostics: RAM + input, one screen (cd-89o.6)
#   menu  - main menu / settings — not built yet (cd-e3p.13); the stack still
#           supports N overlays, engine.Game just wires one for now
#
# A chord event from input.py ("diag", later "menu") toggles its overlay over
# play. ModeStack imports nothing hardware-side (displayio et al. are imported
# lazily inside the mode classes), so its routing is tested off-device in
# tests/test_modes.py (which still exercises a two-overlay stack).
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

# input events that switch modes; consumed by the stack, never seen by a mode.
# "menu" stays listed so it's a no-op (not a stray play action) if a binding
# ever emits it before cd-e3p.13 wires the overlay.
_TOGGLE_EVENTS = ("menu", "diag")

# play-mode input event -> turn action (world.resolve_turn). 4-way only.
_EVENT_ACTION = {
    im.MOVE_N: ("move",) + world_mod.MOVE_DELTAS["n"],
    im.MOVE_S: ("move",) + world_mod.MOVE_DELTAS["s"],
    im.MOVE_W: ("move",) + world_mod.MOVE_DELTAS["w"],
    im.MOVE_E: ("move",) + world_mod.MOVE_DELTAS["e"],
    "wait": ("wait",),   # the DOWN+B chord (cd-e3p.15)
    im.AUX_X: ("use",),  # X alone — use the first usable inventory item (cd-e3p.8)
    # AUX_Y (Y alone) is unbound — weapon/armor auto-equip on pickup now
    # (cd-dsc.4), there's no "equip" action left to trigger.
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
            # Optional lifecycle hook, fired once on entry only (not on every
            # render, not on the way back out to base) -- DiagMode uses this
            # to print its screen to serial, so it can be captured without
            # reading the physical display (cd-dsc.6 follow-up).
            on_enter = getattr(mode, "on_enter", None)
            if on_enter is not None:
                on_enter()

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

    VOID_TILE = 6  # terrain.bmp's solid "void" tile (cd-e17.5) — drawn for
                   # cells off the level *and* for never-seen cells (fog of
                   # war, cd-oht.6): the dungeon reads as solid rock until
                   # the hero's FOV reveals it. Was 2 (wall-top, reused as a
                   # placeholder) before cd-e17.5 added a real void tile.
    DIM_OFFSET = 8  # terrain.bmp's second row is a darkened copy of row one
                    # (cd-e17.5) — add this to a base tile index to get its
                    # "remembered but not currently visible" variant.

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

        # --- icon rail (cd-oht.5): sword + armor level, always-visible
        # minimal-inventory readout (ENGINE.md §10.1) — no selection UI needed,
        # equip is automatic on pickup, so this is just two icons + numbers.
        objects_bmp, objects_pal = self._actor_sheets["objects"]
        icon_x = (rail_w - TILE) // 2   # centre the 16px icon in the 32px rail
        # A gap below the status band: flush against y=0 read as glued to
        # "Gold 0" on the status line right above it (Chris, 2026-09-14).
        rail_top = 12
        # A bordered box behind each icon+number pair — without one, the
        # numbers read as floating loose next to the icons instead of
        # belonging to them (Chris, 2026-09-14). box_h=38 was 30 — the first
        # pass clipped the bottom of the label glyphs (Chris, 2026-09-14).
        box_x, box_w, box_h, box_gap = 2, rail_w - 4, 38, 4
        block_h = box_h + box_gap   # box + breathing room to the next block
        sword_y = rail_top
        armor_y = rail_top + block_h

        for by in (sword_y - 2, armor_y - 2):
            self.rail_group.append(util.solid_rect(box_w, box_h, 0x3A4A70, x=box_x, y=by))
            self.rail_group.append(
                util.solid_rect(box_w - 2, box_h - 2, 0x14203A, x=box_x + 1, y=by + 1)
            )

        self._sword_icon = util.tilegrid(
            objects_bmp, objects_pal, 1, 1, TILE, TILE, x=icon_x, y=sword_y, transparent=0
        )
        self._sword_icon[0, 0] = world_mod.SWORD_TILE
        self._armor_icon = util.tilegrid(
            objects_bmp, objects_pal, 1, 1, TILE, TILE, x=icon_x, y=armor_y, transparent=0
        )
        self._armor_icon[0, 0] = world_mod.ARMOR_TILE
        self._sword_label = util.init_label(terminalio.FONT, 0xC8E0FF, text="")
        self._armor_label = util.init_label(terminalio.FONT, 0xC8E0FF, text="")
        for lbl, y in ((self._sword_label, sword_y + TILE + 2),
                       (self._armor_label, armor_y + TILE + 2)):
            lbl.anchor_point = (0.5, 0.0)
            lbl.anchored_position = (rail_w // 2, y)
        self.rail_group.append(self._sword_icon)
        self.rail_group.append(self._sword_label)
        self.rail_group.append(self._armor_icon)
        self.rail_group.append(self._armor_label)
        self._rail_sig = None

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
        world.refresh_fov()         # seed FOV before the first paint (cd-oht.6)
        self._recenter()
        self._sync_actor_sprites()
        self._paint_terrain()
        self._paint_status()
        self._paint_rail()
        self._paint_message()
        self._render()

    # -- camera + terrain viewport (LAYOUT.md §3) ------------------

    def _recenter(self):
        hero = self.world.hero
        self.cam_x, self.cam_y = world_mod.camera_for(
            hero["x"], hero["y"], MAP_TILES, self.world.width, self.world.height
        )

    def _paint_terrain(self):
        """Repaint the 13×13 terrain window. Fog of war (cd-oht.6, dim tiles
        cd-e17.5): a cell in the hero's current FOV (`world.is_visible`)
        draws as its real tile; one only ever explored draws at `+
        DIM_OFFSET` (the terrain sheet's darkened second row); a cell never
        seen is `VOID_TILE`.

        Runs every turn (FOV moves), so it uses a flat `tg[i]` index — the
        `tg[col, row]` form builds a throwaway tuple per cell, 169 per turn,
        and that churn fragments the heap on a non-compacting GC (cd-dsc.6)."""
        wd = self.world
        g = wd.grid
        w, h = wd.width, wd.height
        visible = wd.is_visible
        explored = wd.is_explored
        tg = self._terrain
        void = self.VOID_TILE
        dim = self.DIM_OFFSET
        i = 0
        for row in range(MAP_TILES):
            wy = self.cam_y + row
            in_y = 0 <= wy < h
            for col in range(MAP_TILES):
                wx = self.cam_x + col
                if in_y and 0 <= wx < w:
                    if visible(wx, wy):
                        tg[i] = g[wy][wx]
                    elif explored(wx, wy):
                        tg[i] = g[wy][wx] + dim
                    else:
                        tg[i] = void
                else:
                    tg[i] = void
                i += 1

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
        wd = self.world
        for actor, spr in zip(wd.actors, self._actor_sprites):
            vx = actor["x"] - self.cam_x
            vy = actor["y"] - self.cam_y
            if (0 <= vx < MAP_TILES and 0 <= vy < MAP_TILES
                    and wd.is_visible(actor["x"], actor["y"])):
                spr.hidden = False          # hide anything outside the hero's FOV
                spr.x = vx * TILE
                spr.y = vy * TILE
                spr[0, 0] = actor["tile"]
            else:
                spr.hidden = True

    # -- status line (cd-oht.3) — HP / depth / turn / gold (LAYOUT.md §4) --

    _STATUS_CHARS = 39   # ~ (240 - 4) / 6 for terminalio

    def _paint_status(self):
        """Repaint the top band only when a shown value changed. The turn
        counter moves every turn, so the format is **fixed-width** — a
        constant bounding box lets bitmap_label rewrite in place instead of
        reallocating its Bitmap (cd-yl4)."""
        h = self.world.hero
        sig = (h.get("hp", 0), h.get("max_hp", 0), self.world.depth,
               self.world.turn, h.get("gold", 0))
        if sig == self._status_sig:
            return
        self._status_sig = sig
        self._status_label.text = (
            "HP %2d/%-2d Dep %2d  Turn %5d  Gold %4d" % sig
        )[: self._STATUS_CHARS]

    # -- icon rail (cd-oht.5) — sword/armor level, ENGINE.md §10.1 ----

    def _paint_rail(self):
        """Repaint the rail only when the equipped levels changed — same
        signature-gated pattern as _paint_status (cd-yl4)."""
        h = self.world.hero
        sig = (h.get("weapon_level", 0), h.get("armor_level", 0))
        if sig == self._rail_sig:
            return
        self._rail_sig = sig
        self._sword_label.text = str(sig[0]) if sig[0] else "-"
        self._armor_label.text = str(sig[1]) if sig[1] else "-"

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
        acted = False
        if action is not None:
            acted = world_mod.resolve_turn(
                self.world, self.scheduler, action, self._monster_turn
            )
            if self.world.roster_version != self._synced_roster:
                self._sync_actor_sprites()     # a monster died / spawned (cd-e3p.5)
            self._paint_status()               # HP / turn / gold moved (cd-oht.3)
            self._paint_rail()                 # sword/armor level moved (cd-oht.5)
            self._paint_message()              # combat / event text (cd-e3p.9)
        cam = (self.cam_x, self.cam_y)
        self._recenter()
        # a resolved turn may have changed the FOV even if the camera is
        # clamped and didn't move (cd-oht.6), so repaint on either.
        if acted or (self.cam_x, self.cam_y) != cam:
            self._paint_terrain()
        return None

    def _monster_turn(self, world, actor):
        ai.take_turn(world, actor)

    def render(self):
        self._render()


# The main-menu overlay (cd-e3p.13) is not built yet. Its ModeStack seam is
# still here — engine.Game just passes a one-entry overlay dict — so bringing
# it back is a matter of adding {"menu": RealMenuMode(...)} and restoring the
# a+b chord in input.DEFAULT_CHORDS. The stub that used to live here (a lone
# "MENU" label) cost ~2.4 KB resident at boot for no gameplay value and was
# dropped in cd-dsc.6 (the RAM pass).


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
    """On-device diagnostics (bead cd-89o.6). One screen; `CANCEL` (B) or the
    X+Y chord exits. RAM (free / low-water / used / heap), gc + frame time,
    flash, board + CP version, actor / turn / depth, then held buttons and the
    per-chord fire/miss counts. (Was two pages — the input page's trace was a
    wait-chord tuning tool, retired with cd-e3p.14/.15; one screen is less
    code and less RAM — cd-dsc.6.)

    Drawn as **one** whole-page `bitmap_label` of fixed geometry
    (`_MAX_LINES` rows × `_LINE_W` cols, every row space-padded), built
    **lazily on first open** and kept. Because the bounding box never
    changes, `.text =` rewrites the existing Bitmap in place — zero
    allocation after the first. Measured on-device (cd-dsc.6.3): one page
    label ≈ 8 KB vs ≈ 21 KB for 14 separate line-labels, the layout this
    replaced. The build is `MemoryError`-guarded and never retried — if the
    heap is too tight to open diag, `render()` no-ops and `.text` still
    reports (the observer effect cuts both ways: not opening diag is the
    right move when you're that close to the edge). One page label was
    rejected in cd-yl4 for wanting its ~9 KB *contiguous* deep in a
    fragmented run; the guard makes that a graceful miss, not a crash, and
    "ready" free is now ~73 KB."""

    _MAX_LINES = 12     # 10 lines used today (2 chords); slack for a metric or two
    _LINE_W = 36        # ~terminalio chars across 240 px (longest real line ~35)

    def __init__(self, display, game_input, metrics=None, world=None):
        import displayio

        self.display = display
        self.input = game_input
        self.metrics = metrics
        self.world = world
        self.group = displayio.Group()
        self._page = None           # the one bitmap_label, built by _ensure_page()
        self._built = False
        self._shown = ""            # last string composed (kept even if _page is None)
        self._every = 4             # lower bound on renders between refreshes
        self._n = 0

    def _blank_page(self):
        return "\n".join([" " * self._LINE_W] * self._MAX_LINES)

    def _ensure_page(self):
        """Build the single page label the first time the screen is drawn.
        On MemoryError, leave `_page` None and never retry — a game that
        can't spare ~8 KB should not be opening diag."""
        if self._built:
            return
        self._built = True
        import terminalio
        import util
        gc.collect()
        try:
            self._page = util.init_label(terminalio.FONT, 0x33FF33,
                                         x=2, y=8, text=self._blank_page())
        except MemoryError:
            self._page = None
            return
        self.group.append(self._page)
        self._shown = self._blank_page()

    def on_enter(self):
        """Called once by ModeStack.toggle() when diag is switched to (not on
        every render). Prints the same lines the screen shows to serial, so
        the diag readout can be captured (screen /dev/tty.usbmodem*, or
        pasted from there) without needing to read the physical display."""
        for line in self._screen_lines():
            print("Ch7 diag   %s" % line)

    def tick(self, events, now):
        if im.CANCEL in events:
            return "exit"
        return None

    def render(self):
        self._n += 1
        if self._n % self._every == 0:
            self._repaint()

    def _repaint(self):
        self._ensure_page()
        page = self._compose()
        if page == self._shown:
            return
        self._shown = page                       # `.text` stays truthful even if...
        if self._page is None:
            return                               # ...the label never allocated
        try:
            self._page.text = page               # constant box -> bitmap reused
        except MemoryError:
            gc.collect()
            try:
                self._page.text = page
            except MemoryError:
                pass                             # skip this pass; game lives on

    def _compose(self):
        rows = self._screen_lines()[: self._MAX_LINES]
        rows += [""] * (self._MAX_LINES - len(rows))
        return "\n".join(("%-*s" % (self._LINE_W, r))[: self._LINE_W] for r in rows)

    @property
    def text(self):
        """The screen as one string — for tests / logging, not render."""
        return "\n".join(s.rstrip() for s in self._shown.split("\n")).rstrip()

    def _screen_lines(self):
        lines = ["DIAG                B:exit"]
        m = self.metrics
        if m is None:
            lines.append("(no metrics)")
        else:
            lines.append("ram  free %-6s low %s" % (_kib(m.free), _kib(m.free_low)))
            lines.append("ram  used %-6s heap %s" % (_kib(m.alloc), _kib(m.heap)))
            # round frame ms to 10 so jitter doesn't force a rebuild
            lines.append("gc %d ms n=%d  frame %d/%d ms"
                         % (m.collect_ms, m.ram_samples,
                            _round10(m.frame_ms), _round10(m.frame_ms_max)))
            ff, ft = m.flash()
            lines.append("flash %s / %s" % (_kib(ff), _kib(ft)))
            ver, osname = m.environment()
            lines.append("cpy  %s  %s" % (ver, osname))
        lines.append("board  %s" % _board_id())
        w = self.world
        if w is not None:
            lines.append("actors %d  turn %d  depth %d"
                         % (len(w.actors), w.turn, w.depth))

        inp = self.input
        snap = inp.snapshot()
        held = " ".join(snap["held"]) or "-"
        if snap["chord_candidates"]:
            held += "  (" + " ".join(snap["chord_candidates"]) + ")"
        lines.append("held: " + held)
        for row in inp.chord_stats():
            sp = row["last_spread_ms"]
            lines.append("%-8s fire %d  miss %d  sp %s"
                         % (row["combo"], row["fired"], row["missed"],
                            "-" if sp is None else sp))
        return lines


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
