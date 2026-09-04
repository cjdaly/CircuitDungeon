# Chapter 8 — Waveshare RP2350-Touch-LCD-1.28 hardware notes

Findings from probing the board live over the USB serial REPL (`screen` /
raw-REPL scripting), 2026-09-04. See `doc/VISION.md` for the chapter pitch and
`doc/DEPLOY.md` for how to get code onto the device.

## Identity

```
Adafruit CircuitPython 10.2.1 on 2026-05-13; Waveshare RP2350-TOUCH-LCD-1.28 with rp2350
Board ID: waveshare_rp2350_touch_lcd_1_28
```

- MCU: RP2350, `microcontroller.cpu.frequency` = 150,000,000 Hz
- RAM: `gc.mem_free()` = **433,280 bytes** free right after boot with just
  `print("Hello World!")` in `code.py` — a much bigger budget than the
  PicoSystem's RP2040 (Chapter 7 lives under ~150 KB total heap). Chapter 8
  doesn't need the aggressive RAM discipline Ch7 required, but keep the habit
  (`gc.collect()`, avoid per-frame label churn) since it's cheap insurance.
- No `lib/` contents shipped on the device out of the box (empty `lib/`
  directory) — everything below had to be installed by hand.
- `downloads/adafruit-circuitpython-waveshare_rp2350_touch_lcd_1_28-en_US-10.2.1.uf2`
  is the matching firmware image (already flashed on the unit in hand).

## Board pins (`dir(board)`)

```
A0 A1 A2 A3 BAT_ADC
GP0..GP28 (plus GP26_A0/GP27_A1/GP28_A2 analog aliases)
IMU_INT1 IMU_INT2 IMU_SCL IMU_SDA
LCD_BL LCD_CLK LCD_CS LCD_DC LCD_DIN LCD_RST
```

No `board.SPI()` / `board.I2C()` default-bus helpers are defined — every bus
must be constructed by hand from the named pins above. No touch-specific pin
is named (no `TP_INT` / `TP_RST` alias); see **Touch controller** below.

## Display — GC9A01A, 240×240 round IPS, SPI

Driver: `adafruit_gc9a01a` (in the Adafruit bundle). Bus is a normal
`fourwire.FourWire` built from a hand-rolled `busio.SPI` (no `board.SPI()`):

```python
import board, busio, displayio, digitalio
from fourwire import FourWire
from adafruit_gc9a01a import GC9A01A

displayio.release_displays()   # MUST come first -- see note below

bl = digitalio.DigitalInOut(board.LCD_BL)
bl.switch_to_output(value=True)          # backlight on

spi = busio.SPI(clock=board.LCD_CLK, MOSI=board.LCD_DIN)   # write-only, no MISO
bus = FourWire(spi, command=board.LCD_DC, chip_select=board.LCD_CS,
               reset=board.LCD_RST, baudrate=24_000_000)
display = GC9A01A(bus, width=240, height=240)
```

**`release_displays()` must run first, before touching `LCD_CLK`/`LCD_DIN` at
all.** CircuitPython auto-configures this board's built-in status display
(for its own boot splash/error screens) on every hard reset, which holds
those SPI pins until released — building the `busio.SPI` bus first throws
`ValueError: LCD_CLK in use` on a truly fresh boot (only doesn't reproduce
mid-REPL-session once something has already released it once).

Verified live: initializes cleanly, fills solid color correctly. **The panel
is physically round** — the four corners of the 240×240 frame buffer are
outside the visible glass. Keep HUD text/graphics inset (roughly a 20–30px
margin, more in the corners) or they'll be clipped by the bezel.

## IMU — QMI8658 6-DoF accel+gyro, I2C

