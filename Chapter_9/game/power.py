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
time.sleep() waits in WFI between reads. CircuitPython 11 has `alarm`, and with
LIGHT_SLEEP = "1" in settings.toml deep idle is a real light sleep that the
IMU's wake-on-motion pin ends (hardware.DevicePower.doze, cd-342.30). Opt-in
only: 11.0.0-alpha.2's light sleep can hang for good.

Pure logic, no hardware imports -- runs under plain desktop Python (see
tests/test_power.py).
"""

ENTER_DELAY = 10.0  # s dark and still before deep idle (a brief pause first,
                    # so setting it down and picking it straight back up is cheap)
WAKE_SHIFT = 2.0  # m/s^2, summed over the 3 axes: how far a deep-idle read must be
                  # from the reading it went to sleep on. At rest they stay within
                  # ~0.15 (ws-1, 2026-11-07); 2.0 is about a 12 degree tilt, and
                  # the same level stillness.py calls "handled".
WAKE_READS = 2  # ...for this many reads in a row. One bump is one odd read; it
                # took 1.0 on a single read to wake ws-1/ws-2 every ~15 min on a
                # kitchen table (2026-11-07), keeping the screen lit a third of
                # the time. Picking it up moves it for longer than 0.25 s.
TICK = 0.25  # s between accelerometer reads while asleep
DOZE = 60.0  # s per light sleep, where the firmware has one (hardware.DevicePower);
             # motion ends it early, the timeout just lets the drain log tick
GLANCE_TIMEOUT = 60.0  # s of stillness before the screen goes dark again after a
                       # wake nobody followed up on (a bump, a passing glance),
                       # instead of the mode's usual timeout
GLANCE_HANDLED = 6.0  # s of handling after a wake that make it a real pickup:
                      # back to the usual timeout. A bump settles in ~3 s
                      # (stillness.STILL_HOLD).


def _shift(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2])


class DeepIdle:
    """Feed .should_enter(lit, still, now) each awake tick, .should_wake(accel) asleep.

    After a wake, .glancing(still, touched, dt) says whether the short
    GLANCE_TIMEOUT applies, until a touch or GLANCE_HANDLED s of handling.
    """

    def __init__(self, enter_delay=ENTER_DELAY, wake_shift=WAKE_SHIFT, wake_reads=WAKE_READS,
                 glance_handled=GLANCE_HANDLED):
        self._enter_delay = enter_delay
        self._wake_shift = wake_shift
        self._wake_reads = wake_reads
        self._glance_handled = glance_handled
        self._calm_since = None
        self._rest = None  # the reading deep idle measures movement from
        self._moved_reads = 0
        self._handled = 0.0
        self.asleep = False
        self.glance = False
        self.shift = 0.0  # the latest read's distance from rest, for logging

    def should_enter(self, lit, still, now):
        """True once the screen has been dark and the device still for enter_delay."""
        if lit or not still:
            self._calm_since = None
            return False
        if self._calm_since is None:
            self._calm_since = now
        return now - self._calm_since >= self._enter_delay

    def should_wake(self, accel):
        """True once wake_reads reads in a row are wake_shift from the resting one."""
        if self._rest is None:
            self._rest = accel
            return False
        self.shift = _shift(accel, self._rest)
        if self.shift > self._wake_shift:
            self._moved_reads += 1
        else:
            self._moved_reads = 0
        return self._moved_reads >= self._wake_reads

    def enter(self):
        self.asleep = True
        self._rest = None
        self._moved_reads = 0

    def wake(self, glance=True):
        """Back to awake; `glance` starts the short timeout (a motion wake)."""
        self.asleep = False
        self._calm_since = None
        self.glance = glance
        self._handled = 0.0

    def glancing(self, still, touched, dt):
        """Call each awake tick: whether the short glance timeout still applies."""
        if self.glance:
            if not still:
                self._handled += dt
            if touched or self._handled >= self._glance_handled:
                self.glance = False
        return self.glance
