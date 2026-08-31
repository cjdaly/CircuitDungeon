# Chapter 7 — Procedural Level Generation

Resolves bead `cd-dsc.1`. Governs epic `cd-dsc`. Sections marked *(open)* are
deferred to the bead that owns them.

## 1. Approach — room + corridor

Classic Rogue: scatter non-overlapping rectangular rooms, tunnel corridors
between them, guarantee connectivity, place stairs.

**BSP stays open.** The generator's public entry point is stable:

```python
# game/generator.py
def generate(seed, depth):
    """-> a level dict (§7). Deterministic for a given (seed, depth)."""
```

Only one internal function picks the layout — `_rooms_and_corridors(rng)` →
`(grid, rooms)`. A `_bsp_layout(rng)` with the same return shape can replace
it later without touching stairs, spawning, or engine integration. Revisit
BSP if rooms come out too sparse or clumped.

## 2. Level parameters

| | value | note |
|---|---|---|
| level size | **64 × 64** tiles | fixed for v1; depth-scaled size is a `cd-dsc.6` tweak |
| grid storage | one `bytearray` per row | 64 B/row × 64 = **4096 B**; trivial vs 264 KB SRAM |
| rooms per level | ~9–16 (tunable) | rejection-sample; give up after K tries per room |
| room size | 4–11 per side (tunable) | 1-tile buffer enforced between rooms |
| corridors | 1-tile wide, orthogonal L-bends | composes with 4-way movement (`ENGINE.md` §1.3) |

Tile indices (`game/tiles/tiles.json`): room floor = **1** (flagstone),
corridor floor = **0** (dirt) — free visual variety; walls = **2** (wall-top),
down-stairs = **4**, up-stairs = **5**. Stairs are walkable floor.

The grid starts all-wall (2); rooms and corridors carve floor.

## 3. Generation steps

1. `random.seed(run_seed + depth)` (§6).
2. Fill the 64×64 grid with wall (2).
3. **Rooms:** for each of ~9–16 attempts, roll a rect within bounds, reject if
   it (±1) overlaps an existing room; else carve flagstone (1) and append
   `(x, y, w, h)` to `rooms`.
4. **Spine:** for consecutive rooms in `rooms` order, carve an L-bend dirt (0)
   corridor between their centres (random H-first / V-first). Guarantees a
   connected graph.
5. **Loops:** carve 1–2 extra corridors between random room pairs (kills the
   single-corridor-of-doom feel).
6. **Stairs:** up-stairs (5) in `rooms[0]` (the entry room); down-stairs (4)
   in the room farthest from it. *(v1: farthest by centre distance; BFS over
   the carved floor is more correct — `cd-dsc.3`.)*
7. **Spawn pool:** collect ~40 random floor tiles that are not in the entry
   room and not a stair tile → `spawn_points` (§5).

Connectivity + stairs detail is `cd-dsc.3`; a real BFS reachability check
(and repair) lives there.

## 4. Feature set — minimal for v1

**In:** rooms, corridors, up/down stairs. That's it.

**Deferred** (the `rooms` list makes each easy to add — tag a room, swap a
tile):

- doors / locked doors + keys — needs a door tile in the art + engine
  open/close interaction
- water, lava, traps — hazard tiles + engine effects
- special rooms — vault / shop / monster nest
- depth-scaled level size / theming

## 5. Spawn tables

The generator returns *positions* (`spawn_points`); `cd-dsc.4` fills them from
tables, scaled by `depth`.

```python
# game/spawns.py  — module-level data, no classes
MONSTERS = [   # (creatures.bmp tile, name, weight, min_depth, max_depth)
    (1, "rat",      10, 1, 4),
    (0, "slime",     8, 1, 6),
    (3, "bat",       6, 2, 8),
    (2, "skeleton",  5, 3, 99),
    (4, "goblin",    4, 3, 99),
]
ITEMS = [ ... ]   # same shape, objects.bmp tiles
```

- **Count** scales with depth: `n_monsters ≈ clamp(4 + 2*depth, 6, 24)`,
  `n_items ≈ clamp(2 + depth, 3, 10)` (starting formulas; `cd-dsc.4` tunes).
