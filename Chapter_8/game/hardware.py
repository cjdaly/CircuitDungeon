# SPDX-License-Identifier: MIT
"""Board bring-up for the Waveshare RP2350-Touch-LCD-1.28.

No board.SPI()/board.I2C() default-bus helpers exist on this board -- every
bus is built by hand from the named pins in doc/HARDWARE.md.
"""
import board
import busio
import digitalio
import displayio
from adafruit_gc9a01a import GC9A01A
from fourwire import FourWire

import qmi8658c
from touch import SafeTouch

WIDTH = 240
HEIGHT = 240

_IMU_ADDRESS = 0x6B
_TOUCH_ADDRESS = 0x15


def init_display():
    """Backlight on, SPI display bus up, GC9A01A driver attached.

    release_displays() must run BEFORE touching LCD_CLK/LCD_DIN: CircuitPython
    auto-configures this board's built-in status display on every boot (for
    its own splash/error screens), which holds those pins until released.
    """
    displayio.release_displays()

    backlight = digitalio.DigitalInOut(board.LCD_BL)
    backlight.switch_to_output(value=True)

    spi = busio.SPI(clock=board.LCD_CLK, MOSI=board.LCD_DIN)  # write-only, no MISO
    bus = FourWire(
        spi,
        command=board.LCD_DC,
        chip_select=board.LCD_CS,
        reset=board.LCD_RST,
        baudrate=24_000_000,
    )
    return GC9A01A(bus, width=WIDTH, height=HEIGHT)


def init_i2c():
    """The one shared I2C bus -- IMU (0x6B) and touch controller (0x15) both live here."""
    return busio.I2C(board.IMU_SCL, board.IMU_SDA)


def init_imu(i2c):
    return qmi8658c.QMI8658C(i2c, address=_IMU_ADDRESS)


def init_touch(i2c):
    return SafeTouch(i2c, address=_TOUCH_ADDRESS)
