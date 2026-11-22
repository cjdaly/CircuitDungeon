# SPDX-License-Identifier: MIT
"""The Ch9 main loop -- cd-342.2, reshaped in cd-342.47.2.

run() makes a Game and ticks it until power-off. A Game owns:

- the sensors (sensors.Sensors): touch, motion, stillness, bus recovery;
- the light and sleep (power_manager.PowerManager): blanking, deep idle;
- the screens (screens.py): gift tag -> title -> game, and the ornament,
  which takes over whenever modes.ModeController says the board is set down.

Each tick reads the sensors, lets the screen up now handle the touch, then
updates it. It lives here rather than in main.py so an off-device smoke test
can drive run() with fake hardware (tests/test_app_smoke.py); main.py is just
the hardware bootstrap. doc/ARCHITECTURE.md has the shape and the budgets.

A touch that wakes the board -- from a dark screen or from the ornament --
is swallowed, and so is the rest of that same finger-down: the screens see
input again only after the finger lifts, so a wake-up touch can't complete
into a room move.
"""
import gc
import time
import traceback

import edge_gesture
import modes
import rooms
from critters import make_roster
from hunt import Hunt
from nav_view import NavView
from power_manager import PowerManager
from screens import GameScreen, OrnamentScreen, TagScreen, TitleScreen
from sensors import Sensors
from settings import Settings

_GC_INTERVAL = 10.0
_TICK = 0.05
_STATS_INTERVAL = 10.0


class _LoopStats:
    """Loop timing, reported as one serial line per interval.

    Printing can itself be slow, so errors are counted here rather than printed
    one by one, and each report says how long the previous report took to print.
    """

    def __init__(self, now):
        self.print_ms = 0
        self._reset(now)

    def _reset(self, now):
        self.next_report = now + _STATS_INTERVAL
        self.ticks = 0
        self.tick_s = 0.0
        self.touch_s = 0.0
        self.imu_s = 0.0
        self.imu_errors = 0
        self.last_imu_error = None

    def report(self, now, mode, touch, clock, extra=""):
        started = clock()
        print(
            "t={:.0f} {} ticks={} worst_ms: tick={} touch={} imu={} | imu_errors={} {} "
            "| touch connects={} drops={} | last_print_ms={} free={}{}".format(
                now,
                mode,
                self.ticks,
                int(self.tick_s * 1000),
                int(self.touch_s * 1000),
                int(self.imu_s * 1000),
                self.imu_errors,
                self.last_imu_error or "",
                getattr(touch, "connects", 0),
                getattr(touch, "drops", 0),
                self.print_ms,
                gc.mem_free(),
                extra,
            )
        )
        self.print_ms = int((clock() - started) * 1000)
        self._reset(now)


