
# CircuitDungeon - Chapter 6 - Chit-chat with Claude

<!-- pics of the devices running the game go here -->

The earlier chapters are a pile of one-off demos: each one re-invents map
loading, movement, and animation from scratch, in whatever style seemed good
that week. Chapter 6 is the cleanup. Working with Claude (Anthropic's coding
assistant), the goal was to take the best ideas from Chapters 0-5 and fold them
into one small, reusable game engine with an example game on top - while also:

* making the code more idiomatic Python,
* moving to current CircuitPython core + library APIs, and
* generalizing across a range of CircuitPython devices with screens and buttons.

The conversation and its outputs live in [`doc/`](doc):

* [`PROMPT.md`](doc/PROMPT.md) - the original ask
* [`COMPARISON.md`](doc/COMPARISON.md) - a feature-by-feature review of Chapters 0-5
* [`SYSTEMS.md`](doc/SYSTEMS.md) - the physical test boards and their quirks
* [`PLAN.md`](doc/PLAN.md) - the implementation plan the code follows

## What got carried forward

| From | Idea |
|---|---|
| Ch 5/PyBadge | sprite transparency (`adafruit_imageload` + `make_transparent`), bounce-back collision, tile-to-pixel math, multi-character hero |
| Ch 5 | `main` / `engine` / `util` module split |
| Ch 4 | resolution independence (`display.width // tile_w`), init-vs-per-frame separation |
| Ch 3 | data-driven levels with triggers - but as a plain INI file, not a scripting DSL |
| Ch 2 | a single frame-counter "pulse" driving all animation |

The `game` grab-bag dict is gone. State is a few composed classes - `Game` owns a
`GameDisplay`, a `Level`, and a `Player`.

## Layout

```
game/            # everything copied to CIRCUITPY
  main.py          # board detect -> Game -> play()
  engine.py        # Game class: loop, movement, collision, triggers, animation, camera
  hardware.py      # GameDisplay + detect(): per-board button/display/NeoPixel setup
  level_loader.py  # .lvl parser (pure text, runs off-device)
  util.py          # displayio helpers
  levels/          # home.lvl, cave.lvl, vault.lvl, garden.lvl
  tiles/           # terrain.bmp, heroes.bmp, explosions.bmp
doc/             # design docs - desktop only
```

## Prerequisites

* A recent CircuitPython (9.x or newer) on a supported board.
* Copy into `CIRCUITPY/lib`: `adafruit_display_text/`, `adafruit_imageload/`,
  `neopixel.mpy`. See [`doc/SYSTEMS.md`](doc/SYSTEMS.md) for details.
* Copy the **contents** of `game/` to the root of `CIRCUITPY`.

Board support (see `hardware.py`):

| Board | Input | Status |
|---|---|---|
| PyBadge / PyBadge LC / EdgeBadge | d-pad + A/B | tested on PyBadge |
| PicoSystem | d-pad + A/B | tested |
| Clue | A/B only (no movement yet) | stub |
| PyGamer, HalloWing, others | thumbstick / none | planned / no-op |

## Running

`main.py` runs on power-up. It starts in `home`, spawns the hero at tile
`(1,1)`, and enters the game loop.

## Controls

* **d-pad** - move (walk into a wall and you bounce back)
* **A** - cycle through the three hero characters
* Step onto an exit tile to move between rooms; step onto an event tile to
  trigger it (a sign, a bomb, a switch, a glowing rune).

## The `.lvl` format

Levels are INI-style text - `[section]` headers, no line-prefix sigils:

```ini
[meta]
name: home
title: Welcome home...
subtitle: ...now go away!
scroll: no

[terrain]
chars: (_)"[#]RGBYOoX^CDEF   # char -> tile index, by position
walls: "[#]RGBYOoX^CDEF      # which of those block movement

[grid]
##########
#(R((((G(#
#((((((((#
##########

[exits]
9,4 -> cave @ 1,4            # at col,row load cave.lvl, place hero at 1,4

[events]
4,1 ! anim rune             # animate this tile
2,6 ! explosion exp1        # play an explosion (chains into adjacent ones)
5,3 ! text Watch out!       # show a HUD message
7,7 ! tile 11               # swap in a different tile (doors, switches)
```

Events fire once; prefix `*` (`2,6 *! explosion exp1`) to make them repeatable
after a short cooldown. A room bigger than the screen with `scroll: yes` is
camera-followed; a room that fits the viewport pays nothing for the feature.

The example game exercises all of it: four connected rooms, an animated rune, a
chain-reacting bomb corridor, a switch that opens a path, and one oversized
`scroll` room (the vault).
