# SPDX-License-Identifier: MIT
"""Board bring-up for the Waveshare RP2350-Touch-LCD-1.28.

Started as a copy of Chapter_8/game/hardware.py (cd-342.1), same board; Ch9 adds
the touch reset and bus line checks used by bus_recovery.py (cd-342.16).

No board.SPI()/board.I2C() default-bus helpers exist on this board -- every
bus is built by hand from the named pins in doc/HARDWARE.md.
"""
import time

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
_TOUCH_RESET_PIN = board.GP22


def init_display():
    """Backlight on, SPI display bus up, GC9A01A driver attached.

    release_displays() must run BEFORE touching LCD_CLK/LCD_DIN: CircuitPython
    auto-configures this board's built-in status display on every boot (for
    its own splash/error screens), which holds those pins until released.

    Returns (display, backlight) -- backlight is a plain digitalio.DigitalInOut
    on board.LCD_BL, independent of the GC9A01A driver, so callers can turn it
    off/on directly (e.g. screen_blanker.py, cd-ork.1) without touching the
    display driver at all.
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
    display = GC9A01A(bus, width=WIDTH, height=HEIGHT)
    return display, backlight


def reset_touch():
    """Pulse the CST816's reset pin, which frees SDA if the chip is holding it low.

    Blocks ~220ms: the chip needs time to restart before it answers on I2C. See
    Chapter_8/doc/HARDWARE.md for how GP22 was identified.
    """
    reset = digitalio.DigitalInOut(_TOUCH_RESET_PIN)
    reset.switch_to_output(value=False)
    time.sleep(0.02)
    reset.deinit()  # released: the line idles high without our help
    time.sleep(0.2)


def init_i2c():
    """The one shared I2C bus -- IMU (0x6B) and touch controller (0x15) both live here."""
    return busio.I2C(board.IMU_SCL, board.IMU_SDA)


def read_bus_lines(samples=20):
    """(SDA high count, SCL high count) over `samples` reads, with the bus deinited.

    A line that stays low with the pull-up on is being held by a chip.
    """
    sda = digitalio.DigitalInOut(board.IMU_SDA)
    scl = digitalio.DigitalInOut(board.IMU_SCL)
    sda.switch_to_input(pull=digitalio.Pull.UP)
    scl.switch_to_input(pull=digitalio.Pull.UP)
    sda_high = scl_high = 0
    for _ in range(samples):
        sda_high += sda.value
        scl_high += scl.value
    sda.deinit()
    scl.deinit()
    return sda_high, scl_high


def init_imu(i2c):
    return qmi8658c.QMI8658C(i2c, address=_IMU_ADDRESS)


def init_touch(i2c):
    return SafeTouch(i2c, address=_TOUCH_ADDRESS)
