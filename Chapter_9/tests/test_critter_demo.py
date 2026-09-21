# SPDX-License-Identifier: MIT
# Off-device checks for the critter look-test -- cd-342.3.
#
#   python3 Chapter_9/tests/test_critter_demo.py
#
# Two things:
#  1. game/art/critters_*.bmp match what critter_demo.py assumes (8-bit
#     indexed, sheet dimensions vs critter_candidates.py) -- parsed straight
#     from the BMP header, no Pillow needed.
#  2. game/critter_demo.py's main loop, run against stubbed displayio/hardware
#     with a scripted touch and a fake clock, to catch wiring bugs (wrong
#     attribute, wrong gesture mapping) that would otherwise cost a board
#     session. It says nothing about how the sprites look.

import os
import struct
import sys
import types
import unittest
from unittest import mock

GAME = os.path.join(os.path.dirname(__file__), "..", "game")
sys.path.insert(0, GAME)

import critter_candidates as cc  # noqa: E402


def _bmp_header(path):
    with open(path, "rb") as f:
        head = f.read(54)
    assert head[:2] == b"BM", path
    width, height, _planes, bpp, compression = struct.unpack("<iihhI", head[18:34])
    return width, abs(height), bpp, compression


class TestBmpSheets(unittest.TestCase):
    def test_sheets_are_8bit_uncompressed_and_match_manifest(self):
        rows = -(-2 * len(cc.CANDIDATES) // cc.TILES_WIDE)
        for method in ("nn", "epx"):
            width, height, bpp, compression = _bmp_header(
                os.path.join(GAME, "art", "critters_{}.bmp".format(method))
            )
            self.assertEqual(bpp, 8, method)
            self.assertEqual(compression, 0, method)
            self.assertEqual(width, cc.TILES_WIDE * cc.TILE, method)
            self.assertEqual(height, rows * cc.TILE, method)

    def test_manifest_ids_unique_and_groups_contiguous(self):
        ids = [c[0] for c in cc.CANDIDATES]
        self.assertEqual(len(ids), len(set(ids)))
        seen, prev = set(), None
        for _id, group, _src in cc.CANDIDATES:
            if group != prev:
                self.assertNotIn(group, seen, "group {} split up".format(group))
                seen.add(group)
                prev = group


# --------------------------------------------------------------------------- #
# stubs for the on-device modules critter_demo imports
# --------------------------------------------------------------------------- #
_labels, _grids, _groups = [], [], []


class _Group(list):
    def __init__(self, **kw):
        super().__init__()
        self.hidden = False
        self.__dict__.update(kw)
        _groups.append(self)


class _Bitmap:
    def __init__(self, *a, **k):
        pass


class _Palette(dict):
    transparent = None

    def __init__(self, n=1):
        super().__init__()

    def make_transparent(self, i):
        self.transparent = i


class _OnDiskBitmap:
    opened = []

    def __init__(self, path):
        self.path = path
        self.pixel_shader = _Palette(256)
        _OnDiskBitmap.opened.append(self)


class _TileGrid:
    def __init__(self, bitmap, pixel_shader=None, tile_width=None, **k):
        self.tile_width = tile_width
        self.hidden = False
        self.flip_x = False
        self.x = self.y = 0
        self._tiles = {}
        if tile_width == cc.TILE:
            _grids.append(self)

    def __setitem__(self, key, value):
        self._tiles[key] = value

    def __getitem__(self, key):
        return self._tiles[key]


class _Shape:
    def __init__(self, **kw):
        self.__dict__.update(kw)


class _Label:
    def __init__(self, font, **kw):
        self.text = ""
        self.__dict__.update(kw)
        _labels.append(self)


class _Done(Exception):
    pass


def _swipe(t0, x0, y0, x1, y1):
    return (t0, t0 + 0.2, lambda dt: (int(x0 + (x1 - x0) * dt / 0.2), int(y0 + (y1 - y0) * dt / 0.2)))


def _tap(t0, x, y):
    return (t0, t0 + 0.1, lambda dt: (x, y))


class TestDemoLoop(unittest.TestCase):
    STUBBED = ("displayio", "vectorio", "terminalio", "adafruit_display_text",
               "adafruit_display_text.bitmap_label", "hardware", "critter_demo")

    def setUp(self):
        self._saved = {n: sys.modules.pop(n, None) for n in self.STUBBED}
        displayio = types.ModuleType("displayio")
        displayio.Group, displayio.Bitmap = _Group, _Bitmap
        displayio.Palette, displayio.TileGrid = _Palette, _TileGrid
        displayio.OnDiskBitmap = _OnDiskBitmap
        vectorio = types.ModuleType("vectorio")
        vectorio.Rectangle = _Shape
        terminalio = types.ModuleType("terminalio")
        terminalio.FONT = object()
        pkg = types.ModuleType("adafruit_display_text")
        bl = types.ModuleType("adafruit_display_text.bitmap_label")
        bl.Label = _Label
        pkg.bitmap_label = bl
        self.script = []
        hardware = types.ModuleType("hardware")
        hardware.WIDTH = hardware.HEIGHT = 240
        hardware.init_display = lambda: (types.SimpleNamespace(root_group=None), None)
        hardware.init_i2c = lambda: None
        hardware.init_touch = lambda i2c: types.SimpleNamespace(poll=self._poll)
        sys.modules.update({
            "displayio": displayio, "vectorio": vectorio, "terminalio": terminalio,
            "adafruit_display_text": pkg, "adafruit_display_text.bitmap_label": bl,
            "hardware": hardware,
        })
        _labels.clear()
        _grids.clear()
        _groups.clear()
        _OnDiskBitmap.opened.clear()
        self.now = 1000.0

    def tearDown(self):
        for n, mod in self._saved.items():
            if mod is None:
                sys.modules.pop(n, None)
            else:
                sys.modules[n] = mod

    def _poll(self, now):
        rel = now - 1000.0
        for t0, t1, fn in self.script:
            if t0 <= rel < t1:
                return fn(rel - t0)
        return None

    def _run(self, seconds):
        """Import (= run) critter_demo; snapshot state every tick until time's up."""
        snaps = []

        def snapshot():
            id_text = [lb.text for lb in _labels if lb.anchored_position[1] == 26][0]
            # grids per method, in creation order: big, small, walker
            nn_big, nn_small, nn_walk, epx_big, epx_small, epx_walk = _grids
            on_epx = nn_big.hidden
            big, small, walker = (
                (epx_big, epx_small, epx_walk) if on_epx else (nn_big, nn_small, nn_walk)
            )
            _root, still_view, walk_view = _groups[:3]
            snaps.append({
                "t": self.now - 1000.0, "id": id_text,
                "nn_hidden": nn_big.hidden, "epx_hidden": epx_big.hidden,
                "tile": big[0, 0], "small_tile": small[0, 0],
                "still_hidden": still_view.hidden, "walk_hidden": walk_view.hidden,
                "walker": (walker.x, walker.y, walker.flip_x), "walker_tile": walker[0, 0],
                "src": [lb.text for lb in _labels if lb.anchored_position[1] == 38][0],
            })

        def sleep(dt):
            self.now += dt
            snapshot()
            if self.now - 1000.0 >= seconds:
                raise _Done

        with mock.patch("time.monotonic", lambda: self.now), mock.patch("time.sleep", sleep):
            with self.assertRaises(_Done):
                import critter_demo  # noqa: F401 -- main() runs at import
        return snaps

    def _at(self, snaps, t):
        return min(snaps, key=lambda s: abs(s["t"] - t))

    def test_loads_both_sheets_with_transparent_index_zero(self):
        self._run(0.5)
        paths = sorted(b.path for b in _OnDiskBitmap.opened)
        self.assertEqual(paths, ["/art/critters_epx.bmp", "/art/critters_nn.bmp"])
        for b in _OnDiskBitmap.opened:
            self.assertEqual(b.pixel_shader.transparent, 0)

    def test_starts_on_first_candidate_nn_and_animates_two_frames(self):
        snaps = self._run(1.6)
        first = snaps[0]
        self.assertEqual(first["id"], "1/{} dog".format(len(cc.CANDIDATES)))
        self.assertFalse(first["nn_hidden"])
        self.assertTrue(first["epx_hidden"])
        tiles = {s["tile"] for s in snaps}
        self.assertEqual(tiles, {0, 1})  # candidate 0 -> frames 0 and 1
        self.assertTrue(all(s["tile"] == s["small_tile"] for s in snaps))

    def test_swipe_left_next_swipe_right_previous(self):
        self.script = [_swipe(1.0, 200, 120, 100, 120), _swipe(2.0, 100, 120, 200, 120)]
        snaps = self._run(3.0)
        self.assertTrue(self._at(snaps, 1.6)["id"].startswith("2/"))
        self.assertTrue(self._at(snaps, 2.8)["id"].startswith("1/"))

    def test_swipe_right_from_start_wraps_to_last(self):
        self.script = [_swipe(1.0, 100, 120, 200, 120)]
        snaps = self._run(2.0)
        n = len(cc.CANDIDATES)
        self.assertTrue(self._at(snaps, 1.8)["id"].startswith("{}/".format(n)))

    def test_swipe_up_jumps_to_next_group_and_down_returns(self):
        first_cat = [i for i, c in enumerate(cc.CANDIDATES) if c[1] == "cat"][0]
        self.script = [_swipe(1.0, 120, 200, 120, 100), _swipe(2.0, 120, 100, 120, 200)]
        snaps = self._run(3.0)
        self.assertEqual(self._at(snaps, 1.6)["id"].split()[0], "{}/{}".format(first_cat + 1, len(cc.CANDIDATES)))
        self.assertTrue(self._at(snaps, 2.8)["id"].startswith("1/"))

    def test_tap_flips_expansion_method(self):
        self.script = [_tap(1.0, 120, 60)]  # top half
        snaps = self._run(2.0)
        after = self._at(snaps, 1.8)
        self.assertTrue(after["nn_hidden"])
        self.assertFalse(after["epx_hidden"])
        self.assertTrue(self._at(snaps, 0.5)["epx_hidden"])

    def test_starts_in_still_view_not_walk(self):
        s = self._run(0.5)[0]
        self.assertFalse(s["still_hidden"])
        self.assertTrue(s["walk_hidden"])

    def test_tap_bottom_half_toggles_walk_mode_and_back(self):
        self.script = [_tap(1.0, 120, 200), _tap(3.0, 120, 200)]
        snaps = self._run(4.0)
        walking = self._at(snaps, 2.0)
        self.assertTrue(walking["still_hidden"])
        self.assertFalse(walking["walk_hidden"])
        self.assertIn("walk", walking["src"])
        back = self._at(snaps, 3.8)
        self.assertFalse(back["still_hidden"])
        self.assertTrue(back["walk_hidden"])
        self.assertNotIn("walk", back["src"])

    def test_tap_top_half_does_not_toggle_walk(self):
        self.script = [_tap(1.0, 120, 60)]
        s = self._at(self._run(2.0), 1.8)
        self.assertTrue(s["walk_hidden"])

    def test_walker_patrols_and_mirrors_by_direction(self):
        self.script = [_tap(0.5, 120, 200)]
        snaps = [s for s in self._run(14.0) if s["t"] > 1.0]
        xs = [s["walker"][0] for s in snaps]
        self.assertGreater(max(xs), 170)  # reached the right end
        self.assertLess(xs[-1], max(xs))  # ...and came back
        flips = [s["walker"][2] for s in snaps]
        self.assertTrue(any(flips) and not all(flips))  # mirrored some, not all
        # heading right (x increasing early on) must be mirrored
        early = [s for s in snaps if 1.0 < s["t"] < 3.0]
        self.assertTrue(all(s["walker"][2] for s in early))
        # stays on the floor path, hops at most BOB_PX above it
        for s in snaps:
            x, y, _ = s["walker"]
            self.assertTrue(30 <= x <= 178 and 94 <= y <= 140, (x, y))

    def test_walking_steps_faster_than_idle(self):
        def flips(snaps, lo, hi):
            tiles = [s["walker_tile"] for s in snaps if lo <= s["t"] < hi]
            return sum(1 for a, b in zip(tiles, tiles[1:]) if a != b)

        self.script = [_tap(0.5, 120, 200)]
        snaps = self._run(4.0)
        # 2s of walking at STEP_PERIOD 0.2 -> ~10 flips; resting would be ~4
        self.assertGreaterEqual(flips(snaps, 1.0, 3.0), 8)

    def test_tile_index_tracks_candidate(self):
        self.script = [_swipe(1.0, 200, 120, 100, 120)]  # -> candidate index 1
        snaps = self._run(2.0)
        self.assertIn(self._at(snaps, 1.9)["tile"], (2, 3))  # frames 2*1, 2*1+1


if __name__ == "__main__":
    unittest.main()
