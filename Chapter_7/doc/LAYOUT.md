# Chapter 7 — Screen Layout

Resolves bead `cd-oht.1`. Governs epic `cd-oht` (screen layout) and the
`display.groups` scaffolding in `modes.PlayMode`. Option comparison and the
reasoning are in [`LAYOUT-OPTIONS.md`](LAYOUT-OPTIONS.md) (chosen: **G**).

## 1. Regions — PicoSystem 240 × 240

```
 x0                                    x207 x239
y0  ┌────────────────────────────────────┬────┐
    │ status line            (240 × 16)  │    │   1 terminalio line
y16 ├────────────────────────────────────┼────┤
    │                                    │    │
    │                                    │ ic │
    │        map viewport                │ on │
    │        208 × 208  =  13 × 13 tiles  │ ra │
    │        hero locked to tile (6,6)    │ il │
    │                                    │ 32 │
    │                                    │×208│
    │                                    │    │
y223├────────────────────────────────────┼────┤
    │ message line           (240 × 16)  │    │   1 terminalio line
y239└────────────────────────────────────┴────┘
```

| Region | origin (x, y) | size | notes |
|---|---|---|---|
| status line | (0, 0) | 240 × 16 | full width, over the rail too |
| **map viewport** | (0, 16) | **208 × 208** | **13 × 13** tiles, 16 px each |
| icon rail | (208, 16) | 32 × 208 | 2 tiles wide × 13 tall |
| message line | (0, 224) | 240 × 16 | full width |

208 + 32 = 240; 16 + 208 + 16 = 240. **True full tiles** — no half-tile
window, no `displayio` offset/clip tricks (that ruled out options D/E).

## 2. Constants

```python
TILE      = 16
MAP_TILES = 13                     # odd → hero on the exact centre tile
MAP_PX    = MAP_TILES * TILE       # 208
BAND_H    = TILE                   # 16 — one terminalio line
RAIL_W    = 240 - MAP_PX           # 32
# regions, from display size (240×240 assumed):
#   status  : (0, 0, W, BAND_H)
#   map     : (0, BAND_H, MAP_PX, MAP_PX)
#   rail    : (MAP_PX, BAND_H, W - MAP_PX, MAP_PX)
#   message : (0, BAND_H + MAP_PX, W, BAND_H)
```

`MAP_TILES = 13` is the fixed choice (hero-centring needs it odd). On a
non-240 screen the rail absorbs the horizontal remainder and the map keeps
`(H - 32) // 16` rows — but Ch7 targets the PicoSystem, so treat 240 × 240 as
the spec.

## 3. Map viewport & camera

- Viewport is **13 × 13 tiles**. The hero is drawn at viewport tile **(6, 6)**
  — screen pixel centre (104 + 0, 120 + 0)-ish.
- Camera follows the hero and **clamps to the level bounds** (Ch6
  `update_camera` style):
  `cam = clamp(hero - 6, 0, level_dim - 13)`. Near a level edge the hero
  drifts off-centre rather than showing out-of-bounds — standard roguelike.
- Implies **levels are ≥ 13 × 13 tiles** (a constraint for `cd-dsc.1`); a
  smaller level just never scrolls on that axis.
- Movement is an instant tile snap (`ENGINE.md` §1.4) — the camera snaps with
  it, no smooth scroll.
- **Fog of war** (`cd-oht.6`, `ENGINE.md` §8): `_paint_terrain` draws a cell
  only once `world.is_explored(x, y)` — unseen cells are `VOID_TILE`
  (wall-top), so the level reads as solid rock until the hero uncovers it.
  `_render` hides any actor outside `world.is_visible`. Terrain repaints after
  every resolved turn, not just camera moves.

## 4. Text — status & message lines

- Font: **`terminalio.FONT`** (frozen built-in, ~6 px advance → ~40 chars
  across 240 px, ~10 px glyph height in the 16 px band). Zero load/RAM cost.
  A bitmap font (DawnLike `SDS_8x8` is in `sourceArt/`) is a later style call,
  not now.
- **Status line** (`cd-oht.3`, done): `PlayMode._paint_status()` writes
  `"HP h/max  Dep d  Turn t  Gold g"` to the top band, **fixed-width** so the
  string's pixel box never changes size. Repaint is gated on a
  `(hp, max_hp, depth, turn, gold)` signature, but the turn moves every turn
  so it repaints every turn anyway — hence (a) the labels are
  `bitmap_label.Label` (one `Bitmap`, redrawn in place; `label.Label` freed +
  rebuilt N glyph TileGrids each time and shredded the heap over ~1000 turns,
  `cd-yl4`) and (b) the fixed width lets `bitmap_label` reuse its bitmap
  instead of reallocating. Turn count is a running total carried across
  descents, not per-level.
- **Message line** (`cd-oht.4`): the latest log line; scroll horizontally when
  longer than the band (Ch6 already has the HUD-scroll mechanism). One line
  only — a fuller scrollback is the toggle screen's job (§6) if it's built.

## 5. Icon rail (`cd-oht.5`)

32 px = 2 tiles wide, 13 tall. **Icons / bars only — no text.** Reserved for:

- equipped-item icons (weapon, armour, and 1–2 more slots) at the top,
- a vertical **HP bar** (coloured fill),
- status-effect icons below.

`cd-oht.5` was "stats/inventory *panel* rendering" — Option G shrinks it to
this rail. Full inventory / detailed stats is **not** on the play screen.

## 6. Expansion — toggle overlay screen  *(deferred)*

Inventory, a full character sheet, and a message-log scrollback are a
**full-screen overlay mode** (a `ModeStack` mode like `menu` / `diag` —
`ENGINE.md` §4), reached by a button or chord (binding TBD). Play freezes
behind it; no game turn passes on open/close.

Not built now — added **only if the game needs it** (`cd-oht.7`). The play
screen deliberately ships without it.

## 7. Child beads

| Bead | Region | |
|---|---|---|
| `cd-oht.2` | region scaffolding + 13×13 terrain viewport + clamped camera | done |
| `cd-oht.3` | status line rendering | done |
| `cd-oht.4` | message line + horizontal scroll | |
| `cd-oht.5` | icon rail (equipped / HP bar / status icons) | |
| `cd-oht.6` | map viewport fog of war — `_paint_terrain` uses `world.is_explored`, `_render` uses `world.is_visible` (§3). Dim-vs-lit shading still needs a dim tile (`cd-e17.5`) | mostly done |
| `cd-oht.7` | *(deferred)* inventory / detail toggle overlay | |
