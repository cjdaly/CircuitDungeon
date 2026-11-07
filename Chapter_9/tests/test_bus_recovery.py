# SPDX-License-Identifier: MIT
# Off-device tests for game/bus_recovery.py, with the hardware faked.
#
#   python3 Chapter_9/tests/test_bus_recovery.py

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "game"))

from bus_recovery import BusRecovery  # noqa: E402


class FakeBus:
    def __init__(self):
        self.deinit_calls = 0

    def deinit(self):
        self.deinit_calls += 1


class FakeGestures:
    imu = "old imu"
    resets = 0

    def reset(self):
        self.resets += 1


class FakeTouch:
    bus = None

    def use_bus(self, i2c):
        self.bus = i2c


class TestBusRecovery(unittest.TestCase):
    def setUp(self):
        self.old_bus = FakeBus()
        self.new_bus = FakeBus()
        self.gestures = FakeGestures()
        self.touch = FakeTouch()
        self.bus_error = None
        self.imu_error = None
        self.events = []
        self.recovery = BusRecovery(
            self.old_bus, self.gestures, self.touch,
            self._make_i2c, self._make_imu, self._read_lines, self._reset_touch,
        )

    def _read_lines(self):
        self.events.append("read lines")
        return (20, 20) if "reset" in self.events else (0, 20)

    def _reset_touch(self):
        self.events.append("reset")

    def _make_i2c(self):
        self.events.append("make bus")
        if self.bus_error:
            raise self.bus_error
        return self.new_bus

    def _make_imu(self, i2c):
        if self.imu_error:
            raise self.imu_error
        return ("new imu", i2c)

    def test_success_moves_imu_and_touch_to_the_new_bus(self):
        status = self.recovery.rebuild()
        self.assertEqual(self.old_bus.deinit_calls, 1)
        self.assertEqual(self.gestures.imu, ("new imu", self.new_bus))
        self.assertIs(self.touch.bus, self.new_bus)
        self.assertTrue(status.startswith("ok"), status)

    def test_success_forgets_the_last_reading(self):
        # A restarted IMU's first reading jumps; it mustn't look like a pickup.
        self.recovery.rebuild()
        self.assertEqual(self.gestures.resets, 1)

    def test_touch_chip_is_reset_before_the_new_bus_is_made(self):
        self.recovery.rebuild()
        self.assertEqual(self.events, ["read lines", "reset", "read lines", "make bus"])

    def test_status_reports_line_levels_before_and_after_the_reset(self):
        status = self.recovery.rebuild()
        self.assertIn("before reset SDA high 0/20", status)
        self.assertIn("after SDA high 20/20", status)

    def test_held_lines_are_reported_without_raising(self):
        self.bus_error = RuntimeError("No pull up found on SDA or SCL")
        status = self.recovery.rebuild()
        self.assertTrue(status.startswith("FAILED"), status)
        self.assertIn("No pull up", status)
        self.assertEqual(self.gestures.imu, "old imu")
        self.assertIsNone(self.touch.bus)

    def test_retry_after_failed_rebuild_can_succeed(self):
        self.bus_error = RuntimeError("No pull up found on SDA or SCL")
        self.recovery.rebuild()
        self.bus_error = None
        status = self.recovery.rebuild()
        self.assertTrue(status.startswith("ok"), status)
        self.assertIs(self.touch.bus, self.new_bus)
        self.assertEqual(self.recovery.rebuilds, 2)

    def test_imu_failure_leaves_the_new_bus_to_deinit_next_time(self):
        self.imu_error = OSError(116, "ETIMEDOUT")
        status = self.recovery.rebuild()
        self.assertTrue(status.startswith("FAILED"), status)
        self.imu_error = None
        self.recovery.rebuild()
        self.assertEqual(self.new_bus.deinit_calls, 1)


if __name__ == "__main__":
    unittest.main()
