# SPDX-License-Identifier: MIT
"""Screen blank-after-idle + wake-on-activity -- cd-zw2.7 (ported from Ch8's
cd-ork.1/cd-ork.2).

This board has no physical power switch (Chapter_8/doc/HARDWARE.md "Power /
battery"): once a battery's plugged in, the display stays lit until
something turns it off or the battery dies. ScreenBlanker turns the
backlight off after a period of no activity, and back on the instant
activity resumes.

The backlight (board.LCD_BL) is a plain GPIO independent of the display
driver -- no display sleep/wake command needed, just toggle the pin (see
Chapter_8/game/hardware.py's init_display(), which returns it alongside the
display object).

First needed here for ornament mode's much-longer keep-alive timeout
(Chapter_8's ornament_demo.py uses "handled" -- not is_still -- as the
activity signal, since ornament mode has no touchscreen input); equally
usable later for Ch9's interactive mode with touch as the activity signal,
same as Chapter_8's main.py.

Pure logic -- takes anything with a settable `.value` (a real
digitalio.DigitalInOut, or a fake in tests), no board/displayio imports, so
this runs under plain desktop Python (see tests/test_screen_blanker.py).
Confirmed working on real Chapter 8 hardware 2026-09-13.
"""

DEFAULT_TIMEOUT = 20.0  # seconds of no activity before blanking -- a first
                        # guess, needs on-device feel-testing per use case
                        # (ornament mode uses a much longer override).


class ScreenBlanker:
    """Feed .update(active, now) every frame; keeps the backlight in sync.

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

    def update(self, active, now):
        """Returns True the tick activity wakes the screen from blanked.

        Callers should swallow that tick's input (treat it as just a wake,
        not a real gesture) so waking the screen doesn't also register as a
        game input -- see Chapter_8/game/main.py.
        """
        if self._last_activity is None:
            self._last_activity = now

        woke = False
        if active:
            self._last_activity = now
            if not self.lit:
                self._backlight.value = True
                self.lit = True
                woke = True
        elif self.lit and now - self._last_activity >= self._timeout:
            self._backlight.value = False
            self.lit = False
        return woke
