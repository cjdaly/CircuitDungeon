# SPDX-License-Identifier: MIT
"""Board bring-up for the Waveshare RP2350-Touch-LCD-1.28.

Started as a copy of Chapter_8/game/hardware.py (cd-342.1), same board; Ch9 adds
the touch reset and bus line checks used by bus_recovery.py (cd-342.16).

No board.SPI()/board.I2C() default-bus helpers exist on this board -- every
bus is built by hand from the named pins in doc/HARDWARE.md.
"""
import time

import analogio
import board
import busio
import digitalio
import displayio
import microcontroller
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


def clock_out_bus(max_clocks=18):
    """Pulse SCL until SDA goes high. Returns the clocks it took, or None if it never did.

    A chip cut off mid-read by a reset keeps driving SDA, waiting for the rest
    of its byte; a few clocks let it finish and let go. Seen on ws-2 2026-11-07:
    after a reset-pin reset the IMU held SDA low (the touch-chip reset didn't
    help) and one clock freed it. Call with the bus deinited.
    """
    sda = digitalio.DigitalInOut(board.IMU_SDA)
    sda.switch_to_input(pull=digitalio.Pull.UP)
    scl = digitalio.DigitalInOut(board.IMU_SCL)
    scl.switch_to_output(value=True, drive_mode=digitalio.DriveMode.OPEN_DRAIN)
    took = 0 if sda.value else None
    clocks = 0
    while took is None and clocks < max_clocks:
        clocks += 1
        scl.value = False
        time.sleep(0.0001)
        scl.value = True
        time.sleep(0.0001)
        if sda.value:
            took = clocks
    sda.deinit()
    scl.deinit()
    return took


def init_imu(i2c):
    """The IMU with its gyro off: Ch9 only uses the accelerometer (cd-342.28)."""
    imu = qmi8658c.QMI8658C(i2c, address=_IMU_ADDRESS)
    imu.gyro_enable = 0
    return imu


def init_touch(i2c):
    return SafeTouch(i2c, address=_TOUCH_ADDRESS)


# Deep idle (power.py, cd-342.28). 48 MHz is the lowest clock that still reads
# the IMU quickly (~4ms): at 24 MHz a read took ~140ms on ws-1, and 12 MHz is
# refused. The low-power accel rate needs the gyro off.
_FULL_CLOCK = 150_000_000
_IDLE_CLOCK = 48_000_000
_GC9A01A_SLPIN, _GC9A01A_SLPOUT = 0x10, 0x11
_GC9A01A_DISPOFF, _GC9A01A_DISPON = 0x28, 0x29

# QMI8658 wake-on-motion (cd-342.30): the IMU toggles an interrupt pin on each
# burst of motion, so the CPU can truly sleep until then. Register sequence
# found on ws-2 2026-11-07. CAL1_H 0x40 asks for INT1, yet the toggle shows up
# on board.IMU_INT2; whichever way that mapping goes, IMU_INT2 is the pin.
_QMI_CTRL1, _QMI_CTRL2, _QMI_CTRL7, _QMI_CTRL9 = 0x02, 0x03, 0x08, 0x0A
_QMI_CAL1_L, _QMI_CAL1_H, _QMI_STATUSINT = 0x0B, 0x0C, 0x2D
_QMI_CTRL1_NORMAL = 0x60  # address auto-increment, big-endian (as the driver sets it)
_QMI_INT_ENABLE = 0x18  # INT1 + INT2 outputs on
_QMI_ACCEL_8G_LP21 = (2 << 4) | 13
_QMI_ACCEL_8G_125HZ = (2 << 4) | 6
_QMI_CMD_WRITE_WOM = 0x08
_WOM_THRESHOLD_MG = 100
_WOM_CAL1_H = 0x40 | 0x08  # interrupt routing, start low, ignore the first 8 samples
_BUS_ERRORS = (OSError, RuntimeError, ValueError)


def _has_alarm():
    try:
        import alarm  # noqa: F401 -- CircuitPython 11+ on RP2350
    except ImportError:
        return False
    return True


