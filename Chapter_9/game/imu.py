# SPDX-License-Identifier: MIT
"""Gesture helpers layered on the vendored qmi8658c.QMI8658C driver.

Copied from Chapter_8/game/imu.py (cd-342.1). Ch9 only reads sample()["jerk"]
(for stillness.py and power.py); tilt/shake are unused here for now. Ch9 runs
with the gyro switched off to save power (hardware.init_imu, cd-342.28), so
sample() skips reading it and reports (0, 0, 0).

Pure math on top of .acceleration/.gyro -- no I2C quirks here (unlike touch.py;
the QMI8658 answers reliably every poll).
"""
import math

# Shake = a big jerk (frame-to-frame change in acceleration) within a short
# window. Tuned by feel against STANDARD_GRAVITY (9.8 m/s^2) reads at rest;
# revisit once someone's actually shaking the device on the bench.
_SHAKE_JERK_THRESHOLD = 18.0  # m/s^2, summed |delta| across x+y+z
_SHAKE_HOLD = 0.4  # seconds the "shake" flag stays latched after it fires


class ImuGestures:
    def __init__(self, imu):
        self.imu = imu
        self._prev_accel = None
        self._shake_until = 0.0
        self.last_raw = None  # the latest read, for logging

    def reset(self):
        """Forget the last reading, so the next sample's jerk is 0.0.

        Call after changing the IMU's rate or rebuilding it: the first reading
        after a change can jump, which would otherwise look like motion.
        """
        self._prev_accel = None

    def sample(self, now):
        """Read the IMU once. Returns accel/gyro plus derived tilt + shake."""
        ax, ay, az = self.last_raw = self.imu.acceleration
        gx = gy = gz = 0.0  # the gyro is off in Ch9; reading it is a wasted I2C trip

        jerk = 0.0
        if self._prev_accel is not None:
            px, py, pz = self._prev_accel
            jerk = abs(ax - px) + abs(ay - py) + abs(az - pz)
            if jerk >= _SHAKE_JERK_THRESHOLD:
                self._shake_until = now + _SHAKE_HOLD
        self._prev_accel = (ax, ay, az)

        # Tilt from the gravity vector -- degrees, 0 when flat/face-up.
        pitch = math.degrees(math.atan2(ay, az)) if (ay or az) else 0.0
        roll = math.degrees(math.atan2(ax, az)) if (ax or az) else 0.0

        return {
            "accel": (ax, ay, az),
            "gyro": (gx, gy, gz),
            "pitch": pitch,
            "roll": roll,
            "shake": now < self._shake_until,
            "jerk": jerk,  # raw frame-to-frame delta, 0.0 on the first sample
        }
