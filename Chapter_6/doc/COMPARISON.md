# CircuitDungeon Chapter Comparison

## Quick Reference

| | Ch 0 | Ch 1 | Ch 2 | Ch 3 | Ch 4 | Ch 5/Clue | Ch 5/PyBadge |
|---|---|---|---|---|---|---|---|
| Hardware | HalloWing | HalloWing | HalloWing | PyBadge | HalloWing/PyPortal | Adafruit Clue | PyBadge |
| Display | 128×128 | 128×128 | 128×128 | 160×128 | adaptive | 240×240 | 160×128 |
| Game loop | none | none | none | yes (4-phase) | yes | yes | yes |
| Input | none | none | none | GamePadShift | none | clue HAL | GamePadShift |
| Map rendering | pre-baked BMP | TileGrid | TileGrid 8×6 | TileGrid 10×6 | dual-buffer scroll | single giant tile | TileGrid 10×8 |
| Sprite transparency | no | no | no | no | no | no | yes |
| Collision | none | none | none | index > 3 | none | none | wall charset + bounce |
| Multi-map | no | no | no | yes (joke DSL) | no | no | yes (`@` triggers) |
| NeoPixel | yes | yes | yes | no | yes | N/A | minimal |
| State container | `splash` Group | `game` dict | `game` dict | `game` + `CCPU` dicts | `data` dict | `game` dict | `game` dict |
| Module split | 1 file | 1 file | 1 file | 3 files | 1 file | 2 + util | 2 + util |

---

## Chapter 0 — "The Rough Beginning"

**Nature:** Static scene proof-of-concept. No game loop, no input, no animation.

**Hardware:** Adafruit HalloWing (128×128 TFT, one NeoPixel).

**Architecture:** Fully procedural, function-based. Display state kept in a bare `displayio.Group`.

**Map pipeline:** Desktop-side `mapgen.py` uses ImageMagick to composite tile images into a single `map1.bmp`. The device just loads and displays the pre-rendered BMP — no tile indexing at runtime. Map format uses `=c=tilename` lines and `/`-prefixed 16-char rows.

**Notable:** `test()` returns the map `TileGrid` for REPL scroll testing — the only interactivity is manual REPL manipulation. Map is positioned at `(-64, -48)` to pan to an interesting region of the 256×256 image.

**Key contribution:** Establishes the basic `displayio` scene graph pattern (`Group` → `TileGrid` → `OnDiskBitmap`) and the desktop tile-compositing pipeline.

---

## Chapter 1 — "The Hallowing!"

**Nature:** First on-device tile rendering. Still no game loop or input, but the map is now assembled from a tileset `TileGrid` rather than a pre-rendered BMP.

**Hardware:** HalloWing.

**Architecture:** Procedural, game state in a `game` dict — the pattern used by all future chapters. `load_tilegrid()` now takes `w, h, tw, th` parameters enabling a 16×16 map grid from a sprite sheet.

**Map pipeline:** `mapgen2.py` (desktop) now uses explicit pixel offsets for ImageMagick crop operations. The map format upgrades to a `?` header line (16 chars = terrain-to-tile-index mapping) plus `/`-prefixed rows. `TM(game, c)` does the character-to-index lookup.

**Notable:** The transition chapter — `init()` calls the old `load_mapbmp()` alongside the new tile approach while the new system is being introduced. The `game` dict established here (display group, NeoPixel, map data) is the ancestor of all future state containers.

**Key contribution:** On-device tileset rendering. The `game` dict state container. The `?`-header map format.

---

## Chapter 2 — "Yet Another Game Concept..."

**Nature:** First animation demo. Hero sprite walks right then left on a loop (`strut()`). Still no player input.

**Hardware:** HalloWing.

**Architecture:** Same `game` dict pattern. Display layout expands: 8×6 terrain grid (128×96px) plus a 8×1 status bar TileGrid below it, plus hero sprite.

**Key advances:**
- `strut()` is the first animation loop — hero tile indices cycle 4–7 (walk right) and 12–15 (walk left), synced with `board.DISPLAY.wait_for_frame()`.
- Multiple `TileGrid`s in one scene (`map_tg`, `status_tg`, `hero_tg`).
- `cycle_lights()` parameterizes brightness and NeoPixel color from the `game` dict.
- `adafruit_display_text` label added for the first time.
- Error sentinel: `TM()` returns tile 14 (a "red flag" tile) for unknown chars instead of 0.
- Terrain char set expands to 35 characters, mapped by string position to tile indices 0–34.

**Key contribution:** `wait_for_frame()` as the frame-sync primitive. Multi-TileGrid scenes. Parameterized NeoPixel/backlight control. The sprite sheet walk-cycle convention (4 frames per direction).

---

## Chapter 3 — "The Dad Joke"

**Nature:** A complete side-scrolling mini-game where each level is a dad joke. The most architecturally ambitious chapter.

**Hardware:** Adafruit PyBadge (160×128, `GamePadShift` button input, `adafruit_bitmap_font` BDF font).

