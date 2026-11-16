# SPDX-License-Identifier: MIT
# The gift tag's pure helpers -- cd-342.44.
#
#   python3 Chapter_9/tests/test_gift_tag.py
import os
import sys
import types
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "game"))
if "adafruit_bitmap_font" not in sys.modules:  # comic_fonts imports it; not used here
    pkg = types.ModuleType("adafruit_bitmap_font")
    pkg.bitmap_font = types.ModuleType("adafruit_bitmap_font.bitmap_font")
    sys.modules["adafruit_bitmap_font"] = pkg
    sys.modules["adafruit_bitmap_font.bitmap_font"] = pkg.bitmap_font

import comic_fonts  # noqa: E402
import gift_tag  # noqa: E402


class _Bitmap(dict):
    pass


class TestGiftTag(unittest.TestCase):
    def test_names_use_only_letters_the_fonts_have(self):
        self.assertEqual(gift_tag.clean_name("Mary-Kate  O'Neil"), "MARY KATE O'NEIL")
        self.assertEqual(gift_tag.clean_name("Zoë"), "ZO")
        for ch in gift_tag.clean_name("Grandpa Joe & co. #1!"):
            self.assertIn(ch, comic_fonts.GLYPHS)
        for ch in "FOR FROM " + gift_tag.FROM:
            self.assertIn(ch, comic_fonts.GLYPHS)

    def test_a_name_always_gets_the_same_look(self):
        self.assertIs(gift_tag.style_for("TEST1"), gift_tag.style_for("TEST1"))
        looks = {gift_tag.STYLES.index(gift_tag.style_for("TEST{}".format(n))) for n in range(1, 9)}
        self.assertGreater(len(looks), 4)  # names spread over the looks

    def test_each_gift_board_gets_its_own_look(self):
        looks = [gift_tag.style_for("SAME", "ws-{:02d}".format(n)) for n in range(1, 11)]
        self.assertEqual(len({id(look) for look in looks}), 10)
        self.assertIs(gift_tag.style_for("A", "ws-1"), gift_tag.style_for("B", "ws-01"))
        self.assertIs(gift_tag.style_for("TEST1", ""), gift_tag.style_for("TEST1"))

    def test_each_reset_moves_on_a_look(self):
        nvm = bytearray(b"\xff" * 4096)  # as provision.py leaves it
        turns = [gift_tag.next_turn(nvm) for _ in range(12)]
        self.assertEqual(turns, list(range(10)) + [0, 1])
        looks = [gift_tag.style_for("TEST2", "ws-02", turn) for turn in range(10)]
        self.assertEqual(len({id(look) for look in looks}), 10)  # every look in turn
        self.assertEqual(nvm[:-1], bytearray(b"\xff" * 4095))  # only the last byte

    def test_boards_reset_together_still_differ(self):
        for turn in range(10):
            looks = {id(gift_tag.style_for("X", "ws-{:02d}".format(n), turn)) for n in range(1, 11)}
            self.assertEqual(len(looks), 10)

    def test_the_drain_log_leaves_the_turn_byte_alone(self):
        import drain_log

        self.assertLess(4096 // drain_log.SIZE * drain_log.SIZE, 4096)

    def test_board_numbers(self):
        self.assertEqual(gift_tag.board_number("ws-07"), 7)
        self.assertEqual(gift_tag.board_number("ws-10"), 10)
        self.assertIsNone(gift_tag.board_number("ws-"))
        self.assertIsNone(gift_tag.board_number(None))

    def test_the_name_is_as_big_as_fits(self):
        self.assertEqual(gift_tag.name_layout((68, 52)), ("title", 2))
        self.assertEqual(gift_tag.name_layout((129, 95)), ("title", 1))
        self.assertEqual(gift_tag.name_layout((182, 137)), ("caption", 1))
        self.assertIsNone(gift_tag.name_layout((260, 200)))

    def test_long_names_split_near_the_middle(self):
        self.assertEqual(gift_tag.split_name("MARY KATE O'NEIL"), ("MARY KATE", "O'NEIL"))
        self.assertEqual(gift_tag.split_name("ABCDEFGHIJKLMNOPQRST"), ("ABCDEFGHIJ", "KLMNOPQRST"))

    def test_every_paper_paints_a_full_tile_of_valid_colours(self):
        for pattern, colours in gift_tag.PAPERS:
            tile = _Bitmap()
            gift_tag.paint_pattern(tile, pattern)
            self.assertEqual(len(tile), 24 * 24, pattern)
            self.assertLessEqual(set(tile.values()), set(range(len(colours))), pattern)
            self.assertGreater(len(set(tile.values())), 1, pattern)  # not a blank sheet

    def test_every_look_names_a_real_paper(self):
        for paper, ribbon, tag in gift_tag.STYLES:
            self.assertLess(paper, len(gift_tag.PAPERS))


if __name__ == "__main__":
    unittest.main()
