# SPDX-License-Identifier: MIT
"""Popups keep off what matters -- cd-342.46 (game/clearance.py)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "game"))

import clearance  # noqa: E402

SIZE = 64  # a critter at 2x
HOME = (88, 104)  # scene_view's standing critter


class _Group(list):
    def __init__(self, x=0, y=0, scale=1):
        super().__init__()
        self.x, self.y, self.scale, self.hidden = x, y, scale, False


class _Grid:
    def __init__(self, x, y, tile=32, width=1, height=1):
        self.x, self.y, self.hidden = x, y, False
        self.tile_width = self.tile_height = tile
        self.width, self.height = width, height


class _Label:
    def __init__(self):
        self.x = self.y = 0
        self.hidden = False
        self.anchored_position = (120, 120)


class TestGeometry(unittest.TestCase):
    def test_overlap_area(self):
        self.assertEqual(clearance.overlap((0, 0, 10, 10), (5, 5, 20, 20)), 25)
        self.assertEqual(clearance.overlap((0, 0, 10, 10), (10, 0, 20, 10)), 0)

    def test_covered_weighs_pairs(self):
        things = [(0, 0, 10, 10), ((0, 0, 10, 10), 4)]
        self.assertEqual(clearance.covered((0, 0, 5, 5), things), 25 + 4 * 25)


    def test_on_panel_allows_see_through_corners_only(self):
        self.assertTrue(clearance.on_panel((88, 88, 152, 152)))
        self.assertTrue(clearance.on_panel((0, 88, 64, 152)))  # edge, corners in
        self.assertFalse(clearance.on_panel((0, 0, 64, 64)))  # off the round panel


BOTTOM, TOP = (60, 160, 180, 190), (60, 50, 180, 80)  # two caption bands
CLOUD_A, CLOUD_B = [(80, 50, 160, 120)], [(150, 120, 200, 170)]  # two bubble spots


class TestLayout(unittest.TestCase):
    def test_the_caption_takes_the_band_covering_least(self):
        spot, band, covers = clearance.layout([BOTTOM, TOP], [None], [(0, 150, 240, 200)])
        self.assertEqual((spot, band, covers), (None, 1, [TOP]))

    def test_a_tie_goes_to_the_first_band(self):
        self.assertEqual(clearance.layout([BOTTOM, TOP], [None], [])[1], 0)

    def test_no_caption_or_bubble_covers_nothing(self):
        self.assertEqual(clearance.layout([None], [None], [(0, 0, 240, 240)]), (None, None, []))

    def test_the_caption_keeps_off_the_bubble_most_of_all(self):
        # The bubble's first spot sits on the top band: the caption goes low.
        spot, band, covers = clearance.layout([TOP, BOTTOM], [CLOUD_A], [])
        self.assertEqual((spot, band), (0, 1))
        self.assertEqual(covers, CLOUD_A + [BOTTOM])

    def test_a_band_that_makes_a_critter_dance_costs_more(self):
        # The standing critter's feet are under the bottom band: the top one
        # leaves it where it is, so it wins though the bottom comes first.
        dancers = [(HOME[0], HOME[1], SIZE)]
        self.assertEqual(clearance.layout([BOTTOM, TOP], [None], [], dancers)[1], 1)
        self.assertEqual(clearance.layout([BOTTOM, TOP], [None], [])[1], 0)

    def test_the_dance_plan_moves_only_whoever_is_covered(self):
        under = (HOME[0], HOME[1], SIZE)
        clear = (0, 0, SIZE)  # off in a corner, nothing over it
        spots, stuck = clearance.plan_dance([under, clear], [BOTTOM])
        self.assertFalse(stuck)
        self.assertIsNone(spots[1])
        x, y = spots[0]
        swept = (x - clearance.DANCE_SWING, y, x + SIZE + clearance.DANCE_SWING, y + SIZE)
        self.assertEqual(clearance.overlap(swept, clearance.grow(BOTTOM, clearance.DANCE_MARGIN)), 0)

    def test_a_dancer_with_nowhere_to_go_is_stuck(self):
        spots, stuck = clearance.plan_dance([(HOME[0], HOME[1], SIZE)], [(0, 0, 240, 240)])
        self.assertEqual((spots, stuck), ([None], True))


class TestDanceSpot(unittest.TestCase):
    def test_stays_home_when_clear(self):
        self.assertEqual(clearance.dance_spot(HOME, SIZE, [(0, 0, 240, 40)]), HOME)

    def test_moves_clear_of_a_caption_over_it(self):
        caption = (27, 140, 213, 204)
        spot = clearance.dance_spot(HOME, SIZE, [caption])
        self.assertIsNotNone(spot)
        x, y = spot
        swing = clearance.DANCE_SWING
        self.assertEqual(clearance.covered((x - swing, y, x + SIZE + swing, y + SIZE), [caption]), 0)
        self.assertTrue(clearance.on_panel((x - swing, y, x - swing + SIZE, y + SIZE)))
        self.assertTrue(clearance.on_panel((x + swing, y, x + swing + SIZE, y + SIZE)))
        self.assertLessEqual(y + SIZE, caption[1])  # just above it, not far off

    def test_none_when_nowhere_is_clear(self):
        self.assertIsNone(clearance.dance_spot(HOME, SIZE, [(0, 0, 240, 240)]))


class TestThingsIn(unittest.TestCase):
    def test_walks_offsets_and_scales_and_skips_hidden_labels_and_skipped(self):
        root = _Group()
        scaled = _Group(x=10, y=20, scale=2)
        scaled.append(_Grid(5, 5))  # 32px tile at 2x, from (10 + 10, 20 + 10)
        root.append(scaled)
        hidden = _Grid(0, 0)
        hidden.hidden = True
        root.append(hidden)
        root.append(_Label())
        dancer = _Group(x=100, y=100)
        dancer.append(_Grid(0, 0))
        root.append(dancer)
        self.assertEqual(clearance.things_in(root, skip=[dancer]), [(20, 30, 84, 94)])
        self.assertEqual(len(clearance.things_in(root)), 2)

    def test_a_hidden_group_has_nothing(self):
        root = _Group()
        root.append(_Grid(0, 0))
        root.hidden = True
        self.assertEqual(clearance.things_in(root), [])


if __name__ == "__main__":
    unittest.main()