**Architecture:** Three modules (`main.py`, `joke.py`, `chomp_code.py`). Game state split into `game` dict (display/sprites) and `CCPU` dict (ChompCode interpreter state).

**ChompCode scripting engine (`chomp_code.py`):** A custom DSL interpreter for `.dad` script files.
- Phase-tagged command lines: `nom:`, `Nom:`, `nOm:`, `NoM:`, `noM:`, `NOM:` — each fires at a different sub-frame phase of the 4-frame-per-turn game loop.
- `YO:key:value` variable bindings in script files.
- `SUP:` / `SDN:` setup and teardown commands run on level enter/exit.
- Sigil-based parameter resolution in `decode_param()`: digit literals, `~str` string literals, `&reg` registers, `$var` YO variables, `@FR/@TR/@LV/@GP` loop state (frame/turn/level/gamepad).
- Built-in ops: `setTopText`, `setBottomText`, `setMiddleText`, `hideText`, `playerPosition`, `playerMove`, `playerMorph`, `randomap`, `levelExit`.
- Regex compiled at init time (good practice on constrained hardware).

**Input:** `GamePadShift` returns bitmask from `gPad.get_pressed()`. Bit 4 (value 16) = right, bit 7 (value 128) = left, bit 0 (value 1) = toggle armor. `CC_playerMove()` does collision via tile index threshold (`> 3`).

**Game loop:** 4 frames per turn, `pL = [frame, turn, level, gamepad]` positional list as loop state.

**Level progression:** 10 `.dad` joke scripts; player walks off the right edge to advance. `levelExit` runs `SDN` commands, loads next script, runs `SUP` commands.

**Display:** 10×6 terrain, top/bottom text labels (magenta/cyan), middle BDF font label (yellow), hero sprite (16×24 `rugrats.bmp`), 3 auxiliary sprites (pet, snack, silly — parked off-screen at `(-33,-33)` when unused).

**Key contribution:** The ChompCode phase-driven scripting engine — the most sophisticated original engineering in the series. `GamePadShift` bitmask input. BDF bitmap font. Data-driven level content via `.dad` files. The concept of auxiliary sprites parked off-screen.

---

## Chapter 4 — "The Rabbit Hole"

**Nature:** Visual demo of scrolling procedural terrain with animated creatures. No player input, no game logic.

**Hardware:** HalloWing or PyPortal. Notably resolution-independent — uses `DSP.width` and `DSP.height` everywhere instead of hardcoded pixel values.

**Architecture:** Single module (`demo.py`), `data` dict. Clean separation between `sceneReset()` (init) and `sceneCycle()` (per-frame update).

**Key advances:**
- **Dual-buffer scrolling:** Two terrain `TileGrid`s side by side; when one scrolls off the left edge it is repositioned to the right for seamless infinite scroll.
- **Procedural terrain generation:** `sceneCycle()` fills new columns using `data['elev']` (floor height) and `data['ceil']` (ceiling height) to create a cave cross-section with random decorations.
- **Creature system:** `tgHeroes` and `tgNasties` are lists of 3 `TileGrid`s each, stored in a sub-group with `scale=2` (creatures rendered double-size without duplicating bitmap data). `creatureTile(attrs, cFrame, nTiles)` computes sprite-sheet tile index from a 3-char attribute string (creature index, facing, animation state).
- **NeoPixel:** Blue channel pulses with frame counter (`cFrame * 4`), creating ambient LED animation synced to display.
- **Game loop:** `cFrame` cycles 0–3; `cTurn` counts total turns; `cScene` / `nextScene` scene transition architecture exists but is not triggered in this demo.
- **`play()` guard:** `if not data: data = init()` allows REPL reuse without reinit.

**Key contribution:** Dual-buffer infinite scroll. Procedural terrain generation. Sub-group `scale=2` for upscaling sprites. The `creatureTile()` sprite-sheet indexing function. Resolution independence via `DSP.width`/`DSP.height`. The `sceneReset` / `sceneCycle` separation pattern.

---

## Chapter 5 / Clue — "Summer Camp"

**Nature:** Map viewport pan proof-of-concept on new hardware.

**Hardware:** Adafruit Clue (nRF52840, 240×240 display, `from adafruit_clue import clue` HAL).

**Architecture:** `main.py` + `game.py` + `util.py`. `util.py` extracts `load_tilegrid()`, `init_tilegrid()`, `init_label()` as a reusable module.

**Map approach:** Unconventional — loads the entire map as a single 500×500-tile `TileGrid` (one "tile" = the whole map BMP). Scrolling is done by moving `M.x`/`M.y` by 10 pixels per button press. No tile indexing, no collision, no sprites.

**Input:** `clue.button_a`, `clue.button_b` (A = left, B = right), `clue.touch_0` (up), `clue.touch_2` (down) — boolean properties from the Clue HAL, no bitmask arithmetic needed.

**Notable:** The Clue HAL (`adafruit_clue`) abstracts all hardware behind clean boolean properties — a very different input model from `GamePadShift`. The `util.py` module split is a portability prototype. A typo (`upateT` vs `updateT`) reveals this is a fast prototype, not a finished demo.

