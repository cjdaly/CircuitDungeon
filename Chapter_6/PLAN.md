# Chapter 6 — Implementation Plan

## Goals

1. A reusable game engine (`engine.py`) with a clean example game on top.
2. Idiomatic CircuitPython — modern API, no deprecated patterns.
3. A new `.level` map/script format that is readable, general-purpose, and not clever.
4. Hardware abstraction so the same engine runs on PyBadge, Clue, HalloWing, and PyPortal.

---

## New Map/Level Format — `.level`

Replace both the `.dad` and `.map` formats with a single INI-style file.
- pushback: I like `.map` or `.lvl` (level) file extension.
  - is there some technical reason to use `.ini`? can we use the INI format with a different extension

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
chars: (_)[#]RGBYOoX^CDEF
walls: [#RGBY

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

**`[terrain]`** — `chars` is the ordered string mapping characters to tile indices (position 0 = tile 0, etc.), matching the sprite sheet. `walls` lists the subset of chars that block movement. Both inherit sensible defaults if the section is absent (useful for trivial test maps).

**`[grid]`** — rows of plain characters, no prefix. Row count and column count are read from the data; no header line needed. Trailing whitespace in a row is trimmed to a configurable fill character (default: first char in `chars`).

**`[exits]`** — each line is `col,row -> mapname @ dest_col,dest_row`. When the hero occupies `col,row`, load `mapname.level` and place the hero at `dest_col,dest_row`.

**`[events]`** — each line is `col,row ! event_type [args]`. Supported event types:
- `explosion name` — play the named explosion animation at that tile position.
- `text message` — display a message (uses the HUD text label).
- `tile index` — replace that tile with a different index (for switches, doors, etc.).

Events are one-shot by default; prefix `*` to make them repeatable (`2,6 *! explosion exp1`).

### What this replaces

| Old feature | New equivalent |
|---|---|
| `.dad` `YO:` variables + `SUP:`/`SDN:` lifecycle + phase-tagged ops | `[meta]` title display + `[events]` triggers |
| `.map` `@col,row~mapname@destcol,destrow` | `[exits]` section |
| `.map` `@col,row*eventname@expx,expy` | `[events]` section |
| `.map` `\|\|walls` override line | `[terrain] walls:` key |
| `.dad` `randomap` op | Handled in engine via a `[events]` `tile` trigger + engine RNG |
| ChompCode frame-phase scheduling | Not carried forward — event triggers are position-based, not time-based |

- pushback on frame-phase scheduling: we should try to keep this in some form
  - it's good for animations (with 'sprite' tiles) and can add spice to the game


---

## Engine Architecture

### Module structure

```
Chapter_6/
  main.py          # board detection, call engine.init() + engine.play()
  engine.py        # init(), play(), game loop
  level_loader.py  # parse .level files → level dict
  hardware.py      # HAL: buttons, display handle, optional NeoPixel
  util.py          # displayio helpers (load_tilegrid, load_sprite, etc.)
  levels/          # .level files
  tiles/           # terrain.bmp, heroes.bmp, explosions.bmp, etc.
```

### State dict structure

Keep the `game` dict but give it named sub-dicts instead of a flat namespace:

```python
game = {
  'display': ...,        # displayio display handle
  'hw':      ...,        # hardware config (from hardware.py)
  'level':   ...,        # current parsed level dict
  'groups':  {...},      # named displayio Groups
  'grids':   {...},      # named TileGrids
  'sprites': {...},      # named sprite TileGrids
  'hero':    {...},      # hero state: tile_x, tile_y, facing, anim_frame
  'cycle':   0,          # frame counter
}
```

### Game loop

```python
def play(game):
    while True:
        buttons = game['hw']['read_buttons']()
        handle_input(game, buttons)
        check_triggers(game)          # exits + events
        update_sprites(game)          # hero animation frame
        board.DISPLAY.refresh()       # or wait_for_frame() if supported
        game['cycle'] += 1
```

No sub-frame phase scheduling (ChompCode-style). A single pass per frame is sufficient for the targeted hardware speed.

### Collision

Directly from Chapter 5/PyBadge — `in_wall(game)` checks the terrain char at the hero's tile position against `level['walls']`. Movement is applied then bounced back if a wall is hit. `getHeroXY` / `setHeroXY` tile↔pixel math is preserved.

### Animation

Hero animation: `cycle % 4` selects walk frame. Direction tracked in `hero['facing']` (`'right'` or `'left'`). Tile index = `hero_base + frame` (right) or `hero_base + 9 + frame` (left), matching the existing sprite sheet convention.

Explosion animation: frame index array (`[0,1,2,...,N]`) from Chapter 5/PyBadge, driven by `cycle % len(frames)`.

### Sprite transparency

`adafruit_imageload.load()` + `palette.make_transparent(0)` throughout. No `OnDiskBitmap` / `ColorConverter` for any sprite.

### Resolution independence

Map grid fills the display: `cols = display.width // tile_w`, `rows = display.height // tile_h`. Same approach as Chapter 4. The `.level` format does not encode display dimensions.

---

## Hardware Abstraction (`hardware.py`)

```python
def detect():
    """Return a hw dict for the current board."""
    import board
    if hasattr(board, 'BUTTON_CLOCK'):      # PyBadge / PyGamer
        return _pybadge()
    elif hasattr(board, 'BUTTON_A'):        # Clue
        return _clue()
    elif hasattr(board, 'NEOPIXEL') and not hasattr(board, 'BUTTON_A'):
        return _hallowing()
    else:
        return _generic()
```

Each `_board()` function returns:

```python
{
  'read_buttons': callable → dict with keys 'up','down','left','right','a','b',
  'neopixel':     NeoPixel object or None,
  'display':      board.DISPLAY,
}
```

Callers use `buttons['left']` — boolean — instead of bitmask arithmetic. The bitmask decoding lives inside `_pybadge()['read_buttons']`, invisible to the engine.

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
2. **`hardware.py`** — write `detect()` with PyBadge and Clue implementations. Stub HalloWing and generic. Test button reads independently.
3. **`level_loader.py`** — write parser for the `.level` format. Input: file path. Output: `{'name', 'title', 'subtitle', 'chars', 'walls', 'grid', 'exits', 'events'}`. Write unit-testable pure functions (no hardware dependency).

### Phase 2 — Engine core

4. **`engine.py` `init()`** — set up display groups, terrain TileGrid, hero sprite, explosion sprite, HUD label. Use `display.width`/`display.height` for all sizing.
5. **`engine.py` `load_level(game, name)`** — parse `.level` file, populate terrain TileGrid, store parsed level in `game['level']`.
6. **`engine.py` movement + collision** — `handle_input`, `in_wall`, `getHeroXY`/`setHeroXY`, bounce-back. Verify on PyBadge first.
7. **`engine.py` triggers** — `check_triggers`: iterate `level['exits']` and `level['events']` against hero tile position each frame.
8. **`engine.py` animation** — hero walk cycle, explosion frame array, `cycle` counter.

### Phase 3 — Example game content

9. **Tile assets** — copy Chapter 5/PyBadge `terrain.bmp`, `heroes.bmp`, `explosions.bmp` into `Chapter_6/tiles/`. Verify palette index 0 is the transparency color.
10. **`.level` files** — write 4–5 rooms: `home.level`, `cave.level`, `vault.level`, `garden.level`. Wire up exits so all rooms are reachable and the player can navigate back.
11. **`main.py`** — `hardware.detect()`, `engine.init()`, `engine.play()`. Board-specific startup (NeoPixel color, backlight).

### Phase 4 — Polish + portability

12. Verify on Clue (240×240) — grid should scale to 15×15 tiles automatically.
13. Verify on HalloWing (128×128, no buttons) — stub input or use capacitive pads if available.
14. Add `[meta] title` display on map enter — brief text overlay that fades (or just hides after N frames).
15. NeoPixel per-room ambient color: add optional `color: R,G,B` key to `[meta]`.

---

## What We Are Not Building (_au contraire_)

- A ChompCode-style scripting interpreter or per-frame phase scheduler.
  - pushback: see above, we should have a pulse / heartbeat with steps to hook into
- Desktop map-generation tools (mapgen.py / ImageMagick pipeline) — tile sheets are managed offline.
  - pushback: look into running those as builds (when needed) in a more pythonic way
- The dual-buffer infinite scroll from Chapter 4 — rooms are fixed-size for the example game.
  - pushback: we should allow for both fixed size and variable (scrolling) games (levels?)
    - scrolling will be better for large levels on small (pixel count) displays
- OOP class hierarchy — the `game` dict + module functions pattern is kept, just better organized.
  - pushback: investigate an OOP rewrite
    - will it use significantly more resources (memory) on these microcontroller systems
    - don't forget to research circuit python docs (especially for latest stable versions)
    - what makes sense as a class?
      - Game (heartbeat/clockwork rhythm counters, world level - contains maps, ...)
      - GameDisplay (hardware abstraction, screen buffering, NeoPixels, sound, ...)
      - Level/Map start with format above
      - Player
      - NPCs / Monsters (this would be largely new I think)
      - ???