class DevicePower:
    """Puts the panel, IMU and CPU into deep idle and back.

    `gestures` (imu.ImuGestures) is passed rather than the IMU itself because
    bus_recovery swaps in a new IMU object; this always reaches the current one.

    With the `alarm` module (CircuitPython 11+), deep idle is a true light
    sleep that the IMU's wake-on-motion pin ends (.can_doze, .doze()). Without
    it, the CPU clock drops and app.py polls the accelerometer instead.
    """

    def __init__(self, display, gestures):
        self._display = display
        self._gestures = gestures
        self.can_doze = _has_alarm()

    def sleep(self):
        self._display.auto_refresh = False
        bus = self._display.bus
        bus.send(_GC9A01A_DISPOFF, b"")
        bus.send(_GC9A01A_SLPIN, b"")
        if self.can_doze:
            self._imu_guarded(self._wake_on_motion, True)
        else:
            self._imu_guarded(self._set_rate, _QMI_ACCEL_8G_LP21)
            microcontroller.cpu.frequency = _IDLE_CLOCK
        self._gestures.reset()

    def wake(self):
        if self.can_doze:
            self._imu_guarded(self._wake_on_motion, False)
        else:
            microcontroller.cpu.frequency = _FULL_CLOCK
            self._imu_guarded(self._set_rate, _QMI_ACCEL_8G_125HZ)
        self._gestures.reset()
        bus = self._display.bus
        bus.send(_GC9A01A_SLPOUT, b"")
        time.sleep(0.12)  # the panel needs 120ms after SLPOUT
        bus.send(_GC9A01A_DISPON, b"")
        self._display.auto_refresh = True

    def doze(self, seconds):
        """Light sleep until the IMU signals motion or `seconds` pass. True if it moved."""
        import alarm
        import alarm.pin
        import alarm.time

        pin = digitalio.DigitalInOut(board.IMU_INT2)
        level = pin.value
        pin.deinit()
        # The pin toggles on each motion burst, so wake on the other level.
        woke = alarm.light_sleep_until_alarms(
            alarm.pin.PinAlarm(board.IMU_INT2, value=not level),
            alarm.time.TimeAlarm(monotonic_time=time.monotonic() + seconds),
        )
        return isinstance(woke, alarm.pin.PinAlarm)

    def _imu_guarded(self, action, arg):
        try:
            action(arg)
        except _BUS_ERRORS as exc:
            print("imu power change failed:", repr(exc))  # the read loop recovers the bus

    def _write(self, register, value):
        device = self._gestures.imu.i2c_device
        with device:
            device.write(bytes((register, value)))

    def _read(self, register):
        device = self._gestures.imu.i2c_device
        out = bytearray(1)
        with device:
            device.write_then_readinto(bytes((register,)), out)
        return out[0]

    def _set_rate(self, ctrl2):
        self._write(_QMI_CTRL7, 0x00)
        self._write(_QMI_CTRL2, ctrl2)
        self._write(_QMI_CTRL7, 0x01)  # accelerometer only; the gyro stays off

    def _wake_on_motion(self, on):
        self._write(_QMI_CTRL7, 0x00)
        self._write(_QMI_CTRL2, _QMI_ACCEL_8G_LP21 if on else _QMI_ACCEL_8G_125HZ)
        self._write(_QMI_CAL1_L, _WOM_THRESHOLD_MG if on else 0)  # 0 turns WoM off
        self._write(_QMI_CAL1_H, _WOM_CAL1_H if on else 0)
        self._write(_QMI_CTRL9, _QMI_CMD_WRITE_WOM)
        deadline = time.monotonic() + 0.5
        while not self._read(_QMI_STATUSINT) & 0x80 and time.monotonic() < deadline:
            time.sleep(0.005)
        self._write(_QMI_CTRL9, 0x00)  # acknowledge the command
        self._write(_QMI_CTRL1, _QMI_CTRL1_NORMAL | (_QMI_INT_ENABLE if on else 0))
        self._write(_QMI_CTRL7, 0x01)


class BatteryAdc:
    """BAT_ADC, averaged: call it for a raw 0-65535 reading (drain_log.py, cd-342.29).

    Raw because the divider ratio is unconfirmed (cd-bp3.6.1). On USB the pin
    reads ~1.57 V, which a x3 divider would make ~4.7 V: probably the system
    rail rather than the cell while USB power is present.
    """

    def __init__(self, samples=16):
        self._adc = analogio.AnalogIn(board.BAT_ADC)
        self._samples = samples

    def __call__(self):
        total = 0
        for _ in range(self._samples):
            total += self._adc.value
        return total // self._samples
