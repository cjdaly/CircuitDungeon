# Chapter 7 — Reference Art Catalogue

Resolves bead `cd-e17.2`. Inventory of the source art in `sourceArt/`, what
each set is good for, and how it feeds the Ch7 sheets. Perspective and style
targets are in [`ART.md`](ART.md).

## Summary

| Source | File | Native tile | Perspective | License | Verdict |
|---|---|---|---|---|---|
| **Project Utumno** | `DungeonCrawl/ProjectUtumno_full.png` (2048×3040) | 32×32 | true overhead 3/4 | CC0 | **Primary** — terrain, monsters, items, heroes |
| **0x72 DungeonTileset v4** | `DungeonTileset/0x72_16x16DungeonTileset.v4.png` (256×256) | 16×16 | side (front-face walls) | CC0 | **Primary** — item silhouettes, palette, sprite compactness |
| **0x72 DungeonTileset II** | `DungeonTilesetII/0x72_DungeonTilesetII_v1.2.png` (512×512) | 16×16 (chars 16×28) | side / oblique | CC0 | **Secondary** — creature designs, palette, animation cadence |
| 0x72 Industrial v2 | `Industrial/industrial.v2.png` (512×512) | 16×16 | side | CC0 | **Skip** — sci-fi genre, near-monochrome palette |
| Medieval Fantasy (Archer/King/Knight) | `MedievalFantasy/*/*.png` | strip frames | side | "free", not CC0 | **Skip** — side-view, license unclear |
| Adafruit sprite sheets | `Adafruit/*.bmp` (48×64, 48×32) | — | — | tutorial assets | **Skip** — too small, unrelated |

The two 0x72 primaries are CC0 by Robert (0x72); Project Utumno is the CC0
Dungeon Crawl Stone Soup supplemental set from OpenGameArt. No attribution
required for any; the chapter README will credit all three anyway.

`DungeonTilesetII/tiles_list_v1` is a machine-readable map of that sheet
(`name x y w h [frames]`) — reuse it directly in `build_tiles.py` if we pull
tiles from set II.

---

## Project Utumno — the overhead backbone

64 cols × 95 rows of 32×32 tiles. Everything is drawn in the top-down 3/4
perspective Ch7 wants. This is the main reference for how Ch7 should *look*.

| Region (approx, top→bottom) | Contents | Feeds |
|---|---|---|
| rows ~0–20 | potions, statues, altars, doors, ore/gem piles, and **dozens of floor + wall textures** (stone, moss, dirt, brick, crystal, lava, wood), decorative floor-edge trims | `terrain.bmp` |
| rows ~20–40 | spell/effect glyphs, scrolls, wands, rings, amulets, food, books — hundreds of **inventory icons** | `objects.bmp`, possible `fx.bmp` |
| rows ~40–65 | the **bestiary** — humanoids, orcs, undead, dragons, elementals, demons, oozes, beasts, in overhead view | `creatures.bmp` |
| rows ~65–95 | **player avatars** (armored humanoids, many classes), then armor / helmets / cloaks / shields, then a large **weapon** block (swords, axes, maces, staves, bows) | `heroes.bmp`, `objects.bmp` |

**Extraction note:** native 32×32. For Ch7's 16×16 grid, downscale 2:1 —
`Image.resize((16,16), NEAREST)` for a crunchy read, or `LANCZOS` then
posterize to the master palette. Utumno tiles are used as **study references
for hand-authoring**, not pasted in wholesale — a 2:1 downscale of detailed
32×32 art rarely survives cleanly at 16×16.

---

## 0x72 DungeonTileset v4 — items & palette

16 cols × 16 rows of 16×16 tiles. Side-view dungeon (brick walls have front
faces), so **not** a terrain reference for Ch7's overhead look — but its
16×16-native item and sprite work is directly on-size.

