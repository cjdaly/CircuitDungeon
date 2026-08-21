# CircuitPython test systems

Physical boards on hand for testing `Chapter_6/game/`. Listed in the order
they'll be brought up — see `doc/PLAN.md` Phase 4.

## PyBadge

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

## PyBadge LC

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

## EdgeBadge

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

## PyGamer

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

## Clue

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
