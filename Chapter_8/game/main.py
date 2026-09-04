# SPDX-License-Identifier: MIT
"""Chapter 8 diagnostic demo.

One combined HUD (not paged -- v1 keeps it all on screen at once): system
info, a live touch marker + tap/swipe gesture readout, and a live
accelerometer/gyro readout with tilt + shake detection. See
doc/HARDWARE.md for the board notes and doc/VISION.md for the chapter pitch.
"""
import gc
import time
import traceback

import displayio
import terminalio
import vectorio
from adafruit_display_text.bitmap_label import Label

import hardware
import imu as imu_gestures
import touch as touch_gestures

_BG_COLOR = 0x101018
_TEXT_COLOR = 0xC0C0C0
_DOT_COLOR = 0x40E0D0
_OFFSCREEN = -20  # parks the touch marker fully outside the 240x240 canvas

# Text rows are inset from the round bezel -- see doc/HARDWARE.md "Display".
# The touch/gesture rows run at 2x scale (the small default font was hard to
# read at a glance); the denser numeric accel/gyro readouts stay at 1x so
# their longer strings still clear the round edge.
_ROW_TITLE = 30  # scale 1
_ROW_TOUCH_STATE = 58  # scale 2
_ROW_TOUCH_LAST = 92  # scale 2
_ROW_TILT = 158  # scale 2
_ROW_ACCEL = 186  # scale 1
_ROW_GYRO = 206  # scale 1

_GC_INTERVAL = 10.0  # seconds between periodic gc.collect() calls


def _make_group(display):
    group = displayio.Group()
    display.root_group = group

    bg_bitmap = displayio.Bitmap(hardware.WIDTH, hardware.HEIGHT, 1)
    bg_palette = displayio.Palette(1)
    bg_palette[0] = _BG_COLOR
    group.append(displayio.TileGrid(bg_bitmap, pixel_shader=bg_palette))
    return group


def _add_line(group, y, scale=1):
    label = Label(
        terminalio.FONT,
        text="",
        color=_TEXT_COLOR,
        scale=scale,
        anchor_point=(0.5, 0.5),
        anchored_position=(hardware.WIDTH // 2, y),
    )
    group.append(label)
    return label


def _add_touch_dot(group):
    palette = displayio.Palette(1)
    palette[0] = _DOT_COLOR
    dot = vectorio.Circle(pixel_shader=palette, x=_OFFSCREEN, y=_OFFSCREEN, radius=7)
    group.append(dot)
    return dot


def main():
    display = hardware.init_display()
    i2c = hardware.init_i2c()
    imu = hardware.init_imu(i2c)
    touch = hardware.init_touch(i2c)

    tracker = touch_gestures.GestureTracker()
    gestures = imu_gestures.ImuGestures(imu)

    group = _make_group(display)
    l_title = _add_line(group, _ROW_TITLE)
    l_touch_state = _add_line(group, _ROW_TOUCH_STATE, scale=2)
    l_touch_last = _add_line(group, _ROW_TOUCH_LAST, scale=2)
    l_tilt = _add_line(group, _ROW_TILT, scale=2)
    l_accel = _add_line(group, _ROW_ACCEL)
    l_gyro = _add_line(group, _ROW_GYRO)
    dot = _add_touch_dot(group)

    last_gesture = "--"
    next_gc = time.monotonic() + _GC_INTERVAL
    # Last-known-good IMU sample -- held on screen (frozen) if a read fails,
    # rather than the HUD losing its numbers or crashing.
    sample = {
        "accel": (0.0, 0.0, 0.0),
        "gyro": (0.0, 0.0, 0.0),
        "pitch": 0.0,
        "roll": 0.0,
        "shake": False,
    }
    imu_ok = True

    print("Ch8 diag ready  free={}".format(gc.mem_free()))

    while True:
        now = time.monotonic()
        # The whole tick is guarded: a diagnostic HUD that hard-crashes on a
        # transient I2C hiccup is worse than useless. One incident wedged the
        # shared I2C bus badly enough that only a USB unplug/replug (not
        # microcontroller.reset()) recovered it -- see doc/HARDWARE.md. This
        # can't fix that (touch.py's SafeTouch already tolerates its own read
        # failures; the IMU read below previously didn't), but it keeps the
        # HUD alive and legible -- showing "IMU ERROR" -- instead of an
        # unhandled exception leaving a silent black screen.
        try:
            point = touch.poll(now)
            gesture = tracker.update(point, now)
            if gesture:
                last_gesture = gesture

            live = tracker.current
            if live:
                dot.x, dot.y = live
                l_touch_state.text = "t:{:3d},{:3d}".format(live[0], live[1])
            else:
                dot.x = dot.y = _OFFSCREEN
                l_touch_state.text = "no touch" if touch.connected else "linking.."
            l_touch_last.text = "last:{}".format(last_gesture)

            try:
                sample = gestures.sample(now)
                imu_ok = True
            except (OSError, ValueError, RuntimeError) as exc:
                imu_ok = False
                traceback.print_exception(exc)

            ax, ay, az = sample["accel"]
            gx, gy, gz = sample["gyro"]
            l_accel.text = "a {:+5.1f} {:+5.1f} {:+5.1f}".format(ax, ay, az)
            l_gyro.text = "g {:+5.1f} {:+5.1f} {:+5.1f}".format(gx, gy, gz)
            if imu_ok:
                shake = " SHAKE" if sample["shake"] else ""
                l_tilt.text = "p{:+3.0f}r{:+3.0f}{}".format(
                    sample["pitch"], sample["roll"], shake
                )
            else:
                l_tilt.text = "IMU ERROR"

            if now >= next_gc:
                gc.collect()
                next_gc = now + _GC_INTERVAL
            l_title.text = "CH8 DIAG  free {:6d}".format(gc.mem_free())
        except Exception as exc:  # noqa: BLE001 -- last-resort guard, see above
            traceback.print_exception(exc)
            try:
                l_title.text = ("ERR " + type(exc).__name__)[:23]
            except Exception:  # display itself may be the thing failing
                pass
            time.sleep(0.5)  # back off so a persistent fault doesn't spam serial

        time.sleep(0.05)


main()
