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

STATUS: confirmed on ws-1 2026-11-02 in Chapter_9, including repeat visits to
ornament mode (the star, randomized ornaments and snow timing are Ch9 changes).
"""
import math
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
_COLOR_HOLD_MIN = 0.5  # seconds an ornament keeps a color, picked at random
_COLOR_HOLD_MAX = 3.0

# Tree geometry -- kept well inside the round bezel's ~20-30px inset
# (Chapter_8/doc/HARDWARE.md "Display"). Fixed absolute positions, matching
# this board's known 240x240 resolution.
_APEX = (120, 66)
_BASE_L = (78, 168)
_BASE_R = (162, 168)
_TRUNK = {"x": 110, "y": 168, "width": 20, "height": 24}
_ORNAMENT_COUNT = 5
_ORNAMENT_RADIUS = 5
_ORNAMENT_MIN_GAP = 20  # px between centers, so they don't overlap or clump
_ORNAMENT_TOP_Y = 86  # placement band, clear of the star and the tree's base
_ORNAMENT_BOTTOM_Y = 158
_STAR_CENTER = (120, 58)
_STAR_OUTER = 13
_STAR_INNER = 5

_SNOW_COUNT = 6
_SNOW_SPEED = 22  # px/second
# Longest time step one update can apply. Snow only updates in ornament mode, so
# without this, returning to the mode wraps every flake to y=0 on one tick and
# they fall as a single row from then on.
_SNOW_MAX_DT = 0.25  # seconds


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


def _star_points(center, outer, inner):
    """Outline of a 5-point star with one tip straight up: tip, notch, tip, ..."""
    points = []
    for i in range(10):
        radius = inner if i % 2 else outer
        angle = math.radians(i * 36 - 90)
        points.append(
            (
                center[0] + int(round(radius * math.cos(angle))),
                center[1] + int(round(radius * math.sin(angle))),
            )
        )
    return points


def _scatter_positions(count=_ORNAMENT_COUNT, randint=random.randint):
    """Random ornament centers inside the tree, kept apart where possible."""
    positions = []
    apex_x, apex_y = _APEX
    tree_half = _BASE_R[0] - apex_x
    tree_height = _BASE_R[1] - apex_y
    for _ in range(count):
        best = None
        best_gap2 = -1
        for _attempt in range(30):
            y = randint(_ORNAMENT_TOP_Y, _ORNAMENT_BOTTOM_Y)
            half = (y - apex_y) * tree_half // tree_height - _ORNAMENT_RADIUS - 1
            x = randint(apex_x - half, apex_x + half)
            gap2 = min(
                ((x - px) ** 2 + (y - py) ** 2 for px, py in positions),
                default=_ORNAMENT_MIN_GAP ** 2,
            )
            if gap2 > best_gap2:
                best, best_gap2 = (x, y), gap2
            if gap2 >= _ORNAMENT_MIN_GAP ** 2:
                break
        positions.append(best)
    return positions


def _next_color_index(current, count=len(_ORNAMENT_COLORS), randint=random.randint):
    """A random color index that always differs from `current`."""
    index = randint(0, count - 2)
    return index + 1 if index >= current else index


class _Ornament:
    def __init__(self, palette, shape, color_index):
        self.palette = palette
        self.shape = shape
        self.color_index = color_index
        self.next_change = 0.0


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
            vectorio.Polygon(
                pixel_shader=self._star_palette,
                points=_star_points(_STAR_CENTER, _STAR_OUTER, _STAR_INNER),
            )
        )

        self._ornaments = []
        for i, (x, y) in enumerate(_scatter_positions()):
            color_index = i % len(_ORNAMENT_COLORS)
            palette = _solid(_ORNAMENT_COLORS[color_index])
            shape = vectorio.Circle(
                pixel_shader=palette, x=x, y=y, radius=_ORNAMENT_RADIUS
            )
            group.append(shape)
            self._ornaments.append(_Ornament(palette, shape, color_index))

    def scatter(self):
        """Move the ornaments to a new random layout."""
        for ornament, (x, y) in zip(self._ornaments, _scatter_positions()):
            ornament.shape.x = x
            ornament.shape.y = y

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

        hold_range = _COLOR_HOLD_MAX - _COLOR_HOLD_MIN
        for ornament in self._ornaments:
            if now >= ornament.next_change:
                ornament.color_index = _next_color_index(ornament.color_index)
                ornament.palette[0] = _ORNAMENT_COLORS[ornament.color_index]
                ornament.next_change = now + _COLOR_HOLD_MIN + random.random() * hold_range


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
        dt = min(now - self._last_update, _SNOW_MAX_DT)
        self._last_update = now
        step = _SNOW_SPEED * dt
        for flake in self._flakes:
            flake.y = int(flake.y + step)
            if flake.y > self._height:
                flake.y = 0
                flake.x = random.randint(10, self._width - 10)
