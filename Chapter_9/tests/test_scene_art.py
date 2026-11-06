# SPDX-License-Identifier: MIT
# Off-device tests for game/scene_art.py -- cd-342.26.
#
#   python3 Chapter_9/tests/test_scene_art.py

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "game"))

import critters  # noqa: E402
import episodes  # noqa: E402
import scene_art  # noqa: E402


class TestSceneArt(unittest.TestCase):
    def test_every_picture_is_16_by_16_in_known_colors(self):
        for name, rows in scene_art.ART.items():
            with self.subTest(name=name):
                self.assertEqual(len(rows), scene_art.TILE)
                for row in rows:
                    self.assertEqual(len(row), scene_art.TILE, row)
                    for ch in row:
                        self.assertIn(ch, scene_art.KEY, row)

    def test_the_key_fits_the_palette(self):
        self.assertEqual(scene_art.KEY["."], 0)
        self.assertEqual(sorted(scene_art.KEY.values()), list(range(len(scene_art.COLORS))))

    def test_every_lure_has_a_picture(self):
        for _species, lure, _habit, _sprites in critters.CAST:
            self.assertIn(lure, scene_art.ART)

    def test_every_hiding_room_has_a_spot_and_nothing_else_does(self):
        hide_rooms = {episode.hide_room for episode in episodes.EPISODES.values()}
        self.assertEqual(set(scene_art.HIDING_SPOTS), hide_rooms)
        for spot in scene_art.HIDING_SPOTS.values():
            self.assertIn(spot, scene_art.ART)
            self.assertIn(spot, scene_art.SPOT_TOP)

    def test_every_locked_lure_picture_exists(self):
        for episode in episodes.EPISODES.values():
            art = episode.unlock.locked_art if episode.unlock else None
            if art is not None:
                self.assertIn(art, scene_art.ART)

    def test_the_odd_corner_has_its_batteries(self):
        self.assertIn("batteries", scene_art.ART)


if __name__ == "__main__":
    unittest.main()