| Rows/cols (r,c from 0) | Contents | Feeds |
|---|---|---|
| r0–5, c0–5 | brick walls, floors, wooden doors, fountains (r3: red/green/blue), grates, portcullis | palette only (walls are side-view) |
| r0–5, c6–15 | **weapons** — ~20 swords, daggers, spears, war hammer, a bomb | `objects.bmp` |
| r3, c12–15 | banners (red/green/blue/yellow) | `terrain.bmp` decor |
| r6–7 | cabinet, coffin, a **palette swatch strip** (the set's own palette — useful for `cd-e17.3`), bat, cloaked figure, horned demon head | palette; `creatures.bmp` |
| r8–12, c0–5 | **monsters** — skeletons, zombies, goblins, imps, ghosts, slimes (~15–20 single-tile front-facing sprites, some with a 2nd idle frame) | `creatures.bmp` (style) |
| r9–11, c6–10 | lit torches (multi-frame flame), ogre, shadow blob, golden spider/sun beast | `terrain.bmp` (torch), `creatures.bmp` |
| r11–12, c6–10 | potion bottles + vial rack (~5–6 tiles) | `objects.bmp` |
| r8–13, c11–15 | bookshelves (2-wide), dark pillar, **treasure chests** closed/open with gold | `terrain.bmp`, `objects.bmp` |
| r13–15, c6–15 | **heroes** — bust portraits (old man, knight, red/blue wizard) + small full-body sprites (orange/red/blue/green tunics), blue guards | `heroes.bmp` |

---

## 0x72 DungeonTileset II — creature designs & animation cadence

16×16 base, characters 16×28, big monsters 32×32+. Side/oblique view. Value
is the **creature roster and its animation structure**, not the perspective.

- **Player characters:** elf (f/m), knight (f/m), wizard (f/m) — each with a
  4-frame idle, 4-frame run, 1-frame hit. Confirms a sane per-hero frame
  budget if Ch7 later adds animation (`cd-e17.11`).
- **Small monsters** (4-frame idle + run): tiny_zombie, goblin, imp, skeleton,
  muddy, swampy, zombie, ice_zombie, masked_orc, orc_warrior, orc_shaman,
  necromancer, wogol, chort.
- **Big monsters** (32×32+, 4-frame): big_zombie, ogre, big_demon.
- **Terrain** (side-view, palette only for Ch7): wall tops/sides/corners,
  8 floor variants, columns, goo, animated fountains, banners, holes.
- **Items:** knife/sword/hammer/mace/katana/axe/staff set (~20), 4+4 flasks,
  animated chests (empty/full/mimic), coin, skull, crate, UI hearts.

---

## What informs what (consolidated)

| Ch7 sheet | Look/perspective from | Silhouettes & palette from | Notes |
|---|---|---|---|
| `terrain.bmp` | Project Utumno (overhead floors, wall-tops) | Utumno + v4 swatches | walls are wall-*tops*, not front faces; procedural texture generator seeded from Utumno palettes |
| `creatures.bmp` | Utumno bestiary (overhead) | v4 monsters + set II | front-facing, one 16×16 tile each to start |
| `heroes.bmp` | Utumno avatars / v4 heroes | v4 hero sprites | 3 classes, ~12px figure in a 16px cell |
| `objects.bmp` | v4 items (already 16×16) | v4 + Utumno icons | potions, weapons, scrolls, gold, chest, corpse, keys |

## Gaps — no reference covers these well

- **Overhead wall-top tiles at 16×16** — Utumno has them but at 32×32;
  expect to hand-author / procedurally generate the Ch7 wall set.
- **Stairs up/down in overhead 16×16** — sketch from Utumno, hand-author.
- **A cohesive 32-colour master palette** — none of the sets ships one that
  small; `cd-e17.3` builds it by sampling across Utumno + v4 (+ the v4 swatch
  strip as a starting point).

## Additional CC0 sources worth pulling in if gaps bite

Not downloaded — candidates only, to keep `sourceArt/` lean until needed:

- **Kenney "Tiny Dungeon" / "1-Bit Pack" / "Roguelike/RPG pack"** (CC0,
  kenney.nl) — clean 16×16 overhead tiles, good gap-filler for wall-tops and
  stairs.
- **DawnBringer DB16 / DB32 palettes** (free to use) — proven small palettes;
  a fallback if a hand-rolled 32-colour palette from the sets looks muddy.
