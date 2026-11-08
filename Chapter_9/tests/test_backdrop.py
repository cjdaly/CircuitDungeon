# SPDX-License-Identifier: MIT
# Off-device tests for game/backdrop.py: file names, reading the built BMPs.
#
#   python3 Chapter_9/tests/test_backdrop.py

import os
import struct
import sys
import tempfile
import types
import unittest

_GAME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "game")
sys.path.insert(0, _GAME)

import backdrop  # noqa: E402
import rooms  # noqa: E402
from scene_art import KEY  # noqa: E402

_ROOMS = os.path.join(_GAME, "art", "rooms")


class _Bitmap(dict):
    def __init__(self, width=backdrop.SIZE, height=backdrop.SIZE, value_count=16):
        super().__init__()
        self.value_count = value_count


def _index(ch):
    return KEY[ch] - 1  # backdrops drop scene_art's see-through slot


class TestFileName(unittest.TestCase):
    def test_names(self):
        self.assertEqual(backdrop.file_name("Kitchen"), "kitchen.bmp")
        self.assertEqual(backdrop.file_name("Kids' Bedroom"), "kids_bedroom.bmp")
        self.assertEqual(backdrop.file_name("Odd Corner"), "odd_corner.bmp")

    def test_every_built_backdrop_is_a_real_room(self):
        names = {backdrop.file_name(room.name) for room in rooms.make_world()._rooms.values()}
        for built in os.listdir(_ROOMS):
            self.assertIn(built, names)


class TestLoad(unittest.TestCase):
    def test_kitchen_reads_the_right_way_up(self):
        bitmap = _Bitmap()
        self.assertTrue(backdrop.load(bitmap, os.path.join(_ROOMS, "kitchen.bmp")))
        self.assertEqual(len(bitmap), backdrop.SIZE * backdrop.SIZE)
        self.assertEqual(bitmap[0, 0], _index("k"))  # wall, top left
        self.assertEqual(bitmap[0, 90], _index("s"))  # grey floor check
        self.assertEqual(bitmap[0, 97], _index("w"))  # white one below it
        self.assertEqual(bitmap[20, 50], _index("w"))  # fridge door
        self.assertLess(max(bitmap.values()), 16)

    def test_every_built_backdrop_loads(self):
        for built in os.listdir(_ROOMS):
            self.assertTrue(backdrop.load(_Bitmap(), os.path.join(_ROOMS, built)), built)

    def test_missing_file(self):
        self.assertFalse(backdrop.load(_Bitmap(), "/no/such/room.bmp"))

    def test_wrong_size_is_refused(self):
        header = bytearray(54)
        header[0:2] = b"BM"
        struct.pack_into("<I", header, 10, 54 + 1024)
        struct.pack_into("<ii", header, 18, 64, 64)
        struct.pack_into("<H", header, 28, 8)
        with tempfile.NamedTemporaryFile(suffix=".bmp", delete=False) as f:
            f.write(bytes(header) + bytes(1024 + 64 * 64))
        self.addCleanup(os.remove, f.name)
        self.assertFalse(backdrop.load(_Bitmap(), f.name))

    def test_short_file_is_refused(self):
        with open(os.path.join(_ROOMS, "kitchen.bmp"), "rb") as f:
            data = f.read()
        with tempfile.NamedTemporaryFile(suffix=".bmp", delete=False) as f:
            f.write(data[:5000])
        self.addCleanup(os.remove, f.name)
        self.assertFalse(backdrop.load(_Bitmap(), f.name))


class _Group(list):
    def __init__(self, scale=1):
        super().__init__()
        self.scale = scale
        self.hidden = False


class TestBackdrop(unittest.TestCase):
    def setUp(self):
        displayio = types.ModuleType("displayio")
        displayio.Bitmap = _Bitmap
        displayio.Palette = lambda n: [0] * n
        displayio.Group = _Group
        displayio.TileGrid = lambda bitmap, pixel_shader: (bitmap, pixel_shader)
        saved = sys.modules.get("displayio")
        sys.modules["displayio"] = displayio
        self.addCleanup(lambda: sys.modules.__setitem__("displayio", saved) if saved
                        else sys.modules.pop("displayio", None))

    def test_one_16_colour_bitmap_at_2x(self):
        view = backdrop.Backdrop(_ROOMS)
        bitmap, palette = view.group[0]
        self.assertEqual(bitmap.value_count, 16)
        self.assertEqual(len(palette), 16)
        self.assertEqual(view.group.scale, 2)
        self.assertTrue(view.group.hidden)

    def test_shows_for_a_room_with_art_and_hides_for_one_without(self):
        view = backdrop.Backdrop(_ROOMS)
        view.show("Kitchen")
        self.assertFalse(view.group.hidden)
        view.show("Nowhere")
        self.assertTrue(view.group.hidden)
        view.show("Kitchen")
        self.assertFalse(view.group.hidden)


if __name__ == "__main__":
    unittest.main()
