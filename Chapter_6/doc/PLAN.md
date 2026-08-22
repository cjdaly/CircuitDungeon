# Chapter 6 — Implementation Plan

## Goals

1. A reusable game engine (`engine.py`) with a clean example game on top.
2. Idiomatic CircuitPython — modern API, no deprecated patterns.
3. A new `.lvl` map/script format that is readable, general-purpose, and not clever.
4. Hardware abstraction so the same engine runs on PyBadge, Clue, HalloWing, and PyPortal.

---

## New Map/Level Format — `.lvl`

Replace both the `.dad` and `.map` formats with a single INI-style file, using the `.lvl` extension. The file extension carries no technical weight — `level_loader.py` hand-rolls its own parser (we need `[grid]` blocks and typed sections `configparser` doesn't give for free), and no parser, hand-rolled or otherwise, inspects the extension of the file it's handed. `.lvl` is chosen over reusing `.map` because Chapter 5/PyBadge still ships `.map` files in the old, incompatible format; a shared extension across two structurally different formats would invite mixing them up during the migration. `.lvl` also matches the vocabulary used everywhere else in this doc (`level_loader.py`, `levels/`, `game.level`, `load_level`).

### Design principles
- `[section]` headers to separate concerns — no line-prefix sigils.
- Grid rows are plain text — no leading `/`.
- Triggers use plain `->` and `!` notation.
- All keys lowercase, values unquoted unless spaces matter.

### Full specification

```ini
# comment

[meta]
name: home
title: Welcome home...
subtitle: ...now go away!

[terrain]
chars: (_)"[#]RGBYOoX^CDEF
walls: "[#]RGBYOoX^CDEF

[grid]
##########
#        #
#  B     #
#        #
#        #
#        #
#
##########

[exits]
# col,row -> mapname @ dest_col,dest_row
9,6 -> forest @ 1,6
9,1 -> sage   @ 1,1

[events]
# col,row ! event_type [args...]
2,6 ! explosion exp1
5,3 ! text Watch out!
7,7 ! tile 11
```

### Section details

**`[meta]`** — optional. `name` is the map identifier used in exit targets. `title` / `subtitle` are displayed as overlaid text on map enter; omit either to suppress it.

**`[terrain]`** — `chars` is the ordered string mapping characters to tile indices (position 0 = tile 0, etc.), matching the sprite sheet. `walls` lists the subset of chars that block movement. Both inherit sensible defaults if the section is absent (useful for trivial test maps). The defaults reuse Chapter 5/PyBadge's `terrain.bmp` order verbatim, minus its leading space char — a literal space can't survive `key: value`'s trailing/leading strip, so tile 0 (a blank-floor variant, visually interchangeable with tile 1) goes unused by the defaults; every other tile keeps Chapter 5's original index.

**`[grid]`** — rows of plain characters, no prefix. Row count and column count are read from the data; no header line needed. Trailing whitespace in a row is trimmed to a configurable fill character (default: first char in `chars`).

**`[exits]`** — each line is `col,row -> mapname @ dest_col,dest_row`. When the hero occupies `col,row`, load `mapname.lvl` and place the hero at `dest_col,dest_row`.

**`[events]`** — each line is `col,row ! event_type [args]`. Supported event types:
- `explosion name [scale]` — play the named explosion animation at that tile position, optionally scaled up (`explosion exp1 3`). Explosions are pooled (several can be on screen at once, oldest evicted past the pool size) and chain-react: detonating one also queues any orthogonally adjacent one-shot `explosion` events to go off a beat later.
- `text message` — display a message (uses the HUD text label).
- `tile index` — replace that tile with a different index (for switches, doors, etc.).
- `anim name` — loop that grid cell's tile through the named frame-index array, driven by the engine pulse (see [Pulse / heartbeat](#pulse--heartbeat)). Fires the same way as any other event — the hero stepping onto a torch or trap tile lights it — after which it keeps animating.

Events are one-shot by default; prefix `*` to make them repeatable (`2,6 *! explosion exp1`) — a repeatable event won't refire on every single frame the hero stands on it, only after a short per-tile cooldown, so a "trap" can be stepped off and back onto rather than firing continuously.

### What this replaces

| Old feature | New equivalent |
|---|---|
| `.dad` `YO:` variables + `SUP:`/`SDN:` lifecycle + phase-tagged ops | `[meta]` title display + `[events]` triggers |
| `.map` `@col,row~mapname@destcol,destrow` | `[exits]` section |
| `.map` `@col,row*eventname@expx,expy` | `[events]` section |
| `.map` `\|\|walls` override line | `[terrain] walls:` key |
| `.dad` `randomap` op | Handled in engine via a `[events]` `tile` trigger + engine RNG |
| ChompCode frame-phase scheduling (`SUP:`/`SDN:`/`nom:` opcode lists) | Replaced by a plain pulse counter + hook list — see [Pulse / heartbeat](#pulse--heartbeat) |

---

## Engine Architecture

### Module structure

```
Chapter_6/
  doc/             # design docs — not deployed to CIRCUITPY
  game/
    main.py          # board detection, construct Game, call game.play()
    engine.py        # Game class: __init__(), play(), game loop
    level_loader.py  # Level class: parse .lvl files → Level instance
    hardware.py      # GameDisplay class + detect(): buttons, display handle, optional NeoPixel
    util.py          # displayio helpers (load_tilegrid, load_sprite, etc.)
    levels/          # .lvl files
    tiles/           # terrain.bmp, heroes.bmp, explosions.bmp, etc.
  tools/
    build_tiles.py # offline, Pillow-based tile sheet builder (desktop only, not deployed to CIRCUITPY)
```

`game/` is everything that gets copied to `CIRCUITPY` — same split Chapter 5/PyBadge and Chapter 5/Clue use. `doc/` and `tools/` stay on the desktop side.

### State — composed objects

State is a small set of classes, composed rather than inherited: `Game` holds a `GameDisplay`, a `Level`, and a `Player`. Each of these has exactly one live instance during play, so the class boundary buys organization — methods instead of `func(game, ...)` threading, clear ownership of what belongs to hardware vs. level vs. hero — at no memory cost over a flat dict: neither CircuitPython nor MicroPython support `__slots__` ([adafruit/circuitpython#10517](https://github.com/adafruit/circuitpython/issues/10517) is open, unresolved), so every instance carries a full `__dict__` regardless; for a singleton, that's the same one dict either way.

That trade-off inverts for objects that can multiply. A future chapter's NPCs or monsters — several per room — stay as plain dicts in a list (`game.npcs = [{...}, {...}]`), not class instances: the missing `__slots__` support makes each additional dict-carrying instance strictly more expensive than an entry in a shared dict, and this example game has no NPCs to need the ergonomics yet.

```python
class Game:
    def __init__(self):
        self.display = None    # a GameDisplay
        self.level   = None    # a Level
        self.hero    = None    # a Player
        self.cycle   = 0       # frame counter (the pulse)
        self.anims   = {}      # active `anim` triggers: (col,row) -> {'name', 'frames'}
        self.camera  = None    # {'x': 0, 'y': 0} when level.scroll, else None

class GameDisplay:              # from hardware.py detect()
    def __init__(self):
        self.screen     = None  # board.DISPLAY
        self.groups     = {}    # named displayio Groups
        self.grids      = {}    # named TileGrids
        self.sprites    = {}    # named sprite TileGrids
        self.neopixel   = None
        self.read_buttons = None  # callable → dict with keys 'up','down','left','right','a','b'

class Level:                    # from level_loader.py
    def __init__(self):
        self.name, self.title, self.subtitle = None, None, None
        self.chars, self.walls = None, None
        self.grid, self.exits, self.events = None, None, None
        self.scroll = False

class Player:
    def __init__(self):
        self.tile_x, self.tile_y = 0, 0
        self.facing, self.anim_frame = 'right', 0
```

### Game loop

```python
class Game:
    def play(self):
        while True:
            buttons = self.display.read_buttons()
            self.handle_input(buttons)
            self.check_triggers()         # exits + events
            self.update_sprites()         # hero animation frame + `anim` events
            self.update_camera()          # no-op unless the level scrolls
            self.display.screen.refresh()   # or wait_for_frame() if supported
            self.cycle += 1
```

No opcode-list scripting (ChompCode's `SUP:`/`SDN:`/`nom:` lines). A single pass per frame, driven by the plain `cycle` counter, is sufficient — see [Pulse / heartbeat](#pulse--heartbeat).

### Collision

Directly from Chapter 5/PyBadge — `Game.in_wall()` checks the terrain char at the hero's tile position against `level.walls`. Movement is applied then bounced back if a wall is hit. `getHeroXY` / `setHeroXY` tile↔pixel math is preserved.

### Animation

Hero animation: `cycle % 4` selects walk frame. Direction tracked in `hero.facing` (`'right'` or `'left'`). Tile index = `hero_base + frame` (right) or `hero_base + 9 + frame` (left), matching the existing sprite sheet convention.

Explosion animation: frame index array (`[0,1,2,...,N]`) from Chapter 5/PyBadge, driven by `cycle % len(frames)`. Unlike Chapter 5, more than one can be running at once — a small pool of explosion sprites (default 4) lets a trap detonate its neighbors without cutting off the first blast — and a triggered explosion can chain into orthogonally adjacent tiles that also carry an `explosion` event, each going off a few cycles after the last.

### Pulse / heartbeat

`Game.cycle` is the shared clock for all cycle-driven behavior, hero/explosion animation included. There is no opcode-list scheduler behind it (ChompCode's `SUP:`/`SDN:`/`nom:` lines and 8-way phase dispatch): everything reads `self.cycle` directly, in plain methods.

- `[events] anim` triggers fire like any other event — the hero has to step onto the tile — and once fired, register into `self.anims`. There's no load-time, walk-past-nothing "ambient" registration: a torch on a wall the hero can never stand on wouldn't be reachable this way, so `anim` tiles are placed on tiles the hero actually crosses (a lit floor rune, a switch that starts sparking), same as `explosion` or `tile`.
- `Game.update_sprites()` walks `self.anims` each frame and sets `grid[col,row] = frames[cycle % len(frames)]` — the same frame-index-array approach already used for explosions, generalized to arbitrary terrain tiles.
- `update_sprites` is the single place all cycle-driven visuals are computed. No lifecycle hooks, no per-phase opcode lists — one method, not a dispatch table.
- A future event type that needs to *act* on a timer rather than animate (e.g. a monster that moves every N frames) reads `self.cycle % N` inside `check_triggers` or `update_sprites`. No separate scheduler is needed for that case either.

### Sprite transparency

`adafruit_imageload.load()` + `palette.make_transparent(0)` throughout. No `OnDiskBitmap` / `ColorConverter` for any sprite.

### Resolution independence

Map grid fills the display: `cols = display.width // tile_w`, `rows = display.height // tile_h`. Same approach as Chapter 4. The `.lvl` format does not encode display dimensions.

### Camera / scrolling

Rooms are fixed-size and match the viewport by default. A room may instead be larger than the display and camera-scrolled to follow the hero — set with `[meta] scroll: yes` (default `no`), read into `Level.scroll`. Same `.lvl` syntax either way: `[grid]`, `[exits]`, and `[events]` don't change shape. Scrolling is a display concern, not a format concern.

The mechanism is a plain offset, not Chapter 4's dual-buffer wraparound (`sceneCycle`'s two side-by-side `TileGrid`s, procedurally regenerated per column for an endless runner — not applicable to a finite, authored room). `displayio` positions a `TileGrid`'s `x`/`y` relative to its `Group`'s root and accepts negative values, so a `TileGrid` larger than the display can be panned by setting `terrain_grid.x = -camera_x * tile_w` — no wraparound bookkeeping, no procedural regeneration.

`Game.load_level()` sets `self.camera = {'x': 0, 'y': 0}` when `level.scroll` is true, else `None`. `Game.update_camera()`, called once per frame from the game loop, clamps the camera to `[0, grid_cols - viewport_cols]` / `[0, grid_rows - viewport_rows]` as the hero moves and repositions the terrain/sprite groups; it's a no-op when `self.camera is None`, so fixed rooms pay nothing for the feature.

A `TileGrid` costs roughly 1–2 bytes per cell regardless of viewport size, so a scrolled level's RAM cost scales with `total_cols * total_rows`, not the viewport. Trivial for anything room-sized — tens of thousands of cells before it registers against a PyBadge's ~32KB free RAM — confirmed on-hardware in Phase 4 rather than assumed.

---

## Hardware Abstraction (`hardware.py`)

```python
def detect():
    """Return a populated GameDisplay for the current board."""
    import board
    board_id = getattr(board, 'board_id', '')
    if board_id in _PYBADGE_FAMILY:          # pybadge, edgebadge
        return _pybadge()
    elif board_id in _CLUE_FAMILY:           # clue_nrf52840_express
        return _clue()
    elif hasattr(board, 'NEOPIXEL') and not hasattr(board, 'BUTTON_A'):
        return _hallowing()
    else:
        return _generic()
```

Each `_board()` function returns a `GameDisplay` (see [State — composed objects](#state--composed-objects)) with `.read_buttons` set to a callable → dict with keys `'up'`,`'down'`,`'left'`,`'right'`,`'a'`,`'b'`, `.neopixel` set to a NeoPixel object or `None`, and `.screen` set to `board.DISPLAY`.

Callers use `buttons['left']` — boolean — instead of bitmask arithmetic. The bitmask decoding lives inside `_pybadge()`'s `read_buttons`, invisible to the engine.

Board detection keys off `board.board_id` — CircuitPython's documented identifier string, matching the slug in each board's `circuitpython.org/board/<id>/` URL (see `doc/SYSTEMS.md`) — rather than `hasattr` duck-typing, for the boards where that id is confirmed. This matters because `hasattr(board, 'BUTTON_CLOCK')` alone doesn't distinguish PyBadge from PyGamer: PyGamer also has a `BUTTON_CLOCK`/`BUTTON_OUT`/`BUTTON_LATCH` shift register (for its 4 face buttons), but reads direction from separate analog `JOYSTICK_X`/`JOYSTICK_Y` pins, not the register — matching it into `_pybadge()` would build a `ShiftRegisterKeys(key_count=8)` expecting PyBadge's d-pad-in-the-register layout and never read the joystick at all. `_PYBADGE_FAMILY`/`_CLUE_FAMILY` are explicit id sets so boards without a dedicated handler yet (PyGamer, PicoSystem, PewPew M4, T-Deck) fall through to `_generic()`'s safe no-op stub instead of silently misreading another board's controls. HalloWing keeps the `hasattr`-based fallback until a unit is on hand to confirm its `board_id`.

---

## Example Game

A small dungeon with 4–5 interconnected rooms demonstrating:
- Navigation between rooms via `[exits]`
- At least one `explosion` event trigger
- At least one `text` event trigger (a sign/notice)
- At least one `tile` event trigger (a door that opens)
- 3 hero character types (A button cycles)
- NeoPixel ambient color that changes per room (on hardware that has one)

Artwork: reuse Chapter 5/PyBadge tile sheets (`terrain.bmp`, `heroes.bmp`, `explosions.bmp`) — they have transparency support and are the most complete.

---

## Implementation Steps

### Phase 1 — Foundation

1. **`util.py`** — copy and clean up Chapter 5/PyBadge `util.py`. Replace `OnDiskBitmap` paths with `adafruit_imageload`. Remove game-specific code; keep only `load_tilegrid`, `load_sprite`, `init_label`.
2. **`hardware.py`** — `GameDisplay` class + `detect()` with PyBadge and Clue implementations. Stub HalloWing and generic. Test button reads independently.
3. **`level_loader.py`** — `Level` class + parser for the `.lvl` format. Input: file path. Output: a `Level` with `.name`, `.title`, `.subtitle`, `.chars`, `.walls`, `.grid`, `.exits`, `.events`, `.scroll`. Write unit-testable pure functions/methods (no hardware dependency).

### Phase 2 — Engine core

4. **`engine.py` `Game.__init__`** — set up display groups, terrain TileGrid, hero sprite, explosion sprite, HUD label. Use `display.width`/`display.height` for all sizing.
5. **`engine.py` `Game.load_level(name)`** — parse `.lvl` file, populate terrain TileGrid, store the `Level` in `self.level`.
6. **`engine.py` movement + collision** — `handle_input`, `in_wall`, `getHeroXY`/`setHeroXY`, bounce-back. Verify on PyBadge first.
7. **`engine.py` triggers** — `check_triggers`: iterate `level.exits` and `level.events` against hero tile position each frame.
8. **`engine.py` animation + pulse** — hero walk cycle, explosion frame array, `anim` events, `cycle` counter.
9. **`engine.py` camera** — `update_camera`: no-op when `level.scroll` is false; otherwise clamp and reposition per [Camera / scrolling](#camera--scrolling).

### Phase 3 — Example game content

10. **Tile assets** — copy Chapter 5/PyBadge `terrain.bmp`, `heroes.bmp`, `explosions.bmp` into `Chapter_6/tiles/`. Verify palette index 0 is the transparency color. `tools/build_tiles.py` (see [What We Are Not Building](#what-we-are-not-building)) is not on the critical path here — it's for whenever a later chapter needs a new tile sheet.
11. **`.lvl` files** — write 4–5 rooms: `home.lvl`, `cave.lvl`, `vault.lvl`, `garden.lvl`. Wire up exits so all rooms are reachable and the player can navigate back. At least one room uses an `anim` event (e.g. a flickering torch) to exercise the pulse hook; at least one room is larger than the viewport with `scroll: yes` to exercise the camera.
12. **`main.py`** — `hardware.detect()`, `Game()`, `game.play()`. Board-specific startup (NeoPixel color, backlight).

### Phase 4 — Polish + portability

On-hardware verification runs against the physical boards catalogued in
[`doc/SYSTEMS.md`](SYSTEMS.md), in this order:

13. **PyBadge** — first and primary target; `TERRAIN_TILE=16` against 160×128 gives the 10×8 grid the engine and example levels were built around. Verify movement/collision, all four `[events]` types, the scrolling room (camera clamps at level edges, `anim` tiles keep animating while scrolled, no visible RAM pressure from the larger `TileGrid`), and NeoPixel per-room color.
14. **PicoSystem** — bumped ahead of the rest of the PyBadge family; different SoC entirely (RP2040, not SAMD51) so it's the first real test of hardware abstraction beyond `_pybadge()`/`_clue()`. `detect()` needs a new branch — RP2040 boards don't set `BUTTON_CLOCK`/`BUTTON_A`/`NEOPIXEL`, so route on a board-id check (e.g. `board.board_id`) instead — and a `_picosystem()` reading its direct-wired D-pad + A/B/X/Y. 240×240 exercises the same resolution-independence path as Clue (15×15 tiles). Before wiring buttons, check whether the board's frozen `stage`/`ugame` modules need to be avoided/uninstalled to leave `displayio` free, per `doc/SYSTEMS.md`.
15. **PyBadge LC** — same screen and button layout as PyBadge, so `_pybadge()` should need no changes; confirm it runs within the LC's tighter RAM/flash and that skipping the (absent) accelerometer and extra NeoPixels degrades gracefully.
16. **EdgeBadge** — same SAMD51 core, screen, and buttons as PyBadge; expect a clean run with zero code changes, confirming `_pybadge()` isn't accidentally PyBadge-specific.
17. **PyGamer** — same screen as PyBadge but an analog thumbstick + 4 buttons instead of a d-pad; add a `_pygamer()` path to `hardware.py` that thresholds thumbstick X/Y into `up`/`down`/`left`/`right`, and confirm there's no Select/Start-bound functionality to lose.
18. **Clue** — 240×240 screen (grid should scale to 15×15 tiles automatically via the resolution-independence math) and only A/B buttons, no d-pad. Movement needs a fallback input scheme (e.g. driven by the built-in accelerometer/gyro) since `_clue()` currently only reads A/B; scope this down to a non-movement demo if a full control scheme isn't worth building for this chapter.

Also in this phase:

19. Add `[meta] title` display on map enter — brief text overlay that fades (or just hides after N frames).
20. NeoPixel per-room ambient color: add optional `color: R,G,B` key to `[meta]`.

Not yet scheduled into the order above: PewPew M4 (own SAMD51 board, non-d-pad button wiring — see `doc/SYSTEMS.md`) and T-Deck (no d-pad/face buttons, but its keyboard could approximate `up`/`down`/`left`/`right`/`a`/`b` via key mapping — worth a `_tdeck()` pass once the boards above are working).

---

## What We Are Not Building

- A ChompCode-style scripting interpreter — string-decoded opcodes (`nom:`, `SUP:`, `SDN:`) and an 8-way phase dispatch table. Cycle-driven behavior runs through `Game.cycle` and plain methods instead; see [Pulse / heartbeat](#pulse--heartbeat).
- A desktop art pipeline coupled to ImageMagick and bash. Tile sheets are still built offline, from source art, as a manual step run only when assets change — just from a Python script, `tools/build_tiles.py` ([Pillow](https://pillow.readthedocs.io/): `Image.crop().paste()` over a source-rect table), rather than `Chapter_5/PyBadge/tools/extract-tilesets.sh`'s `convert` invocations. Same offline workflow and committed `.bmp` output; one dependency and one language instead of two.
- Chapter 4's dual-buffer infinite scroll — wrapping `TileGrid`s procedurally regenerated per column, built for an endless runner. Large, authored rooms scroll by camera offset instead; see [Camera / scrolling](#camera--scrolling).
- A class for every kind of game object. The singleton concepts (`Game`, `GameDisplay`, `Level`, `Player`) are classes; objects that can multiply (NPCs, monsters, in a future chapter) are plain dicts in a list — see [State — composed objects](#state--composed-objects).
