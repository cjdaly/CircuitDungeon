# SPDX-License-Identifier: MIT
# Off-device tests for game/sprite_scale.py's clamp_actor_position() -- pure
# arithmetic, no hardware. make_scenery_grid()/make_actor() need displayio
# and can't be unit tested (see the module docstring).
#
#   python3 Chapter_9/tests/test_sprite_scale.py

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "game"))

import sprite_scale  # noqa: E402

WIDTH = HEIGHT = 240


class TestClampActorPosition(unittest.TestCase):
    def test_position_already_inside_margin_is_unchanged(self):
        x, y = sprite_scale.clamp_actor_position(100, 100, WIDTH, HEIGHT)
        self.assertEqual((x, y), (100, 100))

    def test_position_past_left_top_edge_clamps_to_margin(self):
        x, y = sprite_scale.clamp_actor_position(-50, -50, WIDTH, HEIGHT)
        self.assertEqual((x, y), (sprite_scale.EDGE_MARGIN, sprite_scale.EDGE_MARGIN))

    def test_position_past_right_bottom_edge_clamps_inside_margin(self):
        x, y = sprite_scale.clamp_actor_position(500, 500, WIDTH, HEIGHT)
        size = sprite_scale.ACTOR_SIZE
        margin = sprite_scale.EDGE_MARGIN
        self.assertEqual((x, y), (WIDTH - margin - size, HEIGHT - margin - size))

    def test_custom_size_and_margin_respected(self):
        x, y = sprite_scale.clamp_actor_position(
            0, 0, WIDTH, HEIGHT, size=16, margin=10
        )
        self.assertEqual((x, y), (10, 10))

    def test_exact_boundary_is_unchanged(self):
        margin = sprite_scale.EDGE_MARGIN
        size = sprite_scale.ACTOR_SIZE
        hi_x, hi_y = WIDTH - margin - size, HEIGHT - margin - size
        x, y = sprite_scale.clamp_actor_position(hi_x, hi_y, WIDTH, HEIGHT)
        self.assertEqual((x, y), (hi_x, hi_y))


if __name__ == "__main__":
    unittest.main()
