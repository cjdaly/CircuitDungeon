# Chapter 9 — Deploying to the Waveshare RP2350-Touch-LCD-1.28

How to get `Chapter_9/game/` onto the board and run it. It's the same board
as Chapter 8, so **the one-time device setup is identical** — CircuitPython
10.2.1 firmware, the `lib/` bundle libraries, the vendored `qmi8658c.py`, and
the per-unit `settings.toml` (`DEVICE_ID`, battery info). Follow steps 1–4 of
[`Chapter_8/doc/DEPLOY.md`](../../Chapter_8/doc/DEPLOY.md); a unit that's
already running Chapter 8 needs nothing more. Ch9 needs `adafruit_bitmap_font`
in `lib/` for its comic fonts (`game/fonts/`).

## Deploy

```
Chapter_9/tools/deploy.sh                     # -> /Volumes/CIRCUITPY, ejects when done
Chapter_9/tools/deploy.sh --no-eject          # skip the eject
Chapter_9/tools/deploy.sh /Volumes/CIRCUITPY  # explicit target
Chapter_9/tools/deploy.sh --art-set sdxl-repaint  # which room art (default: drawn)
Chapter_9/tools/deploy.sh --mpy                # modules precompiled (needs mpy-cross, see below)
```

Same mechanism as Chapter 8's script (`boot.py` turns auto-reload off; the
script ejects the drive to flush the FAT cache; then RESET / power-cycle to
run). It rsyncs with `--delete`, so a previously deployed Chapter 8 demo or
`main.py` is replaced — but `lib/` and `settings.toml` are never touched, so
`DEVICE_ID` survives. `--demo NAME` copies `game/NAME.py` over the device's `main.py` so a
look-test runs instead of the game (e.g. `--demo critter_demo`, the animated
critter browser, or `--demo overlay_demo`, every comic overlay in turn); the
desktop `main.py` is untouched, and a plain re-deploy puts the game back. To go back to a Chapter 8 demo, run
`Chapter_8/tools/deploy.sh`.

`deploy.sh` warns (but doesn't fail) if anything's missing from `lib/`.

Room art comes from `Chapter_9/art_sets/`, not `game/`: `--art-set` picks one
set and only that set is copied, as `/art/rooms/` (see `art_sets/README.md`).

`--mpy` puts the game modules on the board as `.mpy`, compiled by `mpy-cross`
for the board's CircuitPython (`downloads/mpy-cross/`, gitignored; Adafruit's
build from their download server). It refuses a version mismatch. Measured on
ws-10 (2026-11-08, `cd-342.38`) it saves **no RAM** once the game is running,
since the board keeps the bytecode in RAM either way, so plain `.py` stays the
default.

## What you should see

1. Boot → the **Living Room**: the tree with five presents under it, one per
   critter. After the `9 PM` caption, Chirpy's escape plays (tap to skip ahead):
   her red box rattles, a close-up, `POP!`, eyes over the rim, `CHIRPY!`, and
   she bolts out of the tipped box toward the Dining Room. Then `CHIRPY ESCAPED!`
   and her clue. Green pulsing dots on the edges open this episode (right →
   Dining Room, up → Hallway), dim dots on the rest. A box tipped over is a
   critter that's out; a critter sitting on its box is home.
2. **Tap toward an edge** (anywhere outside the middle 120px circle: the ring is
   split into four slices along the diagonals), or **swipe anywhere**, to move. A
   swipe drags the world, like on a watch: swipe left to go right. Touching a dot's zone snaps it gold (live exit) or red (blocked). A closed
   exit shows a reason in a caption (left: "brr! too cold out there"); no exit at
   all gets a `BONK!` burst and a shake. **While a caption or burst is up, a tap
   anywhere only moves it along**: it never walks you out of the room.
3. **Play episode 1 by tapping the things in the middle of the screen.** The room
   name is at the top:
   - Right three times → Sun Porch: Chirpy peeks over a potted plant, which
     rustles. Tap her: `FOUND!`, then a thought bubble of the yarn she wants, and
     the stuck door up from the Dining Room creaks open.
   - Left twice → Dining Room, up → Sewing Nook: the yarn bobs in the middle. Tap
     it, and its icon moves to the bottom left: you're holding it.
   - Down, right, right → Sun Porch: tap Chirpy again (hearts), and she hops
     along in the bottom right as you go.
   - Back left three times to the tree, where she curls up on the rug. The next
     critter escapes straight away; the dog, robot and squirrel come in a random
     order, then the reindeer. After that the whole map opens (the real finale is
     `cd-342.6`).
4. **Leave it alone, set down or hung, for ~30s** → the ornament scene
   (tree, star, snow). **Touch it** → back to the game, where you left off; that
   first touch only wakes it, it doesn't also move you.
5. Ornament still for 5 min, or handled but untouched in the game for 2 min →
   backlight off; touch wakes it.

To check how screens look without deploying, `/usr/bin/python3
Chapter_9/tools/preview.py` renders them to `Chapter_9/preview/*.png` (`contact.png`
shows them all), using the game's real view code (`cd-342.25`).

Serial (`screen /dev/tty.usbmodem*`) prints `Ch9 ready -- start: ... player=... free=N` at
boot, `moved <dir> -> <room>` on each move, `tap in <room>: [...]` on each
center tap, and a stats line every 10s: longest stalls in ms, IMU errors, touch
connects/drops. `bus rebuild` lines mean the touch chip locked the I2C bus and
the game recovered (`cd-342.16`); idle hitches of 0.5–2.5s are that. Timeouts
live in `game/modes.py` (`DEFAULT_IDLE_TIMEOUT`) and `game/app.py`
(`_INTERACTIVE_BLANK_TIMEOUT`, `_ORNAMENT_BLANK_TIMEOUT`) — all first guesses
awaiting on-device feel-testing (`cd-342.7`).

## Naming a board

To end the game with `MERRY CHRISTMAS,` then the player's name, add this to the
board's `settings.toml`, which deploys leave alone:

```
PLAYER = "Sam"
```

Use letters, digits and `! ' , . ?` only, since the comic fonts have nothing else.
Anything else draws as a gap. Without it, the game says `MERRY CHRISTMAS!`.

## Review mode: every room open

Each episode opens only part of the house (`doc/EPISODES.md`), so some rooms
can't be reached for most of the game. To walk round every room, for example to
look at an art set, add this to the board's `settings.toml` and reset:

```
OPEN_ALL_ROOMS = "1"
```

The story still runs, but no door is shut. The start-up line shows
`OPEN_ALL_ROOMS` while it's on. Take it out for real play, and never put it on a
gift unit.

## Review mode: straight to the finale

To try the finale (`doc/EPISODES.md` §6) without playing all five episodes
first, add this and reset:

```
FINALE_NOW = "1"
```

The game starts with every critter already home, and the first tap past the
title sets off the burst. The start-up line shows `FINALE_NOW` while it's on.
Same rule: take it out for real play, never on a gift unit.

## Diagnostic: the touch log

To see why a tap or swipe didn't do what you meant, add this and reset:

```
TOUCH_LOG = "1"
```

Every stroke then prints a line on the serial console: where the finger went down
and up, how long, how many readings the touch chip gave, and what the game did
with it (a move, a centre tap, a caption moved on, a cutscene beat). The 10s
stats line adds how many reads the chip refused. See `game/touch_log.py`.

## Two boards

With two boards plugged in, the second mounts as `CIRCUITPY 1`, and which is
which depends on plug-in order. Check `DEVICE_ID` in each drive's `settings.toml`
and pass the exact path.
