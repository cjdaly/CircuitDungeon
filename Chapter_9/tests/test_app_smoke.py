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

_STUBBED = ("displayio", "vectorio", "bitmaptools", "adafruit_display_text",
            "adafruit_display_text.bitmap_label",
            "adafruit_bitmap_font", "adafruit_bitmap_font.bitmap_font")
_GAME_MODULES = ("app", "nav_view", "room_banner", "comic", "comic_fonts", "ornament",
                 "scene_view")
_GAME_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "game")
_saved = {}
_labels = []


class _Group(list):
    def __init__(self, x=0, y=0, scale=1):
        super().__init__()
        self.x, self.y, self.scale, self.hidden = x, y, scale, False


class _Bitmap:
    def __init__(self, *a, **k):
        pass

    def __setitem__(self, position, value):
        pass


class _Palette(dict):
    def __init__(self, n=1):
        super().__init__()

    def make_transparent(self, index):
        pass


class _OnDiskBitmap(_Bitmap):
    def __init__(self, path):
        if not os.path.exists(os.path.join(_GAME_DIR, path.lstrip("/"))):
            raise OSError("no bitmap file: " + path)
        self.pixel_shader = _Palette()


class _TileGrid:
    def __init__(self, *a, pixel_shader=None, **k):
        self.x, self.y, self.hidden = 0, 0, False
        self.pixel_shader = pixel_shader

    def __setitem__(self, position, tile):
        pass


class _Shape:
    def __init__(self, **kw):
        self.__dict__.update(kw)


class _Font:
    def __init__(self, path):
        if not os.path.exists(os.path.join(_GAME_DIR, path)):  # relative, as on the device
            raise OSError("no font file: " + path)

    def load_glyphs(self, glyphs):
        pass


class _Label:
    def __init__(self, font, **kw):
        self.text = ""
        self.__dict__.update(kw)
        _labels.append(self)

    @property
    def bounding_box(self):
        return (0, 0, 10 * len(self.text), 24)


