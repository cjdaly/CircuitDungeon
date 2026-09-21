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
"""
import gc
import time
import traceback

import edge_gesture
import modes
import ornament
import rooms
import stillness
from nav_view import NavView
from screen_blanker import ScreenBlanker

_INTERACTIVE_BLANK_TIMEOUT = 120.0  # s of no touch -- > modes' idle timeout
_ORNAMENT_BLANK_TIMEOUT = 300.0  # s of continuous stillness, as in Ch8's demo
_GC_INTERVAL = 10.0
_TICK = 0.05


def run(display, backlight, touch, imu_gestures, width, height,
        max_ticks=None, clock=time.monotonic, sleep=time.sleep):
    """Run the game forever (or `max_ticks` frames, for the smoke test).

    `touch` needs .poll(now) -> (x, y) | None; `imu_gestures` needs
    .sample(now) -> dict with "jerk" (imu.ImuGestures).
    """
    import displayio

    world = rooms.make_world()
    tracker = edge_gesture.EdgeGestureTracker(width, height)
    detector = stillness.StillnessDetector()
    mode_ctl = modes.ModeController()

    nav = NavView(width, height)
    nav.show_room(world.room.name, world.live_exits())

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
    next_gc = clock() + _GC_INTERVAL
    ticks = 0

    print("Ch9 ready -- start: {}  free={}".format(world.current, gc.mem_free()))

    while max_ticks is None or ticks < max_ticks:
        ticks += 1
        now = clock()
        try:
            point = touch.poll(now)
            touched = point is not None

            try:
                detector.update(imu_gestures.sample(now)["jerk"], now)
            except (OSError, ValueError, RuntimeError) as exc:
                traceback.print_exception(exc)  # hold last-known stillness

            new_mode = mode_ctl.update(touched, detector.is_still, now)
            if mode_ctl.just_switched:
                mode = new_mode
                display.root_group = (
                    nav.group if mode == modes.INTERACTIVE else ornament_group
                )
                blanker = blanker_for(mode)
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
                    if point is not None
                    else None
                )
                direction = tracker.update(point, now)
                if direction is not None:
                    if world.move(direction):
                        nav.show_room(world.room.name, world.live_exits())
                        print("moved {} -> {}".format(direction, world.current))
                    else:
                        nav.blocked(direction, now)
                nav.update(now, zone)
            else:
                # "handled" counts as activity: wakes a blanked ornament.
                blanker.update(not detector.is_still, now)
                tree.update(now, lit=detector.is_still)
                snow.update(now)

            if now >= next_gc:
                gc.collect()
                next_gc = now + _GC_INTERVAL
        except Exception as exc:  # noqa: BLE001 -- a hard-crashed game is a black screen
            traceback.print_exception(exc)
            sleep(0.5)  # back off so a persistent fault doesn't spam serial

        sleep(_TICK)
