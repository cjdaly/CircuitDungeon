# SPDX-License-Identifier: MIT
"""Ambient ornament-mode scene: a small animated Christmas tree -- cd-zw2.7.

A separate top-level mode (no gameplay, no input expected) so the device
can be hung as a physical ornament on a real tree and show an ambient/idle
demo. Ported from Chapter_8/game/ornament_demo.py (cd-45v.5's prototype) --
confirmed working on real hardware 2026-09-13 (scene renders correctly,
dims while "handled" per stillness.py, brightens once "still").

Twinkling ornaments, a pulsing star, drifting snow -- all vectorio
primitives, no bitmap art needed (none exists for Ch9 yet). These are
placeholder shapes, not final art; `Tree`/`Snow` take a `group` to draw
into and a `lit`/`now` signal to animate, same as the Ch8 prototype, so
swapping in real art later means replacing what's inside these classes,
not how callers use them.

This module is the scene only -- no `main()`, no `hardware`/`imu` calls.
Wiring it into an actual on-device entry point (display init, IMU sampling,
stillness.StillnessDetector, screen_blanker.ScreenBlanker with a long
timeout, the mode-switching between this and interactive gameplay) is
future Ch9 integration work, not yet a numbered bead.

STATUS: ported, not yet re-tested on-device in Chapter_9 -- displayio isn't
importable under plain desktop Python, so this can only be desk-checked
here. The underlying scene and animation are already proven on Chapter 8
hardware.
"""
import random

WIDTH = HEIGHT = 240

_BG_COLOR = 0x05050C
_TREE_COLOR = 0x1E7A34
_TREE_DIM = 0x0E3A18
_TRUNK_COLOR = 0x5A3A1E
_STAR_BRIGHT = 0xF5E050
_STAR_DIM = 0x806000
_SNOW_COLOR = 0xE8F0FF

_ORNAMENT_COLORS = (0xE04040, 0x4070E0, 0xF0C020, 0xFFFFFF)
_ORNAMENT_PERIOD = 1.6  # seconds per color-cycle step, staggered per ornament

# Tree geometry -- kept well inside the round bezel's ~20-30px inset
# (Chapter_8/doc/HARDWARE.md "Display"). Fixed absolute positions, matching
# this board's known 240x240 resolution.
_APEX = (120, 66)
_BASE_L = (78, 168)
_BASE_R = (162, 168)
_TRUNK = {"x": 110, "y": 168, "width": 20, "height": 24}
_ORNAMENT_POS = ((105, 100), (135, 100), (95, 130), (145, 130), (120, 150))

_SNOW_COUNT = 6
_SNOW_SPEED = 22  # px/second


def make_background(group, width=WIDTH, height=HEIGHT, color=_BG_COLOR):
    import displayio

    bg_bitmap = displayio.Bitmap(width, height, 1)
    bg_palette = displayio.Palette(1)
    bg_palette[0] = color
    group.append(displayio.TileGrid(bg_bitmap, pixel_shader=bg_palette))


def _solid(color):
    import displayio

    palette = displayio.Palette(1)
    palette[0] = color
    return palette


def _blend(color_a, color_b, t):
    """Linear-interpolate two 0xRRGGBB colors; t=0 -> a, t=1 -> b."""
    ar, ag, ab = (color_a >> 16) & 0xFF, (color_a >> 8) & 0xFF, color_a & 0xFF
    br, bg, bb = (color_b >> 16) & 0xFF, (color_b >> 8) & 0xFF, color_b & 0xFF
    r = int(ar + (br - ar) * t)
    g = int(ag + (bg - ag) * t)
    b = int(ab + (bb - ab) * t)
    return (r << 16) | (g << 8) | b


class Tree:
    """The tree + star + ornaments. .update(now, lit) drives the animation."""

    def __init__(self, group):
        import vectorio

        self._tree_palette = _solid(_TREE_COLOR)
        points = [_APEX, _BASE_L, _BASE_R]
        group.append(vectorio.Polygon(pixel_shader=self._tree_palette, points=points))
        group.append(
            vectorio.Rectangle(pixel_shader=_solid(_TRUNK_COLOR), **_TRUNK)
        )

        self._star_palette = _solid(_STAR_BRIGHT)
        group.append(
            vectorio.Circle(
                pixel_shader=self._star_palette, x=_APEX[0], y=_APEX[1] - 6, radius=6
            )
        )

        self._ornaments = []
        for i, (x, y) in enumerate(_ORNAMENT_POS):
            palette = _solid(_ORNAMENT_COLORS[i % len(_ORNAMENT_COLORS)])
            group.append(vectorio.Circle(pixel_shader=palette, x=x, y=y, radius=5))
            self._ornaments.append((palette, i * 0.3))

    def update(self, now, lit):
        """`lit` should track stillness.StillnessDetector.is_still."""
        self._tree_palette[0] = _TREE_COLOR if lit else _TREE_DIM
        if not lit:
            self._star_palette[0] = _STAR_DIM
            return
        # Slow star pulse between dim and bright gold.
        phase = (now % 2.0) / 2.0
        brightness = 0.6 + 0.4 * abs(1 - 2 * phase)
        self._star_palette[0] = _blend(_STAR_DIM, _STAR_BRIGHT, brightness)

        for palette, phase_offset in self._ornaments:
            step = int((now + phase_offset) / _ORNAMENT_PERIOD) % len(_ORNAMENT_COLORS)
            palette[0] = _ORNAMENT_COLORS[step]


class Snow:
    """Drifting snow dots. .update(now) drives them regardless of `lit`."""

    def __init__(self, group, width=WIDTH, height=HEIGHT):
        import vectorio

        self._width = width
        self._height = height
        self._palette = _solid(_SNOW_COLOR)
        self._flakes = []
        for _ in range(_SNOW_COUNT):
            x = random.randint(10, width - 10)
            y = random.randint(0, height)
            flake = vectorio.Circle(pixel_shader=self._palette, x=x, y=y, radius=2)
            group.append(flake)
            self._flakes.append(flake)
        self._last_update = None

    def update(self, now):
        if self._last_update is None:
            self._last_update = now
            return
        dt = now - self._last_update
        self._last_update = now
        step = _SNOW_SPEED * dt
        for flake in self._flakes:
            flake.y = int(flake.y + step)
            if flake.y > self._height:
                flake.y = 0
                flake.x = random.randint(10, self._width - 10)
