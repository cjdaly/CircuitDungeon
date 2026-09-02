# Chapter 7 — Deploying to the PicoSystem

How to get `Chapter_7/game/` onto a Pimoroni PicoSystem and run it. Board
notes are in `Chapter_6/doc/SYSTEMS.md` (§ *Pimoroni PicoSystem*); this doc is
the Ch7-specific procedure. First target: the `cd-89o.8` smoke test.

## What runs on the device

The **contents of `Chapter_7/game/`** are copied to the root of the `CIRCUITPY`
drive (not into a `game/` subdir — `util.py` loads tiles from `/tiles/`):

```
CIRCUITPY/
  boot.py                       # turns auto-reload OFF (see "Deploy" below)
  main.py  engine.py  modes.py  input.py  world.py  ai.py  hardware.py
  util.py  level_loader.py
  tiles/  terrain.bmp creatures.bmp heroes.bmp objects.bmp
          (palette.* / tiles.json copied too; not imported yet)
  lib/  adafruit_display_text/  adafruit_imageload/
```

`doc/`, `tools/`, and `tests/` stay on the desktop.

**No `neopixel` on the PicoSystem.** It has no NeoPixel — its status LED is a
plain RGB LED on 3 PWM pins (`board.LED_R`/`LED_G`/`LED_B` = GPIO 14/13/15),
and CircuitPython defines no `board.NEOPIXEL` for this board.
`hardware._picosystem()` sets `neopixel = None` and never imports the lib, so
`neopixel.mpy` in `lib/` is an unused leftover — harmless to keep, fine to
delete. `deploy.sh` only checks for `adafruit_display_text` and
`adafruit_imageload`.

## Current device state (2026-08-30)

The unit already runs **Chapter 6** with its libs installed, so device setup
is **done** for the first Ch7 test — you just swap the code (see *Deploy*).

Known-good baseline (`downloads/`, gitignored):

| | version |
|---|---|
| CircuitPython (`pimoroni_picosystem`) | **10.2.1** |
| bundle | `adafruit-circuitpython-bundle-10.x-mpy-20260820` |
| `adafruit_display_text` | 5.0.5 |
| `adafruit_imageload` | 1.24.8 |
| `neopixel` | 6.4.2 (unused on the PicoSystem path) |

CP 10.x has every displayio API Ch7 uses (`TileGrid.hidden`,
`Group(x=,y=)`, `Label.anchor_point`/`anchored_position` — all 7.x-era), and
Ch6 running proves `displayio` + `adafruit_imageload` + `adafruit_display_text`
coexist fine with the board's frozen `stage`/`ugame`. So the smoke test is
really just: does the Ch7 code run, and what's the RAM headroom.

## One-time device setup *(already done — reference only)*

1. **CircuitPython.** `downloads/adafruit-circuitpython-pimoroni_picosystem-en_US-10.2.1.uf2`,
   or a fresh build from <https://circuitpython.org/board/pimoroni_picosystem/>.
   Bootloader entry: **hold `X` while pressing the power button** → an
   `RPI-RP2` drive mounts (screen stays blank — normal). Drop the `.uf2` on
   it. Connect straight to the Mac, not through a hub.
2. **Bundle libraries** into `CIRCUITPY/lib/` — `circup` matches the bundle
   version automatically:
   ```
   pip install circup
   circup --path /Volumes/CIRCUITPY install adafruit_display_text adafruit_imageload
   ```
   (or hand-copy those two folders from the matching bundle's `lib/`.
   `neopixel.mpy` is not used on this board — see above.)

## Why deploying isn't just "copy the files"

CircuitPython **soft-reboots on every filesystem write**. `rsync` writes a
dozen files, so the board reboots partway and tries to run a half-copied
codebase (`ImportError`, a truncated module, …). And on macOS the FAT write
cache isn't reliably flushed by `sync` alone (worse since the Sonoma
small-drive bug) — resetting before it flushes can corrupt the drive.

Two guards, both handled for you:

- **`game/boot.py`** turns auto-reload **off**. `boot.py` runs once at hard
  reset, before the USB workflow — so once it's on the device, no file write
  ever reboots the board. You deploy the whole project, *then* reset it.
- **`deploy.sh` ejects the drive** at the end, forcing the flush. Re-mount by
  resetting / power-cycling — the board then runs the new code.

## Deploy

