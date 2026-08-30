# Chapter 7 — Art Specification

Resolves bead `cd-e17.1`. Governs the tile/sprite work in epic `cd-e17`.
Sub-decisions marked *(open)* are deferred until the roster and level-gen
tables exist; everything else is settled.

## 1. Perspective & style

- **Overhead / top-down.** Floors are seen straight down. Walls are drawn as
  chunky wall-top blocks (Project Utumno style), *not* the front-face wall
  slabs of the 0x72 platformer sets.
- **Creatures and heroes are small front-facing figures** — the sprite faces
  the player; movement direction is *not* shown by the sprite. This is the
  standard roguelike convention (Dungeon Crawl does exactly this). No
  side-profile stances, no directional walk cycles.
- **One light direction: from the top.** Consistent thin highlight on top
  edges, shade on the bottom, across every sheet.

## 2. Tile grid

- **16×16 px for everything** — terrain, objects, creatures, heroes.
- Ch6 used 16×24 for heroes; Ch7 goes uniform 16×16 so a hero, a monster,
  and an item each occupy exactly one map cell. Simplifies collision, camera,
  and sprite handling.
- **13×13 tiles visible** in the map viewport (`cd-oht.1` / [`LAYOUT.md`](LAYOUT.md)):
  a 208×208 px viewport, 16 px status line above, 16 px message line below,
  32 px icon rail on the right.
- Rationale: matches the native size of the 0x72 reference sets; proven in Ch6.

## 3. Sheet files

One palette-indexed BMP per category, in `Chapter_7/game/tiles/`:

| File | Tile | Contents |
|---|---|---|
| `terrain.bmp` | 16×16 | floors, walls, doors, stairs up/down, rubble, liquid, decor |
| `creatures.bmp` | 16×16 | monsters (one tile each) |
| `heroes.bmp` | 16×16 | player classes (one tile each) |
| `objects.bmp` | 16×16 | items — on the ground and in the inventory panel |
| `fx.bmp` | 16×16 | *(optional, deferred)* hit spark, death puff, targeting glyphs |

- **Tile index = row-major position**, index 0 = top-left. Same convention as
  Ch5/Ch6.
- Sheets are packed tight — no margins, no inter-tile spacing.
- Grid dimensions per sheet are *(open)* — they follow the rosters from
  `cd-e3p.4` (monsters), `cd-e3p.8` (items), and `cd-dsc.1` (spawn tables).

## 4. Animation / frames

A roguelike is turn-based, so animation is deliberately minimal.

- **Start with one tile per entity** — hero, monster, object.
- Pulse-driven 2-frame variants (a slime that wobbles, gold that glints) use
  the same `Game.cycle` mechanism as Ch6's `anim` events. Added only in the
  polish pass (`cd-e17.9`), and only where they earn the RAM.
- If `fx.bmp` happens, effects are short frame-index sequences like Ch6
  explosions (2–4 frames).

## 5. Palette & transparency

- **One shared master palette** across all four sheets. Finalized in `cd-e17.3`.
- **Index 0 = transparent** — reserved, never drawn. Loaded with
  `adafruit_imageload.load()` + `palette.make_transparent(0)`, exactly as Ch6.
- **64-slot capacity, ~40 populated to start** (`cd-e17.3`). 32 vs 64 costs
  nothing on-device — indexed sheets are 8 bpp for any count in 17–256; the
  only saving is at ≤16 colors (4 bpp), which this palette can't hit anyway.
  So we take the headroom: unused slots are free and avoid re-quantising every
  sheet in the polish pass.
- **Indices 0–15 are the frozen core** — transparent, outline, and the
  neutral / stone / dirt / wood ramps every sheet leans on. Hand-authored
  sprites pixel against these slot numbers, so 0–15 are never renumbered or
  deleted (RGB values may still be nudged). Indices 16–39 are append-only
  while art is in flight; 40–63 are reserved for the polish pass (venom,
  frost, corpse-grey, crystal, lava, cloth dyes).
- **Ramps, not free colors.** Every material is a dark→highlight ramp (3–5
  steps) sharing a hue; `off_white` doubles as the shared brightest step.
  Coherence comes from the ramp structure, not a low count.
- Authoring convention: index 0 maps to bright magenta (`0xFF00FF`) so any
  unpainted pixel is obvious before it's made transparent.
- Character: muted dungeon earth and stone, a small set of saturated accents
  for magic / potions / blood / gold.
- Built + validated by `tools/build_palette.py` → `game/tiles/palette.{json,py}`
  and `doc/preview/palette.png`. Every color is checked against Utumno + 0x72
  v4; worst drift in v1 is d≈10 RGB (all colors real in the source sets).

## 6. Reference art

The three **primary** sources — Project Utumno, 0x72 DungeonTileset v4, 0x72
DungeonTileset II — are all CC0; derivatives need no attribution and we credit
them in the chapter README anyway.

