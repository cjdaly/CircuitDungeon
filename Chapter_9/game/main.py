# SPDX-License-Identifier: MIT
"""Chapter 9 - Christmas Critters: on-device entry point (cd-342.2).

Hardware bootstrap only -- the game loop itself is app.run(), which takes its
hardware as arguments so it can be smoke-tested off-device.
"""
import app
import hardware
import imu as imu_gestures


def main():
    display, backlight = hardware.init_display()
    i2c = hardware.init_i2c()
    imu = hardware.init_imu(i2c)
    touch = hardware.init_touch(i2c)
    gestures = imu_gestures.ImuGestures(imu)
    app.run(display, backlight, touch, gestures, hardware.WIDTH, hardware.HEIGHT)


main()
