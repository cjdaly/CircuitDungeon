# SPDX-License-Identifier: MIT
"""Gesture helpers layered on the vendored qmi8658c.QMI8658C driver.

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

    def sample(self, now):
        """Read the IMU once. Returns accel/gyro plus derived tilt + shake."""
        ax, ay, az = self.imu.acceleration
        gx, gy, gz = self.imu.gyro

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