```
Chapter_7/tools/deploy.sh                     # -> /Volumes/CIRCUITPY, ejects when done
Chapter_7/tools/deploy.sh --no-eject          # skip the eject
Chapter_7/tools/deploy.sh /Volumes/CIRCUITPY  # explicit target
```

`rsync -rt --delete` of `game/`'s contents to the drive root. `--delete`
**removes the Chapter 6 files** (`levels/`, `explosions.bmp`, …) not in Ch7's
`game/` — that's the Ch6→Ch7 swap. Anchored excludes protect `lib/`,
`boot_out.txt`, `settings.toml`, and the macOS FAT dotfiles.

**First Ch7 deploy** (before `boot.py` is on the device, auto-reload is still
on): connect serial first and `Ctrl-C` to the REPL — that pauses the running
code *and* auto-reload — then run `deploy.sh` from another shell.

**Every deploy after:** `deploy.sh` → **reset the board** (the power button, or
`Ctrl-C` then `Ctrl-D` in serial) → it re-mounts `CIRCUITPY` and runs the new
code.

## Watch it boot

```
screen /dev/tty.usbmodem*        # find the exact name with: ls /dev/tty.usbmodem*
```

- `Ctrl-C` → REPL, `Ctrl-D` → restart · Detach: `Ctrl-A` then `d`

`boot.py` then `main.py` print:

```
boot.py: autoreload OFF — deploy fully, then reset to run
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
| wait chord | `Down+B` together → the `chord_stats` `b+down` row's `fired` climbs (`Left+Right` / `Up+Down` were dropped after the first run — see below) |

## First smoke test — 2026-08-30

Passed. The Option-G scene renders, the camera scrolls and keeps the hero
centred, and both overlay modes work.

```
Ch7 boot   board=pimoroni_picosystem  free=146896
Ch7 ready  free=99616  X+Y=diag  A+B=menu
```

**RAM:** ~144 KB free after imports; `engine.Game(...)` construction costs
~47 KB (3 tile sheets, displayio groups, the 13×13 grid, actor sprites, the
mode stack) leaving **~97 KB free heap**. Comfortable for now — the real
64×64 level adds only ~3 KB (the terrain TileGrid stays viewport-sized), FOV
+ a full monster/item roster maybe ~15 KB more. `cd-dsc.6` does the proper
RAM pass; an easy win noted there is swapping the `adafruit_display_text`
labels for the lighter `bitmap_label`.

| | |
|---|---|
| ![Ch7 play screen: the 13×13 map viewport with the hero, wall border and interior cross; dark status/message bands top and bottom.](../pics/test1/smoke-play-viewport.jpg) | ![Same, camera scrolled — a monster sprite near the room edge.](../pics/test1/smoke-play-scrolled.jpg) |
| ![The DIAG input page: the `chord_stats` table, `held:` line, and the newest-last input trace showing `press x / press y / chord diag / release x / release y`.](../pics/test1/smoke-diag-input.jpg) | ![The MENU stub overlay — "MENU / (CANCEL / chord to exit)".](../pics/test1/smoke-menu-stub.jpg) |

**Wait-chord data** (`cd-e3p.15`) — after mashing each binding:

![DIAG chord_stats after the wait-chord test: b+down fired 4 / missed 0; x+y 2/0; a+b 2/0; up+down 0/1; left+right 0/1.](../pics/test1/smoke-diag-chord-stats.jpg)

| chord | fired | missed |
|---|---|---|
| **Down + B** | 4 | 0 |
| Up + Down | 0 | 1 |
| Left + Right | 0 | 1 |

`Down + B` lands every time; the opposing-d-pad squeezes never formed a chord
and each logged a miss. Confirms Chris's hunch — narrow to `Down + B` in
`cd-e3p.15`.

## Second playtest — 2026-09-01

First on-device run of the procedural build (generator + `world_from_level`,
combat, message log, SYSTEM diag, stair descent). Deployed the post-`4e5c6d3`
tree.

**Boots, renders, scrolls.** The 64×64 generated level draws correctly — dirt
corridors, flagstone rooms, wall border, the hero on the up-stairs — and the
camera scrolls the full level with the hero clamped to the viewport centre.
Both diag pages work; `A` flips INPUT ⇄ SYSTEM.

**One crash — fixed.** The first monster-on-hero hit threw:

```
File "world.py", line 253, in resolve_attack
AttributeError: 'str' object has no attribute 'capitalize'
```

CircuitPython's `str` has no `.capitalize()` / `.title()` (only
`.upper()`/`.lower()`), and CPython does, so the desktop suite never caught it
(`cd-icp`). Fixed with `world._cap()` + a source-scan regression test
(`test_combat.CircuitPythonStr`). **Not yet re-verified on hardware** — next
deploy.

**RAM — margin has shrunk, watch it.** SYSTEM diag mid-game (depth 1, 4
actors, after opening/closing diag a few times):

| | |
|---|---|
| free | **47 KB** |
| low-water (`free_low`) | **42 KB** |
| used / heap | 111 KB / 159 KB |
| `gc.collect` | 16 ms (n=32) |
| flash free | 15010 KB / 15328 KB |
| env | CircuitPython 10.2.1 · rp2040 |

Still clear of the ~20 KB danger line, but the 2026-08-30 smoke test had
~97 KB free right after construction — the generator (the transient
`_dist_grid` bytearray + int BFS queue), combat, the log ring and the diag
labels have eaten ~50 KB. `cd-dsc.6` (RAM pass) should now be treated as
due, not optional — `bitmap_label` swap + a look at whether the BFS queue can
be capped.

**`frame max` reads ~7.8 s** on the SYSTEM page — almost certainly the
first-frame cost (initial full terrain paint / first `gc.collect`), not a
steady-state stall; `frame` (current) sits at ~30 ms. Worth confirming on the
next run whether descent triggers a second multi-second hitch (regenerate +
repaint). The frame line ghosts in the photo because it repaints ~7×/s over a
slow LCD — not a rendering bug.

**Stair descent:** stepping onto the depth-1 up-stairs correctly shows
*"The way out has sealed behind you."* Down-stairs descent not exercised this
run (didn't reach them).

![PicoSystem running the generated level: status band "HP 20/20  Depth 1  Turn 2  Gold 0", the 13×13 viewport showing flagstone room and dirt corridors, hero centred, a monster two tiles south.](../pics/test2/t2-play-generated.jpg)
![Camera scrolled across the 64×64 level — the hero off-centre near unexplored dark tiles, message band still reading "The way out has sealed behind you."](../pics/test2/t2-play-scrolled.jpg)

![SYSTEM diag page: ram free 47k / low 42k, ram used 111k / heap 159k, gc.collect 16 ms (n=32), flash free 15010k / 15328k, cpy 10.2.1 rp2040, frame 30 ms max 7783 ms, board pimoroni_picosystem, actors 4 turn 2 depth 1.](../pics/test2/t2-diag-system.jpg)
![INPUT diag page: chord table (x+y, b+down, a+b) with fire/miss/spread columns, "held: -", and the newest-last input trace of press/release/single a events.](../pics/test2/t2-diag-input.jpg)

![The message band reads "The way out has sealed behind you." after the hero stepped onto the depth-1 up-stairs; status band "HP 20/20  Depth 1  Turn 31  Gold 0".](../pics/test2/t2-stairs-sealed.jpg)
![The on-screen traceback: modes.py:91 handle → modes.py:272 tick → world.py:224 resolve_turn → modes.py:285 _monster_turn → ai.py:54 take_turn → ai.py:90 _step_toward → world.py:253 resolve_attack, ending "AttributeError: 'str' object has no attribute 'capitalize'".](../pics/test2/t2-hit-crash.jpg)

## Troubleshooting

- **Blank screen, no serial** — likely still in the UF2 bootloader (check for
  `RPI-RP2` in `ls /Volumes/`), or a hub problem. Reconnect directly.
- **`ImportError` / traceback right after "Ch7 boot"**, or the board rebooted
  mid-`deploy.sh` — a partial copy. Re-run `deploy.sh` (it ejects), then reset.
  If `CIRCUITPY` looks corrupt (missing files, weird names), reformat it from
  the CircuitPython REPL: `import storage; storage.erase_filesystem()` and
  re-deploy (libs too).
- **`ImportError: no module named 'adafruit_...'`** — lib missing or wrong
  bundle major version. `circup --path /Volumes/CIRCUITPY install …`.
- **Traceback on screen** — read it over serial; `Ctrl-C` then
  `import gc; gc.mem_free()` to check for OOM.
- **Buttons do nothing** — board misdetected (see the banner) or a frozen
  `stage`/`ugame` conflict; check `import hardware; hardware.detect().read_buttons()`
  in the REPL while pressing a button.
- **Want live-reload back** (single-file tweaking) — delete `boot.py` from
  `CIRCUITPY`, or in the REPL: `import supervisor; supervisor.runtime.autoreload = True`.
