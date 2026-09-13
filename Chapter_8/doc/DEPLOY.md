# Chapter 8 — Deploying to the Waveshare RP2350-Touch-LCD-1.28

How to get `Chapter_8/game/` onto the board and run it. Board notes (chips,
pins, the touch controller's sleep quirk) are in `doc/HARDWARE.md`; this doc
is the deploy procedure. Mirrors `Chapter_7/tools/deploy.sh` — see that
chapter's `doc/DEPLOY.md` for the underlying "why not just cp" rationale.

## What runs on the device

The **contents of `Chapter_8/game/`** are copied to the root of the
`CIRCUITPY` drive:

```
CIRCUITPY/
  boot.py                       # turns auto-reload OFF
  main.py  hardware.py  touch.py  imu.py
  lib/  adafruit_cst8xx.mpy  adafruit_gc9a01a.mpy  adafruit_ticks.mpy
        adafruit_register/  adafruit_display_text/  qmi8658c.py
```

`doc/`, `tools/`, and `vendor/` stay on the desktop.

## One-time device setup

1. **CircuitPython.** `downloads/adafruit-circuitpython-waveshare_rp2350_touch_lcd_1_28-en_US-10.2.1.uf2`,
   or a fresh build from <https://circuitpython.org/board/waveshare_rp2350_touch_lcd_1_28/>.
   Hold BOOT while plugging in (or double-tap RESET) to mount the `RP2350`
   bootloader drive, then drop the `.uf2` on it.
2. **Bundle libraries** into `CIRCUITPY/lib/`:
   ```
   pip install circup
   circup --path /Volumes/CIRCUITPY install \
       adafruit_cst8xx adafruit_gc9a01a adafruit_register \
       adafruit_display_text adafruit_ticks
   ```
   (or hand-copy those from the matching bundle's `lib/` — see
   `downloads/adafruit-circuitpython-bundle-10.x-mpy-20260820/`.)
3. **Vendored QMI8658C driver** — not in the Adafruit bundle, `circup` won't
   find it:
   ```
   cp Chapter_8/vendor/qmi8658c.py /Volumes/CIRCUITPY/lib/
   ```
4. **Device identity + battery info** (`cd-bp3.7`) — every unit gets a
   `DEVICE_ID` (Chris tells you which one when unboxing — `ws-1`, `ws-2`,
   or a name like `ws-monica`) and its battery's Adafruit product number +
   mAh capacity, written into `settings.toml`:
   ```
   Chapter_8/tools/set_device_config.py --id ws-monica \
       --battery-product adafruit-4236 --battery-mah 420
   ```
   `settings.toml` is CircuitPython's own config file (read on-device with
   `os.getenv()`) and is never touched by `deploy.sh` — set once, survives
   every later code deploy. Check what's currently set on a unit with
   `set_device_config.py --show`. Also record the unit in `../rpi-fleet`'s
   `INVENTORY.md`.

`Chapter_8/tools/deploy.sh` warns (but doesn't fail) if any of steps 2-3 are
missing from `lib/`.

## Deploy

```
Chapter_8/tools/deploy.sh                     # -> /Volumes/CIRCUITPY, ejects when done
Chapter_8/tools/deploy.sh --no-eject          # skip the eject
Chapter_8/tools/deploy.sh /Volumes/CIRCUITPY  # explicit target
```

**First deploy** (before `boot.py` is on the device, auto-reload is still
on): connect serial first and `Ctrl-C` to the REPL — that pauses the running
code *and* auto-reload — then run `deploy.sh` from another shell.

**Every deploy after:** `deploy.sh` → **reset the board** → it re-mounts
`CIRCUITPY` and runs the new code.

## Watch it boot

```
screen /dev/tty.usbmodem*        # find the exact name with: ls /dev/tty.usbmodem*
```

- `Ctrl-C` → REPL, `Ctrl-D` → restart · Detach: `Ctrl-A` then `d`

`main.py` prints on start:

```
Ch8 diag ready  free=NNNNNN
```

The screen then shows the combined diagnostic HUD (`doc/VISION.md` /
`cd-bp3.5`): a title/RAM line, live touch position + last tap/swipe gesture
(with a marker dot that follows your finger), and a live accel/gyro readout
with a derived tilt (pitch/roll) and shake flag.

## Running a prototype demo instead of the diagnostic HUD

`game/` also has a growing set of standalone `*_demo.py` prototypes (room
navigation, mixed sprite scales, ornament mode, ...) that are not `main.py`.
Use `deploy.sh --demo NAME` to try one on the device without touching the
checked-in `main.py`:

```
Chapter_8/tools/deploy.sh --demo room_nav_demo
```

This deploys `game/` as usual, then overwrites the **device's** `main.py`
with `game/room_nav_demo.py`. Reset to run it; re-run `deploy.sh` with no
`--demo` to put the diagnostic HUD back. Each demo has a walkthrough —
what to do, what to expect — in [`doc/demos/`](demos/README.md).

## Troubleshooting

Same categories as `Chapter_7/doc/DEPLOY.md` §Troubleshooting apply here
(blank screen / no serial, partial-copy ImportError, missing lib, reading a
traceback over serial, live-reload for single-file tweaking). One addition
specific to this board:

- **Touch position never updates** — `touch.py`'s `SafeTouch` connects lazily
  and swallows transient I2C errors, so this shouldn't crash anything; check
  `i2c.scan()` in the REPL a few times in a row — you should see `0x15`
  flicker in and out alongside the IMU's steady `0x6b`.
- **Screen goes black; `RuntimeError: No pull up found on SDA or SCL`** — the
  shared I2C bus is wedged (seen once, after repeated quick resets while
  poking the touch chip from the REPL). `microcontroller.reset()` does **not**
  clear this. **Unplug the USB cable and plug it back in** — a real power
  cycle, not just a reset — to power-cycle the touch chip too. See
  `doc/HARDWARE.md` "Touch controller".
