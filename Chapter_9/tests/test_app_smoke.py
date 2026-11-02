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


_LEFT_EDGE, _RIGHT_EDGE = _at(10, 120), _at(230, 120)
_TOP_EDGE, _BOTTOM_EDGE = _at(120, 10), _at(120, 230)
_CENTER = _at(120, 120)


class _Run:
    """Runs app.run() for `seconds` of fake time and records what's on screen."""

    def __init__(self, windows=(), jerk=0.0, seconds=5.0, imu=None, bus_recovery=None):
        _labels.clear()
        import app  # after stubs are in place

        self.clock = _Clock()
        self.display, self.backlight = _Display(), _Backlight()
        self.imu = imu if imu is not None else _Imu(jerk)
        self.groups = []  # root_group at the end of each tick

        def on_tick():
            self.groups.append(self.display.root_group)

        self.clock.on_tick = on_tick
        app.run(
            self.display, self.backlight, _Touch(self.clock, windows), self.imu,
            240, 240, max_ticks=int(seconds / 0.05),
            clock=self.clock.now, sleep=self.clock.sleep, bus_recovery=bus_recovery,
        )
        self.nav_group = self.groups[0]

    def room(self):
        return [lb for lb in _labels if lb.anchored_position == (120, 100)][0].text

    def banner(self):
        return [lb for lb in _labels if lb.anchored_position == (120, 172)][0].text

    def message(self):
        """The banner text as one line, with wrapping and centering undone."""
        return " ".join(line.strip() for line in self.banner().split("\n"))

    def held(self):
        return [lb for lb in _labels if lb.anchored_position == (120, 72)][0].text


class _StalledImu:
    """Times out on every read until `healthy` is set."""

    healthy = False
    reads = 0

    def sample(self, now):
        self.reads += 1
        if not self.healthy:
            raise OSError(116, "ETIMEDOUT")
        return {"jerk": 0.0}


class _Recovery:
    def __init__(self, imu=None):
        self.imu = imu  # healed by rebuild, if given
        self.calls = 0

    def rebuild(self):
        self.calls += 1
        if self.imu is not None:
            self.imu.healthy = True
        return "ok"


class TestBusRecoveryWiring(unittest.TestCase):
    def test_imu_timeout_triggers_one_rebuild_when_it_helps(self):
        imu = _StalledImu()
        recovery = _Recovery(imu)
        _Run(imu=imu, bus_recovery=recovery, seconds=3.0)
        self.assertEqual(recovery.calls, 1)
        self.assertGreater(imu.reads, 10)

    def test_rebuilds_are_rate_limited_when_they_do_not_help(self):
        recovery = _Recovery()
        _Run(imu=_StalledImu(), bus_recovery=recovery, seconds=10.0)
        self.assertIn(recovery.calls, (2, 3))

    def test_healthy_imu_never_rebuilds(self):
        recovery = _Recovery()
        _Run(bus_recovery=recovery, seconds=3.0)
        self.assertEqual(recovery.calls, 0)

    def test_stalled_imu_without_recovery_keeps_running(self):
        imu = _StalledImu()
        _Run(imu=imu, seconds=1.0)
        self.assertEqual(imu.reads, 20)


def _taps(*touches, start=0.5, spacing=0.5):
    """Scripted short taps, one every `spacing` seconds."""
    return [
        (start + i * spacing, start + i * spacing + 0.2, touch)
        for i, touch in enumerate(touches)
    ]


