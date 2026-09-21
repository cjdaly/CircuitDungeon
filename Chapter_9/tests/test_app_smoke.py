# SPDX-License-Identifier: MIT
# Off-device smoke test for game/app.py's main loop -- cd-342.2.
#
#   python3 Chapter_9/tests/test_app_smoke.py
#
# app.run() takes its hardware as arguments, and the displayio-family
# modules it draws with are stubbed here with just enough surface to be
# constructed and poked. This catches wiring bugs (wrong attribute, wrong
# call shape, mode/blanker/gesture interplay) that otherwise only show up as
# a black screen on the board. It does NOT check what anything looks like --
# rendering is still desk-checked / on-device.

import gc
import os
import sys
import types
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "game"))

_STUBBED = ("displayio", "vectorio", "terminalio", "adafruit_display_text",
            "adafruit_display_text.bitmap_label")
_GAME_MODULES = ("app", "nav_view", "room_banner", "ornament")
_saved = {}
_labels = []


class _Group(list):
    pass


class _Bitmap:
    def __init__(self, *a, **k):
        pass


class _Palette(dict):
    def __init__(self, n=1):
        super().__init__()


class _TileGrid:
    def __init__(self, *a, **k):
        pass


class _Shape:
    def __init__(self, **kw):
        self.__dict__.update(kw)


class _Label:
    def __init__(self, font, **kw):
        self.text = ""
        self.__dict__.update(kw)
        _labels.append(self)


def setUpModule():
    if not hasattr(gc, "mem_free"):  # CircuitPython-only
        gc.mem_free = lambda: 0
    for name in _STUBBED + _GAME_MODULES:
        _saved[name] = sys.modules.pop(name, None)
    displayio = types.ModuleType("displayio")
    displayio.Group, displayio.Bitmap = _Group, _Bitmap
    displayio.Palette, displayio.TileGrid = _Palette, _TileGrid
    vectorio = types.ModuleType("vectorio")
    vectorio.Circle = vectorio.Rectangle = vectorio.Polygon = _Shape
    terminalio = types.ModuleType("terminalio")
    terminalio.FONT = object()
    pkg = types.ModuleType("adafruit_display_text")
    bl = types.ModuleType("adafruit_display_text.bitmap_label")
    bl.Label = _Label
    pkg.bitmap_label = bl
    sys.modules.update({
        "displayio": displayio, "vectorio": vectorio, "terminalio": terminalio,
        "adafruit_display_text": pkg, "adafruit_display_text.bitmap_label": bl,
    })


def tearDownModule():
    if getattr(gc.mem_free, "__name__", "") == "<lambda>":
        del gc.mem_free
    for name, mod in _saved.items():
        if mod is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = mod


class _Display:
    root_group = None


class _Backlight:
    value = True


class _Clock:
    def __init__(self):
        self.t = 100.0
        self.on_tick = None

    def now(self):
        return self.t

    def sleep(self, dt):
        self.t += dt
        if self.on_tick:
            self.on_tick()


class _Touch:
    """Scripted touch: `windows` = [(t0, t1, fn(t_into_window) -> (x, y))]."""

    def __init__(self, clock, windows):
        self._clock, self._windows = clock, windows

    def poll(self, now):
        rel = now - 100.0
        for t0, t1, fn in self._windows:
            if t0 <= rel < t1:
                return fn(rel - t0)
        return None


class _Imu:
    def __init__(self, jerk=0.0):
        self.jerk = jerk

    def sample(self, now):
        return {"jerk": self.jerk}


def _at(x, y):
    return lambda dt: (x, y)


def _swipe_right_from(x, y):
    return lambda dt: (int(x + dt * 100), y)


class _Run:
    """Runs app.run() for `seconds` of fake time and records what's on screen."""

    def __init__(self, windows=(), jerk=0.0, seconds=5.0):
        _labels.clear()
        import app  # after stubs are in place

        self.clock = _Clock()
        self.display, self.backlight = _Display(), _Backlight()
        self.imu = _Imu(jerk)
        self.groups = []  # root_group at the end of each tick

        def on_tick():
            self.groups.append(self.display.root_group)

        self.clock.on_tick = on_tick
        app.run(
            self.display, self.backlight, _Touch(self.clock, windows), self.imu,
            240, 240, max_ticks=int(seconds / 0.05),
            clock=self.clock.now, sleep=self.clock.sleep,
        )
        self.nav_group = self.groups[0]

    def room(self):
        return [lb for lb in _labels if lb.anchored_position == (120, 100)][0].text

    def banner(self):
        return [lb for lb in _labels if lb.anchored_position == (120, 172)][0].text


class TestAppSmoke(unittest.TestCase):
    def test_starts_in_living_room_interactive(self):
        r = _Run(seconds=1.0)
        self.assertEqual(r.room(), "Living Room")
        self.assertIs(r.display.root_group, r.nav_group)

    def test_swipe_from_left_edge_moves_to_entryway(self):
        r = _Run(windows=[(0.5, 0.9, _swipe_right_from(10, 120))], seconds=3.0)
        self.assertEqual(r.room(), "Entryway")

    def test_swipe_from_center_does_not_move(self):
        r = _Run(windows=[(0.5, 0.9, _swipe_right_from(100, 120))], seconds=3.0)
        self.assertEqual(r.room(), "Living Room")

    def test_blocked_edge_flashes_banner(self):
        # Living Room has no UP exit.
        r = _Run(windows=[(0.5, 0.7, _at(120, 10))], seconds=2.0)
        self.assertEqual(r.room(), "Living Room")
        self.assertEqual(r.banner(), "can't go up")

    def test_idle_and_still_goes_to_ornament(self):
        r = _Run(seconds=35.0)
        self.assertIsNot(r.display.root_group, r.nav_group)
        self.assertTrue(r.backlight.value)

    def test_idle_but_handled_stays_interactive(self):
        r = _Run(jerk=10.0, seconds=35.0)
        self.assertIs(r.display.root_group, r.nav_group)

    def test_touch_wakes_ornament_and_is_swallowed(self):
        # Ornament by ~33s; then a left-edge swipe that would move a room
        # if it weren't swallowed as the wake-up touch.
        r = _Run(windows=[(40.0, 40.4, _swipe_right_from(10, 120))], seconds=45.0)
        self.assertIs(r.display.root_group, r.nav_group)
        self.assertEqual(r.room(), "Living Room")

    def test_navigation_works_again_after_waking_from_ornament(self):
        r = _Run(
            windows=[
                (40.0, 40.4, _swipe_right_from(10, 120)),  # wakes, swallowed
                (42.0, 42.4, _swipe_right_from(10, 120)),  # real move
            ],
            seconds=45.0,
        )
        self.assertEqual(r.room(), "Entryway")

    def test_interactive_blanks_when_handled_but_untouched(self):
        r = _Run(jerk=10.0, seconds=125.0)
        self.assertFalse(r.backlight.value)


if __name__ == "__main__":
    unittest.main()
