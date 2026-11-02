# SPDX-License-Identifier: MIT
"""Recover the shared I2C bus when the touch chip locks it -- cd-342.16.

The CST816 touch chip sometimes holds SDA low. Every touch and IMU read then
takes the full 1s timeout, so a game tick takes 2s, and it can last for minutes.
Tested on ws-1: 64 SCL clocks don't release the line, but a pulse on the chip's
reset pin does (Chapter_8/doc/HARDWARE.md). So rebuild() resets the chip and
then brings up a new busio.I2C.

Its status reports the line levels before and after the reset, so the serial log
shows what happened. The hardware comes in as arguments so this runs under plain
desktop Python (see tests/test_bus_recovery.py).
"""

_BUS_ERRORS = (RuntimeError, OSError, ValueError)
_LINES = "SDA high {}/20, SCL high {}/20"


class BusRecovery:
    def __init__(self, i2c, gestures, touch, make_i2c, make_imu, read_lines, reset_touch):
        self._i2c = i2c
        self._gestures = gestures
        self._touch = touch
        self._make_i2c = make_i2c
        self._make_imu = make_imu
        self._read_lines = read_lines
        self._reset_touch = reset_touch
        self.rebuilds = 0

    def rebuild(self):
        """Reset the touch chip and rebuild the bus. Returns a status line, never raises."""
        self.rebuilds += 1
        self._i2c.deinit()
        before = _LINES.format(*self._read_lines())
        self._reset_touch()
        lines = "before reset {}; after {}".format(
            before, _LINES.format(*self._read_lines())
        )
        try:
            self._i2c = self._make_i2c()
            imu = self._make_imu(self._i2c)
        except _BUS_ERRORS as exc:
            return "FAILED ({}) {!r}".format(lines, exc)
        self._gestures.imu = imu
        self._touch.use_bus(self._i2c)
        return "ok ({})".format(lines)
