# Chapter 7 — Screen Layout Options

Working doc for the `cd-oht.1` decision (layout geometry). Once a layout is
chosen, the result is written into `LAYOUT.md` and drives `cd-oht.2`
(region scaffolding). Background: `VISION.md` (text line top + bottom, map
~2/3, stats ~1/3) and `ART.md` §2 (16×16 tiles, "~14×9 visible").

## The space budget

The PicoSystem screen is **240 × 240**, tiles are **16 px**.

- **Horizontal is a zero-sum trade:** `map width + right column = 240`. Every
  extra map tile (16 px) comes straight out of the stats/inventory column.
- **A hero-centred map needs an odd tile count** so the hero sits on the exact
  middle tile. 9→144 px, 11→176, 13→208, 15→240.
- **One line of `terminalio.FONT`** (the frozen built-in, ~6×14 box) wants
  **~16 px**. A 12 px band clips descenders; going smaller means a bitmap
  font file (DawnLike `SDS_6x6` is in `sourceArt/`, costs a few KB RAM).
- **Half-tile windows** (options D, E): the map TileGrid is drawn 8 px larger
  than its window, offset −8,−8, so the hero lands on the pixel centre and the
  outer ring shows at 50 %. `displayio` has no clip rect, so the 8 px bleed is
  hidden by drawing the opaque HUD bands/column *after* the map group (the
  left bleed is simply off-screen). Edge monsters show half — a free
  "something at the edge of vision" cue.

## Reading the diagrams

```
1 char = 8 px wide   |   1 line = 16 px tall   |   240×240 = 30 chars × 15 lines
#  HUD band (status / message)      .  map floor, full tile
I  stats / inventory column         :  map floor, half-tile rim (clipped 50%)
@  hero (always centred in the map)
```

Monospace stretches every diagram vertically by the same amount, so relative
sizes are honest even if a single box doesn't look square.

---

## A — 9×13 map · full tiles · 6-tile column

```
##############################   status   240 × 16   (1 line)
..................IIIIIIIIIIII
..................IIIIIIIIIIII
..................IIIIIIIIIIII
..................IIIIIIIIIIII
..................IIIIIIIIIIII
..................IIIIIIIIIIII
........@.........IIIIIIIIIIII   map  144 × 208      col  96 × 208
..................IIIIIIIIIIII   9 × 13 tiles        6 × 13 tiles
..................IIIIIIIIIIII   full, hero centred  full panel
..................IIIIIIIIIIII
..................IIIIIIIIIIII
..................IIIIIIIIIIII
..................IIIIIIIIIIII
##############################   message  240 × 16   (1 line)
```

| status | map window | message | map shown | right region |
|---|---|---|---|---|
| 16 | 144 × 208 | 16 | **9 × 13** full | **96 (6 t)** column |

- \+ Simplest: no offset tricks, no clipping, everything tile-aligned.
- \+ Widest persistent column (96 px) — room for a real inventory grid.
- − Map is portrait 9-wide; you see only 4 tiles left/right of the hero.
- − 1-line message band (Ch6-style single line + scroll).

---

## C — 11×11 map · full tiles · 4-tile column

```
##############################   status   240 × 32   (2 lines)
##############################
......................IIIIIIII
......................IIIIIIII
......................IIIIIIII
......................IIIIIIII
......................IIIIIIII
..........@...........IIIIIIII   map  176 × 176      col  64 × 176
......................IIIIIIII   11 × 11 tiles       4 × 11 tiles
......................IIIIIIII   full, hero centred  icon strip +
......................IIIIIIII                       short text
......................IIIIIIII
......................IIIIIIII
##############################   message  240 × 32   (2 lines)
##############################
```

| status | map window | message | map shown | right region |
|---|---|---|---|---|
| 32 | 176 × 176 | 32 | **11 × 11** full | **64 (4 t)** column |

- \+ Square 11×11 map, full tiles, no rendering tricks.
- \+ 2-line status + 2-line message log.
- − Column down to 64 px: an icon strip + `HP 12/12`-width text, no grid.
  Numeric stats move up into the status bar.

---

## D — 11×11 shown in a 160 window · half-tile rim · 5-tile column

```
##############################   status   240 × 32   (2 lines)
##############################
::::::::::::::::::::IIIIIIIIII
:..................:IIIIIIIIII
:..................:IIIIIIIIII
:..................:IIIIIIIIII
:..................:IIIIIIIIII
:........@.........:IIIIIIIIII   window 160 × 160     col  80 × 160
:..................:IIIIIIIIII   shows 11 × 11        5 × 10 tiles
:..................:IIIIIIIIII   (9 full + half rim)  usable panel
:..................:IIIIIIIIII   hero centred
::::::::::::::::::::IIIIIIIIII
##############################   message  240 × 48   (3 lines)
##############################
##############################
```

| status | map window | message | map shown | right region |
|---|---|---|---|---|
| 32 | 160 × 160 | 48 | **11 × 11** (half rim) | **80 (5 t)** column |

- \+ 11-tile map awareness in only 160 px → 80 px column *and* a 3-line log.
- \+ Best balance for a "HUD-heavy" screen.
- − Needs the −8,−8 offset + draw-order discipline (see space budget).
- − Outer ring of tiles is half-shown.

---

## E — 13×13 shown in a 192 window · half-tile rim · 3-tile rail

