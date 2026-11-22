# SPDX-License-Identifier: MIT
"""The screen's light and the board's sleep -- cd-342.47.2.

Blanking is per mode, since the two modes want opposite things: the game
blanks after a long stretch of no *touch* (a backstop for a board carried
around but not played -- one set down goes to the ornament first, modes.py);
the ornament blanks after a much longer stretch of *stillness*, and being
handled counts as activity. The blanker is rebuilt on every mode switch, with
the backlight forced on, so its lit/unlit bookkeeping can't disagree with the
real pin. Nothing is redrawn while the backlight is off.

Deep idle (power.py, cd-342.28): once the screen is dark and the board has
been still a while, the panel, IMU and CPU clock go low-power and the loop
only reads the accelerometer a few times a second until the board moves.
"""
import gc

import modes
import power as deep_idle
from screen_blanker import ScreenBlanker

INTERACTIVE_BLANK_TIMEOUT = 120.0  # s of no touch -- > modes' idle timeout
ORNAMENT_BLANK_TIMEOUT = 300.0  # s of continuous stillness, as in Ch8's demo


class PowerManager:
    """`power`, if given, needs .sleep(), .wake(), .can_doze and .doze(s)
    (hardware.DevicePower), and turns deep idle on; `drain`, if given,
    .tick(now, lit, asleep) and .woke(shift) (drain_log.DrainLog)."""

    def __init__(self, display, backlight, sensors, clock, power=None, drain=None):
        self._display = display
        self._backlight = backlight
        self._sensors = sensors
        self._clock = clock
        self._power = power
        self._drain = drain
        self._deep = deep_idle.DeepIdle()
        self._mode = modes.INTERACTIVE
        self._blanker = None
        self._lit = True  # what the display was last told
        self._last_tick = clock()

    @property
    def lit(self):
        return self._blanker.lit

    def reset(self, mode):
        """A fresh blanker for `mode`, with the backlight on."""
        self._mode = mode
        if self._deep.glance:  # woken by motion nobody has followed up on yet
            timeout = deep_idle.GLANCE_TIMEOUT
        elif mode == modes.ORNAMENT:
            timeout = ORNAMENT_BLANK_TIMEOUT
        else:
            timeout = INTERACTIVE_BLANK_TIMEOUT
        self._backlight.value = True
        self._blanker = ScreenBlanker(self._backlight, timeout=timeout)

    @property
    def sleeping(self):
        """In deep idle: the loop calls asleep() instead of a normal tick."""
        return self._deep.asleep

    def activity(self, active, now):
        """Feed the blanker; True if this woke a dark screen."""
        return self._blanker.update(active, now)

    def asleep(self, now):
        """In deep idle, wait for motion. Returns how long the loop should sleep
        before its next tick, or None once it's woken and the tick should go on."""
        if self._power.can_doze:  # a real light sleep, ended by the IMU's motion pin
            moved = self._power.doze(deep_idle.DOZE)
            now = self._clock()
            why = "motion pin"
        else:
            sample = self._sensors.read_imu(now)
            moved = sample is not None and self._deep.should_wake(sample["accel"])
            why = "moved {:.2f} from rest".format(self._deep.shift) if moved else ""
        if not moved:
            if self._drain is not None:
                self._drain.tick(now, False, True)
            return 0 if self._power.can_doze else deep_idle.TICK
        self._power.wake()
        self._deep.wake()  # a glance until someone handles or touches it
        self._sensors.handled()
        self.reset(self._mode)
        self._blanker.update(True, now)
        self._last_tick = now
        if self._drain is not None:
            self._drain.woke(self._deep.shift)
        print("t={:.1f} deep idle -> awake ({})".format(now, why))
        return None

    def settle(self, now, touched):
        """End of an awake tick: the glance timeout, the display's refresh, and
        whether to drop into deep idle."""
        still = self._sensors.still
        if self._deep.glance and not self._deep.glancing(still, touched, now - self._last_tick):
            self.reset(self._mode)  # picked up for real: the usual timeout
            print("t={:.1f} handled after wake: usual blank timeout".format(now))
        self._last_tick = now
        lit = self._blanker.lit
        if lit != self._lit:
            self._lit = lit
            self._display.auto_refresh = lit  # don't redraw a dark screen
            print("t={:.1f} backlight {}".format(now, "on" if lit else "off"))
        if self._power is not None and self._deep.should_enter(lit, still, now):
            self._sensors.sleep()
            self._deep.enter()
            self._power.sleep()
            gc.collect()
            print("t={:.1f} awake -> deep idle  free={}".format(now, gc.mem_free()))
        if self._drain is not None:
            self._drain.tick(now, lit, False)
