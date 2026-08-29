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

---

# Extended survey (cd-e17.13)

A wider pass over [opengameart.org](https://opengameart.org/) and
[itch.io](https://itch.io/game-assets) for open-source 2D roguelike art, to
broaden the reference base beyond the four sets in `sourceArt/`. Nothing here
is downloaded — these are candidates, ranked by fit to the Ch7 spec
(16×16 uniform grid, true overhead, front-facing figures — see `ART.md` §1–2).

Chris flagged the original hunt (~6 yrs ago) drew mostly from these two sites,
plus [oco.itch.io](https://oco.itch.io/) and [0x72.itch.io](https://0x72.itch.io/).

**Status:** candidates #1–5 and #7 are now downloaded into `sourceArt/`
(`DawnLike/`, `TopDownDungeon/`, `BuchDungeon/`, `KenneyRoguelike/`,
`KenneyTinyDungeon/`, `DarkDungeon/`) — each with a `README.md` recording
author, source URL, and license. **CC-BY attribution owed if their pixels
ship:** DawnLike → *DawnBringer* (palette) + *DragonDePlatino*, CC-BY 4.0;
TopDownDungeon → *Michele "Buch" Bucelli* + sponsor *Abram Connelly*, CC-BY 3.0.
The rest (#3 BuchDungeon, #4/#5 Kenney, #7 Kosina) are CC0.

## Summary — ranked

| # | Source | Creator | License | Native tile | Perspective | Best for | Verdict |
|---|---|---|---|---|---|---|---|
| 1 | **DawnLike — Universal Rogue-like tileset v1.81** ([OGA](https://opengameart.org/content/dawnlike-16x16-universal-rogue-like-tileset-v181)) | DragonDePlatino + DawnBringer | **CC-BY 4.0** (must credit DawnBringer for the palette) | 16×16 | true overhead, "isometric-style" wall blocks | terrain, wall-tops, stairs, monsters, heroes, items, UI — *everything* | **Primary candidate** — closest match to `ART.md` §1 at native size |
| 2 | **Top down dungeon tileset** ([OGA](https://opengameart.org/content/top-down-dungeon-tileset)) | Michele "Buch" Bucelli | **CC-BY 3.0** (credit Buch + sponsor Abram Connelly) | 16×16 (best at 2×) | Zelda-like top-down (some known perspective drift) | **wall-tops + stairs**, doors, chests, barrels, decor | **Pull** — directly fills the two cd-e17.2 gaps |
| 3 | **Dungeon tileset** ([OGA](https://opengameart.org/content/dungeon-tileset)) | Buch (water by surt) | **CC0** | 16×16 (8×8 subdividable) | orthographic top-down | floors, walls, wooden doors, stairs, water/waterfall; basic mage/knight/dwarf | **Pull** — CC0, on-spec; note tiles carry offset/spacing, not a tight grid |
| 4 | **Roguelike/RPG pack (1,700+ tiles)** ([OGA](https://opengameart.org/content/roguelikerpg-pack-1700-tiles)) | Kenney (16× conv. by Lynn Evers) | **CC0** | 16×16 | top-down overworld | floors, walls, roofs, flora, doors, furniture, **UI panels/buttons** | **Pull** — env + HUD widgets (feeds `cd-oht`); no creatures/items |
| 5 | **Tiny Dungeon** ([kenney.nl](https://kenney.nl/assets/tiny-dungeon)) | Kenney | **CC0** | 16×16 | top-down | ~130 files: dungeon/sewer tiles, characters, monsters, items | **Pull** — clean all-round CC0 gap-filler |
| 6 | **1-Bit Pack** ([kenney.nl](https://kenney.nl/assets/1-bit-pack)) | Kenney | **CC0** | 16×16 (also 8×8) | top-down + platformer | 1078 monochrome tiles incl. dungeon/interior | **Reference only** — silhouette/readability study; palette-agnostic |
| 7 | **16x16 Dark Dungeon Tileset** ([itch](https://kosinaz.itch.io/16x16-dark-dungeon-tileset)) | Zoltan Kosina | **CC0** | 16×16 | top-down | darker floor, centred walls, **4 trap variants**, 8 fountains | **Pull if traps/fountains needed** — built on 0x72 II, palette-compatible with our set II ref |
| 8 | **Micro Roguelike** ([kenney.nl](https://kenney.nl/assets/micro-roguelike)) | Kenney | **CC0** | 8×8 | top-down, 1-bit | terrain, characters, elements | **Reference only** — too small for the grid; icon/mini-map study |
| 9 | **Pixel Crawler — Topdown 16x16** ([itch](https://anokolisa.itch.io/free-pixel-art-asset-pack-topdown-tileset-rpg-16x16-sprites)) | Anokolisa | **custom "permanently free"** — links a terms doc, *not* a standard CC licence; read before any use | 16×16 | top-down | 500+ sprites: dungeon/forest/cave tiles, **3 heroes**, 8 enemies (skeleton/orc), 50+ weapons, crafting stations | **Study only until licence confirmed** — 3 heroes maps to our 3 classes |
| 10 | **µFantasy Tileset** ([itch](https://0x72.itch.io/)) | 0x72 (Robert) | free; **licence unconfirmed** (0x72's dungeon sets are CC0 — verify this one) | ~16×16 | top-down | outdoor/fantasy overworld tiles | **Hold** — only relevant if Ch7 adds above-ground levels |
| — | **Medieval Fantasy Character Packs 1–7** ([oco.itch.io](https://oco.itch.io/)) | oco / OcO | free, licence not stated | strip frames | **side view** | animated humanoids | **Skip** — same family as the repo's `MedievalFantasy/` set; side-view breaks `ART.md` §1 |

Context set (not a new find): **Dungeon Crawl Stone Soup 32×32**
([OGA](https://opengameart.org/content/dungeon-crawl-32x32-tiles), CC0, ~3000
tiles + a ~3000-tile supplemental) — our `sourceArt/DungeonCrawl/ProjectUtumno_full.png`
is the supplemental set. The full CDS main tilesheet is a second CC0 well of
overhead terrain/monster/item art in the same perspective, if Utumno runs thin.

## Gaps from cd-e17.2 — revisited

| Gap | Status | Source(s) |
|---|---|---|
| Overhead wall-top tiles at **native 16×16** | **Found** (was: hand-author only) | DawnLike (#1), Buch "Top down dungeon tileset" (#2), Kenney Roguelike/RPG pack (#4); 0x72 "16x16 Dungeon Tileset" v4 already on hand also has them |
| **Stairs up/down** overhead 16×16 | **Found** | Buch "Top down dungeon tileset" (#2), Buch "Dungeon tileset" (#3), DawnLike (#1), Kenney Tiny Dungeon (#5) |
| Cohesive small master palette | **Closed** by `cd-e17.3` (64-slot / 40 populated). DawnLike renders a *complete* roguelike on the 16-colour DB16 palette — good evidence our 40 slots are generous, and DB16/DB32 remain the fallback |

Net: hand-authoring the Ch7 wall/stair set is still likely (palette + style
fit), but there are now several native-16 overhead references to sketch from
instead of only 2:1 downscales of Utumno's 32×32 tiles.

## Perspective & palette notes

- **True-overhead references** (safe to study for the Ch7 look): DawnLike, both
  Buch sets, Kenney Roguelike/RPG + Tiny Dungeon, Kosina, Project Utumno, CDS.
- **Off-spec** (side / oblique — silhouette & anim-cadence value only):
  oco packs, the repo's `MedievalFantasy/`, 0x72 v4 walls, 0x72 II.
- **Palette lineage:** DawnLike → DB16; several itch sets → 0x72 II's palette.
  Our master palette (`cd-e17.3`) is sampled from Utumno + 0x72 v4, so DawnLike
  colours will need a remap, not a paste.

## Recommended next action

Pull #2 (Buch top-down) and #3 (Buch dungeon, CC0) into `sourceArt/` first —
smallest, most on-point for the wall-top/stair gap. Add **DawnLike** as the
big overhead study reference, tracking its CC-BY 4.0 attribution in the
chapter README alongside the existing credits. Treat #5/#6 as CC0 safety net.
Everything on itch with an unconfirmed or custom licence (#9, #10) stays a
look-don't-copy study until the terms are read.
