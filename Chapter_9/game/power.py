# SPDX-License-Identifier: MIT
"""Deep idle: when to drop into low power and when to wake -- cd-342.28.

The backlight going off (screen_blanker) only saves the backlight. Once the
screen is dark AND the device has been still for a while, app.py enters deep
idle: the display panel sleeps, the IMU drops to a low-power rate, the CPU
clock drops (hardware.DevicePower), and the loop slows to a few reads a second
of the accelerometer alone. Touch isn't polled while asleep: the CST816 is what
wedges the shared I2C bus (cd-342.16), and picking the device up, or tapping it
hard enough to matter, moves it.

CircuitPython 10 has no `alarm` module on this board (Chapter_8/doc/POWER.md,
cd-ork.4), so there "asleep" is still Python running, just rarely and slowly:
time.sleep() waits in WFI between reads. CircuitPython 11 has `alarm`, and then
deep idle is a real light sleep that the IMU's wake-on-motion pin ends
(hardware.DevicePower.doze, cd-342.30).

Pure logic, no hardware imports -- runs under plain desktop Python (see
tests/test_power.py).
"""

ENTER_DELAY = 10.0  # s dark and still before deep idle (a brief pause first,
                    # so setting it down and picking it straight back up is cheap)
WAKE_JERK = 1.0  # m/s^2 between deep-idle reads; at rest in the low-power
                 # accel mode they top out near 0.15 (ws-1, 2026-11-07)
TICK = 0.25  # s between accelerometer reads while asleep
DOZE = 60.0  # s per light sleep, where the firmware has one (hardware.DevicePower);
             # motion ends it early, the timeout just lets the drain log tick


class DeepIdle:
    """Feed .should_enter(lit, still, now) each awake tick, .should_wake(jerk) asleep."""

    def __init__(self, enter_delay=ENTER_DELAY, wake_jerk=WAKE_JERK):
        self._enter_delay = enter_delay
        self._wake_jerk = wake_jerk
        self._calm_since = None
        self.asleep = False

    def should_enter(self, lit, still, now):
        """True once the screen has been dark and the device still for enter_delay."""
        if lit or not still:
            self._calm_since = None
            return False
        if self._calm_since is None:
            self._calm_since = now
        return now - self._calm_since >= self._enter_delay

    def should_wake(self, jerk):
        return jerk > self._wake_jerk

    def enter(self):
        self.asleep = True

    def wake(self):
        self.asleep = False
        self._calm_since = None
