# Chapter 9 — Architecture

How the game is put together, what the board allows it, and the shape it is
being moved to (`cd-342.47`). Read §1 before changing anything that runs on
every frame or draws text.

## 1. The board's budgets

The desktop tests run under CPython, which has none of these limits, so a
change can pass every test and still fail on the board. Check anything that
touches these on a board (§5 has the tool).

| budget | what we have | notes |
|---|---|---|
| **Python call stack** (pystack) | 1536 bytes, CircuitPython's default `CIRCUITPY_PYSTACK_SIZE` | Every active call holds a frame: about 28 bytes of overhead plus 4 bytes per local variable and per stack slot. Run out and the call raises `RuntimeError: pystack exhausted`. |
| **Deepest call: drawing text** | `bitmap_label`'s `text` setter goes 5 calls deep inside the library | This is the call that runs out first. On 2026-11-22 the escape cutscene died here (`cd-342.46`). Headroom, measured with `tools/device_run.py --depth` (extra small calls the game survives): 3 after the first fix, 7 after step 2 (`cd-342.47.2`), **11 after step 3** (`cd-342.47.3`; `--no-title`). Start-up, which builds the gift tag's labels, survives 8. |
| **RAM** | about 150 KB headroom, largest free block at least 128 KB (ws-10, `cd-342.38`) | `gc.mem_free()` misleads on CircuitPython 10, because the heap grows on demand. Measure `gc.mem_alloc()` differences instead. |
| **Frame time** | loop sleeps `_TICK` = 50 ms; about 18 fps in play | |
| **Drawing a caption's words** | about 570 ms on the board | This is `bitmap_label` rendering the text. Nothing else per beat comes close. Keep captions to what the story needs. |
| **Touch chip** | can lock the I2C bus (`cd-342.16`); can hang light sleep (`cd-342.30`) | `bus_recovery.py` rebuilds the bus. |
| **USB while asleep** | in deep idle the board barely services USB | A deploy's eject can hang until the game is woken or stopped (2026-11-22). |

What follows from these:

