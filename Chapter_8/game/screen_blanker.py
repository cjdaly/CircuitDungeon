# SPDX-License-Identifier: MIT
"""Screen blank-after-idle + wake-on-touch -- cd-ork.1.

This board has no physical power switch (doc/HARDWARE.md "Power / battery"):
once a battery's plugged in, the display stays lit until something turns it
off or the battery dies. ScreenBlanker turns the backlight off after a
period of no touch activity, and back on the instant a touch arrives.

The backlight (board.LCD_BL, see hardware.init_display()) is a plain GPIO
independent of the GC9A01A display driver -- no display sleep/wake command
needed, just toggle the pin.

Pure logic -- takes anything with a settable `.value` (a real
digitalio.DigitalInOut, or a fake in tests), no board/displayio imports, so
this runs under plain desktop Python (see tests/test_screen_blanker.py).
"""

DEFAULT_TIMEOUT = 20.0  # seconds of no touch before blanking -- a first
                        # guess, needs on-device feel-testing like the
                        # cd-45v prototypes' tunables did.


class ScreenBlanker:
    """Feed .update(touched, now) every frame; keeps the backlight in sync.

    Starts lit (matching hardware.init_display() turning the backlight on
    at boot) and counts idle time from the first call, not from construction
    -- so a slow startup before the main loop begins doesn't eat into the
    very first timeout.
    """

    def __init__(self, backlight, timeout=DEFAULT_TIMEOUT):
        self._backlight = backlight
        self._timeout = timeout
        self._last_activity = None
        self.lit = True

    def update(self, touched, now):
        """Returns True the tick a touch wakes the screen from blanked.

        Callers should swallow that tick's touch (treat it as just a wake,
        not a real gesture) so waking the screen doesn't also register as a
        game input -- see main.py.
        """
        if self._last_activity is None:
            self._last_activity = now

        woke = False
        if touched:
            self._last_activity = now
            if not self.lit:
                self._backlight.value = True
                self.lit = True
                woke = True
        elif self.lit and now - self._last_activity >= self._timeout:
            self._backlight.value = False
            self.lit = False
        return woke
