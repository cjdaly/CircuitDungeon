# The MIT License (MIT)
#
# Copyright (c) 2026 Chris J Daly (github user cjdaly)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import board


class GameDisplay:
    def __init__(self):
        self.screen = None
        self.groups = {}
        self.grids = {}
        self.sprites = {}
        self.neopixel = None
        # callable → dict with keys 'up','down','left','right','a','b','x','y'.
        # Boards without X/Y (PyBadge d-pad, Clue) always report them False;
        # PicoSystem — Chapter 7's target — wires all four face buttons.
        self.read_buttons = None


# board.board_id is CircuitPython's documented board identifier — matches the
# slug in each board's circuitpython.org/board/<id>/ URL (see doc/SYSTEMS.md).
# Boards sharing an entry here share a button layout: PyBadge and EdgeBadge
# are both plain d-pad-on-shift-register. PyGamer is deliberately *not*
# listed — it also exposes BUTTON_CLOCK/BUTTON_OUT/BUTTON_LATCH (a
# shift-register for its 4 face buttons), which used to make it match the
# PyBadge branch below by accident, but its directional input is a separate
# analog thumbstick (JOYSTICK_X/JOYSTICK_Y) that _pybadge()'s
# ShiftRegisterKeys(key_count=8) can't read. Same story for PewPew M4/T-Deck:
# no dedicated handler yet, so they fall through to _generic() rather than
# silently misreading the wrong board's controls. PicoSystem has its own
# entry (_PICOSYSTEM_FAMILY below) — direct-wired GPIOs, not a shift register.
_PYBADGE_FAMILY = {"pybadge", "edgebadge"}
_CLUE_FAMILY = {"clue_nrf52840_express"}
_PICOSYSTEM_FAMILY = {"pimoroni_picosystem"}


def detect():
    """Return a populated GameDisplay for the current board."""
    board_id = getattr(board, "board_id", "")
    if board_id in _PYBADGE_FAMILY:
        return _pybadge()
    elif board_id in _CLUE_FAMILY:
        return _clue()
    elif board_id in _PICOSYSTEM_FAMILY:
        return _picosystem()
    elif hasattr(board, "NEOPIXEL") and not hasattr(board, "BUTTON_A"):  # HalloWing
        # HalloWing's board_id isn't confirmed yet (no unit on hand — see
        # doc/SYSTEMS.md); this heuristic fallback stays until it is.
        return _hallowing()
    else:
        return _generic()


_NO_BUTTONS = {
    "up": False, "down": False, "left": False, "right": False,
    "a": False, "b": False, "x": False, "y": False,
}


def _pybadge():
    import keypad
    import neopixel

    gd = GameDisplay()
    gd.screen = board.DISPLAY
    gd.neopixel = neopixel.NeoPixel(board.NEOPIXEL, 1)

    keys = keypad.ShiftRegisterKeys(
        clock=board.BUTTON_CLOCK,
        data=board.BUTTON_OUT,
        latch=board.BUTTON_LATCH,
        key_count=8,
        value_when_pressed=True,
    )
    # key_number order on the 74HC165 shift register: B,A,START,SELECT,RIGHT,DOWN,UP,LEFT.
    # START/SELECT have no slot in the engine's button dict, so they're dropped (None).
    names = ["b", "a", None, None, "right", "down", "up", "left"]
    state = dict(_NO_BUTTONS)

    def read_buttons():
        while True:
            event = keys.events.get()
            if event is None:
                break
            name = names[event.key_number]
            if name is not None:
                state[name] = event.pressed
        return dict(state)

    gd.read_buttons = read_buttons
    return gd


def _clue():
    import digitalio
    import neopixel

    gd = GameDisplay()
    gd.screen = board.DISPLAY
    gd.neopixel = neopixel.NeoPixel(board.NEOPIXEL, 1)

    btn_a = digitalio.DigitalInOut(board.BUTTON_A)
    btn_a.switch_to_input(pull=digitalio.Pull.DOWN)
    btn_b = digitalio.DigitalInOut(board.BUTTON_B)
    btn_b.switch_to_input(pull=digitalio.Pull.DOWN)

    # Clue has no d-pad, only the two side buttons.
    def read_buttons():
        buttons = dict(_NO_BUTTONS)
        buttons["a"] = btn_a.value
        buttons["b"] = btn_b.value
        return buttons

    gd.read_buttons = read_buttons
    return gd


def _picosystem():
    import digitalio

    gd = GameDisplay()
    gd.screen = board.DISPLAY
    # The status LED is 3 discrete PWM-driven pins (LED_R/LED_G/LED_B), not an
    # addressable strip like PyBadge's — no NeoPixel-compatible object to hand back.
    gd.neopixel = None

    # RP2040 GPIOs wired directly to the D-pad and all four face buttons (no
    # shift register like PyBadge's). Each has an internal pull-up and reads
    # low when pressed — confirmed against Pimoroni's own C++ SDK, which does
    # the same: `button(b) { return !(_io & (1U << b)); }`
    # (pimoroni/picosystem hardware.cpp). Chapter 7 uses X and Y for chorded
    # actions (see the button-input-model bead), so all eight are wired here.
    pin_names = {
        "up": board.SW_UP,
        "down": board.SW_DOWN,
        "left": board.SW_LEFT,
        "right": board.SW_RIGHT,
        "a": board.SW_A,
        "b": board.SW_B,
        "x": board.SW_X,
        "y": board.SW_Y,
    }
    switches = {}
    for name, pin in pin_names.items():
        sw = digitalio.DigitalInOut(pin)
        sw.switch_to_input(pull=digitalio.Pull.UP)
        switches[name] = sw

    def read_buttons():
        return {name: not sw.value for name, sw in switches.items()}

    gd.read_buttons = read_buttons
    return gd


def _hallowing():
    gd = GameDisplay()
    gd.screen = board.DISPLAY
    gd.read_buttons = _stub_buttons
    try:
        import neopixel

        gd.neopixel = neopixel.NeoPixel(board.NEOPIXEL, 1)
    except (ImportError, AttributeError):
        gd.neopixel = None
    return gd


def _generic():
    gd = GameDisplay()
    gd.screen = board.DISPLAY
    gd.read_buttons = _stub_buttons
    gd.neopixel = None
    return gd


def _stub_buttons():
    return dict(_NO_BUTTONS)