class TestEpisodeOne(unittest.TestCase):
    TO_YARN = (_RIGHT_EDGE, _TOP_EDGE)
    YARN_TO_CAT = (_BOTTOM_EDGE, _RIGHT_EDGE, _RIGHT_EDGE)
    CAT_TO_TREE = (_LEFT_EDGE, _LEFT_EDGE, _LEFT_EDGE)

    def test_opening_announces_the_escape(self):
        r = _Run(seconds=1.0)
        self.assertEqual(r.message(), "CHIRPY ESCAPED!")

    def test_closed_exit_shows_its_reason_and_does_not_move(self):
        r = _Run(windows=_taps(_LEFT_EDGE), seconds=1.5)
        self.assertEqual(r.room(), "Living Room")
        self.assertEqual(r.message(), "BRR! TOO COLD OUT THERE")

    def test_center_tap_takes_the_yarn(self):
        r = _Run(windows=_taps(*self.TO_YARN, _CENTER), seconds=2.5)
        self.assertEqual(r.room(), "Sewing Nook")
        self.assertEqual(r.message(), "GOT THE BALL OF YARN!")
        self.assertEqual(r.held(), "Holding ball of yarn")

    def test_edge_tap_in_the_yarn_room_does_not_take_it(self):
        r = _Run(windows=_taps(*self.TO_YARN, _LEFT_EDGE), seconds=2.5)
        self.assertEqual(r.held(), "")

    def test_a_swipe_from_the_center_does_not_count_as_a_tap(self):
        touches = _taps(*self.TO_YARN) + [(1.5, 1.9, _swipe_right_from(90, 120))]
        r = _Run(windows=touches, seconds=2.5)
        self.assertEqual(r.held(), "")

    def test_cat_without_yarn_says_what_it_wants(self):
        r = _Run(windows=_taps(_RIGHT_EDGE, _RIGHT_EDGE, _RIGHT_EDGE, _CENTER), seconds=3.0)
        self.assertEqual(r.room(), "Sun Porch")
        self.assertEqual(r.message(), "FOUND CHIRPY!")

    def test_messages_play_in_sequence(self):
        r = _Run(windows=_taps(_RIGHT_EDGE, _RIGHT_EDGE, _RIGHT_EDGE, _CENTER), seconds=7.0)
        self.assertEqual(r.message(), "SHE WANTS THE BALL OF YARN")

    def test_full_episode_from_escape_to_home(self):
        touches = _taps(
            *self.TO_YARN, _CENTER, *self.YARN_TO_CAT, _CENTER, *self.CAT_TO_TREE
        )
        r = _Run(windows=touches, seconds=6.0)
        self.assertEqual(r.room(), "Living Room")
        self.assertEqual(r.held(), "")
        self.assertEqual(r.message(), "CHIRPY CURLS UP ON THE RUG")

        r = _Run(windows=touches, seconds=9.0)
        self.assertEqual(r.message(), "ALL HOME! MORE CRITTERS SOON")

    def test_map_opens_after_the_last_episode(self):
        touches = _taps(
            *self.TO_YARN, _CENTER, *self.YARN_TO_CAT, _CENTER, *self.CAT_TO_TREE,
            _LEFT_EDGE,
        )
        r = _Run(windows=touches, seconds=7.0)
        self.assertEqual(r.room(), "Entryway")


class TestAppSmoke(unittest.TestCase):
    def test_starts_in_living_room_interactive(self):
        r = _Run(seconds=1.0)
        self.assertEqual(r.room(), "Living Room")
        self.assertIs(r.display.root_group, r.nav_group)

    def test_tap_on_right_edge_moves_to_dining_room(self):
        r = _Run(windows=[(0.5, 0.7, _RIGHT_EDGE)], seconds=3.0)
        self.assertEqual(r.room(), "Dining Room")

    def test_swipe_from_left_edge_moves_when_that_exit_is_open(self):
        r = _Run(
            windows=[
                (0.5, 0.7, _RIGHT_EDGE),
                (1.0, 1.4, _swipe_right_from(10, 120)),  # back to the Living Room
            ],
            seconds=3.0,
        )
        self.assertEqual(r.room(), "Living Room")

    def test_swipe_from_center_does_not_move(self):
        r = _Run(windows=[(0.5, 0.9, _swipe_right_from(100, 120))], seconds=3.0)
        self.assertEqual(r.room(), "Living Room")

    def test_blocked_edge_flashes_banner(self):
        # Living Room has no DOWN exit (UP is the Hallway, cd-342.12).
        r = _Run(windows=[(0.5, 0.7, _at(120, 230))], seconds=2.0)
        self.assertEqual(r.room(), "Living Room")
        self.assertEqual(r.banner(), "can't go down")

    def test_idle_and_still_goes_to_ornament(self):
        r = _Run(seconds=35.0)
        self.assertIsNot(r.display.root_group, r.nav_group)
        self.assertTrue(r.backlight.value)

    def test_idle_but_handled_stays_interactive(self):
        r = _Run(jerk=10.0, seconds=35.0)
        self.assertIs(r.display.root_group, r.nav_group)

    def test_touch_wakes_ornament_and_is_swallowed(self):
        # Ornament by ~33s; then a right-edge tap that would move a room
        # if it weren't swallowed as the wake-up touch.
        r = _Run(windows=[(40.0, 40.2, _RIGHT_EDGE)], seconds=45.0)
        self.assertIs(r.display.root_group, r.nav_group)
        self.assertEqual(r.room(), "Living Room")

    def test_navigation_works_again_after_waking_from_ornament(self):
        r = _Run(
            windows=[
                (40.0, 40.2, _RIGHT_EDGE),  # wakes, swallowed
                (42.0, 42.2, _RIGHT_EDGE),  # real move
            ],
            seconds=45.0,
        )
        self.assertEqual(r.room(), "Dining Room")

    def test_interactive_blanks_when_handled_but_untouched(self):
        r = _Run(jerk=10.0, seconds=125.0)
        self.assertFalse(r.backlight.value)


if __name__ == "__main__":
    unittest.main()