def setUpModule():
    if not hasattr(gc, "mem_free"):  # CircuitPython-only
        gc.mem_free = lambda: 0
    for name in _STUBBED + _GAME_MODULES:
        _saved[name] = sys.modules.pop(name, None)
    displayio = types.ModuleType("displayio")
    displayio.Group, displayio.Bitmap = _Group, _Bitmap
    displayio.Palette, displayio.TileGrid = _Palette, _TileGrid
    displayio.OnDiskBitmap = _OnDiskBitmap
    vectorio = types.ModuleType("vectorio")
    vectorio.Circle = vectorio.Rectangle = vectorio.Polygon = _Shape
    font_pkg = types.ModuleType("adafruit_bitmap_font")
    font_mod = types.ModuleType("adafruit_bitmap_font.bitmap_font")
    font_mod.load_font = _Font
    font_pkg.bitmap_font = font_mod
    bitmaptools = types.ModuleType("bitmaptools")
    bitmaptools.fill_region = lambda *a: None
    pkg = types.ModuleType("adafruit_display_text")
    bl = types.ModuleType("adafruit_display_text.bitmap_label")
    bl.Label = _Label
    pkg.bitmap_label = bl
    sys.modules.update({
        "displayio": displayio, "vectorio": vectorio, "bitmaptools": bitmaptools,
        "adafruit_display_text": pkg, "adafruit_display_text.bitmap_label": bl,
        "adafruit_bitmap_font": font_pkg, "adafruit_bitmap_font.bitmap_font": font_mod,
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


def _swipe_left_from(x, y):
    return lambda dt: (int(x - dt * 100), y)


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

    def visible_labels(self, group=None):
        """The labels actually showing: nothing inside a hidden group counts."""
        found = []
        for item in self.nav_group if group is None else group:
            if isinstance(item, _Group):
                if not item.hidden:
                    found.extend(self.visible_labels(item))
            elif isinstance(item, _Label) and item.text:
                found.append(item)
        return found

    def room(self):
        return [lb for lb in _labels if lb.anchored_position == (120, 50)][0].text

    def message(self):
        """The caption's text as one line, with wrapping undone."""
        lines = [lb.text for lb in self.visible_labels() if 146 <= lb.anchored_position[1] <= 198]
        return " ".join(lines)

    def burst(self):
        words = [lb.text for lb in self.visible_labels() if lb.anchored_position == (120, 120)]
        return words[0] if words else None

    def holding(self):
        """Whether the held-item icon is showing (scene_view's 7th layer, after home)."""
        layers = self.nav_group[1][0]  # the scene: SceneView's group
        return not layers[6].hidden

    def scene_x(self):
        return self.nav_group[1].x


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


_OPENING_S = 17.0  # the opening captions and escape cutscene have run by now
_CUTSCENE_BEATS = 6
_TAP_SPACING = 10.0  # likewise any overlay a tap brought up, unless a test wants it


def _taps(*touches, start=_OPENING_S, spacing=_TAP_SPACING):
    """Scripted short taps, spaced so each overlay clears by itself first."""
    return [
        (start + i * spacing, start + i * spacing + 0.2, touch)
        for i, touch in enumerate(touches)
    ]


def _after_taps(count, wait=1.0):
    """Run this long to end `wait` seconds after the last of `count` _taps()."""
    return _OPENING_S + (count - 1) * _TAP_SPACING + wait


class TestEpisodeOne(unittest.TestCase):
    # She has to be found first, since that opens the door to the yarn.
    TO_YARN = (_RIGHT_EDGE, _RIGHT_EDGE, _RIGHT_EDGE, _CENTER, _LEFT_EDGE, _LEFT_EDGE, _TOP_EDGE)
    YARN_TO_CAT = (_BOTTOM_EDGE, _RIGHT_EDGE, _RIGHT_EDGE)
    CAT_TO_TREE = (_LEFT_EDGE, _LEFT_EDGE, _LEFT_EDGE)

    def test_opening_announces_the_escape(self):
        r = _Run(seconds=1.0)
        self.assertEqual(r.message(), "9 PM")
        r = _Run(seconds=3.0)
        self.assertEqual(r.burst(), "RATTLE!")  # the cutscene, after the hour
        r = _Run(seconds=11.0)
        self.assertEqual(r.message(), "CHIRPY ESCAPED!")

    def test_closed_exit_shows_its_reason_and_does_not_move(self):
        r = _Run(windows=_taps(_LEFT_EDGE), seconds=_after_taps(1))
        self.assertEqual(r.room(), "LIVING ROOM")
        self.assertEqual(r.message(), "BRR! TOO COLD OUT THERE")

    def test_center_tap_takes_the_yarn(self):
        r = _Run(windows=_taps(*self.TO_YARN, _CENTER), seconds=_after_taps(len(self.TO_YARN) + 1))
        self.assertEqual(r.room(), "SEWING NOOK")
        self.assertEqual(r.message(), "GOT THE BALL OF YARN!")
        self.assertTrue(r.holding())

    def test_edge_tap_in_the_yarn_room_does_not_take_it(self):
        r = _Run(windows=_taps(*self.TO_YARN, _LEFT_EDGE), seconds=_after_taps(len(self.TO_YARN) + 1))
        self.assertFalse(r.holding())

    def test_a_swipe_from_the_center_does_not_count_as_a_tap(self):
        at = _OPENING_S + len(self.TO_YARN) * _TAP_SPACING
        touches = _taps(*self.TO_YARN) + [(at, at + 0.4, _swipe_right_from(90, 120))]
        r = _Run(windows=touches, seconds=at + 1.0)
        self.assertFalse(r.holding())

    def test_cat_without_yarn_says_what_it_wants(self):
        r = _Run(
            windows=_taps(_RIGHT_EDGE, _RIGHT_EDGE, _RIGHT_EDGE, _CENTER),
            seconds=_after_taps(4, wait=0.5),
        )
        self.assertEqual(r.room(), "SUN PORCH")
        self.assertEqual(r.burst(), "FOUND!")

    def test_messages_play_in_sequence(self):
        r = _Run(
            windows=_taps(_RIGHT_EDGE, _RIGHT_EDGE, _RIGHT_EDGE, _CENTER),
            seconds=_after_taps(4, wait=4.0),
        )
        self.assertEqual(r.message(), "CHIRPY WANTS THE YARN")

    def test_the_yarn_door_is_stuck_until_she_is_found(self):
        r = _Run(windows=_taps(_RIGHT_EDGE, _TOP_EDGE), seconds=_after_taps(2))
        self.assertEqual(r.room(), "DINING ROOM")
        self.assertEqual(r.message(), "THE DOOR'S STUCK")

    def test_full_episode_from_escape_to_home(self):
        touches = _taps(
            *self.TO_YARN, _CENTER, *self.YARN_TO_CAT, _CENTER, *self.CAT_TO_TREE
        )
        r = _Run(windows=touches, seconds=_after_taps(len(touches)))
        self.assertEqual(r.room(), "LIVING ROOM")
        self.assertFalse(r.holding())
        self.assertEqual(r.message(), "CHIRPY CURLS UP ON THE RUG")

        r = _Run(windows=touches, seconds=_after_taps(len(touches), wait=4.0))
        self.assertEqual(r.message(), "10 PM")  # the next pet is already out


class TestOverlays(unittest.TestCase):
    def test_a_caption_times_out_by_itself(self):
        r = _Run(seconds=_OPENING_S)
        self.assertEqual(r.message(), "")

    def test_an_edge_tap_during_a_caption_advances_instead_of_moving(self):
        r = _Run(windows=[(0.5, 0.7, _RIGHT_EDGE)], seconds=1.5)
        self.assertEqual(r.room(), "LIVING ROOM")
        self.assertEqual(r.burst(), "RATTLE!")  # on into the escape cutscene

    def test_a_corner_tap_also_advances(self):
        r = _Run(windows=[(0.5, 0.7, _at(5, 5))], seconds=1.5)
        self.assertEqual(r.burst(), "RATTLE!")

    def test_a_center_tap_during_a_caption_only_advances(self):
        to_odd_corner = (_RIGHT_EDGE, _RIGHT_EDGE, _TOP_EDGE)
        at = _OPENING_S + (len(to_odd_corner) - 1) * _TAP_SPACING + 0.5  # "Batteries!" is up
        r = _Run(windows=_taps(*to_odd_corner) + [(at, at + 0.2, _CENTER)], seconds=at + 1.0)
        self.assertEqual(r.room(), "ODD CORNER")
        self.assertEqual(r.message(), "")  # dismissed, and no "So close!" from a real tap

    def test_moving_works_as_soon_as_the_last_caption_is_tapped_away(self):
        beats = 3 + _CUTSCENE_BEATS  # 9 PM, the cutscene, escaped, the clue
        windows = [(0.5 + 0.5 * i, 0.6 + 0.5 * i, _CENTER) for i in range(beats)]
        at = 0.5 + 0.5 * beats
        r = _Run(windows=windows + [(at, at + 0.1, _RIGHT_EDGE)], seconds=at + 0.5)
        self.assertEqual(r.room(), "DINING ROOM")

    def test_the_cutscene_cuts_in_without_the_room_name_or_markers(self):
        r = _Run(seconds=4.5)  # 9 PM (2.25s), RATTLE! (1.6s), then the close-up
        chrome = r.nav_group[1][1]
        self.assertTrue(chrome.hidden)
        r = _Run(seconds=_OPENING_S)
        self.assertFalse(r.nav_group[1][1].hidden)


class TestAppSmoke(unittest.TestCase):
    def test_starts_in_living_room_interactive(self):
        r = _Run(seconds=1.0)
        self.assertEqual(r.room(), "LIVING ROOM")
        self.assertIs(r.display.root_group, r.nav_group)

    def test_tap_on_right_edge_moves_to_dining_room(self):
        r = _Run(windows=_taps(_RIGHT_EDGE), seconds=_after_taps(1))
        self.assertEqual(r.room(), "DINING ROOM")

    def test_swipe_from_left_edge_moves_when_that_exit_is_open(self):
        back = _OPENING_S + _TAP_SPACING
        r = _Run(
            windows=_taps(_RIGHT_EDGE) + [(back, back + 0.4, _swipe_right_from(10, 120))],
            seconds=back + 1.0,
        )
        self.assertEqual(r.room(), "LIVING ROOM")

    def test_swipe_left_from_the_center_goes_right_like_a_watch(self):
        at = _OPENING_S
        r = _Run(windows=[(at, at + 0.4, _swipe_left_from(150, 120))], seconds=at + 1.0)
        self.assertEqual(r.room(), "DINING ROOM")

    def test_a_swipe_toward_a_closed_exit_shows_its_reason(self):
        at = _OPENING_S
        r = _Run(windows=[(at, at + 0.4, _swipe_right_from(100, 120))], seconds=at + 1.0)
        self.assertEqual(r.room(), "LIVING ROOM")
        self.assertEqual(r.message(), "BRR! TOO COLD OUT THERE")

    def test_an_edge_with_no_exit_bonks_and_shakes(self):
        # Living Room has no DOWN exit (UP is the Hallway, cd-342.12).
        at = _OPENING_S
        r = _Run(windows=[(at, at + 0.2, _at(120, 230))], seconds=at + 0.45)
        self.assertEqual(r.room(), "LIVING ROOM")
        self.assertEqual(r.burst(), "BONK!")
        self.assertNotEqual(r.scene_x(), 0)

    def test_the_bonk_clears_and_the_scene_settles(self):
        at = _OPENING_S
        r = _Run(windows=[(at, at + 0.2, _at(120, 230))], seconds=at + 2.0)
        self.assertIsNone(r.burst())
        self.assertEqual(r.scene_x(), 0)

    def test_a_long_message_runs_on_into_a_second_caption(self):
        import nav_view

        nav = nav_view.NavView(240, 240)
        nav.say(["one two three four five six seven eight"], 0.0)  # three lines
        self.assertTrue(nav.overlay_up)
        nav.tap_overlay(0.1)
        self.assertTrue(nav.overlay_up)  # the text didn't fit in one caption
        nav.tap_overlay(0.2)
        self.assertFalse(nav.overlay_up)

    def test_the_overlay_demos_beats_all_draw(self):
        import comic
        import overlay_demo

        stage = comic.Stage(240, 240, shake_target=_Group())
        for beat in overlay_demo.beats((_Bitmap(), _Palette())):
            self.assertLessEqual(len(beat.emanata), comic.MAX_EMANATA)
            stage.show(beat, 0.0)
            stage.update(0.1)
        stage.clear()

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
        self.assertEqual(r.room(), "LIVING ROOM")

    def test_navigation_works_again_after_waking_from_ornament(self):
        r = _Run(
            windows=[
                (40.0, 40.2, _RIGHT_EDGE),  # wakes, swallowed
                (42.0, 42.2, _RIGHT_EDGE),  # real move
            ],
            seconds=45.0,
        )
        self.assertEqual(r.room(), "DINING ROOM")

    def test_interactive_blanks_when_handled_but_untouched(self):
        r = _Run(jerk=10.0, seconds=125.0)
        self.assertFalse(r.backlight.value)


if __name__ == "__main__":
    unittest.main()
