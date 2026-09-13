# SPDX-License-Identifier: MIT
"""Retry-safe wrapper around adafruit_cst8xx, plus a tap/swipe classifier.

Ported from Chapter_8/game/touch.py -- same CST816 touch controller (shares
the IMU's I2C bus, unreliable to reach, see Chapter_8/doc/HARDWARE.md), same
board. Chapter_8's version was proven on real hardware 2026-09-13 via
room_nav_demo.py's edge-gesture navigation; this is a straight port, not a
rewrite.

SafeTouch connects lazily: construction never raises, poll() attempts a
(re)connect at most once per _RETRY_INTERVAL and otherwise just reports "no
touch" -- callers stay alive whether or not touch has come up yet. Check
.connected if you want to show that state explicitly.

adafruit_cst8xx is imported lazily inside SafeTouch.poll() rather than at
module level, so GestureTracker (pure logic, no hardware) stays importable
under plain desktop Python -- see tests/test_edge_gesture.py and
edge_gesture.py, which reuses it.
"""

_RETRY_INTERVAL = 1.0  # seconds between reconnect attempts while not connected

# Gesture thresholds, in touch-panel units (assumed == screen pixels, 240x240)
# and seconds.
_TAP_MAX_MOVE = 12
_TAP_MAX_DURATION = 0.4
_SWIPE_MIN_MOVE = 30


class SafeTouch:
    """Poll-friendly wrapper: .poll(now) -> (x, y) or None, never raises."""

    def __init__(self, i2c, address=0x15, retry_interval=_RETRY_INTERVAL):
        self._i2c = i2c
        self._address = address
        self._retry_interval = retry_interval
        self._ctp = None
        self._next_attempt = 0.0

    @property
    def connected(self):
        return self._ctp is not None

    def poll(self, now):
        """Return (x, y) of the first active touch this tick, or None.

        Swallows every I2C error -- both "not connected yet" and a dropped
        connection read as "no touch" rather than an exception.
        """
        if self._ctp is None:
            if now < self._next_attempt:
                return None
            try:
                import adafruit_cst8xx

                self._ctp = adafruit_cst8xx.Adafruit_CST8XX(self._i2c, address=self._address)
            except (ValueError, OSError):
                self._next_attempt = now + self._retry_interval
                return None

        try:
            touches = self._ctp.touches
        except (ValueError, OSError):
            self._ctp = None  # dropped -- next poll() retries the connection
            self._next_attempt = now + self._retry_interval
            return None
        if not touches:
            return None
        point = touches[0]
        return point["x"], point["y"]


class GestureTracker:
    """Turns a stream of SafeTouch.poll() points into tap/swipe events.

    Call .update(point, now) once per frame with the latest poll() result and
    time.monotonic(). Returns a gesture label the tick a touch-and-release
    completes, else None. .current holds the live touch point while one is
    in progress (for drawing a follow-the-finger marker).
    """

    def __init__(self):
        self._start = None
        self._start_t = None
        self._last = None

    def update(self, point, now):
        gesture = None
        if point is not None:
            if self._start is None:
                self._start = point
                self._start_t = now
            self._last = point
        elif self._start is not None:
            gesture = self._classify(now)
            self._start = None
            self._start_t = None
            self._last = None
        return gesture

    def _classify(self, now):
        dx = self._last[0] - self._start[0]
        dy = self._last[1] - self._start[1]
        duration = now - self._start_t
        dist = (dx * dx + dy * dy) ** 0.5

        if dist <= _TAP_MAX_MOVE and duration <= _TAP_MAX_DURATION:
            return "tap"
        if dist >= _SWIPE_MIN_MOVE:
            if abs(dx) >= abs(dy):
                return "swipe_right" if dx > 0 else "swipe_left"
            return "swipe_down" if dy > 0 else "swipe_up"
        return None

    @property
    def current(self):
        """The live touch point mid-stroke, or None between touches."""
        return self._last if self._start is not None else None
