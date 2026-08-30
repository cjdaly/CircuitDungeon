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

# Headless scene smoke test (cd-89o.8). Stubs displayio / terminalio / board /
# adafruit_* just enough to construct engine.Game against a fake display and
# step the real loop body — input model, mode dispatch, camera, sprite sync.
#
# It does NOT prove on-device displayio behaviour; it catches the "called a
# method that doesn't exist / wrong constructor args" class of bug before a
# flash cycle. Real hardware verification is cd-89o.8 proper.
#
#   python3 Chapter_7/tests/test_scene.py

import os
import sys
import types
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "game"))

_KEYS = ("up", "down", "left", "right", "a", "b", "x", "y")


# -- fake CircuitPython modules -----------------------------------------


class _FakeGroup:
    def __init__(self, x=0, y=0, scale=1):
        self.x, self.y, self.scale = x, y, scale
        self._children = []

    def append(self, c):
        self._children.append(c)

    def remove(self, c):
        self._children.remove(c)

    def __iter__(self):
        return iter(self._children)

    def __len__(self):
        return len(self._children)


class _FakeTileGrid:
    def __init__(self, bitmap, pixel_shader=None, width=1, height=1,
                 tile_width=16, tile_height=16, default_tile=0, x=0, y=0):
        self.bitmap = bitmap
        self.pixel_shader = pixel_shader
        self.width, self.height = width, height
        self.tile_width, self.tile_height = tile_width, tile_height
        self.x, self.y = x, y
        self.hidden = False
        self._cells = {}

    def __setitem__(self, key, value):
        self._cells[key] = value

    def __getitem__(self, key):
        return self._cells.get(key, 0)


class _FakeBitmap:
    def __init__(self, *a, **k):
        pass


class _FakePalette:
    def __init__(self, *a, **k):
        self._transparent = set()

    def make_transparent(self, i):
        self._transparent.add(i)

    def __setitem__(self, i, v):
        pass


class _FakeLabel:
    def __init__(self, font, color=0, text="", x=0, y=0, **k):
        self.font, self.color, self._text = font, color, text
        self.x, self.y = x, y
        self.anchor_point = None
        self.anchored_position = None

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, v):
        assert isinstance(v, str)
        self._text = v


def _install_fakes():
    displayio = types.ModuleType("displayio")
    displayio.Group = _FakeGroup
    displayio.TileGrid = _FakeTileGrid
    displayio.Bitmap = _FakeBitmap
    displayio.Palette = _FakePalette
    sys.modules["displayio"] = displayio

    terminalio = types.ModuleType("terminalio")
    terminalio.FONT = object()
    sys.modules["terminalio"] = terminalio

    imageload = types.ModuleType("adafruit_imageload")
    imageload.load = lambda path, bitmap=None, palette=None: (_FakeBitmap(), _FakePalette())
    sys.modules["adafruit_imageload"] = imageload

    adt = types.ModuleType("adafruit_display_text")
    adt_label = types.ModuleType("adafruit_display_text.label")
    adt_label.Label = _FakeLabel
    adt.label = adt_label
    sys.modules["adafruit_display_text"] = adt
    sys.modules["adafruit_display_text.label"] = adt_label

    board = types.ModuleType("board")
    board.board_id = "pimoroni_picosystem"
    sys.modules["board"] = board


_install_fakes()

import engine  # noqa: E402
import modes  # noqa: E402
import world as world_mod  # noqa: E402
import input as im  # noqa: E402
import ai  # noqa: E402

ai.WANDER_CHANCE = 0.0  # deterministic — no random idle steps in the harness


# -- fake display (mimics hardware.GameDisplay) ------------------------


class _FakeScreen:
    def __init__(self):
        self.width = 240
        self.height = 240
        self.auto_refresh = True
        self.root_group = None
        self.refreshes = 0

    def refresh(self):
        self.refreshes += 1


class _FakeDisplay:
    def __init__(self):
        self.screen = _FakeScreen()
        self.groups = {}
        self.grids = {}
        self.sprites = {}
        self.neopixel = None
        self.buttons = {k: False for k in _KEYS}
        self.read_buttons = lambda: dict(self.buttons)


