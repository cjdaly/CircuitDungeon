# SPDX-License-Identifier: MIT
"""The Ch9 main loop -- cd-342.2.

Wires the cd-zw2 building blocks together: touch -> edge-gesture navigation
over the room graph (interactive mode), and the ornament scene (ornament
mode), with modes.ModeController deciding which is showing. Lives here rather
than in main.py so an off-device smoke test can drive `run()` with fake
hardware (see tests/test_app_smoke.py); main.py is just the hardware bootstrap.

Screen blanking is per-mode, since the two modes want opposite things:
interactive blanks after a long stretch of no *touch* (backstop for a device
that's being carried around, not touched -- one that's set down goes to
ornament mode first, see modes.py); ornament blanks after a much longer
stretch of continuous *stillness*, and being handled counts as activity
(no touchscreen input to lean on there, same as Chapter_8's ornament_demo.py).
The blanker is rebuilt on every mode switch, with the backlight forced on,
so its lit/unlit bookkeeping can never disagree with the real pin.

A touch that wakes the device -- from a blanked screen or from ornament
mode -- is swallowed, and so is the rest of that same finger-down: the
tracker only sees input again after the finger lifts, so a wake-up touch
can't complete into a room move.

Deep idle (power.py, cd-342.28): once the screen is dark and the device has
been still a while, the panel, IMU and CPU clock go low-power and the loop only
reads the accelerometer a few times a second until the device moves. Even in
plain blanking, nothing is redrawn while the backlight is off.
"""
import gc
import os
import time
import traceback

import edge_gesture
import modes
import ornament
import power as deep_idle
import rooms
import stillness
from critters import make_roster
from hunt import Hunt
from nav_view import NavView
from screen_blanker import ScreenBlanker

_INTERACTIVE_BLANK_TIMEOUT = 120.0  # s of no touch -- > modes' idle timeout
_ORNAMENT_BLANK_TIMEOUT = 300.0  # s of continuous stillness, as in Ch8's demo
_GC_INTERVAL = 10.0
_TICK = 0.05
_STATS_INTERVAL = 10.0
_REBUILD_MIN_INTERVAL = 5.0  # s between I2C bus rebuilds, if they aren't helping


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

    def report(self, now, mode, touch, clock):
        started = clock()
        print(
            "t={:.0f} {} ticks={} worst_ms: tick={} touch={} imu={} | imu_errors={} {} "
            "| touch connects={} drops={} | last_print_ms={} free={}".format(
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
            )
        )
        self.print_ms = int((clock() - started) * 1000)
        self._reset(now)


