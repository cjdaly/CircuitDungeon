# Chapter 7 — Deploying to the PicoSystem

How to get `Chapter_7/game/` onto a Pimoroni PicoSystem and run it. Board
notes are in `Chapter_6/doc/SYSTEMS.md` (§ *Pimoroni PicoSystem*); this doc is
the Ch7-specific procedure. First target: the `cd-89o.8` smoke test.

## What runs on the device

The **contents of `Chapter_7/game/`** are copied to the root of the `CIRCUITPY`
drive (not into a `game/` subdir — `util.py` loads tiles from `/tiles/`):

```
CIRCUITPY/
  main.py  engine.py  modes.py  input.py  world.py  hardware.py
  util.py  level_loader.py
  tiles/  terrain.bmp creatures.bmp heroes.bmp objects.bmp
          (palette.* / tiles.json copied too; not imported yet)
  lib/  adafruit_display_text/  adafruit_imageload/  neopixel.mpy
```

`doc/`, `tools/`, and `tests/` stay on the desktop.

## One-time device setup

1. **CircuitPython.** Flash the PicoSystem build from
   <https://circuitpython.org/board/pimoroni_picosystem/>.
   Bootloader entry: **hold `X` while pressing the power button** → an
   `RPI-RP2` drive mounts (the screen stays blank — that's normal). Drop the
   `.uf2` on it. Connect straight to the Mac, not through a hub (RP2040
   BOOTSEL enumeration is flaky through hubs).
2. **Bundle libraries.** Check the CP version first (REPL:
   `import sys; sys.implementation.version`), grab the matching
   [Adafruit bundle](https://circuitpython.org/libraries), and copy into
   `CIRCUITPY/lib/`:
   - `adafruit_display_text/` (folder)
   - `adafruit_imageload/` (folder)
   - `neopixel.mpy` (not used on PicoSystem's code path, but harmless and
     keeps `hardware.py` importable if the board is misdetected)

   Or: `pip install circup && circup install adafruit_display_text adafruit_imageload neopixel`.
3. **Sanity-check the frozen modules.** The PicoSystem CP build ships frozen
   `stage` / `ugame`. In the REPL, confirm the standard display stack is
   intact and nothing auto-grabbed the screen:
   ```python
   import board, displayio
   board.DISPLAY            # -> a Display object, not None
   board.DISPLAY.root_group # fine if None
   import adafruit_imageload  # imports without error
   ```

## Deploy

```
Chapter_7/tools/deploy.sh            # to /Volumes/CIRCUITPY
Chapter_7/tools/deploy.sh /Volumes/CIRCUITPY   # explicit target
```

It rsyncs `game/`'s contents to the drive (dropping `__pycache__`/`*.pyc`) and
warns if any of the three libs are missing from `lib/`.

## Watch it boot

```
screen /dev/tty.usbmodem*        # find the exact name with: ls /dev/tty.usbmodem*
```

- `Ctrl-C` → REPL, `Ctrl-D` → restart `main.py`
- Detach: `Ctrl-A` then `d`

`main.py` prints a smoke-test banner:

```
Ch7 boot   board=pimoroni_picosystem  free=NNNNNN
Ch7 ready  free=NNNNNN  X+Y=diag  A+B=menu
```

Then the screen shows the Option-G layout: a status band on top, the 13×13
map viewport (hero centred, flagstone floor, a wall border + interior cross),
the icon-rail strip on the right, a message band on the bottom.

## What to check (cd-89o.8)

| | |
|---|---|
| boots, no traceback | banner prints twice; screen renders |
| RAM headroom | `free=` after "ready" — want comfortably > 20 KB |
| board detect | banner says `board=pimoroni_picosystem` (else `hardware.detect()` fell through to `_generic()` and buttons are dead) |
| camera | hold a d-pad direction → the map scrolls, hero stays centred |
| off-view culling | the second test monster (bottom-right of the room) only appears when you scroll to it |
| `X`+`Y` together | switches to the DIAG page — live `chord_stats` table, held buttons, input trace |
| `X`+`Y` again / `B` | back to the game |
| `A`+`B` together | the MENU stub label; `B` exits |
| wait chords | on the DIAG page, mash `Left+Right`, `Up+Down`, `Down+B` — compare `fired` / `missed` / `sprd` (feeds `cd-e3p.15`) |

## Troubleshooting

- **Blank screen, no serial** — likely still in the UF2 bootloader (check for
  `RPI-RP2` in `ls /Volumes/`), or a hub problem. Reconnect directly.
- **`ImportError: no module named 'adafruit_...'`** — lib missing or wrong
  bundle major version.
- **Traceback on screen** — read it over serial; `Ctrl-C` then
  `import gc; gc.mem_free()` to check for OOM.
- **Buttons do nothing** — board misdetected (see the banner) or a frozen
  `stage`/`ugame` conflict; check `import hardware; hardware.detect().read_buttons()`
  in the REPL while pressing a button.
