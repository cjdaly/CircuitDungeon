# CircuitPython test systems

Physical boards on hand for testing `Chapter_6/game/`. Listed in the order
they'll be brought up — see `doc/PLAN.md` Phase 4.

When connecting the device to a Mac via USB we can use the `screen` command
to get into the Pyton REPL.
- PyBadge example: `screen /dev/tty.usbmodem313401`
  - if program running use `Ctrl-c` to exit to REPL
  - use `Ctrl-d` to restart program
  - try `help()` and `help('modules')` in REPL
  - more info: https://learn.adafruit.com/welcome-to-circuitpython/the-repl
  - to detach from screen use `Ctrl-a`, then `d`

## Libraries (all boards)

`game/`'s imports (`adafruit_imageload` in `util.py`, `adafruit_display_text.label` in
`engine.py`, `neopixel` in `hardware.py`) need three folders/files dropped into
`/Volumes/CIRCUITPY/lib`:
- `adafruit_display_text/` (folder — provides `label`)
- `adafruit_imageload/` (folder)
- `neopixel.mpy`

Everything else `game/` imports (`board`, `displayio`, `terminalio`, `digitalio`,
`keypad`) is built into the CircuitPython firmware itself, not a bundle library —
nothing to copy for those.

To install: grab the [Adafruit CircuitPython
Bundle](https://circuitpython.org/libraries) build that matches the *major*
version of CircuitPython installed on the board (check with `import sys;
print(sys.implementation.version)` in the REPL, or read the first line CIRCUITPY
prints as a comment in `boot_out.txt`), then copy those three items from the
bundle's `lib/` into `CIRCUITPY/lib`. `circup` (`pip install circup`, then
`circup install adafruit_display_text adafruit_imageload neopixel`) does the same
lookup/copy automatically and is less error-prone once it's set up.

This library set is identical across every board below — `hardware.py`'s
per-board branches only change which *built-in* modules they import
(`keypad` for PyBadge-family, `digitalio` for Clue), not the bundle libraries.

## Adafruit PyBadge

The primary target. 160×128 matches the `TERRAIN_TILE=16` grid math the
engine was built against (10×8 tiles), and its d-pad is the closest match to
Chapter 5/PyBadge's button layout, so `hardware.py`'s `_pybadge()` path needs
the least new code.

### docs
- https://circuitpython.org/board/pybadge/
- https://www.adafruit.com/product/4200
- https://learn.adafruit.com/adafruit-pybadge

### specs
- microprocessor: ATSAMD51J19, Cortex-M4F @ 120MHz
- ram: 192KB
- flash: 512KB internal + 2MB SPI flash
- screen: 1.8" color TFT, 160×128 px, dimmable backlight
- buttons: 8 — d-pad (up/down/left/right), A, B, Select, Start
- sensors: triple-axis accelerometer, light sensor
- audio: buzzer speaker; mono Class-D driver (4-8Ω, up to 2W)
- neopixels: 5
- connectors: 2× Feather headers, 3× STEMMA (2×3-pin ADC/PWM, 1×4-pin I2C), micro USB, LiPoly + charging

### setup

- shows up as `/dev/tty.usbmodem313401` on Mac
- to enter bootloader (for CircuitPython version update):
  - double-click RESET button on back of board near USB connector
  - look for mounted drive `/Volumes/BADGEBOOT`
