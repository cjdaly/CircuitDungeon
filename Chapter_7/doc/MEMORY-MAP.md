# Chapter 7 — RP2040 Memory Map

Where the RAM goes on the PicoSystem, why the margin is thin, and which
levers actually move it. Companion to the RAM work tracked in `cd-yl4`
(crash fixes, closed) and `cd-dsc.6` (the ongoing perf & RAM pass).

All figures are approximate — from on-device `DiagMode` readings and the
`boot.py` serial log, not a static analysis. Treat them as "which bucket is
big", not "this bucket is 4,096 bytes".

---

## 1. The frame

```
┌─────────────────────────────────────────── RP2040: 264 KB SRAM ───────────┐
│                                                                            │
│  ~105 KB   CircuitPython core, C stack, USB buffers, display row buffers    │
│            — gone before main.py runs. Not ours to fight.                   │
│                                                                            │
│  ~159 KB   MicroPython heap  ← the entire budget we manage                  │
│            (DiagMode "heap" = free + used)                                  │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

There is **no full framebuffer in the heap.** The PicoSystem's ST7789 is
refreshed in horizontal slices from a small buffer on the C side; a 240×240×2
framebuffer (115 KB) would not fit alongside everything else and does not
exist as a Python object. That cost is already inside the ~105 KB above.

CircuitPython 10.2.1, board id `pimoroni_picosystem`.

---

## 2. The heap, bucket by bucket (~159 KB)

| Bucket | Approx | Lifetime | Notes |
|---|---:|---|---|
| CircuitPython baseline heap objects | ~7 KB | boot → forever | interned strings, module table, etc. |
| **Game module bytecode** — 12 modules imported at boot | ~28–30 KB | boot → forever | `main engine modes world generator input fov ai hardware metrics log` + `board`. Compiled `.py` lives on the heap. |
| **Adafruit library bytecode** — `imageload`, `display_text/__init__`, `bitmap_label`, `adafruit_ticks` | ~15 KB | first `Game()` → forever | imported lazily via `util` inside `PlayMode.__init__` |
| `terminalio` font glyph bitmap | ~4 KB | first label → forever | |
| **Generator BFS scratch** — `generator._DIST` (2,304 B) + `_QUEUE` (4,608 B) | ~7 KB | import → forever | module-level `bytearray` / `array('H')`, allocated once when the heap is pristine. Deliberate: a fragmented mid-game heap cannot hand out a fresh contiguous 4 KB block, and descent's `generate()` was OOMing exactly there (`cd-yl4`). |
| **Tile sheets** — `terrain / heroes / creatures / objects .bmp` | ~16 KB | `PlayMode.__init__` → play | each: a 2 KB `Bitmap` (128×16 @ 8bpp) + a ~2 KB 256-entry `Palette`. All four are preloaded up front so the first `objects.bmp` load doesn't land mid-fight (`cd-yl4`). |
| **HUD labels** — 2 fixed-width `bitmap_label`s (status + message) | ~4 KB | play | fixed-width format so the `Bitmap` is reused across turn-counter rollover instead of reallocated (`cd-yl4`) |
| **DiagMode page** — one lazy whole-screen `bitmap_label` | **~12 KB** (measured on-device 2026-09-04, 4× avg) | **only after diag is first opened** | `cd-dsc.6.3`: replaced the 14 separate line-labels (~21.5 KB) with one fixed-geometry page label — `_MAX_LINES` (12) rows × `_LINE_W` (36) cols, every row space-padded, so `.text =` rewrites the Bitmap in place (repaint-after-first ≈ 0.1 KB). Lazy build is `MemoryError`-guarded → if the heap can't spare it, diag no-ops and `.text` still reports. Still an observer effect (~12 KB to open the RAM screen), just a smaller one. |
| **World state** — one level's worth | ~8 KB | play, rebuilt per level | grid: 48 `bytearray(48)` rows ≈ 2.3 KB data + object overhead ≈ 3–4 KB · FOV masks `visible`+`explored` = 288 B each · `actors` list of ~4–10 dicts ≈ 2–3 KB · `log` ≤ 24 strings ≈ 1 KB · `rooms` ~10 tuples |
| displayio groups, terrain `TileGrid` (13×13), actor sprite `TileGrid`s, first-paint refresh buffers | ~5–10 KB | play | |
| **Free margin** | see §3 | | |

### Serial-log checkpoints (`boot.py` / `main.py`)

Measured 2026-09-04, current tree (48×48 levels + `cd-dsc.6.1` step A +
`cd-dsc.6.3` diag + menu removal):

```
Ch7 boot    free ~123 KB    imports + generator scratch done
Ch7 level   free ~118 KB    _new_game(): generate() + world + spawns  (~5 KB)
Ch7 ready   free ~ 76 KB    Game() built: 4 sheets, scene, HUD labels (~42 KB)
                            + open diag → ~12 KB → ~62 KB