- **Roster** filtered to `min_depth ≤ depth ≤ max_depth`, then weighted-random.
- **Placement:** consume `spawn_points` — never the entry room, never a stair
  tile, one entity per tile.

## 6. Seed & reproducibility

`random.seed(run_seed + depth)`, generate the **whole** level, then stop
touching the RNG for generation. CircuitPython's `random` is module-level
only (no `random.Random` instances), so generation must complete before any
gameplay RNG runs. Same run replays identically; each depth is deterministic.

## 7. Output & engine integration

`generate()` returns a plain dict — **not** `level_loader.Level` (that type is
`.lvl`-format-specific and stays unused for Ch7 gameplay):

```python
{
  "grid": [bytearray, ...],        # 64 rows × 64 tile indices
  "rooms": [(x, y, w, h), ...],
  "up": (x, y), "down": (x, y),
  "spawn_points": [(x, y), ...],
  "depth": int, "seed": int,
}
```

- **`cd-dsc.5` (done):** `world.world_from_level(level)` builds the `World`
  (`wall_tiles=(2,)`, `depth` carried through) with the hero on `level["up"]`.
  `main.py._new_game(depth)` calls it, then drops placeholder monsters on the
  first few `spawn_points` until `cd-dsc.4`. `_test_room()` is gone.
- Terrain TileGrid is **viewport-sized** — `modes.PlayMode` (as of `cd-oht.2`)
  holds a 13×13 grid repainted from `world.camera_for(...)` on each camera
  move, **not** the whole 64×64 level. Verified end-to-end in
  `test_scene.GeneratedLevel`.

## 8. Child beads

| Bead | | |
|---|---|---|
| `cd-dsc.2` | `generator.py` — steps §3, reproducible from a seed | **done** |
| `cd-dsc.3` | BFS connectivity guarantee + smarter stairs placement | **done** |
| `cd-dsc.4` | populate `spawn_points` from `spawns.py`, depth-scaled | open |
| `cd-dsc.5` | feed the level dict into the engine; viewport TileGrid | **done** |
| `cd-dsc.6` | RP2040 perf & RAM pass (gen time, depth-scaled size) | open |

### 8.1 As built (`cd-dsc.2`) — deviations from the spec above

- `generate(seed, depth, rng=None)` — the extra `rng` arg is an escape hatch
  for hermetic tests (`random.Random`); left `None` on device, where the
  module RNG is seeded per §6. `tests/test_generator.py`.
- **Degenerate-seed guard:** if rejection sampling yields fewer than 2 rooms,
  the generator carves two guaranteed-disjoint corner rooms so `rooms[0]`
  and a distinct farthest room always exist. `cd-dsc.3`'s BFS repair
  supersedes this.
- Room rolling: keep going until 14 rooms **or** 120 attempts (yields the
  ~9–16 of §2). Farthest room is by squared centre distance (argmax-equiv).
- Corridors overwrite **only** wall, so a corridor crossing a room leaves the
  room floor (flagstone) intact rather than cutting a dirt stripe through it.
- Spawn pool: distinct floor tiles outside the entry room (stairs excluded
  since they aren't floor). All floor is now one connected region (`_connect`
  below), so no separate reachability filter is needed — `cd-dsc.4` just
  assigns entities.

### 8.2 As built (`cd-dsc.3`) — connectivity + stairs

- `_dist_grid(grid, start)` → a flat `bytearray[64*64]` of BFS step counts over
  non-wall tiles (`_UNREACHED` = 255 elsewhere). Flat, **not** a
  `{(x, y): steps}` dict — that dict is ~1500 tuple keys and would blow the
  RP2040 heap. Queue is an int list drained by a head index (no
  `collections.deque`). `_dist_at(dist, (x, y))` indexes it.
- `_connect(grid, rooms, rng)` runs right after layout: flood from `rooms[0]`;
  for any room whose centre isn't reached, carve a repair corridor to the
  nearest connected room and re-flood. Loops until every room is in. Result:
  the whole floor is a single connected region.
- Down-stairs go in `_farthest_room_bfs` — the room whose centre is the most
  BFS steps from the entry room (Euclidean `_farthest_room` kept as a
  pathological-case fallback). This is a real "end of the longest walk", not
  just the far corner.