**Key contribution:** Adafruit Clue hardware integration. The `util.py` module extraction pattern. High-level HAL input (booleans vs bitmasks). Demonstration that the viewport-pan approach works for large maps on a 240×240 display.

---

## Chapter 5 / PyBadge — "Summer Camp"

**Nature:** The most complete interactive dungeon demo in the series — full movement, collision, map transitions, explosion effects.

**Hardware:** Adafruit PyBadge (160×128, `GamePadShift`).

**Architecture:** `main.py` + `game.py` + `util.py`. `util.py` is the richest helper module in the series.

**`util.py` highlights:**
- `init_sprite()`: uses `adafruit_imageload.load()` instead of `OnDiskBitmap`, enabling palette manipulation — `pal.make_transparent(0)` marks color index 0 transparent. First use of sprite transparency in the series.
- `load_map()`: richest map loader yet. Handles `/` rows, `?key: chars` terrain header, `||walls` wall charset override, `@x,y~mapname@nx,ny` exit triggers, `@x,y*expname@ex,ey` explosion triggers.
- `in_wall(game)`: checks current hero tile char against `game['mapWalls']` string — readable and efficient for small char sets.
- `handle_buttons(game)`: full 4-directional movement with bounce-back collision (`hero.x += 2`, if `in_wall` → `hero.x -= 4`). Button A cycles hero character (3 types: base offsets 0, 18, 36). Button B reloads home map.
- `getHeroXY(game)` / `setHeroXY(game)`: convert between pixel position and tile coordinates, accounting for sprite offset relative to tile grid.
- `check_exits()` / `check_exps()`: data-driven map trigger handlers.

**Game:** 10×8 terrain TileGrid (full 160×128 screen). Hero sprite (16×24, transparent). Explosion sprite (32×32, animated via frame index arrays). `cycle` counter drives hero animation (`cycle % 4`) and explosion animation (`cycle % len(expArr)`). Face direction stored in `game['face_right']` boolean.

**Map format:** `?key: chars` header (optional), `||walls` wall override, `/` rows (10 chars × 8 rows), `@x,y~mapname@nx,ny` exits, `@x,y*expname@ex,ey` explosion triggers.

**Key contribution:** Sprite transparency via `adafruit_imageload` + `make_transparent`. Configurable wall charset. Bounce-back collision. Data-driven map exit and explosion triggers. Tile↔pixel coordinate math (`getHeroXY`/`setHeroXY`). Multi-character hero types. Frame index array explosion animation. The best-organized code in the series.

---

## Cross-Cutting Themes

### What every chapter shares
- `displayio` scene graph: `Group` → `TileGrid` → bitmap
- The `game` dict as universal state container (Ch 1 onward)
- 2-space indentation, procedural style, no OOP
- Terrain chars mapped to tile indices via string position lookup
- `board.DISPLAY` as the display handle

### Strongest individual contributions to carry forward

| Feature | Best source |
|---|---|
| Sprite transparency | Ch 5/PyBadge (`adafruit_imageload` + `make_transparent`) |
| Map trigger system (exits, events) | Ch 5/PyBadge (`@` trigger lines in `.map` files) |
| Configurable wall charset | Ch 5/PyBadge (`||walls` + `in_wall()`) |
| Bounce-back collision + tile↔pixel math | Ch 5/PyBadge (`handle_buttons`, `getHeroXY`/`setHeroXY`) |
| Multi-file module split | Ch 5 (`main.py` / `game.py` / `util.py`) |
| Resolution independence | Ch 4 (`DSP.width`/`DSP.height` everywhere) |
| Dual-buffer infinite scroll | Ch 4 (two `TileGrid`s swapping positions) |
| `sceneReset` / `sceneCycle` separation | Ch 4 (init vs. per-frame update) |
| Sub-group `scale=2` for sprite upscaling | Ch 4 (`GRP_CR` with `scale=2`) |
| `play()` REPL guard | Ch 4 (`if not data: data = init()`) |
| ChompCode phase-driven scripting | Ch 3 (if a scripting/event system is wanted) |
| `GamePadShift` bitmask input | Ch 3 / Ch 5/PyBadge |
| BDF bitmap font | Ch 3 (`adafruit_bitmap_font`) |
| `wait_for_frame()` frame sync | Ch 2 (though Ch 5 drops it for free-running loop) |
| Parameterized NeoPixel/backlight control | Ch 2 (`cycle_lights()`) |
| Desktop map pipeline | Ch 0–2 (mapgen.py + ImageMagick) |

### Things to leave behind
- Pre-rendered BMP maps (Ch 0, Ch 1 transitional) — tile-based rendering is strictly better.
- The single-giant-tile pan approach (Ch 5/Clue) — only useful for pre-rendered maps on devices with enough RAM.
- The `game` dict as an untyped grab-bag — a Chapter 6 engine should at minimum organize state into named sub-dicts or simple classes, even if staying broadly procedural.
- Hardcoded pixel dimensions — resolution independence (Ch 4 approach) should be standard.
- `OnDiskBitmap` + `ColorConverter` for sprites — `adafruit_imageload` with palette transparency is the right approach.
