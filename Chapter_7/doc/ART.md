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
- ~14×9 tiles visible in the map region of a 240×240 screen (exact figure
  set by `cd-oht.1`).
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
- **Target 32 colors** (index 0 transparent + 31 ink). Keeps BMPs small,
  forces coherence, comfortable in RP2040 RAM. Bump to 64 only if the terrain
  candidates clearly need it — *(open)*, revisit after `cd-e17.5`.
- Authoring convention: index 0 maps to bright magenta (`0xFF00FF`) so any
  unpainted pixel is obvious before it's made transparent.
- Character: muted dungeon earth and stone, a small set of saturated accents
  for magic / potions / blood / gold.

## 6. Reference art

All three sources are CC0 (`sourceArt/*/README.md`) — derivatives need no
attribution; we credit them in the chapter README anyway.

| Need | Primary reference | Note |
|---|---|---|
| Floor / wall / terrain look | Project Utumno | true overhead; 32→16 downscale as a study |
| Palette | Utumno + 0x72 DungeonTileset v4 | |
| Item silhouettes | 0x72 v4 | potions, swords, keys, chests, books — already 16×16 |
| Monster style | Utumno overhead monsters + 0x72 II | small, front-facing |
| Hero style | 0x72 v4 characters | front-facing, ~12 px tall inside the 16 px cell |

## 7. Build pipeline

- `Chapter_7/tools/build_tiles.py` (`cd-e17.4`) emits the four BMPs:
  procedural generators for terrain textures + hand-authored pixel grids for
  entities. Output is palette-indexed, index-0 transparent, tight-packed.
- The committed `.bmp` files are the deployed artifact. The generators and
  pixel-grid sources live in `tools/` and are desktop-only (Pillow) — not
  copied to `CIRCUITPY`.

## 8. Open sub-decisions

- Tile count per sheet — waits on the monster/item rosters.
- 32 vs 64 palette colors — revisit after the first terrain candidates.
- Whether `heroes.bmp` needs a "dead" tile, or the engine just drops a corpse
  tile from `objects.bmp`.

## 9. Flagged for deliberate revisit (`cd-e17.11`)

This spec is v1, chosen to get moving. Two choices are explicitly provisional
and will be reconsidered once first art candidates and the engine roster exist:

- **Perspective** — front-facing figures on top-down floors (§1) vs. a truer
  overhead treatment for creatures and heroes.
- **Animation depth** — one frame per entity (§4) vs. idle bobs, multi-frame,
  or directional sprites.

Changing either means reworking `creatures.bmp` / `heroes.bmp`, so the revisit
is scheduled before those sheets are considered final, not after.
