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

import displayio
import terminalio

import util
import level_loader

TERRAIN_TILE = 16
HERO_TILE_W, HERO_TILE_H = 16, 24
EXPLOSION_TILE = 32
HERO_BASES = (0, 18, 36)  # hero.bmp holds 3 character variants, 18 tile indices apart
OFFSCREEN = -1000

EXPLOSION_POOL_SIZE = 4  # concurrent blasts on screen at once; oldest is reused past this
CHAIN_DELAY = 4          # cycles between a chain-reaction link and the neighbor it detonates
TRIGGER_COOLDOWN = 30    # cycles before a repeatable (`*`) event can refire at the same tile

# Named frame-index arrays, ported from Chapter 5/PyBadge.
EXPLOSION_FRAMES = {
    "exp1": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31],
    "exp2": [1, 2, 3],
}
# terrain.bmp has no dedicated torch-flicker art, so `rune` reuses the two
# ring tiles (big/small, tile indices 11/12 — chars 'O'/'o') as a pulse.
ANIM_FRAMES = {
    "rune": [11, 12],
}


def _clamp(value, lo, hi):
    return max(lo, min(hi, value))


class Player:
    def __init__(self):
        self.tile_x, self.tile_y = 0, 0
        self.facing, self.anim_frame = "right", 0
        self.base = HERO_BASES[0]


