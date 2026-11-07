# SPDX-License-Identifier: MIT
"""Chapter 9 - Christmas Critters: on-device entry point (cd-342.2).

Hardware bootstrap only -- the game loop itself is app.run(), which takes its
hardware as arguments so it can be smoke-tested off-device.
"""
import os
import time

import app
import hardware
import imu as imu_gestures
from bus_recovery import BusRecovery


def main():
    display, backlight = hardware.init_display()
    # A software reset doesn't reach the touch chip, which may still be holding
    # the bus; busio.I2C would raise "No pull up found" before anything is drawn.
    hardware.reset_touch()
    i2c = hardware.init_i2c()
    imu = hardware.init_imu(i2c)
    touch = hardware.init_touch(i2c)
    gestures = imu_gestures.ImuGestures(imu)
    recovery = BusRecovery(
        i2c, gestures, touch, hardware.init_i2c, hardware.init_imu,
        hardware.read_bus_lines, hardware.reset_touch,
    )
    app.run(
        display, backlight, touch, gestures, hardware.WIDTH, hardware.HEIGHT,
        bus_recovery=recovery, power=hardware.DevicePower(display, gestures),
        drain=make_drain_log(),
    )


def make_drain_log():
    """The battery drain logger if settings.toml has POWER_LOG = "<minutes>", else None."""
    minutes = os.getenv("POWER_LOG")
    if not minutes:
        return None
    import microcontroller
    from drain_log import DrainLog

    log = DrainLog(
        microcontroller.nvm, hardware.BatteryAdc(), float(minutes) * 60, time.monotonic()
    )
    print("drain log on: every {} min".format(minutes))
    return log


main()
