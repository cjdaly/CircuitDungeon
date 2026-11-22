# SPDX-License-Identifier: MIT
"""Touch and motion, read once a tick -- cd-342.47.2.

read() polls the touch chip and the IMU and keeps stillness up to date. A
failed IMU read usually means the touch chip has locked the shared I2C bus
(cd-342.16): the bus is rebuilt, at most every _REBUILD_MIN_INTERVAL s, and
the last known stillness holds meanwhile.
"""
import stillness

_REBUILD_MIN_INTERVAL = 5.0  # s between I2C bus rebuilds, if they aren't helping


class Sensors:
    """`touch` needs .poll(now) -> (x, y) | None; `imu` needs .sample(now) -> dict
    with "jerk" and "accel" (imu.ImuGestures); `bus_recovery`, if given,
    .rebuild() -> status string. Timings and IMU errors go into `stats`."""

    def __init__(self, touch, imu, clock, stats, bus_recovery=None, tlog=None):
        self.touch = touch
        self._imu = imu
        self._clock = clock
        self._stats = stats
        self._bus_recovery = bus_recovery
        self._tlog = tlog
        self._set_awake = getattr(touch, "set_awake", None)
        self._detector = stillness.StillnessDetector()
        self._next_rebuild = 0.0
        self._awaiting_good_read = False

    @property
    def still(self):
        return self._detector.is_still

    def read(self, now):
        """This tick's touch point (or None), with stillness brought up to date."""
        point = self.touch.poll(now)
        if self._tlog is not None:
            self._tlog.sample(now, point, getattr(self.touch, "last_quiet", False))
        after_touch = self._clock()
        self._stats.touch_s = max(self._stats.touch_s, after_touch - now)
        sample = self.read_imu(now)
        if sample is not None:  # on a failed read, hold last-known stillness
            self._feel(sample["jerk"], now)
        self._stats.imu_s = max(self._stats.imu_s, self._clock() - after_touch)
        return point

    def _feel(self, jerk, now):
        was_still = self._detector.is_still
        self._detector.update(jerk, now)
        if self._detector.is_still != was_still:
            raw = getattr(self._imu, "last_raw", None)
            print("t={:.1f} {} (jerk {:.2f}, raw {})".format(
                now, "still" if self._detector.is_still else "handled", jerk,
                tuple(round(v, 2) for v in raw) if raw else "?"))

    def read_imu(self, now):
        """One IMU sample, or None after a failed read (rebuilding the bus if due)."""
        try:
            sample = self._imu.sample(now)
        except (OSError, ValueError, RuntimeError) as exc:
            self._stats.imu_errors += 1
            self._stats.last_imu_error = repr(exc)
            if self._bus_recovery is not None and now >= self._next_rebuild:
                started = self._clock()
                status = self._bus_recovery.rebuild()
                print("t={:.1f} bus rebuild {}ms: {}".format(
                    now, int((self._clock() - started) * 1000), status))
                self._next_rebuild = self._clock() + _REBUILD_MIN_INTERVAL
                self._awaiting_good_read = True
            return None
        if self._awaiting_good_read:
            self._awaiting_good_read = False
            print("t={:.1f} imu read ok after bus rebuild".format(now))
        return sample

    def handled(self):
        """Woken by motion: it's in someone's hands, not still."""
        self._detector = stillness.StillnessDetector()

    def awake(self, on):
        """Whether the touch chip should stay awake (only while it's being played)."""
        if self._set_awake is not None:
            self._set_awake(on)

    def sleep(self):
        """Into deep idle: the touch chip to sleep, the IMU's history forgotten."""
        if hasattr(self.touch, "sleep_now"):
            self.touch.sleep_now()
        self._imu.reset()