The broader reference set added under `cd-e17.13` (`sourceArt/*/README.md`,
catalogued in [`REFERENCES.md`](REFERENCES.md) → *Extended survey*) is mixed:
most is CC0, but **DawnLike is CC-BY 4.0** (credit DawnBringer + DragonDePlatino)
and **`sourceArt/TopDownDungeon/` is CC-BY 3.0** (credit Buch + sponsor Abram
Connelly). If any pixels derived from those two reach a shipped sheet, the
chapter README must carry the attribution — tracked in `cd-e17.14`.

| Need | Primary reference | Note |
|---|---|---|
| Floor / wall / terrain look | Project Utumno | true overhead; 32→16 downscale as a study |
| Palette | Utumno + 0x72 DungeonTileset v4 | |
| Item silhouettes | 0x72 v4 | potions, swords, keys, chests, books — already 16×16 |
| Monster style | Utumno overhead monsters + 0x72 II | small, front-facing |
| Hero style | 0x72 v4 characters | front-facing, ~12 px tall inside the 16 px cell |
| Overhead wall-tops + stairs at 16×16 | `sourceArt/TopDownDungeon/` (Buch), DawnLike | fills the `cd-e17.2` gap; CC-BY — see above |

## 7. Build pipeline

`Chapter_7/tools/` (desktop-only, Pillow + numpy; nothing here is copied to
`CIRCUITPY`):

| File | Role |
|---|---|
| `build_palette.py` | master palette → `game/tiles/palette.{json,py}` + swatch preview (`cd-e17.3`) |
| `tilelib.py` | shared: ASCII-grid → indices, sheet packing, 8-bit BMP writer, rgba render |
| `art/terrain.py` | procedural tile generators (`cd-e17.5`) |
| `art/{creatures,heroes,objects}.py` | hand-authored pixel grids — ASCII art + per-file legend of palette colour names (`cd-e17.7/.6/.8`) |
| `build_tiles.py` | assembles the four sheets → BMPs + `tiles.json` manifest; `--preview` emits the review artifacts (`cd-e17.4`, `cd-e17.12`) |

- Each `art/*.py` exposes `build(pal) -> list[Tile]`. Hand-authored tiles are
  16×16 ASCII grids; `.`/space → transparent index 0, every other char maps to
  a master-palette colour *name*. Procedural tiles hand back a 16×16 index array.
- Sheets pack row-major, tight (no margins). `tile index = row-major position`,
  index 0 = top-left (ART.md §3).
- Output BMPs are 8-bit palette-indexed, 256-entry table, `BITMAPINFOHEADER` —
  loaded on device exactly as Ch6: `adafruit_imageload.load()` +
  `palette.make_transparent(0)`.
- `game/tiles/tiles.json` is the tile-index ↔ name manifest for the engine.
- The committed `.bmp` files + `tiles.json` are the deployed artifact.
- Deterministic and re-runnable: `python3 Chapter_7/tools/build_tiles.py`.

## 8. Open sub-decisions

- Tile count per sheet — waits on the monster/item rosters.
- ~~32 vs 64 palette colors~~ — resolved: 64-slot capacity, ~40 populated,
  core 0–15 frozen (see §5).
- Whether `heroes.bmp` needs a "dead" tile, or the engine just drops a corpse
  tile from `objects.bmp`.
- Which slots fill 40–63, and final RGB tuning of the v1 ramps — after the
  first terrain + sprite candidates.

## 9. Flagged for deliberate revisit (`cd-e17.11`)

This spec is v1, chosen to get moving. Two choices are explicitly provisional
and will be reconsidered once first art candidates and the engine roster exist:

- **Perspective** — front-facing figures on top-down floors (§1) vs. a truer
  overhead treatment for creatures and heroes.
- **Animation depth** — one frame per entity (§4) vs. idle bobs, multi-frame,
  or directional sprites.

Changing either means reworking `creatures.bmp` / `heroes.bmp`, so the revisit
is scheduled before those sheets are considered final, not after.

## 10. Review workflow (`cd-e17.12`)

Every candidate/review/refine round is reviewed on-screen *before* anything is
loaded onto the PicoSystem. `build_tiles.py --preview` emits:

- **8× contact-sheet PNGs** per sheet into `Chapter_7/doc/preview/` (committed,
  diffable), with tile-index labels and the master palette strip.
- an **HTML review artifact** with a zoom toggle (2× / 4× / 8× / 12×),
  `image-rendering: pixelated`, each sheet shown on both dark and light grounds.

Scale reference on a ~109 ppi monitor: 2× ≈ actual PicoSystem physical size,
8× is the working size for judging a single tile, 10–16× for pixel-level
dithering inspection. This is the off-device counterpart to `cd-e17.10`
(on-device verification).