def _room(w, h):
    FLOOR, WALL = 0, 2
    grid = []
    for y in range(h):
        row = bytearray(FLOOR for _ in range(w))
        for x in range(w):
            if x in (0, w - 1) or y in (0, h - 1):
                row[x] = WALL
        grid.append(row)
    wd = world_mod.World(grid, wall_tiles=(WALL,))
    wd.add_actor(world_mod.make_actor(w // 2, h // 2, "heroes", 0))
    wd.add_actor(world_mod.make_actor(2, 2, "creatures", 1))
    wd.add_actor(world_mod.make_actor(w - 3, h - 3, "creatures", 2))  # off-view
    return wd


class Harness:
    def __init__(self, w=24, h=24):
        self.display = _FakeDisplay()
        self.world = _room(w, h)
        self.game = engine.Game(self.display, self.world)
        self.now = 0.0

    def press(self, *names):
        for k in _KEYS:
            self.display.buttons[k] = k in names

    def tick(self, *held):
        """One iteration of engine.Game.run()'s body."""
        self.press(*held)
        g = self.game
        events = g.input.tick(self.display.read_buttons(), self.now)
        g.stack.handle(events, self.now)
        g.input.repeat_paused = g.stack.overlay_active()
        g.stack.render(self.display.screen)
        self.display.screen.refresh()
        self.now += 0.05
        return events


# -- tests -----------------------------------------------------------


class Construction(unittest.TestCase):
    def test_game_builds_without_error(self):
        h = Harness()
        self.assertIs(h.display.screen.root_group, h.game.play.group)
        self.assertFalse(h.display.screen.auto_refresh)

    def test_terrain_viewport_is_13x13(self):
        h = Harness()
        tg = h.display.grids["terrain"]
        self.assertEqual((tg.width, tg.height), (modes.MAP_TILES, modes.MAP_TILES))

    def test_hud_region_groups_exist_at_layout_coords(self):
        h = Harness()
        p = h.game.play
        self.assertEqual((p.status_group.x, p.status_group.y), (0, 0))
        self.assertEqual((p.rail_group.x, p.rail_group.y), (modes.MAP_PX, modes.BAND_H))
        self.assertEqual((p.message_group.x, p.message_group.y), (0, modes.BAND_H + modes.MAP_PX))

    def test_actor_sprites_parallel_world_actors(self):
        h = Harness()
        self.assertEqual(len(h.game.play._actor_sprites), len(h.world.actors))


class Loop(unittest.TestCase):
    def test_idle_ticks_do_not_raise(self):
        h = Harness()
        for _ in range(30):
            h.tick()
        self.assertGreater(h.display.screen.refreshes, 0)

    def test_move_advances_a_turn_and_shifts_the_hero(self):
        h = Harness()
        hero = h.world.hero
        x0 = hero["x"]
        h.tick("right")
        # first press may sit in the chord window one tick; a couple more ticks
        for _ in range(3):
            h.tick("right")
        self.assertGreater(hero["x"], x0)
        self.assertGreater(h.world.turn, 0)

    def test_camera_follows_hero_and_repaints(self):
        h = Harness()
        seen = set()
        for _ in range(40):
            h.tick("right")
            seen.add((h.game.play.cam_x, h.game.play.cam_y))
        self.assertGreater(len(seen), 1)  # camera actually moved
        # hero stays inside the 13x13 window
        vx = h.world.hero["x"] - h.game.play.cam_x
        self.assertTrue(0 <= vx < modes.MAP_TILES)

    def test_offview_actor_sprite_is_hidden(self):
        h = Harness()
        h.tick()
        # actors[2] starts bottom-right, well outside the viewport
        self.assertTrue(h.game.play._actor_sprites[2].hidden)
        self.assertFalse(h.game.play._actor_sprites[0].hidden)  # hero visible


class ModeSwitch(unittest.TestCase):
    def test_xy_chord_opens_diag_and_swaps_root_group(self):
        h = Harness()
        diag = h.game.stack._overlays["diag"]
        h.tick("x", "y")
        self.assertIs(h.game.stack.top, diag)
        self.assertIs(h.display.screen.root_group, diag.group)

    def test_diag_renders_text_without_error(self):
        h = Harness()
        h.tick("x", "y")
        for _ in range(6):          # DiagMode refreshes text every 3rd render
            h.tick()
        self.assertIn("INPUT DIAG", h.game.stack.top._label.text)

    def test_diag_toggles_back_to_play(self):
        h = Harness()
        h.tick("x", "y")
        h.tick()                    # release
        h.tick("x", "y")            # toggle off
        self.assertIs(h.game.stack.top, h.game.play)
        self.assertIs(h.display.screen.root_group, h.game.play.group)

    def test_menu_chord_and_cancel(self):
        h = Harness()
        menu = h.game.stack._overlays["menu"]
        h.tick("a", "b")
        self.assertIs(h.game.stack.top, menu)
        h.tick()                    # release both
        # b is chord-eligible, so its lone CANCEL press sits in the chord
        # window one tick before firing (INPUT.md) — hold it two ticks.
        h.tick("b")
        h.tick("b")
        self.assertIs(h.game.stack.top, h.game.play)

    def test_no_turn_passes_while_an_overlay_is_up(self):
        h = Harness()
        h.tick("x", "y")           # into diag
        t = h.world.turn
        for _ in range(10):
            h.tick("right")        # movement ignored by DiagMode
        self.assertEqual(h.world.turn, t)


if __name__ == "__main__":
    unittest.main()