def run(display, backlight, touch, imu_gestures, width, height,
        max_ticks=None, clock=time.monotonic, sleep=time.sleep, bus_recovery=None,
        power=None, drain=None):
    """Run the game forever (or `max_ticks` frames, for the smoke test).

    `touch` needs .poll(now) -> (x, y) | None; `imu_gestures` needs
    .sample(now) -> dict with "jerk" (imu.ImuGestures); `bus_recovery`, if
    given, needs .rebuild() -> status string (bus_recovery.BusRecovery);
    `power`, if given, needs .sleep() and .wake() (hardware.DevicePower) and
    turns on deep idle; `drain`, if given, needs .tick(now, lit, asleep)
    (drain_log.DrainLog).
    """
    import displayio

    world = rooms.make_world()
    tracker = edge_gesture.EdgeGestureTracker(width, height)
    detector = stillness.StillnessDetector()
    deep = deep_idle.DeepIdle()
    mode_ctl = modes.ModeController()

    # Who this board is for: optional, set per board in settings.toml.
    player = os.getenv("PLAYER")
    hunt = Hunt(world, make_roster(), player=player)

    nav = NavView(width, height)

    def tell(messages, now):
        """Show what the hunt just said, drawn the way its last event wants."""
        want = hunt.critter.preferred_item if hunt.critter else None
        nav.say(messages, now, hunt.event, want, hunt.escape, hunt.escape_at)

    opening = hunt.start()  # sets the episode's gate, so before show_room
    nav.show_room(world.room.name, world.live_exits())
    nav.show_scene(hunt.scene(), clock())
    tell(opening, clock())

    ornament_group = displayio.Group()
    ornament.make_background(ornament_group, width, height)
    tree = ornament.Tree(ornament_group)
    snow = ornament.Snow(ornament_group, width, height)

    def blanker_for(mode):
        timeout = (
            _ORNAMENT_BLANK_TIMEOUT
            if mode == modes.ORNAMENT
            else _INTERACTIVE_BLANK_TIMEOUT
        )
        backlight.value = True
        return ScreenBlanker(backlight, timeout=timeout)

    mode = mode_ctl.mode
    display.root_group = nav.group
    blanker = blanker_for(mode)
    wait_for_release = False
    backlight_lit = True
    next_gc = clock() + _GC_INTERVAL
    stats = _LoopStats(clock())
    next_rebuild = 0.0
    awaiting_good_read = False
    ticks = 0

    def read_jerk(now):
        """The IMU's jerk, or None after a failed read (rebuilding the bus if due)."""
        nonlocal next_rebuild, awaiting_good_read
        try:
            jerk = imu_gestures.sample(now)["jerk"]
        except (OSError, ValueError, RuntimeError) as exc:
            stats.imu_errors += 1
            stats.last_imu_error = repr(exc)
            if bus_recovery is not None and now >= next_rebuild:
                started = clock()
                status = bus_recovery.rebuild()
                print("t={:.1f} bus rebuild {}ms: {}".format(
                    now, int((clock() - started) * 1000), status))
                next_rebuild = clock() + _REBUILD_MIN_INTERVAL
                awaiting_good_read = True
            return None
        if awaiting_good_read:
            awaiting_good_read = False
            print("t={:.1f} imu read ok after bus rebuild".format(now))
        return jerk

    print("Ch9 ready -- start: {}  player={}  free={}".format(
        world.current, player, gc.mem_free()))

    while max_ticks is None or ticks < max_ticks:
        ticks += 1
        now = clock()
        try:
            if deep.asleep:
                if power.can_doze:  # a real light sleep, ended by the IMU's motion pin
                    moved = power.doze(deep_idle.DOZE)
                    now = clock()
                    why = "motion pin"
                else:
                    jerk = read_jerk(now)
                    moved = jerk is not None and deep.should_wake(jerk)
                    why = "jerk {:.2f}".format(jerk) if moved else ""
                if moved:
                    power.wake()
                    deep.wake()
                    detector = stillness.StillnessDetector()  # it's being handled
                    blanker.update(True, now)
                    print("t={:.1f} deep idle -> awake ({})".format(now, why))
                elif power.can_doze:
                    if drain is not None:
                        drain.tick(now, False, True)
                    continue
                else:
                    if drain is not None:
                        drain.tick(now, False, True)
                    sleep(deep_idle.TICK)
                    continue

            point = touch.poll(now)
            touched = point is not None
            after_touch = clock()
            stats.touch_s = max(stats.touch_s, after_touch - now)

            jerk = read_jerk(now)
            if jerk is not None:  # on a failed read, hold last-known stillness
                was_still = detector.is_still
                detector.update(jerk, now)
                if detector.is_still != was_still:
                    raw = getattr(imu_gestures, "last_raw", None)
                    print("t={:.1f} {} (jerk {:.2f}, raw {})".format(
                        now, "still" if detector.is_still else "handled", jerk,
                        tuple(round(v, 2) for v in raw) if raw else "?"))
            stats.imu_s = max(stats.imu_s, clock() - after_touch)

            new_mode = mode_ctl.update(touched, detector.is_still, now)
            if mode_ctl.just_switched:
                mode = new_mode
                display.root_group = (
                    nav.group if mode == modes.INTERACTIVE else ornament_group
                )
                blanker = blanker_for(mode)
                print("t={:.1f} mode -> {}".format(now, mode))
                if mode == modes.ORNAMENT:
                    tree.scatter()
                if touched:
                    wait_for_release = True  # the touch that woke us

            if mode == modes.INTERACTIVE:
                if blanker.update(touched, now):
                    wait_for_release = True  # touch woke a blanked screen
                if wait_for_release:
                    if touched:
                        point = None
                    else:
                        wait_for_release = False

                zone = (
                    edge_gesture.edge_of(point[0], point[1], width, height)
                    if point is not None and not nav.overlay_up
                    else None
                )
                direction = tracker.update(point, now)
                if nav.overlay_up:
                    # Navigation waits: captions sit in the edge zones.
                    if tracker.gesture_done:
                        nav.tap_overlay(now)
                elif direction is not None:
                    if world.move(direction):
                        print("moved {} -> {}".format(direction, world.current))
                        # May start the next episode, so before show_room reads the gate.
                        messages = hunt.entered()
                        nav.show_room(world.room.name, world.live_exits())
                        nav.show_scene(hunt.scene(), now)
                        tell(messages, now)
                    else:
                        reason = hunt.bumped(direction)
                        if reason:
                            nav.say([reason], now)
                        else:
                            nav.bonk(now)
                elif tracker.center_tapped:
                    messages = hunt.tapped()
                    print("tap in {}: {}".format(world.current, messages))
                    nav.show_scene(hunt.scene(), now)
                    tell(messages, now)
                nav.update(now, zone)
            else:
                # "handled" counts as activity: wakes a blanked ornament.
                blanker.update(not detector.is_still, now)
                if blanker.lit:  # no point animating a dark screen
                    tree.update(now, lit=detector.is_still)
                    snow.update(now)

            if blanker.lit != backlight_lit:
                backlight_lit = blanker.lit
                display.auto_refresh = backlight_lit  # don't redraw a dark screen
                print("t={:.1f} backlight {}".format(now, "on" if backlight_lit else "off"))

            if power is not None and deep.should_enter(blanker.lit, detector.is_still, now):
                deep.enter()
                power.sleep()
                imu_gestures.reset()
                gc.collect()
                print("t={:.1f} awake -> deep idle  free={}".format(now, gc.mem_free()))

            if drain is not None:
                drain.tick(now, blanker.lit, False)

            if now >= next_gc:
                gc.collect()
                next_gc = now + _GC_INTERVAL

            stats.ticks += 1
            stats.tick_s = max(stats.tick_s, clock() - now)
            if now >= stats.next_report:
                stats.report(now, mode, touch, clock)
        except Exception as exc:  # noqa: BLE001 -- a hard-crashed game is a black screen
            traceback.print_exception(exc)
            sleep(0.5)  # back off so a persistent fault doesn't spam serial

        sleep(_TICK)