- libraries to load: see [Libraries (all boards)](#libraries-all-boards) above

## Adafruit PyBadge LC

Cost-reduced PyBadge variant — same screen and button layout, so the same
`_pybadge()` code path should work unmodified, but with less headroom and no
accelerometer.

### docs
- https://www.adafruit.com/product/3939
- https://learn.adafruit.com/adafruit-pybadge

### specs
- microprocessor: ATSAMD51J19, Cortex-M4F @ 120MHz
- ram: 192KB
- flash: 512KB internal + 2MB SPI flash
- screen: 1.8" color TFT, 160×128 px, dimmable backlight
- buttons: 8 — d-pad, A, B, Select, Start (same layout as PyBadge)
- sensors: none (no accelerometer, no light sensor)
- audio: buzzer mini-speaker only (no external speaker header)
- neopixels: 1 (vs. 5 on the full PyBadge)
- differences from PyBadge: no Feather headers, no STEMMA/JST connectors, no accelerometer

## Adafruit EdgeBadge

Same core hardware as PyBadge (SAMD51, 192KB RAM, 512KB flash) plus a PDM
microphone for on-device TensorFlow Lite ML — not relevant to this game, but
the display/button/CircuitPython path is identical to PyBadge, so it should
run `game/` with zero changes once PyBadge works.

### docs
- https://circuitpython.org/board/edgebadge/
- https://www.adafruit.com/product/4400

### specs
- microprocessor: ATSAMD51, Cortex-M4F @ 120MHz
- ram: 192KB
- flash: 512KB internal + 2MB QSPI flash
- screen: same 1.8" 160×128 TFT as PyBadge
- buttons: same 8-button layout as PyBadge (d-pad, A, B, Select, Start)
- extra: PDM microphone (front-facing, for ML/speech recognition — unused here)
- form factor: credit-card sized, Feather-compatible

## Adafruit PyGamer

Same SAMD51/192KB/160×128 core as PyBadge, but the d-pad is replaced by an
analog thumbstick and there are only 4 face buttons (no Select/Start).
`hardware.py` will need a PyGamer-specific `read_buttons()` that thresholds
the thumbstick's X/Y ADC values into `up`/`down`/`left`/`right` rather than
reading a `ShiftRegisterKeys` d-pad directly.

### docs
- https://circuitpython.org/board/pygamer/
- https://www.adafruit.com/product/4242
- https://learn.adafruit.com/adafruit-pygamer

### specs
- microprocessor: ATSAMD51J19, Cortex-M4F @ 120MHz
- ram: 192KB
- flash: 512KB internal + 8MB QSPI flash
- screen: 1.8" color TFT, 160×128 px, dimmable backlight
- controls: analog thumbstick (X/Y) + 4 game buttons (no d-pad, no Select/Start)
- sensors: triple-axis accelerometer, light sensor
- audio: stereo headphone jack; mono Class-D speaker driver (4-8Ω, up to 2W)
- neopixels: 5
- connectors: Feather headers, 3× STEMMA, micro SD slot, micro USB, LiPoly

## Adafruit Clue

Different screen size (240×240, not 160×128) and only two buttons — no d-pad
at all. Exercises the engine's resolution-independence (`cols = width //
tile_w`) and needs an input scheme beyond directional buttons; `hardware.py`
already stubs `_clue()` reading only A/B, so movement will need a rethink
(e.g. touchscreen-free control via the sensor suite, or accept it's a
non-movement demo on this board for now).

### docs
- https://circuitpython.org/board/clue_nrf52840_express/
- https://www.adafruit.com/product/4500
- https://learn.adafruit.com/adafruit-clue

### specs
- microprocessor: Nordic nRF52840, Cortex-M4F @ 64MHz
- ram: 256KB
- flash: 1MB internal + 2MB internal (datalogging)
- screen: 1.3" color IPS TFT, 240×240 px
- buttons: 2 — A, B (plus reset; no d-pad)
- sensors: accelerometer/gyro (LSM6DS3TR), magnetometer (LIS3MDL), proximity/light/color/gesture (APDS9960), PDM mic, humidity (SHT), temp/pressure (BMP280)
- audio: buzzer/speaker
- neopixel: 1
- connectivity: Bluetooth LE (nRF52840), STEMMA QT/Qwiic I2C

## Pimoroni PicoSystem

Different SoC family entirely (RP2040, not SAMD51) and a real D-pad + 4 face
buttons wired directly (no shift register), so `hardware.py`'s
`detect()` won't route to it via any existing `hasattr(board, ...)` branch —
it needs its own `_picosystem()` case and board-id check. 240×240 matches
Clue's resolution math, not PyBadge's. The CircuitPython build for this board
also ships frozen `stage`/`ugame` modules aimed at game dev directly on this
hardware; worth checking whether they conflict with or duplicate
`displayio`/`adafruit_imageload` before assuming a drop-in port. Second in
the Phase 4 order (see `doc/PLAN.md`) — right after PyBadge, ahead of the
rest of the PyBadge family.

**Bootloader mode**: the official sequence is "hold `X` and toggle the
power." The power control is labeled "Power Toggle" on the packaging, but
it's a clicky physical button, not a slide switch — press and release it
(while holding `X`) rather than looking for something to flip. Also:
bootloader mode runs the RP2040's tiny UF2 bootloader, not CircuitPython —
**the screen stays blank/off**, which looks identical to "didn't start up"
but usually isn't a failure. The real signal is whether an `RPI-RP2` drive
mounts (check `ls /Volumes/` in Terminal, not just Finder). Confirmed on
this unit: the actual blocker was the USB hub — RP2040 BOOTSEL/DFU
enumeration is finicky through hubs (power-delivery/timing) — connecting
straight to the Mac's USB port fixed it.

### docs
- https://circuitpython.org/board/pimoroni_picosystem/
- https://shop.pimoroni.com/products/picosystem
- https://learn.pimoroni.com/article/getting-started-with-picosystem
- https://github.com/pimoroni/picosystem

### specs
- microprocessor: RP2040, dual-core Cortex-M0+ @ up to 133MHz
- ram: 264KB SRAM
- flash: 16MB QSPI
- screen: 1.54" color IPS LCD, 240×240 px
- buttons: D-pad + A/B/X/Y face buttons, power button (bootloader entry: hold X while powering on → mounts as `RPI-RP2`)
- sensors: none
- audio: piezo buzzer/speaker
- neopixels: 1 RGB LED (status indicator, not addressable strip like PyBadge's)
- connectors: USB-C (charge + program), 525mAh LiPo (~6h on-time), debug pins under the case
- case: CNC-milled aluminium, wrist strap included

## PewPew M4 (Radomir Dopieralski)

Same SAMD51 chip family as PyBadge/PyGamer/EdgeBadge, but a different, smaller
board (`160×128` display, 7 buttons in a non-d-pad layout, AAA-battery
powered) built for the `pewpew` teaching library rather than general
`displayio` apps. Buttons aren't behind a `BUTTON_CLOCK` shift register like
PyBadge's, so it likely needs its own `hardware.py` branch too — exact button
pin/matrix layout not yet confirmed here, check the schematic before wiring
`_pewpew()`. Not in the current Phase 4 order; same "candidate, not yet
scoped in" status as PicoSystem above.

### docs
- https://circuitpython.org/board/pewpew_m4/
- https://www.makerfabs.com/circuitpython-pewpew-m4.html
- https://pewpew.readthedocs.io/en/latest/pewpew-m4/overview.html
- https://pewpew.readthedocs.io/en/latest/pewpew-m4/hardware.html
- schematic: https://github.com/pypewpew/pewpew-m4-v8/blob/master/pewpew-m4-v8-schematic.pdf

### specs
- microprocessor: SAMD51, Cortex-M4 (same family as PyBadge; exact clock/variant not confirmed — check schematic or on-device `sys.implementation`)
- ram / flash: not confirmed from docs (likely close to PyBadge's 192KB/512KB given the shared chip family — verify on-device before relying on this)
- screen: 160×128 color TFT (same panel as PyBadge)
- buttons: 7 total, non-d-pad layout (exact mapping not yet documented here)
- sensors: none noted
- audio: 7mm buzzer
- neopixels: none noted
- connectors: micro USB; powered by 2×AAA batteries (sold separately)

## LilyGo T-Deck (Plus)

The odd one out: ESP32-S3 (not SAMD51/RP2040/nRF52), a 320×240 screen (not
matching any existing `TERRAIN_TILE` grid math without recomputing), and no
d-pad or face buttons at all — input is a mini QWERTY keyboard plus a
trackball. `hardware.py`'s `detect()` has no branch that would ever match it
(no `BUTTON_CLOCK`, no `BUTTON_A`, no plain `NEOPIXEL`), so it'll need its own
board-id check. The keyboard is the plan for input here — map WASD (or
arrows, if the keyboard has them) + two more keys to `up`/`down`/`left`/
`right`/`a`/`b` in a `_tdeck()` `read_buttons()`, same shape as every other
board's dict. Not literal buttons, but a real approximation, not a dead end.
Later work, though — after the boards in `doc/PLAN.md` Phase 4's current
order (PyBadge, PicoSystem, PyBadge LC, EdgeBadge, PyGamer, Clue).

Two device variants exist: the original T-Deck and the newer T-Deck Plus
(adds GPS and a larger 2000mAh built-in battery). The CircuitPython
`lilygo_tdeck` board build's page notes it now covers the Plus variant too,
so the same download should work for either.

### docs
- https://circuitpython.org/board/lilygo_tdeck/
- https://lilygo.cc/products/t-deck
- https://lilygo.cc/products/t-deck-plus-1

### specs
- microprocessor: ESP32-S3FN16R8, dual-core LX7
- ram: 8MB PSRAM
- flash: 16MB
- screen: 2.8" ST7789 SPI IPS LCD, 320×240 px
- controls: mini QWERTY keyboard + trackball (no d-pad, no A/B/X/Y face buttons)
- sensors: none beyond battery-voltage ADC (IO04)
- audio: onboard microphone + speaker
- connectivity: Wi-Fi + Bluetooth 5 LE, optional SX1262 LoRa (433/868/915MHz, +22dBm); T-Deck Plus adds GPS
- connectors: USB-C; battery — T-Deck Plus has a built-in 2000mAh cell (original T-Deck's battery situation not confirmed here)

