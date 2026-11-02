# Chapter 9 — Deploying to the Waveshare RP2350-Touch-LCD-1.28

How to get `Chapter_9/game/` onto the board and run it. It's the same board
as Chapter 8, so **the one-time device setup is identical** — CircuitPython
10.2.1 firmware, the `lib/` bundle libraries, the vendored `qmi8658c.py`, and
the per-unit `settings.toml` (`DEVICE_ID`, battery info). Follow steps 1–4 of
[`Chapter_8/doc/DEPLOY.md`](../../Chapter_8/doc/DEPLOY.md); a unit that's
already running Chapter 8 needs nothing more. (`adafruit_bitmap_font` isn't
needed yet — Ch9 doesn't load the comic fonts until `cd-bp3.13`.)

## Deploy

```
Chapter_9/tools/deploy.sh                     # -> /Volumes/CIRCUITPY, ejects when done
Chapter_9/tools/deploy.sh --no-eject          # skip the eject
Chapter_9/tools/deploy.sh /Volumes/CIRCUITPY  # explicit target
```

Same mechanism as Chapter 8's script (`boot.py` turns auto-reload off; the
script ejects the drive to flush the FAT cache; then RESET / power-cycle to
run). It rsyncs with `--delete`, so a previously deployed Chapter 8 demo or
`main.py` is replaced — but `lib/` and `settings.toml` are never touched, so
`DEVICE_ID` survives. `--demo NAME` copies `game/NAME.py` over the device's `main.py` so a
look-test runs instead of the game (e.g. `--demo critter_demo`, the animated
critter browser); the desktop `main.py` is untouched, and a plain re-deploy
puts the game back. To go back to a Chapter 8 demo, run
`Chapter_8/tools/deploy.sh`.

`deploy.sh` warns (but doesn't fail) if anything's missing from `lib/`.

## What you should see

1. Boot → the **Living Room**, and Chirpy's escape message: green pulsing dots
   on the edges open this episode (right → Dining Room, up → Hallway), dim dots
   on the rest.
2. **Tap or swipe starting in an edge band** (the outer 45px) to move.
   Touching a dot's zone snaps it gold (live exit) or red (blocked). A closed
   exit shows a reason (left: "brr! too cold out there"); no exit at all flashes
   "can't go `<direction>`".
3. **Play episode 1 by tapping the middle of the screen:**
   - Right → Dining Room, up → Sewing Nook: tap to take the ball of yarn.
   - Down, right → Kitchen, right → Sun Porch: tap Chirpy. Without the yarn she
     says what she wants; with the yarn she follows you home.
   - Back left three times to the tree, where she curls up on the rug. Episodes
     2–5 aren't written yet (`cd-342.14`), so this ends the game and opens the
     whole map.
4. **Leave it alone, set down or hung, for ~30s** → the ornament scene
   (tree, star, snow). **Touch it** → back to the game, where you left off; that
   first touch only wakes it, it doesn't also move you.
5. Ornament still for 5 min, or handled but untouched in the game for 2 min →
   backlight off; touch wakes it.

Serial (`screen /dev/tty.usbmodem*`) prints `Ch9 ready -- start: ... free=N` at
boot, `moved <dir> -> <room>` on each move, `tap in <room>: [...]` on each
center tap, and a stats line every 10s: longest stalls in ms, IMU errors, touch
connects/drops. `bus rebuild` lines mean the touch chip locked the I2C bus and
the game recovered (`cd-342.16`); idle hitches of 0.5–2.5s are that. Timeouts
live in `game/modes.py` (`DEFAULT_IDLE_TIMEOUT`) and `game/app.py`
(`_INTERACTIVE_BLANK_TIMEOUT`, `_ORNAMENT_BLANK_TIMEOUT`) — all first guesses
awaiting on-device feel-testing (`cd-342.7`).

With two boards plugged in, the second mounts as `CIRCUITPY 1`, and which is
which depends on plug-in order. Check `DEVICE_ID` in each drive's `settings.toml`
and pass the exact path.