```
##############################   status   240 × 16   (1 line)
::::::::::::::::::::::::IIIIII
:......................:IIIIII
:......................:IIIIII
:......................:IIIIII
:......................:IIIIII
:..........@...........:IIIIII  window 192 × 192      rail 48 × 192
:......................:IIIIII  shows 13 × 13         3 × 12 tiles
:......................:IIIIII  (11 full + half rim)  icons + HP text
:......................:IIIIII  hero centred          only
:......................:IIIIII
:......................:IIIIII
::::::::::::::::::::::::IIIIII
##############################   message  240 × 32   (2 lines)
##############################
```

| status | map window | message | map shown | right region |
|---|---|---|---|---|
| 16 | 192 × 192 | 32 | **13 × 13** (half rim) | **48 (3 t)** rail |

- \+ 13-tile awareness — big field of view.
- − Right side is a 48 px *rail*, not a panel: equipped-item column + one
  line like `HP 12/12`. No inventory grid.
- − Half-tile rendering; contradicts `VISION.md`'s "~1/3 stats region".

---

## F — 13×13 full width · no persistent panel · inventory is a screen

```
##############################   status  240 × 16   HP · depth · turn · $
..............................
..............................
..............................
..............................
..............................
..............................
...............@..............   map  240 × 208
..............................   15 × 13 tiles, full width, hero centred
..............................
..............................
..............................
..............................
..............................
##############################   message  240 × 16   the log
```

Inventory / stats is a **toggle overlay** (an extra `ModeStack` mode, like
menu/diag — bind to `AUX_X` or a chord):

```
##############################
#  INVENTORY / STATS         #
#                            #
#  full-screen when open,    #   240 × 240 overlay
#  play frozen behind it     #
#                            #
##############################
```

| status | map window | message | map shown | right region |
|---|---|---|---|---|
| 16 | 240 × 208 | 16 | **15 × 13** full | **none** — overlay screen |

- \+ Biggest map by far; no rendering tricks; play screen is dead simple.
- \+ Inventory screen can be as rich as you want (full 240×240).
- − No at-a-glance stats/inventory — everything not in the two text lines
  needs a button press. Breaks `VISION.md`'s persistent-panel intent.

---

## G — true 13×13 map · full tiles · 32 px icon rail

```
##############################   status  240 × 16   HP · depth · turn · $
..........................IIII
..........................IIII
..........................IIII
..........................IIII
..........................IIII
..........................IIII
............@.............IIII   map  208 × 208      rail  32 × 208
..........................IIII   true 13 × 13 full   2 × 13 tiles
..........................IIII   tiles, hero centred equipped icons +
..........................IIII   no rendering trick  HP bar + status
..........................IIII                       icons; no text
..........................IIII
..........................IIII
##############################   message  240 × 16   the log
```

| status | map window | message | map shown | right region |
|---|---|---|---|---|
| 16 | 208 × 208 | 16 | **13 × 13** full | **32 (2 t)** icon rail |

- \+ Biggest *full-tile* square map — a genuine 13×13, no −8,−8 offset, no
  clip-by-draw-order, everything tile-aligned.
- \+ Keeps a sliver of always-on state (equipped gear, an HP bar, status
  icons) — you don't lose *all* the glance-able info like F.
- − 32 px is icons only, no text — HP/depth/turn/gold live in the status
  line. Full inventory still wants a toggle screen (as in F).
- − 1-line message band.

---

## Comparison

| | status | map window | msg | map shown | persistent right region | half-tile? | notes |
|---|---|---|---|---|---|---|---|
| **A** | 16 | 144×208 | 16 | 9×13 | 96 px (6 t) column | no | simplest; portrait map |
| **C** | 32 | 176×176 | 32 | 11×11 | 64 px (4 t) column | no | square map; skinny column |
| **D** | 32 | 160×160 | 48 | 11×11 | 80 px (5 t) column | yes | best HUD balance |
| **E** | 16 | 192×192 | 32 | 13×13 | 48 px (3 t) rail | yes | big FOV; rail not panel |
| **F** | 16 | 240×208 | 16 | 15×13 | none (toggle screen) | no | max map; no glance-able stats |
| **G** | 16 | 208×208 | 16 | 13×13 | 32 px (2 t) icon rail | no | true 13×13, no tricks; icons only |

Map field of view (tiles the hero can see around itself), and column
character capacity (`terminalio` ≈ 6 px/char):

| | tiles each side (H × V) | column text width |
|---|---|---|
| A | 4 × 6 | ~16 chars |
| C | 5 × 5 | ~10 chars |
| D | 5 × 5 (+half) | ~13 chars |
| E | 6 × 6 (+half) | ~8 chars |
| F | 7 × 6 | n/a |
| G | 6 × 6 | icons only (~5 chars) |

## What to decide

The axis is **persistent HUD vs map size**:

- Want a real always-visible inventory/stats panel → **A** or **D**
  (D if you also want the bigger map and a fat message log).
- Want maximum map and are fine with inventory-on-a-button → **F**, or **G**
  to keep a thin always-on icon rail (equipped gear + HP bar) and a true,
  trick-free 13×13.
- **C** and **E** are the middle; both make the right region too thin to be
  a proper panel, so they're only worth it if the icon-strip/rail is genuinely
  all you want on screen.

Recommendation: **D** if the persistent panel matters (it's the `VISION.md`
intent, best balance), **F** if "see more dungeon" wins.
