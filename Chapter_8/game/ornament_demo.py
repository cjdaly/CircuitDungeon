# SPDX-License-Identifier: MIT
"""Ambient/idle ornament-mode tryout -- cd-45v.5 prototype (relates to Ch9's
cd-zw2.7).

Not main.py: run this standalone (rename to main.py or `import
ornament_demo` from a scratch main.py). Proves out Ch9's "hang the device on
a real tree, no input expected" ornament mode: a small animated Christmas
tree (twinkling ornaments, a pulsing star, drifting snow) drawn entirely
with vectorio primitives -- no bitmap art exists yet, and this doesn't need
any.

Also proves the IMU-driven mode signal from stillness.py: StillnessDetector
watches imu.py's jerk reading and flips to "still" after a few quiet
seconds, standing in for "the device is actually hanging" vs. "someone's
carrying it to the tree". The animation runs either way (ornament mode has
no input, so there's nothing to gate on stillness alone), but it dims and
the twinkling pauses while "handled", as a first cut at the kind of thing
that signal could drive. A bottom debug line shows the raw state -- that
line is a prototype aid, not part of the eventual no-UI ornament mode.

Screen blanking (screen_blanker.py, cd-ork.2) uses a much longer timeout
than main.py's normal-mode default (cd-ork.1) -- the whole point of
ornament mode is to be glanced at across a room, so a short touch-style
timeout would defeat it. There's no touchscreen input to treat as
"activity" here, so being picked up (StillnessDetector reporting "handled")
stands in for it instead: the screen wakes the instant it's handled, and
only blanks after a long stretch of continuous "still".

STATUS: scene, stillness-driven dimming, and screen-blanking (cd-ork.2)
all confirmed on-device 2026-09-13 (ws-2 for the scene, ws-1 for blanking
-- tested with a temporarily shortened timeout, then restored to the real
300s). Blanks after continuous stillness, wakes instantly on being
handled, as designed. The 300s figure itself is still a first guess, not
tuned against real battery-life data.
"""
import random
import time

import displayio
import terminalio
import vectorio
from adafruit_display_text.bitmap_label import Label

import hardware
import imu as imu_gestures
import stillness
from screen_blanker import ScreenBlanker

_BG_COLOR = 0x05050C
_TREE_COLOR = 0x1E7A34
_TREE_DIM = 0x0E3A18
_TRUNK_COLOR = 0x5A3A1E
_STAR_BRIGHT = 0xF5E050
_STAR_DIM = 0x806000
_SNOW_COLOR = 0xE8F0FF
_DEBUG_COLOR = 0x707070

_ORNAMENT_COLORS = (0xE04040, 0x4070E0, 0xF0C020, 0xFFFFFF)
_ORNAMENT_PERIOD = 1.6  # seconds per color-cycle step, staggered per ornament

# Tree geometry -- kept well inside the round bezel's ~20-30px inset
# (doc/HARDWARE.md "Display").
_APEX = (120, 66)
_BASE_L = (78, 168)
_BASE_R = (162, 168)
_TRUNK = {"x": 110, "y": 168, "width": 20, "height": 24}
_ORNAMENT_POS = ((105, 100), (135, 100), (95, 130), (145, 130), (120, 150))

_SNOW_COUNT = 6
_SNOW_SPEED = 22  # px/second

_DEBUG_Y = 216

# Much longer than main.py's normal-mode default (cd-ork.1, 20s) -- the
# point of ornament mode is to be visible across a room, not just while
# someone's actively touching it. Being "handled" (picked up/moved) stands
# in for touch-as-activity, since there's no touchscreen input here.
_BLANK_TIMEOUT = 300.0  # 5 minutes of continuous stillness before blanking


def _make_group(display):
    group = displayio.Group()
    display.root_group = group

    bg_bitmap = displayio.Bitmap(hardware.WIDTH, hardware.HEIGHT, 1)
    bg_palette = displayio.Palette(1)
    bg_palette[0] = _BG_COLOR
    group.append(displayio.TileGrid(bg_bitmap, pixel_shader=bg_palette))
    return group


def _solid(color):
    palette = displayio.Palette(1)
    palette[0] = color
    return palette


class Tree:
    def __init__(self, group):
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
    def __init__(self, group):
        self._palette = _solid(_SNOW_COLOR)
        self._flakes = []
        for _ in range(_SNOW_COUNT):
            x = random.randint(10, hardware.WIDTH - 10)
            y = random.randint(0, hardware.HEIGHT)
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
            if flake.y > hardware.HEIGHT:
                flake.y = 0
                flake.x = random.randint(10, hardware.WIDTH - 10)


def _blend(color_a, color_b, t):
    """Linear-interpolate two 0xRRGGBB colors; t=0 -> a, t=1 -> b."""
    ar, ag, ab = (color_a >> 16) & 0xFF, (color_a >> 8) & 0xFF, color_a & 0xFF
    br, bg, bb = (color_b >> 16) & 0xFF, (color_b >> 8) & 0xFF, color_b & 0xFF
    r = int(ar + (br - ar) * t)
    g = int(ag + (bg - ag) * t)
    b = int(ab + (bb - ab) * t)
    return (r << 16) | (g << 8) | b


def main():
    display, backlight = hardware.init_display()
    i2c = hardware.init_i2c()
    imu = hardware.init_imu(i2c)
    gestures = imu_gestures.ImuGestures(imu)
    detector = stillness.StillnessDetector()
    blanker = ScreenBlanker(backlight, timeout=_BLANK_TIMEOUT)

    group = _make_group(display)
    tree = Tree(group)
    snow = Snow(group)
    l_debug = Label(
        terminalio.FONT,
        text="",
        color=_DEBUG_COLOR,
        anchor_point=(0.5, 0.5),
        anchored_position=(hardware.WIDTH // 2, _DEBUG_Y),
    )
    group.append(l_debug)

    print("Ch8 ornament demo ready")

    while True:
        now = time.monotonic()
        try:
            sample = gestures.sample(now)
            is_still = detector.update(sample["jerk"], now)
        except (OSError, ValueError, RuntimeError):
            is_still = detector.is_still  # hold last-known mode on a read glitch

        blanker.update(not is_still, now)  # "handled" counts as activity

        tree.update(now, lit=is_still)
        snow.update(now)
        l_debug.text = "still" if is_still else "handled"

        time.sleep(0.05)


main()