- Address **0x6B** on `board.IMU_SCL` / `board.IMU_SDA`.
- No CircuitPython driver in the Adafruit bundle. Vendored
  `Chapter_8/vendor/qmi8658c.py` (MIT, from
  [tkomde/CircuitPython_QMI8658C](https://github.com/tkomde/CircuitPython_QMI8658C))
  unmodified — it only needs `adafruit_bus_device` (frozen into this build's
  firmware already) and `adafruit_register` (bundle, copied to `lib/`).
- Confirmed live, board resting flat:

  ```python
  i2c = busio.I2C(board.IMU_SCL, board.IMU_SDA)
  imu = qmi8658c.QMI8658C(i2c)
  imu.acceleration   # (0.61, 0.29, -10.25)  m/s^2 -- ~1g on Z, board face-down/up
  imu.gyro           # (-0.03, -0.04, 0.005) rad/s -- ~0 at rest
  imu.temperature    # 25.9 C
  ```

## Touch controller — CST816, I2C, **shares the IMU's bus**

- Address **0x15**, on the *same* `IMU_SCL`/`IMU_SDA` pins as the QMI8658 —
  there is only one exposed I2C bus on this board.
- Driver: `adafruit_cst8xx.Adafruit_CST8XX` (Adafruit bundle) — its chip-ID
  table already includes CST816S/T/D, matching the Waveshare wiki's chip.
- **Quirk found by probing, not documented anywhere we could reach:** the
  CST816 duty-cycles into a low-power state and stops ACKing on I2C roughly
  half the time, *even at rest with no finger on the glass* — confirmed with
  a tight `i2c.scan()` loop:

  ```
  ['0x15', '0x6b']
  ['0x6b']
  ['0x15', '0x6b']
  ['0x6b']
  ...
  ```

  Right after a hard/soft reset the chip answers reliably for its first
  ~0.5s, then settles into that flicker. `adafruit_cst8xx`'s constructor
  does an unconditional register read at `__init__` time — if it lands on a
  "quiet" tick you get `ValueError: No I2C device at address: 0x15`, even
  though the chip is present and fine. Same risk on every `.touched` /
  `.touches` poll.
- No hardware interrupt pin is exposed for it (`irq_pin=None` is the only
  option from `board`'s pin list), so we can't gate reads on a real touch-
  ready signal. `Chapter_8/game/touch.py`'s `SafeTouch` connects **lazily**
  instead of blocking at startup (a fixed retry budget at construction time
  wasn't dependable — seen quiet for 3+ seconds straight) and swallows a
  transient `OSError`/`ValueError` on every poll as "no touch this tick".
  See `cd-bp3.3`.
- **Worse than transient: it can wedge the whole shared bus.** Once, after
  repeated quick resets while poking at it from the REPL, `SDA` came up
  stuck **permanently low** — `digitalio.DigitalInOut(board.IMU_SDA)` with
  `Pull.UP` still read `False`, and the standard software recovery (manually
  toggling `SCL` 16 times to walk a wedged slave out of a mid-byte state,
  then a STOP condition) did **not** clear it. That means the CST816's own
  internal state was wedged, not just the RP2350's I2C peripheral —
  `microcontroller.reset()` only resets the RP2350, not the touch chip's
  power rail, so software resets couldn't recover it. Only a **full USB
  unplug/replug** (power-cycling the touch chip too) cleared it, after which
  the bus, the IMU, and touch all came back up fine. Symptom on-device: the
  screen goes black because `main.py` now throws `RuntimeError: No pull up
  found on SDA or SCL; check your wiring` out of `busio.I2C(...)` before it
  draws anything. **If that happens: unplug and replug, don't just reset.**
- The Waveshare wiki page (`waveshare.com/wiki/...`) 403s to automated
  fetches; a mirror (spotpear.com) confirms the chip names but not pin
  numbers or this sleep behavior — this section is the only write-up of it.

## Libraries needed on `CIRCUITPY/lib/`

None of these are frozen into the firmware except `adafruit_bus_device` and
`adafruit_pixelbuf` (checked via `help('modules')`). Everything else here
came from `downloads/adafruit-circuitpython-bundle-10.x-mpy-20260820/lib/`:

| library | why |
|---|---|
| `adafruit_gc9a01a.mpy` | display driver |
| `adafruit_cst8xx.mpy` | touch controller driver |
| `adafruit_register/` | `RWBits` / `Struct` — dependency of vendored `qmi8658c.py` |
| `adafruit_display_text/`, `adafruit_ticks.mpy` | `bitmap_label.Label` for the HUD text (same choice Ch7 made, `cd-yl4`) |
| `qmi8658c.py` | vendored (see above) — not in the Adafruit bundle |

`help('modules')` frozen-in built-ins relevant to this chapter: `displayio`,
`busdisplay`, `fourwire`, `i2cdisplaybus`, `terminalio`, `fontio`,
`lvfontio`, `tilepalettemapper`, `vectorio`, `touchio` (capacitive-*pin*
touch, not this I2C touch controller — not used here), `keypad`,
`rotaryio`, `ulab` (`numpy`/`scipy` — available if gesture math ever needs
it, unused for now), `qrio`.