class Game:
    def __init__(self, display):
        self.display = display  # a GameDisplay
        self.level = None       # a Level
        self.hero = Player()
        self.cycle = 0                 # frame counter (the pulse)
        self.anims = {}                # (col,row) -> frames, from `anim` events
        self.camera = None             # {'x':0,'y':0} when level.scroll, else None
        self.active_explosions = []    # list of {'pos','frames','started_at','slot'}
        self._pending = []             # chain-reaction queue: (fire_at_cycle, pos, event)
        self._last_fired = {}          # (col,row) -> cycle, for repeatable-event cooldown
        self._prev_a = False           # edge-detect for A-button hero cycling
        self._terrain_cols = display.screen.width // TERRAIN_TILE
        self._terrain_rows = display.screen.height // TERRAIN_TILE
        self.viewport_cols = self._terrain_cols
        self.viewport_rows = self._terrain_rows

        display.groups["world"] = displayio.Group()
        display.groups["root"] = displayio.Group()

        terrain = util.load_tilegrid("terrain", self._terrain_cols, self._terrain_rows, TERRAIN_TILE, TERRAIN_TILE)
        display.grids["terrain"] = terrain
        display.groups["world"].append(terrain)

        hero_sprite = util.load_sprite("heroes", 1, 1, HERO_TILE_W, HERO_TILE_H, x=OFFSCREEN, y=OFFSCREEN)
        display.sprites["hero"] = hero_sprite
        display.groups["world"].append(hero_sprite)

        self._explosion_pool = []
        for _ in range(EXPLOSION_POOL_SIZE):
            exp_group = displayio.Group(scale=1)
            exp_group.x, exp_group.y = OFFSCREEN, OFFSCREEN
            exp_sprite = util.load_sprite("explosions", 1, 1, EXPLOSION_TILE, EXPLOSION_TILE)
            exp_group.append(exp_sprite)
            display.groups["world"].append(exp_group)
            self._explosion_pool.append({"group": exp_group, "sprite": exp_sprite})
        display.sprites["explosions"] = [slot["sprite"] for slot in self._explosion_pool]

        hud = util.init_label(terminalio.FONT, 40, 0x00FFFF, x=1, y=display.screen.height - 9, text="")
        display.groups["hud"] = hud

        display.groups["root"].append(display.groups["world"])
        display.groups["root"].append(hud)

        display.screen.root_group = display.groups["root"]
        display.screen.auto_refresh = False

    # -- levels ------------------------------------------------------

    def load_level(self, name):
        level = level_loader.load("/levels/" + name + ".lvl")
        self.level = level
        self.anims = {}
        self.active_explosions = []
        self._pending = []
        self._last_fired = {}
        for slot in self._explosion_pool:
            slot["group"].x, slot["group"].y = OFFSCREEN, OFFSCREEN

        grid_cols = len(level.grid[0]) if level.grid else self.viewport_cols
        grid_rows = len(level.grid)
        self._ensure_terrain_size(grid_cols, grid_rows)

        terrain = self.display.grids["terrain"]
        for row, text in enumerate(level.grid):
            for col, char in enumerate(text):
                terrain[col, row] = self._char_to_index(char)

        if level.scroll:
            self.camera = {"x": 0, "y": 0}
        else:
            self.camera = None
            self.display.groups["world"].x = 0
            self.display.groups["world"].y = 0

    def _ensure_terrain_size(self, cols, rows):
        if cols == self._terrain_cols and rows == self._terrain_rows:
            return
        world = self.display.groups["world"]
        old = self.display.grids["terrain"]
        world.remove(old)
        terrain = util.load_tilegrid("terrain", cols, rows, TERRAIN_TILE, TERRAIN_TILE)
        self.display.grids["terrain"] = terrain
        world.insert(0, terrain)
        self._terrain_cols, self._terrain_rows = cols, rows

    def _char_to_index(self, char):
        idx = self.level.chars.find(char)
        return idx if idx >= 0 else 0

    # -- movement + collision ----------------------------------------

    def get_hero_xy(self):
        sprite = self.display.sprites["hero"]
        col = (sprite.x + 8) // TERRAIN_TILE
        row = (sprite.y + 16) // TERRAIN_TILE
        self.hero.tile_x, self.hero.tile_y = col, row
        return col, row

    def set_hero_xy(self, col, row):
        sprite = self.display.sprites["hero"]
        sprite.x = col * TERRAIN_TILE
        sprite.y = row * TERRAIN_TILE - 8
        self.hero.tile_x, self.hero.tile_y = col, row

    def in_wall(self):
        col, row = self.get_hero_xy()
        grid = self.level.grid
        if row < 0 or row >= len(grid) or col < 0 or col >= len(grid[row]):
            return True
        return grid[row][col] in self.level.walls

    def handle_input(self, buttons):
        if buttons["a"] and not self._prev_a:
            next_index = (HERO_BASES.index(self.hero.base) + 1) % len(HERO_BASES)
            self.hero.base = HERO_BASES[next_index]
        self._prev_a = buttons["a"]

        sprite = self.display.sprites["hero"]
        if buttons["right"]:
            self.hero.facing = "right"
            sprite.x += 2
            if self.in_wall():
                sprite.x -= 4
        if buttons["left"]:
            self.hero.facing = "left"
            sprite.x -= 2
            if self.in_wall():
                sprite.x += 4
        if buttons["down"]:
            sprite.y += 2
            if self.in_wall():
                sprite.y -= 4
        if buttons["up"]:
            sprite.y -= 2
            if self.in_wall():
                sprite.y += 4

    # -- triggers ------------------------------------------------------

    def check_triggers(self):
        self._process_pending()
        pos = self.get_hero_xy()

        exit_ = self.level.exits.get(pos)
        if exit_ is not None:
            dcol, drow = exit_["dest"]
            self.load_level(exit_["map"])
            self.set_hero_xy(dcol, drow)
            return  # new level loaded; its own events are checked next frame

        events = self.level.events.get(pos)
        if not events:
            return

        fired, kept = [], []
        for ev in events:
            on_cooldown = ev["repeat"] and self.cycle - self._last_fired.get(pos, -TRIGGER_COOLDOWN) < TRIGGER_COOLDOWN
            if on_cooldown:
                kept.append(ev)
                continue
            fired.append(ev)
            if ev["repeat"]:
                kept.append(ev)
        for ev in fired:
            self._fire_event(pos, ev)
            self._last_fired[pos] = self.cycle
        if kept:
            self.level.events[pos] = kept
        else:
            del self.level.events[pos]

    def _fire_event(self, pos, ev):
        # Hero-triggered: stepping onto a torch, trap, sign, or switch tile
        # fires it directly (see the `[events]` walkthrough in the plan).
        if ev["type"] == "explosion":
            self._queue_explosion(pos, ev["args"])
        elif ev["type"] == "anim":
            self.anims[pos] = ANIM_FRAMES.get(ev["args"], [0])
        elif ev["type"] == "text":
            self.display.groups["hud"].text = ev["args"]
        elif ev["type"] == "tile":
            self._apply_tile_event(pos, int(ev["args"]))

    # -- explosions: pooled, scalable, chain-reacting -------------------

    def _queue_explosion(self, pos, args):
        name, _, scale_text = args.partition(" ")
        scale = int(scale_text) if scale_text.strip() else 1
        frames = EXPLOSION_FRAMES.get(name, [0])
        self._start_explosion(pos, frames, scale)
        self._propagate_chain(pos)

    def _start_explosion(self, pos, frames, scale):
        slot_index = self._next_explosion_slot()
        self.active_explosions.append({"pos": pos, "frames": frames, "started_at": self.cycle, "slot": slot_index})
        self._explosion_pool[slot_index]["group"].scale = scale

    def _next_explosion_slot(self):
        used = {exp["slot"] for exp in self.active_explosions}
        for i in range(len(self._explosion_pool)):
            if i not in used:
                return i
        oldest = min(self.active_explosions, key=lambda exp: exp["started_at"])
        self.active_explosions.remove(oldest)
        return oldest["slot"]

    def _propagate_chain(self, pos):
        col, row = pos
        for neighbor in ((col + 1, row), (col - 1, row), (col, row + 1), (col, row - 1)):
            neighbor_events = self.level.events.get(neighbor)
            if not neighbor_events:
                continue
            for ev in list(neighbor_events):
                if ev["type"] == "explosion" and not ev["repeat"]:
                    neighbor_events.remove(ev)
                    if not neighbor_events:
                        del self.level.events[neighbor]
                    self._pending.append((self.cycle + CHAIN_DELAY, neighbor, ev))

    def _process_pending(self):
        ready = [p for p in self._pending if p[0] <= self.cycle]
        if not ready:
            return
        self._pending = [p for p in self._pending if p[0] > self.cycle]
        for _, pos, ev in ready:
            self._queue_explosion(pos, ev["args"])

    def _apply_tile_event(self, pos, index):
        col, row = pos
        chars = self.level.chars
        char = chars[index] if 0 <= index < len(chars) else chars[0]
        row_text = self.level.grid[row]
        self.level.grid[row] = row_text[:col] + char + row_text[col + 1:]
        self.display.grids["terrain"][col, row] = index

    # -- animation + pulse ---------------------------------------------

    def update_sprites(self):
        hero_sprite = self.display.sprites["hero"]
        frame = self.cycle % 4
        if self.hero.facing == "right":
            hero_sprite[0, 0] = self.hero.base + frame
        else:
            hero_sprite[0, 0] = self.hero.base + 9 + frame
        self.hero.anim_frame = frame

        if self.active_explosions:
            self._update_explosions()

        terrain = self.display.grids["terrain"]
        for (col, row), frames in self.anims.items():
            terrain[col, row] = frames[self.cycle % len(frames)]

    def _update_explosions(self):
        still_active = []
        for exp in self.active_explosions:
            frames = exp["frames"]
            elapsed = self.cycle - exp["started_at"]
            slot = self._explosion_pool[exp["slot"]]
            if elapsed < len(frames):
                col, row = exp["pos"]
                size = EXPLOSION_TILE * slot["group"].scale
                slot["group"].x = col * TERRAIN_TILE - (size - TERRAIN_TILE) // 2
                slot["group"].y = row * TERRAIN_TILE - (size - TERRAIN_TILE) // 2
                slot["sprite"][0, 0] = frames[elapsed]
                still_active.append(exp)
            else:
                slot["group"].x, slot["group"].y = OFFSCREEN, OFFSCREEN
        self.active_explosions = still_active

    # -- camera ----------------------------------------------------------

    def update_camera(self):
        if self.camera is None:
            return
        col, row = self.get_hero_xy()
        grid_cols = len(self.level.grid[0])
        grid_rows = len(self.level.grid)
        cam_x = _clamp(col - self.viewport_cols // 2, 0, max(0, grid_cols - self.viewport_cols))
        cam_y = _clamp(row - self.viewport_rows // 2, 0, max(0, grid_rows - self.viewport_rows))
        self.camera["x"], self.camera["y"] = cam_x, cam_y
        world = self.display.groups["world"]
        world.x = -cam_x * TERRAIN_TILE
        world.y = -cam_y * TERRAIN_TILE

    # -- main loop ---------------------------------------------------------

    def play(self):
        while True:
            buttons = self.display.read_buttons()
            self.handle_input(buttons)
            self.check_triggers()
            self.update_sprites()
            self.update_camera()
            self.display.screen.refresh()
            self.cycle += 1