class Game:
    """The whole game on one board. tick() once per loop; it returns how long
    to sleep before the next. See run() for the arguments."""

    def __init__(self, display, backlight, touch, imu, width, height, clock=time.monotonic,
                 sleep=time.sleep, bus_recovery=None, power=None, drain=None, title=True,
                 tag_turn=0):
        # Few locals here: the gift tag's words are drawn under this frame.
        self._display = display
        self._clock = clock
        self._settings = Settings()
        self._tlog = self._touch_log()
        # The gift tag goes up first, so it's on screen while the rest loads.
        tag = self._gift_tag(self._settings, width, height, tag_turn) if title else None
        nav = NavView(width, height)
        self._screen = self._screens(nav, tag, title, width, height)
        self._stats = _LoopStats(clock())
        self._sensors = Sensors(touch, imu, clock, self._stats, bus_recovery, self._tlog)
        self._power = PowerManager(display, backlight, self._sensors, clock, power, drain)
        self._ornament = OrnamentScreen(nav.backdrop, width, height, self._power, self._sensors)
        self._modes = modes.ModeController()
        self._mode = self._modes.mode
        self._wait_for_release = False
        self._next_gc = clock() + _GC_INTERVAL
        display.root_group = self._screen.group
        self._screen.enter(clock())
        self._power.reset(self._mode)
        self._ready(nav, tag, tag_turn)

    def _touch_log(self):
        if not self._settings.touch_log:
            return None
        from touch_log import TouchLog

        return TouchLog()

    def _screens(self, nav, tag, title, width, height):
        """The game, and the title and gift tag ahead of it; returns the first."""
        settings = self._settings
        world = rooms.make_world()
        world.open_all = settings.open_all_rooms
        roster = make_roster()
        hunt = Hunt(world, roster, player=settings.player, difficulty=settings.difficulty)
        if settings.finale_now:
            hunt.skip_to_finale()
        tracker = edge_gesture.EdgeGestureTracker(width, height)
        self._game = GameScreen(nav, world, hunt, tracker, self._tlog, width, height)
        if not title:
            return self._game
        import title_view

        cast = [(critter.species, critter.sprite) for critter in roster.all()]
        view = title_view.TitleView(nav.backdrop, nav.sprite_sheets(), cast, width, height)
        screen = TitleScreen(view, tracker, self._tlog, self._game)
        if tag is not None:
            screen = TagScreen(tag, tracker, self._tlog, screen)
        return screen

    def _gift_tag(self, settings, width, height, tag_turn):
        """FOR <PLAYER>, FROM CHRIS (cd-342.44), up on the display now; None without a PLAYER."""
        if not settings.player:
            return None
        import gift_tag

        show_s = gift_tag.SHOW_S if settings.tag_seconds is None else settings.tag_seconds
        tag = gift_tag.GiftTag(settings.player, width=width, height=height, now=self._clock(),
                               show_s=show_s, device_id=settings.device_id, turn=tag_turn)
        self._display.root_group = tag.group
        return tag

    def _ready(self, nav, tag, tag_turn):
        settings = self._settings
        tag_note = ""
        if tag is not None:  # loading took a while: give it a moment once taps work
            import gift_tag

            tag_note = "  tag up {:.1f}s, turn {} ({})".format(
                self._clock() - tag.shown_at, tag_turn, tag.style[0])
            tag.until = max(tag.until, self._clock() + gift_tag.MIN_LIVE_S)
        world = self._game.world
        print("Ch9 ready -- start: {}  player={}  art={}  clues={}{}  free={}{}".format(
            world.current, settings.player, getattr(nav, "art_set", None),
            self._game.hunt.difficulty,
            ("  OPEN_ALL_ROOMS" if world.open_all else "")
            + ("  FINALE_NOW" if settings.finale_now else ""),
            gc.mem_free(), tag_note))

    def tick(self):
        now = self._clock()
        if self._power.sleeping:
            pause = self._power.asleep(now)
            if pause is not None:
                return pause
            now = self._clock()  # just woken: a light sleep can last a minute
        point = self._sensors.read(now)
        touched = point is not None
        mode = self._modes.update(touched, self._sensors.still, now)
        # The touch chip stays awake only while played.
        self._sensors.awake(self._mode == modes.INTERACTIVE and self._power.lit)
        if self._modes.just_switched:
            self._switch(mode, now, touched)
        if mode == modes.INTERACTIVE:
            self._play(point, now)
        else:
            # Being handled counts as activity: it wakes a dark ornament.
            self._power.activity(not self._sensors.still, now)
            self._ornament.update(now)
        self._power.settle(now, touched)
        self._upkeep(now)
        return _TICK

    def _switch(self, mode, now, touched):
        """Between the game's screens and the ornament."""
        self._mode = mode
        screen = self._screen if mode == modes.INTERACTIVE else self._ornament
        self._display.root_group = screen.group
        self._power.reset(mode)
        print("t={:.1f} mode -> {}".format(now, mode))
        screen.enter(now)
        if touched:
            self._wait_for_release = True  # the touch that woke us

    def _play(self, point, now):
        """One tick of the gift tag, title or game."""
        touched = point is not None
        if self._power.activity(touched, now):
            self._wait_for_release = True  # a touch woke a dark screen
        if self._wait_for_release:
            if touched:
                point = None
            else:
                self._wait_for_release = False
        following = self._screen.handle(point, now)
        if following is not None:
            self._screen = following  # the last one's sprites and labels can go
            self._display.root_group = following.group
            following.enter(now)
            if touched:  # a finger still down mustn't then act on the new screen
                self._wait_for_release = True
            gc.collect()
        self._screen.update(now)

    def _upkeep(self, now):
        if now >= self._next_gc:
            gc.collect()
            self._next_gc = now + _GC_INTERVAL
        stats = self._stats
        stats.ticks += 1
        stats.tick_s = max(stats.tick_s, self._clock() - now)
        if now >= stats.next_report:
            mode = self._mode if self._screen is self._game else self._mode + "/title"
            stats.report(now, mode, self._sensors.touch, self._clock,
                         "" if self._tlog is None else " | " + self._tlog.report())


def run(display, backlight, touch, imu_gestures, width, height, max_ticks=None, **options):
    """Run the game forever (or `max_ticks` loops, for the smoke test).

    `touch` needs .poll(now) -> (x, y) | None; `imu_gestures` needs
    .sample(now) -> dict with "jerk", "accel" (imu.ImuGestures). `options` are
    Game's: clock, sleep, bus_recovery (.rebuild() -> status string,
    bus_recovery.BusRecovery), power (.sleep() and .wake(), hardware.DevicePower;
    turns on deep idle), drain (.tick(now, lit, asleep) and .woke(shift),
    drain_log.DrainLog), title, and tag_turn (the gift tag's look,
    gift_tag.next_turn).

    This frame sits under every call the game makes, so it stays small: the
    options go through as one dict (doc/ARCHITECTURE.md sec 1).
    """
    game = Game(display, backlight, touch, imu_gestures, width, height, **options)
    sleep = options.get("sleep", time.sleep)
    ticks = 0
    while max_ticks is None or ticks < max_ticks:
        ticks += 1
        try:
            pause = game.tick()
        except Exception as exc:  # noqa: BLE001 -- a hard-crashed game is a black screen
            traceback.print_exception(exc)
            sleep(0.5)  # back off so a persistent fault doesn't spam serial
            pause = _TICK
        if pause:
            sleep(pause)
