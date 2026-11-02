# SPDX-License-Identifier: MIT
# Off-device tests for SafeTouch's error handling in game/touch.py, with
# adafruit_cst8xx replaced by a fake whose constructor/touches can fail.
#
#   python3 Chapter_9/tests/test_safe_touch.py

import os
import sys
import types
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "game"))

import touch  # noqa: E402

BAD_CHIP_ID = RuntimeError("Did not find supported CST8XX chip")
NO_ACK = ValueError("No I2C device at address: 0x15")
TIMEOUT = OSError(116, "ETIMEDOUT")


class FakeChip:
    """Stands in for adafruit_cst8xx.Adafruit_CST8XX."""

    ctor_error = None
    ctor_calls = 0
    touches_result = ()

    def __init__(self, i2c, address):
        type(self).ctor_calls += 1
        if type(self).ctor_error is not None:
            raise type(self).ctor_error

    @property
    def touches(self):
        result = type(self).touches_result
        if isinstance(result, Exception):
            raise result
        return result


class TestSafeTouchErrors(unittest.TestCase):
    def setUp(self):
        FakeChip.ctor_error = None
        FakeChip.ctor_calls = 0
        FakeChip.touches_result = ()
        module = types.ModuleType("adafruit_cst8xx")
        module.Adafruit_CST8XX = FakeChip
        sys.modules["adafruit_cst8xx"] = module
        self.addCleanup(sys.modules.pop, "adafruit_cst8xx", None)
        self.touch = touch.SafeTouch(i2c=None, retry_interval=1.0)

    def test_connect_errors_read_as_no_touch(self):
        for error in (BAD_CHIP_ID, NO_ACK, TIMEOUT):
            with self.subTest(error=error):
                FakeChip.ctor_error = error
                self.touch = touch.SafeTouch(i2c=None, retry_interval=1.0)
                self.assertIsNone(self.touch.poll(0.0))
                self.assertFalse(self.touch.connected)

    def test_bad_chip_id_backs_off_before_retrying(self):
        FakeChip.ctor_error = BAD_CHIP_ID
        self.touch.poll(0.0)
        self.touch.poll(0.5)
        self.assertEqual(FakeChip.ctor_calls, 1)
        self.touch.poll(1.0)
        self.assertEqual(FakeChip.ctor_calls, 2)

    def test_reconnects_after_bad_chip_id_clears(self):
        FakeChip.ctor_error = BAD_CHIP_ID
        self.touch.poll(0.0)
        FakeChip.ctor_error = None
        FakeChip.touches_result = ({"x": 5, "y": 7},)
        self.assertEqual(self.touch.poll(1.0), (5, 7))
        self.assertTrue(self.touch.connected)

    def test_use_bus_reconnects_on_the_next_poll(self):
        FakeChip.ctor_error = BAD_CHIP_ID
        self.touch.poll(0.0)  # failed, backing off until t=1
        FakeChip.ctor_error = None
        self.touch.use_bus(object())
        self.assertFalse(self.touch.connected)
        self.touch.poll(0.1)
        self.assertTrue(self.touch.connected)

    def test_poll_errors_drop_the_connection(self):
        for error in (BAD_CHIP_ID, NO_ACK, TIMEOUT):
            with self.subTest(error=error):
                self.touch = touch.SafeTouch(i2c=None, retry_interval=1.0)
                FakeChip.touches_result = ()
                self.assertIsNone(self.touch.poll(0.0))
                self.assertTrue(self.touch.connected)
                FakeChip.touches_result = error
                self.assertIsNone(self.touch.poll(0.1))
                self.assertFalse(self.touch.connected)


if __name__ == "__main__":
    unittest.main()
