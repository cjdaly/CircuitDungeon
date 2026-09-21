# SPDX-License-Identifier: MIT
"""Top-level mode switching: interactive game <-> ornament -- cd-342.2.

Ch9 has two top-level modes (see project memory ch9-christmas-critters-
design): the interactive game, and a passive ornament scene for hanging the
device on a real tree. BOOT can't serve as an explicit toggle (it isn't a
GPIO on RP2350, see Chapter_8's cd-bp3.9), so the switch is inferred from
the two signals the board does have:

- **Interactive -> ornament**: no touch for `idle_timeout` seconds AND the
  IMU says the device is still (stillness.StillnessDetector). Requiring
  stillness means a device being carried around or held in a hand, just not
  touched, doesn't fall into ornament mode -- only one that's set down or
  hanging does.
- **Ornament -> interactive**: any touch. Deliberately touch-only, not
  "handled": the ornament scene already dims itself while being handled
  (ornament.Tree), and being carried to the tree shouldn't drop the device
  back into the game.

`just_switched` is True for the one tick a switch happens, so the caller
can swallow that tick's touch (it woke the device, it isn't a game input) --
same convention as screen_blanker.ScreenBlanker.update()'s return value.

Pure logic, no hardware imports -- runs under plain desktop Python (see
tests/test_modes.py).
"""

INTERACTIVE = "interactive"
ORNAMENT = "ornament"

DEFAULT_IDLE_TIMEOUT = 30.0  # seconds untouched before ornament mode -- a
                             # first guess, needs on-device feel-testing.


class ModeController:
    """Feed .update(touched, still, now) every frame; read .mode."""

    def __init__(self, idle_timeout=DEFAULT_IDLE_TIMEOUT):
        self._idle_timeout = idle_timeout
        self._last_touch = None
        self.mode = INTERACTIVE
        self.just_switched = False

    def update(self, touched, still, now):
        """Returns the current mode after applying this tick's inputs."""
        # Idle time counts from the first call, not construction, so slow
        # startup doesn't eat into the first timeout (same as ScreenBlanker).
        if self._last_touch is None:
            self._last_touch = now

        self.just_switched = False
        if touched:
            self._last_touch = now
            if self.mode == ORNAMENT:
                self.mode = INTERACTIVE
                self.just_switched = True
        elif (
            self.mode == INTERACTIVE
            and still
            and now - self._last_touch >= self._idle_timeout
        ):
            self.mode = ORNAMENT
            self.just_switched = True
        return self.mode