```

`ready` free progression: ~48 KB (pre-48×48) → ~64 KB (post-shrink) →
~73 KB (+ step A palettes, ~9 KB) → ~76 KB (− menu stub, ~2.7 KB).
Opening diag now costs ~12 KB, was ~21.5 KB. (Hard-reset readings; a serial
soft-reboot lands ~2 KB lower — the RP2040 heap isn't fully cleared.)

Historic drift, for context:

- `146,896 → 134,000` at boot when `generator.py` + `metrics.py` + a fuller
  `world`/`main` landed (~13 KB of code).
- `134,000 → 115,200` at boot when `bitmap_label` + `adafruit_ticks` were
  added **and** the generator moved its BFS scratch to module level (the
  ~7 KB resident is most of that drop).

---

## 3. Transient spikes — what actually caused the crashes

These are momentary allocations, not footprint. On a **non-compacting GC**
(`gc.collect()` frees but never moves objects) a fragmented heap can be 30 KB
"free" and still unable to serve one contiguous 4 KB request.

| Spike | Peak | Status |
|---|---|---|
| **Descent** — `generate()` building a new grid while the old level was still live | ~19 KB | **fixed**: `engine._change_level` nulls `world` / `play.world` / `diag.world` and `gc.collect()`s *before* `_new_level()`; BFS buffers are resident and reused; `_spawn_pool` rejection-samples instead of materialising a ~1,500-tuple candidate list |
| **First frame** — displayio's first `refresh()` + first `gc.collect()` | one-time ~7.8 s stall | expected; not a memory failure |
| **Opening DiagMode** — the page bitmap | ~13 KB, needs it contiguous | **mitigated** (`cd-dsc.6.3`): one lazy page label, `MemoryError`-guarded → diag no-ops, game lives; was 14 line-labels at ~21.5 KB |
| **`label.Label` per-turn churn** — old status line freed/realloc'd ~38 glyph `TileGrid`s every turn; ~1,000 turns shredded the heap until an 84-byte alloc failed | slow death | **fixed**: `bitmap_label` + fixed-width format |
| **`_paint_terrain` tuple churn** — `tg[col,row]` built 169 throwaway tuples/turn | fragmentation | **fixed**: flat `tg[i]` index |
| **`input._trace` ring** — 1 alloc per keypress + ~2 KB resident | fragmentation | **fixed**: trace removed entirely (`cd-dsc.6`) |

---

## 4. The unexplained part

Pre-RAM-pass, depth 7 / turn 1153 (~640 s, 7 descents): `free 22 KB`,
`free == free_low`. Post-RAM-pass, depth 4 / turn 342: `free 57 KB`,
`free == free_low` (diag was opened during the run, so ~12 KB of the
~76 → 57 KB drop is the diag page). No crash either time. The low-water
mark still tracks the current free number — the heap is **slowly
declining**, not oscillating around a steady state — but from a much
healthier start. Whether the decline flattens deeper in a run is the open
question; needs a longer playtest.

Open suspects (`cd-dsc.6`):

- **`World.refresh_fov()` defines two closures** (`_blocked`, `_mark`) on
  every hero move — allocation + fragmentation each turn.
- **Something retained across `_change_level`** — the descent free-print
  (`Ch7 descend depth N free A -> B`) is instrumented for exactly this;
  watch whether `B` trends down descent-over-descent.
- **Fragmentation is permanent** here — even a perfect leak fix leaves the
  heap more perforated after 1,000 turns than at `ready`.

---

## 5. Levers, by payoff

### Big

1. **Right-size the sheet palettes** — **done 2026-09-04 (`cd-dsc.6.1`
   step A), confirmed on-device.** Each `.bmp` shipped a padded 256-entry
   palette table, so `adafruit_imageload` built a `displayio.Palette(256)`
   per sheet for a 40-colour master palette. `tilelib.Palette.flat_table()`
   now emits exactly 40; `biClrUsed` 256 → 40, `len(pal)` on device is 40,
   a sheet load is ~3.0 KB (was ~5 KB). **~9 KB** back at "ready".
   Index-stable — no engine or `tiles.json` change.
2. **Rework DiagMode** — **done 2026-09-04 (`cd-dsc.6.3`).** Was 14
   separate `bitmap_label` line-labels at ~21.5 KB; now one lazy
   fixed-geometry page label (12 rows × 36 cols, space-padded) that
   rewrites its Bitmap in place. Measured on-device (4× avg): ~12 KB to
   open, ~0.1 KB per repaint after. `MemoryError`-guarded — a heap too
   tight to open diag no-ops instead of crashing. **~9 KB** saved when
   diag opens.
3. **Remove the menu stub** — **done 2026-09-04.** `_StubOverlay` /
   `MenuMode` was a lone "MENU" label built eagerly in `Game.__init__`,
   ~2.4 KB for no gameplay (the real menu is `cd-e3p.13`). Gone, along
   with the A+B → "menu" chord (so A now fires with no chord-window
   delay). The `ModeStack` overlay-dict seam stays; re-adding is one
   entry + one chord. **~2.7 KB** back at "ready" (confirmed: 72.9 → 75.6).
4. **Merge the four tile sheets into one** — `cd-dsc.6.1` step B. All 21
   tiles in one 128×48 `.bmp` + one `Palette`: ~2 KB less bitmap and 4
   Palette objects collapse to 1 (~2 KB now they're 40-entry), so **~4 KB**
   on top of step A. Needs a global tile renumber + `*_TILE` constant
   rewrites in `world.py` / `generator.py`, the `actor["sheet"]` key gone,
   and test updates. Weigh the churn against the 4 KB — the per-turn churn
   (item 5) is the better spend.

### Medium

5. **Cut per-turn churn** — hoist `refresh_fov`'s closures to module-level
   functions taking `world` explicitly; they're re-created 1×/turn now.
   This targets the slow depth-over-depth decline (§4) directly.
6. **Reconsider `bitmap_label` for the HUD.** Its win was killing per-turn
   `label.Label` churn — that's fixed now by the fixed-width format. A
   `label.Label` with a change-gate might have a smaller resident footprint
   *and* drop the `adafruit_ticks` dependency. Measure both.

### Small / hygiene (flash, not RAM — see §6)

7. `label.mpy`, `outlined_label.mpy`, `scrolling_label.mpy`, `text_box.mpy`
   in `lib/adafruit_display_text/` — nothing imports them. **Removed
   2026-09-03.**
8. `gif/jpg/png` + `pnm/` in `lib/adafruit_imageload/` — we only ever
   `load()` `.bmp`. *Left in place* — `load()` imports the format submodule
   lazily so they cost nothing, and the risk/reward on hand-editing a
   vendored lib tree is poor.
9. `level_loader.py` (tests only) and `tiles/{tiles,palette}.json` +
   `tiles/palette.py` (build artifacts) — **done 2026-09-03**: removed from
   the device and added to `deploy.sh`'s exclude list so `--delete` keeps
   them off.

---

## 6. Device files: flash vs RAM

**Deleting files from `/Volumes/CIRCUITPY` does not free heap.** Only
*imported* modules cost RAM; an unused `.mpy` or a stray `.json` on the
filesystem costs only flash. And flash is not tight — the CIRCUITPY
partition is 15 MB with ~334 KB used.

So the §5 "hygiene" items are worth doing for tidiness and to prevent an
accidental import, but they will not move the `free` number on the diag
screen. The RAM budget is won in code: DiagMode's footprint (§5.2), the menu
stub (§5.3), sheet/palette footprint (§5.1, §5.4), and per-turn churn (§4,
§5.5).

macOS `._*` AppleDouble files and `.Trashes` / `.fseventsd` on the drive are
harmless junk from Finder copies — CircuitPython ignores dot-prefixed names
for imports. Cleaned 2026-09-03 along with the four unused
`adafruit_display_text` variants (`label`, `outlined_label`,
`scrolling_label`, `text_box` — only `bitmap_label` is imported); it changed
nothing at runtime, as expected.
