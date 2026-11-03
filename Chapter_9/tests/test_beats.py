# SPDX-License-Identifier: MIT
# Off-device tests for the comic overlay kit's timing and shapes -- cd-342.9.
#
#   python3 Chapter_9/tests/test_beats.py

import math
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "game"))

import comic_shapes  # noqa: E402
from beats import Beat, BeatPlayer  # noqa: E402

_PANEL_RADIUS = 120


class _Stage:
    def __init__(self):
        self.showing = None
        self.clears = 0

    def show(self, beat, now):
        self.showing = beat

    def clear(self):
        self.showing = None
        self.clears += 1


class TestBeatDurations(unittest.TestCase):
    def test_longer_words_stay_up_longer(self):
        self.assertGreater(
            Beat(caption="Chirpy loves fresh air!").duration, Beat(caption="So close!").duration
        )

    def test_a_burst_is_quick(self):
        self.assertLess(Beat(burst="Bonk!").duration, Beat(caption="So close!").duration)

    def test_an_explicit_duration_wins(self):
        self.assertEqual(Beat(caption="So close!", duration=9).duration, 9)


class TestBeatPlayer(unittest.TestCase):
    def setUp(self):
        self.stage = _Stage()
        self.player = BeatPlayer(self.stage)
        self.first = Beat(caption="one", duration=2)
        self.second = Beat(caption="two", duration=3)

    def test_starts_idle(self):
        self.assertFalse(self.player.active)

    def test_plays_beats_in_order_on_their_timers(self):
        self.player.play([self.first, self.second], 10)
        self.assertIs(self.stage.showing, self.first)
        self.player.update(11.9)
        self.assertIs(self.stage.showing, self.first)
        self.player.update(12)
        self.assertIs(self.stage.showing, self.second)
        self.assertTrue(self.player.active)
        self.player.update(15)
        self.assertIsNone(self.stage.showing)
        self.assertFalse(self.player.active)

    def test_tap_moves_to_the_next_beat_and_restarts_its_timer(self):
        self.player.play([self.first, self.second], 10)
        self.player.tap(10.5)
        self.assertIs(self.stage.showing, self.second)
        self.player.update(13.4)
        self.assertIs(self.stage.showing, self.second)
        self.player.update(13.5)
        self.assertFalse(self.player.active)

    def test_tap_on_the_last_beat_clears_it(self):
        self.player.play([self.first], 10)
        self.player.tap(10.5)
        self.assertFalse(self.player.active)
        self.assertIsNone(self.stage.showing)

    def test_play_replaces_what_is_playing(self):
        self.player.play([self.first, self.second], 10)
        replacement = Beat(burst="Bonk!")
        self.player.play([replacement], 10.5)
        self.assertIs(self.stage.showing, replacement)
        self.player.update(20)
        self.assertFalse(self.player.active)

    def test_playing_nothing_clears_the_stage(self):
        self.player.play([self.first], 10)
        self.player.play([], 10.5)
        self.assertFalse(self.player.active)
        self.assertIsNone(self.stage.showing)

    def test_tap_while_idle_does_nothing(self):
        self.player.tap(10)
        self.assertEqual(self.stage.clears, 0)


def _on_panel(points):
    return all(
        math.hypot(x - _PANEL_RADIUS, y - _PANEL_RADIUS) <= _PANEL_RADIUS for x, y in points
    )


class TestShapes(unittest.TestCase):
    def test_a_burst_stays_on_the_panel_at_any_word_width(self):
        for width in range(20, 240, 10):
            rx, ry = comic_shapes.burst_radii(width)
            with self.subTest(width=width):
                self.assertTrue(_on_panel(comic_shapes.burst_points(120, 120, rx, ry, grow=3)))

    def test_a_burst_alternates_out_and_in(self):
        points = comic_shapes.burst_points(120, 120, 100, 50)
        self.assertEqual(len(points), 24)
        self.assertEqual(points[0], (220, 120))
        self.assertLess(abs(points[1][0] - 120), 100)

    def test_the_longest_planned_sound_word_fits_inside_its_burst(self):
        rx, _ry = comic_shapes.burst_radii(112)  # RATTLE!/SQUEAK! are about this wide
        self.assertGreaterEqual(rx * comic_shapes.BURST_WAIST, 112 / 2)

    def test_a_balloon_tail_reaches_its_target(self):
        below = comic_shapes.balloon_points(120, 72, 150, 60, (120, 200))
        above = comic_shapes.balloon_points(120, 168, 150, 60, (120, 40))
        self.assertIn((120, 200), below)
        self.assertIn((120, 40), above)

    def test_the_outline_is_wider_than_the_fill(self):
        fill = comic_shapes.balloon_points(120, 72, 150, 60, (120, 200))
        outline = comic_shapes.balloon_points(120, 72, 150, 60, (120, 200), grow=2)
        self.assertGreater(
            max(x for x, _y in outline), max(x for x, _y in fill)
        )

    def test_a_balloon_at_the_text_budget_stays_on_the_panel(self):
        # Two 15-character lines of Bangers, in the upper and lower positions.
        self.assertTrue(_on_panel(
            comic_shapes.balloon_points(120, 72, 176, 60, (120, 200), grow=2)
        ))
        self.assertTrue(_on_panel(
            comic_shapes.balloon_points(120, 168, 176, 60, (120, 40), grow=2)
        ))

    def test_the_ring_is_solid_at_the_rim_and_clear_in_the_middle(self):
        spans = comic_shapes.ring_spans(240, 6)
        rows = {}
        for y, x0, x1 in spans:
            rows.setdefault(y, []).append((x0, x1))
        self.assertEqual(rows[0], [(0, 240)])
        self.assertEqual(rows[239], [(0, 240)])
        self.assertEqual(rows[120], [(0, 7), (233, 240)])  # 6px, plus rounding

    def test_every_ring_span_stays_inside_the_bitmap(self):
        for y, x0, x1 in comic_shapes.ring_spans(240, 6):
            self.assertTrue(0 <= y < 240)
            self.assertTrue(0 <= x0 < x1 <= 240)


class TestEmanata(unittest.TestCase):
    def test_the_full_set_exists(self):
        self.assertEqual(
            set(comic_shapes.EMANATA),
            {"wiggle", "bang", "question", "heart", "zzz", "sweat", "dust", "speed"},
        )

    def test_every_glyph_is_16_by_16_with_known_inks(self):
        for name, rows in comic_shapes.EMANATA.items():
            with self.subTest(glyph=name):
                self.assertEqual(len(rows), 16)
                for row in rows:
                    self.assertEqual(len(row), 16, row)
                    self.assertTrue(set(row) <= set(comic_shapes.INK_INDEX), row)

    def test_every_ink_has_a_color(self):
        self.assertEqual(len(comic_shapes.COLORS), len(comic_shapes.INK_INDEX))


if __name__ == "__main__":
    unittest.main()