- **Draw only from the update pass** (`cd-342.47.3`). Input handlers
  change state and say what to show: `NavView.show_room`, `show_scene`,
  `say`, `bonk`, `tap_overlay` and `BeatPlayer.play` / `tap` only record it.
  `NavView.update` (from the loop's `GameScreen.update`) does the drawing,
  so text is always drawn at one known, shallow depth. Anything that drives
  a `NavView` outside the game (`tools/preview.py`) calls `update()` after
  each event, as the loop does.
- **Set words once, not every frame.** A label's text is the deepest thing
  drawn: set it when a shot or beat starts (`HomeView.shot`), not in the
  per-frame drawing under it.
- **Keep frames small on the drawing path.** A function that draws text, or
  calls something that does, keeps few locals. Put heavy work (layout
  searches, big loops) in its own function, called before or after the
  drawing, not around it.
- **Keep loop-level frames small.** Whatever sits under every call (today
  `app.run`, with 68 locals) is paid for on every path.

## 2. The parts as they are now

```
boot.py, main.py            bootstrap: display, I2C bus, touch, IMU; starts app.run
hardware.py, touch.py,      the board: pins, display, touch chip wrapper,
imu.py, bus_recovery.py     motion sensor, bus recovery

app.py  Game, run()         THE LOOP: read sensors, handle, update (cd-342.47.2)
settings.py                 the game's settings.toml keys, read once
sensors.py                  touch, motion, stillness, bus recovery
power_manager.py            blanking per mode, deep idle, drain log
  modes.py, stillness.py,   the policies it uses: game or ornament, still or
  screen_blanker.py,        handled, when to blank, when to sleep; battery log
  power.py, drain_log.py

-- screens (screens.py: group, enter, handle, update) --
TagScreen    gift_tag.py    FOR <PLAYER>, FROM CHRIS, before the title
TitleScreen  title_view.py  CHRISTMAS CRITTERS, until a tap
GameScreen   nav_view.py    the game; NavView owns everything below
OrnamentScreen ornament.py  the ornament scenes

-- the game's model (plain Python, no displayio) --
rooms.py                    the room graph, exits, gates
critters.py                 the cast, roster, lures
episodes.py                 per-critter episodes: open rooms, hiding and lure rooms, clues
hunt.py      Hunt           the playable loop: start, entered, tapped, bumped -> messages
scene_art.py                names of lures, hiding spots and props

-- the game screen's drawing --
backdrop.py                 the room's art
scene_view.py  SceneView    what's in the room: critters, lures, props, cutscene shots
  home_view.py              the Living Room's presents, the escape shots
  finale_view.py            the finale's shots
  walk.py                   critter walking motion
room_banner.py              the room name
comic.py  Stage             caption, balloon, thought bubble, burst, emanata, ink ring
  comic_shapes.py, comic_fonts.py
clearance.py                keeping popups off the scene (cd-342.46)
beats.py  BeatPlayer        plays comic beats in order, on taps or timers
escape.py, finale.py        cutscenes, written as beats

-- not the game --
critter_demo.py, overlay_demo.py   look-tests (deploy.sh --demo)
touch_log.py                       diagnostic, TOUCH_LOG = "1"
critter_candidates.py              GENERATED sprite index (tools/build_critter_candidates.py)
sprite_scale.py                    unused: nothing imports it, but it is deployed
```

The model layer is in good shape: small, testable, no displayio. Most of the
problems are in how the loop and the screens are wired together.

## 3. What's wrong with the wiring

*Step 2 (`cd-342.47.2`) has since split `app.run` into the parts in §2, and
step 3 (`cd-342.47.3`) moved drawing out of input handling: every caption is
now drawn from `run → Game.tick → _play → GameScreen.update → NavView.update →
BeatPlayer.update`, about 880 bytes deep before the library, against 1150 in
the chain below. The frame sizes below are from before both.*

**`app.run` does everything.** It is one 340-line function with 68 locals and
4 nested helper functions. It covers:

- the gift tag → title → game sequence;
- switching between the game and the ornament;
- blanking and deep idle;
- bus recovery;
- the touch log;
- the stats line.

Its frame is about 90 slots (about 390 bytes, a quarter of the pystack), and
it sits under every call. Each new feature has made it harder to change.

**Drawing happens inside input handling.** A move calls straight down to the
pixels. This is the path that ran out of stack, with each frame's approximate
size in slots (locals + cells + value stack):

```
main()                      19
app.run                     90   <- under everything
  run.start_game             7
  run.tell                  12
  NavView.say               30
  BeatPlayer.play            6
  BeatPlayer._next           7
  _Director.show            11
  comic.Stage.show          10
  _Caption.draw              7
  _Lines.show               12
  bitmap_label (5 frames)   ?? <- ran out here
```

How deep text gets drawn depends on what triggered it: the title tap, a move,
a centre tap or a timer each reach it by a different route. Nobody can see the
budget, so nothing protects it.

**Story and screen are tangled.**

- `app.tell` pulls six fields out of the hunt (`event`, `critter`, `escape`,
  `escape_at`, `cutscenes`, messages) to hand to `NavView.say`.
- `say` then knows about hunt events, the escape, the finale's cutscene
  table, thought-bubble icons and hearts.
- Turning *what happened* into *what to show* is spread over `hunt.py`,
  `nav_view.py`, `escape.py` and `finale.py`.
- The views import `hunt`.

**Popup placement is spread out** over `comic.Stage`, `SceneView` and
`nav_view._Director` (`cd-342.46`).

**The budgets in §1 were written down nowhere and checked nowhere.**

## 4. The target

```
main.py ──> Game(hardware)                    small object, short methods
              tick(now):
                read inputs (touch, IMU)      -> plain values
                power.update(...)             blanking, deep idle, bus recovery
                screen.handle(input)          changes state, queues; draws nothing
                screen.update(now)            THE ONLY PLACE THAT DRAWS

screens: GiftTagScreen -> TitleScreen -> GameScreen, and OrnamentScreen
         each: group, enter(now), handle(input, now), update(now), done/next

GameScreen
  hunt (model)  --story events-->  storyboard  --beats-->  BeatPlayer (queue)
                                                              |
  update(now): SceneView, room chrome, BeatPlayer.update -> Stage (draws text)
```

The steps, each one keeping the game playable and the tests green, checked
on a board:

1. This document (`cd-342.47.1`).
2. **The main loop becomes a `Game` object** (`cd-342.47.2`). Each screen
   becomes an object with the same few methods. Power, blanking and bus
   recovery move into their own object. Settings are read in one place.
   Behaviour stays the same; `test_app_smoke` guards it.
3. **Draw only from the update pass** (`cd-342.47.3`). `say` and `play`
   queue; the next `update()` shows the first beat.
4. **One storyboard** (`cd-342.47.4`). The hunt reports what happened as
   plain data, and one module builds the beats from it. That replaces
   `app.tell`, most of `NavView.say`, and the cutscene wiring. Views stop
   importing `hunt`.
5. **Guardrails** (`cd-342.47.5`), see §5.
6. **Details** (`cd-342.47.6`): tidy `comic.py` and `scene_view.py`, gather
   popup placement in one place, and drop `sprite_scale.py`.

## 5. Checking on the board

- **The preview tool** shows how screens look without a board:
  `/usr/bin/python3 Chapter_9/tools/preview.py`. It can't show stack, RAM or
  timing.
- **A scripted run on the board**: `tools/device_run.py SERIAL` runs the
  real game with fake taps (through the gift tag, the title and the escape
  cutscene) and reports any traceback.
  - `--depth N` runs it under N extra nested calls: the smallest N that
    fails tells you how much stack is to spare. Run it after any change on
    the drawing path, and note the number in §1.
  - `--push FILE...` loads changed modules over serial instead of from the
    board's flash, so a change can be tried without deploying (or when macOS
    won't mount the drive). A reset puts the board back on what's deployed.
  - It talks to the REPL over serial and never writes files to the drive:
    macOS caches writes to the CIRCUITPY drive, and a reset can read a
    half-written file. It doesn't `import main`, because `main.py` starts the
    game when imported.
- **A frame-size test** on the desktop (`cd-342.47.5`) keeps the drawing
  path's frames small, using CPython's code objects as a stand-in for the
  board's.
- **More stack, as a backstop** (to be decided in `cd-342.47.5`):
  `CIRCUITPY_PYSTACK_SIZE` in `settings.toml`. Deploys don't touch that file,
  so every board would need it by hand.
