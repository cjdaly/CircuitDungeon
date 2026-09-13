# SPDX-License-Identifier: MIT
"""Stillness/handled detection from a stream of IMU jerk readings -- cd-zw2.7.

Ornament mode is meant to run non-interactively while the device hangs on a
tree. This is the signal for telling "hanging still" apart from "being
picked up/handled", using only accelerometer jerk (frame-to-frame change in
acceleration) -- the same quantity Chapter 8's imu.py's ImuGestures computes
for shake detection (returned as sample["jerk"]), just tracked over a
longer continuous-quiet window instead of a single spike.

Ported from Chapter_8/game/stillness.py (cd-45v.5's prototype) -- confirmed
working on real hardware 2026-09-13 (flips to "still" after ~3s of no
motion, back to "handled" immediately on pickup).

Pure logic, no hardware imports -- runs under plain desktop Python (see
tests/test_stillness.py).

STATUS: default thresholds (STILL_JERK_MAX/STILL_HOLD) are the same ones
tried on Chapter 8 hardware and found acceptable there; not independently
recalibrated for Chapter 9.
"""

STILL_JERK_MAX = 2.0  # m/s^2 -- frame-to-frame jerk at/below this counts as "quiet"
STILL_HOLD = 3.0  # seconds of continuous quiet before switching to "still"


class StillnessDetector:
    """Feed .update(jerk, now) each tick; .is_still reports the current mode.

    Starts "not still" (handled) -- a fresh device shouldn't claim to be
    calmly hanging before it's had a chance to observe anything.
    """

    def __init__(self, jerk_max=STILL_JERK_MAX, hold=STILL_HOLD):
        self._jerk_max = jerk_max
        self._hold = hold
        self._quiet_since = None
        self.is_still = False

    def update(self, jerk, now):
        if jerk > self._jerk_max:
            self._quiet_since = None
            self.is_still = False
        elif self._quiet_since is None:
            self._quiet_since = now
        elif now - self._quiet_since >= self._hold:
            self.is_still = True
        return self.is_still
