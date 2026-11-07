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


_START_TRIES = 5
_RESTART_DELAY = 10  # s to show a fatal error before starting over


def start_bus():
    """The I2C bus and IMU, clearing whatever holds the bus first. Retries.

    A reset doesn't reach the touch chip or the IMU, so either may still be
    holding SDA from before it, and busio.I2C would raise "No pull up found"
    before anything is drawn: reset the touch chip, then clock out the IMU.
    """
    for attempt in range(1, _START_TRIES + 1):
        hardware.reset_touch()
        clocks = hardware.clock_out_bus()
        try:
            i2c = hardware.init_i2c()
        except RuntimeError as exc:
            print("start: bus attempt {} failed ({} clocks): {}".format(attempt, clocks, exc))
            time.sleep(0.5 * attempt)
            continue
        try:
            return i2c, hardware.init_imu(i2c)
        except (OSError, RuntimeError, ValueError) as exc:
            print("start: imu attempt {} failed: {!r}".format(attempt, exc))
            i2c.deinit()
            time.sleep(0.5 * attempt)
    raise RuntimeError("I2C bus never came up")


def main():
    display, backlight = hardware.init_display()
    i2c, imu = start_bus()
    touch = hardware.init_touch(i2c)
    gestures = imu_gestures.ImuGestures(imu)
    recovery = BusRecovery(
        i2c, gestures, touch, hardware.init_i2c, hardware.init_imu,
        hardware.read_bus_lines, hardware.reset_touch, hardware.clock_out_bus,
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


try:
    main()
except Exception as exc:  # noqa: BLE001 -- a gift must never sit at the REPL
    import supervisor
    import traceback

    traceback.print_exception(exc)
    print("main: starting over in {} s".format(_RESTART_DELAY))
    time.sleep(_RESTART_DELAY)
    supervisor.reload()
