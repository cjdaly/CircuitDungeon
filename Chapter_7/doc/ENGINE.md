# Chapter 7 — Engine Specification

The engine-core counterpart to [`ART.md`](ART.md). Governs epic `cd-e3p`
(roguelike engine core) and constrains `cd-dsc` (level generation) and
`cd-oht` (screen layout).

Ch7 forks the Ch6 engine (`Chapter_6/game/{engine,hardware,util,level_loader}.py`)
and replaces its real-time frame loop with a turn-based one. Sections marked
*(open)* are deferred to the bead that owns them.

---

## 1. Turn model

Resolves bead `cd-e3p.1`.

### 1.1 Scheduling — strict, equal speed

One **turn** is:

```
1. resolve the player's action
2. for each monster (fixed list order): monster.act()
3. upkeep: status-effect ticks, regen, level bookkeeping, anim pulse advance
```

Every actor acts exactly once per turn, at the same rate. No initiative, no
per-actor speed in v1.

The actor list is **snapshotted before step 1** (`resolve_turn` calls
`scheduler.actors_for_turn()` first thing): turn order is fixed at the start
of the turn, a monster the player kills mid-turn is filtered out (it's no
longer in `world.actors`), and a **corpse created this turn is not in the
snapshot** so it never gets an AI turn. Corpses also carry `corpse=True` and
`resolve_turn` skips any actor with it — belt-and-suspenders for corpses that
outlive the turn they were made in (without it they woke to `"hunt"` and
trailed the hero).

**Built for a later swap.** Actor turn-taking goes through a small scheduler
seam, not a bare `for m in monsters` in the turn loop:

```python
class Scheduler:            # v1 implementation: round-robin
    def actors_for_turn(self): ...   # yields player, then each monster once
```

so a speed/energy scheduler can replace it later without touching monster AI
(`cd-e3p.4`), combat (`cd-e3p.5`), or the turn loop body. Two future rungs,
both **stretch goals, not scheduled**:

- *Integer speed* — each actor acts every N turns / N× per turn.
- *Full energy / action points* — energy counter per actor, gained ∝ speed,
  acts at threshold. Enables haste / slow / paralyze / multi-attack.

The seam is the commitment; the rungs are optional.

### 1.2 What consumes a turn

| Consumes a turn | Free (no turn, monsters don't move) |
|---|---|
| Move into an open tile | Move into a wall (move fails) |
| Attack (move into a hostile) — see `cd-e3p.5` | Open / close inventory or map view |
| Wait one turn | Toggle diagnostic mode (`cd-89o.6`) |
| Pick up / drop / use / equip an item | Look / cursor / examine mode |
| Descend or ascend stairs (`cd-e3p.10`) | An input that maps to no action |

A failed move (into a wall) is a no-op: no turn passes, the player just
stays put. Bumping a hostile is an attack and *does* pass the turn.

There is a **wait** action that passes exactly one turn — bound to the
`Down + B` chord (`cd-e3p.15`).

### 1.3 Movement — 4-way, single step

- **Directions: 4-way only** (N/S/E/W). No diagonals in v1.
  - Distance metric is Manhattan (`abs(dx) + abs(dy)`); adjacency is the
    4-neighbourhood. FOV (`cd-e3p.6`), monster pathing (`cd-e3p.4`), and
    combat reach (`cd-e3p.5`) are all built on this.
  - **This is a deliberate revisit gate**, same as `ART.md` §9's perspective
    call: moving to 8-way later means reworking FOV (needs symmetric
    shadowcasting), the distance metric (Chebyshev), and every monster's
    "can I hit the player" check. Decide before those three beads are
    considered final, not after. The PicoSystem d-pad is a 4-way rocker;
    8-way would ride on Up+Right chords from `cd-e3p.11`.
- **One press = one tile step**, resolving a full turn.
- **Held direction** = `cd-e3p.11` auto-repeats single-tile steps, one turn
  each, rate-capped for readability. Repeat **pauses while a monster is in
  view** so you don't sprint into a fight. No junction/door detection.
- *Auto-travel / run-to-interesting-tile is (open)* — a possible later
  addition, noted on `cd-e3p.11`, not in v1.

### 1.4 Movement presentation — snap now, slide later

- **v1: instant tile snaps.** An actor's logical position changes and the map
  redraws; no interpolation.
- The move pipeline **splits logical move from presentation** — `apply_move()`
  updates game state; a separate presentation step draws it — so tile-to-tile
  slide animation can be added later without touching turn logic.
- **Slides stay strict when added:** within one turn, the player's slide plays
  during the player's sub-turn, then each monster's slide during its own
  sub-turn. Turn order is still fully sequential; animation does not
  parallelise the simulation.
  - *(open, for the animation bead)* Sequential per-actor slides can total
    noticeably (~6 monsters × ~100 ms = ~0.6 s of watching per turn). Likely
    resolution: resolve sub-turns sequentially but batch the *on-screen*
    actors' slides into one concurrent ~100 ms tween. Settle when animation
    is actually built.

### 1.5 Main loop shape

Not a blocking `read_input()` — idle 2-frame anims (`ART.md` §4) and button
auto-repeat need a clock while the game waits for the player.

```
loop at a modest fixed tick (~15–20 fps, like Ch6's TARGET_TICK_SECONDS):
    poll input  -> zero or one actionable event (from cd-e3p.11)
    if an actionable event:
        resolve one turn (§1.1)
        redraw map / HUD
    else:
        advance the anim pulse only (idle wobble, torch flicker, HUD scroll)
    refresh display
```

The `cycle` pulse from Ch6 carries over as the wall-clock heartbeat for
presentation-only animation; it is **not** the turn counter. Turn count is
its own integer, incremented once per resolved turn.

---

## 2. Engine fork

Resolves bead `cd-e3p.2`. Forked from
`Chapter_6/game/{engine,hardware,util,level_loader}.py`.

### 2.1 Module layout

```
Chapter_7/game/
  main.py          # board detect -> build a World -> Game(display, world).run()
  engine.py        # Game: owns the InputModel + ModeStack; the ~20fps loop
  modes.py         # ModeStack + PlayMode / MenuMode / DiagMode  (§4; cd-e3p.12)
  input.py         # InputModel: raw buttons -> named events  (§3; cd-e3p.11)
  ai.py            # per-monster idle/wander/chase  (§6; cd-e3p.4)
  fov.py           # Pure: recursive shadowcasting field of view  (§8; cd-e3p.6)
  log.py           # message log  (§11; cd-e3p.9)
  metrics.py       # RAM / flash / frame-time readout for DiagMode  (§4.1; cd-89o.6)
  generator.py     # Pure: seed -> level dict (grid/rooms/stairs/spawns).
                   #   No displayio/board.  (LEVELGEN.md; cd-dsc.2)
  world.py         # Pure core: grid, actors, movement, scheduler, turn loop,
                   #   combat, camera, line-of-sight, FOV state. No displayio.
  hardware.py      # forked verbatim + X/Y face buttons wired for PicoSystem
  util.py          # forked verbatim (displayio helpers)
  level_loader.py  # forked verbatim; the `.lvl` Level type is a handy target
                   #   for the generator (cd-dsc) but nothing calls it yet
  tiles/           # terrain/creatures/heroes/objects .bmp + palette + tiles.json
Chapter_7/tests/
  test_{world,input,modes,turn,ai,fov,combat,log,metrics,generator,scene}.py  # python3 <file>
```

The **`world.py` / presentation split is the fork's main structural move** and
it is what makes §1.4 ("logical move separate from presentation") real:
`world.move_actor()` changes state and returns a result; `PlayMode.render()`
reflects state onto sprites. It also keeps the turn model testable without a
display. (The scene itself moved from `engine.Game` into `modes.PlayMode` when
mode dispatch landed — §4.)

### 2.2 What was stripped from the Ch6 engine

2px real-time movement · the fixed-rate frame loop whose `time.sleep` paced
movement speed · explosion pool + chain reactions · HUD scroll animation ·
the `.lvl` exit/event trigger system · pixel-scroll camera.

### 2.3 What is still left for later beads

- The hero moves, turns advance, monsters chase and fight, bump-combat kills
  (corpses, xp), death → game-over, and combat text shows on the message line
  (§§5–7, §9, §11). FOV is computed and drawn as fog of war (§8,
  `cd-e3p.6` / `cd-oht.6`). Still missing: inventory (`cd-e3p.8`), `_upkeep`
  regen, the dim-vs-lit tile distinction, and the rest of the HUD content
  (`cd-oht.4`/`.5`).
- `PlayMode` lays out the Option-G regions (`cd-oht.2`): a 13×13 terrain
  viewport with a hero-centred clamped camera, plus empty `status_group` /
  `rail_group` / `message_group` for `cd-oht.3` / `.5` / `.4` to fill.
- `main.py` now builds the level with `generator.generate(seed, depth)` →
  `world.world_from_level(level)` (hero on the up-stairs); `cd-dsc.5`. Seed is
  fixed (`RUN_SEED`) and monsters are three placeholders on `spawn_points`
  until `cd-dsc.4` reads the spawn tables and `cd-89o.1` owns seed/depth.
- No idle animation yet — the placeholder tile sheets are one frame each;
  it lands with the art (`cd-e17.*`) and the polish pass.
- FOV is drawn as fog of war (§8, `cd-e3p.6` / `cd-oht.6`): unseen cells are
  rock, seen cells stay revealed, out-of-sight monsters are hidden. The
  dim-vs-lit shading of remembered tiles waits on a dim tile from `cd-e17.5`.
- `MenuMode` is a stub overlay — real screen is `cd-e3p.13`. `DiagMode` is a
  single RAM/perf/input screen (§4.4, `cd-89o.6`); the always-on diagnostic
  event-log ring buffer is still open (`cd-89o.10`).

### 2.4 Actor representation

Actors are **plain dicts in `world.actors`**, not classes (CircuitPython has
no `__slots__`; Ch6 `PLAN.md` "State"). `actors[0]` is the hero. Shape:
`{"x", "y", "sheet", "tile", "blocks", ...}` — `make_actor()` builds one.
Sprites are a parallel list in `PlayMode`, re-synced by `_sync_actor_sprites()`
when the roster changes (it `gc.collect()`s first — it rebuilds every sprite
TileGrid). All four tile sheets (`terrain` / `heroes` / `creatures` /
`objects`) load in `PlayMode.__init__`, not on first use: the lazy path put
the first `objects.bmp` load in the middle of a fight and it OOM'd (`cd-yl4`).

## 3. Button input model

Resolves bead `cd-e3p.11`. Full spec in [`INPUT.md`](INPUT.md); in brief:

- `Chapter_7/game/input.py` — `InputModel.tick(buttons, now)` turns the raw
  8-key `hardware.read_buttons()` dict into named events; `get()` pops one per
  loop pass. Pure, off-device tested (`tests/test_input.py`).
- Events: `MOVE_N/S/E/W` (d-pad, edge + auto-repeat), `CONFIRM`/`CANCEL`/
  `AUX_X`/`AUX_Y` (face, one per press, no long-press), plus chord names.
- Chords: simultaneous pairs, once per hold. v1 bindings — **X+Y → `diag`**,
  **A+B → `menu`** — consumed by the mode dispatch (§4).
- Repeat timing is instance config (settings-tunable); `repeat_paused` is set
  by the engine per §1.3. Output queue bounded at 4, drop-oldest.
- `snapshot()` / `chord_stats()` feed the `cd-89o.6` diag screen. (The old
  per-event `trace()` ring is gone — `cd-dsc.6`.)

## 4. Screen / mode dispatch

Resolves bead `cd-e3p.12`. `Chapter_7/game/modes.py`.

### 4.1 Modes

A **mode** is an object with `tick(events, now)`, `render()`, and a `.group`
(its displayio scene). v1 modes:

| Mode | Class | Scene | switched by |
|---|---|---|---|
| play | `PlayMode` | Option-G scene: 13×13 terrain viewport + camera + actor layer + empty HUD region groups (`LAYOUT.md`, `cd-oht.2`) | — (base) |
| menu | `MenuMode` → `_StubOverlay` | centred label; real screen is `cd-e3p.13` | `A+B` chord |
| diag | `DiagMode` | one screen (§4.4): RAM / flash / frame-time / board+CP / actor counts, then held buttons + per-chord fire/miss (`cd-89o.6`) | `X+Y` chord |
| game-over | `GameOverMode` | "YOU DIED" — `CONFIRM` calls the restart callback (§9.2) | `stack.show()` on death |

`tick()` returns `"exit"` to ask the stack to drop back to play (the menu/diag
overlays do this on `CANCEL`); anything else returns `None`.

### 4.2 ModeStack

`ModeStack(base, {"menu": …, "diag": …})` — `base` (play) is always at the
bottom; at most one overlay sits on top (never two).

- `handle(events, now)` — the `"menu"` / `"diag"` **chord events are consumed
  here** and toggle their overlay (same chord again, or a `tick()` `"exit"`,
  returns to play). Every other event is passed to `top.tick()`.
- `show(mode)` forces a non-chord overlay (game-over) that chords and `"exit"`
  can't dismiss — the mode leaves on its own terms.
- Because the toggle event never reaches `PlayMode.tick()` and play isn't
  ticked while an overlay is up, **entering/leaving menu or diag passes no
  game turn** (§1.1).
- `render(screen)` — calls `top.render()` and points `screen.root_group` at
  `top.group`, only reassigning when the top actually changed.

`ModeStack` imports nothing hardware-side (the mode classes lazy-import
`displayio`/`util` in `__init__`), so its routing is unit-tested off-device
(`tests/test_modes.py`).

### 4.3 The loop (`engine.Game`)

`Game` shrank to: own the `InputModel` + the `ModeStack`, and run

```
each ~20fps tick:
    metrics.maybe_sample_ram(now)                  # §4.4 — gc.collect() on a timer
    events = input.tick(read_buttons(), now)
    stack.handle(events, now)
    if play on top and hero dead:  stack.show(gameover)     # §9
    elif world.transition:         _change_level(...)       # §5.4
    input.repeat_paused = stack.overlay_active()   # no d-pad repeat in a menu
    stack.render(screen); screen.refresh()
    metrics.note_frame(dt)
```

### 4.4 Diagnostics (`cd-89o.6`)

`DiagMode` is **one screen**; `CANCEL` (B) or the `X+Y` chord exits. It was
two pages (SYSTEM / INPUT) toggled with `A`, but the INPUT page's per-event
trace was a wait-chord tuning tool retired with `cd-e3p.14`/`.15` — one screen
is less code and less RAM (`cd-dsc.6`).

Layout / RAM notes (all `cd-yl4`):

- All labels are `bitmap_label.Label` (`util.init_label`), not `label.Label`
  (a Group of one TileGrid per glyph, freed and rebuilt on every `.text =` —
  the status line does that every turn and it shredded the heap over ~1000
  turns).
- The screen is **≤ 14 per-line labels**, each a small constant-width
  `bitmap_label` that rewrites its own bitmap in place. A single
  `bitmap_label` for the whole page wanted one ~9 KB contiguous Bitmap and
  OOM'd on open. The lines are built **lazily on first open** (so an unused
  diag costs nothing) and every allocation is `MemoryError`-guarded — a
  tight open gives a short screen, never a crash.
- Content is diffed per line; only changed lines touch a label. The
  frame-time readout is rounded to 10 ms so jitter isn't a change. Refresh is
  throttled to every 4th render.

The screen shows, top to bottom:

- **RAM / perf** — from `game/metrics.py` (pure: `gc` / `os` / `sys` / `time`):
  - **RAM** — `gc.mem_free()` / `gc.mem_alloc()` read *after* `gc.collect()`,
    since raw `mem_free()` counts not-yet-collected garbage as used. The
    engine loop calls `metrics.maybe_sample_ram(now)` every tick, but it
    only collects + reads on a ~0.5 Hz timer (`RAM_INTERVAL`) — `collect()`
    costs a few ms. `free_low` is the low-water mark since boot: the number
    that says how close to the edge you actually got.
  - **flash** — `os.statvfs("/")` free / total.
  - **frame time** — last / max ms (`metrics.note_frame`), on the gc line.
  - board id, CircuitPython version, actor / turn / depth counts.
  - Off-device (`gc` has no `mem_free`) the RAM fields read `None` → shown
    as `-`; `metrics` still runs, tested headless in `test_metrics.py`.
- **input** — `held:` buttons (+ any forming chord in parens), then one row
  per chord binding: `fire` / `miss` / last `sp`read ms from
  `input.chord_stats()`. No per-event trace — `input.py` dropped its 32-entry
  ring (`~2 KB` + an alloc per keypress) once the bindings were settled.

The always-on diagnostic **event-log ring buffer** (compact codes recorded
from boot, so a bug is captured before you go looking) is a follow-up,
`cd-89o.10` — deliberately split from this readout.

## 5. Turn loop

Resolves bead `cd-e3p.3`. The loop body lives in `world.py` (pure, tested in
`tests/test_turn.py`); `modes.PlayMode` maps input to actions and renders.

### 5.1 Action

`PlayMode.tick(events, now)` takes the first play-mode event and maps it to an
**action** tuple:

| Event | Action | |
|---|---|---|
| `MOVE_N/S/E/W` | `("move", dx, dy)` | 4-way, ±1 |
| `wait` | `("wait",)` | passes a turn in place — the `Down + B` chord (`cd-e3p.15`) |
| `CONFIRM` / `CANCEL` / `AUX_X` / `AUX_Y` | — | belong to later beads (inventory, look); pass no turn |

At most one action per tick — extra events are dropped (auto-repeat is already
rate-capped in `input.py`, so >1 move per ~50 ms tick is nearly impossible).

### 5.2 `world.resolve_turn(world, scheduler, action, monster_turn)`

```
roster = scheduler.actors_for_turn()          # §1.1 — snapshot BEFORE anyone acts
if not _apply_player_action(world, action):   # move → move_actor(); "moved" spends
    return False                              #   a turn, "blocked"/"bump"/None don't
for actor in roster:                          # hero first, then each monster once
    if actor is world.hero: continue
    if actor not in world.actors: continue    # killed by the hero this turn
    if actor.get("corpse"): continue          # scenery — never gets an AI turn
    if not world.hero_alive(): break
    monster_turn(world, actor)                # per-monster AI — ai.take_turn (§6)
_upkeep(world)                                # status ticks / regen — empty until cd-e3p.7
world.turn += 1
return True
```

- **A failed move (wall/edge) passes no turn.** A `bump` onto a fightable
  actor (`hp` key) is an attack and *does* spend the turn (§7).
- `monster_turn` is `ai.take_turn` (§6); `_upkeep` is still the `cd-e3p.7` seam.
- Movement is an instant snap — `PlayMode.render()` repositions sprites from
  `world.actors` on the next frame (§1.4). No tween.
- `world.turn` counts real turns; `PlayMode.cycle` is the wall-clock pulse.

### 5.3 What's still open

- Repeat-pause while a monster is in view (§1.3): `world.is_visible()` exists
  now (§8), so the check is `any(world.is_visible(m["x"], m["y"]) for m in
  world.monsters())` — not yet wired; the engine only pauses repeat for
  overlays.

### 5.4 Descent between levels (`cd-e3p.10`)

Stairs are walkable floor (`STAIRS_DOWN_TILE = 4`, `STAIRS_UP_TILE = 5`).
When the hero **moves onto** one, `world._check_transition` sets
`world.transition` to `"down"` / `"up"` (spawning on a stair tile does not —
`world_from_level` adds the hero without going through the move path).

The engine loop checks `world.transition` right after the game-over check
(death wins) and calls `Game._change_level(direction)`:

```
depth  = world.depth ± 1
arrive = "up"  when descending  (you drop in at the new level's up-stairs)
         "down" when ascending  (you climb back up through the hole you made)
world  = new_level(depth, arrive)          # main._new_game — generate() + spawn
play.load_world(world);  diag.world = world
```

- **Regenerate on entry.** `generator.generate(seed, depth)` is deterministic,
  so re-entering a depth gives the *same layout* with *fresh* monsters — no
  level state is persisted (RAM: only the current level exists).
- **Release the old level first.** `_change_level` nulls `self.world` /
  `play.world` / `diag.world` and `gc.collect()`s *before* calling
  `new_level` — the outgoing grid + `generate()`'s transient BFS buffers
  would otherwise peak together on an already-tight heap (`cd-yl4`).
- `PlayMode.load_world(world)` reuses the displayio scene (viewport, HUD
  groups) and just re-points + repaints — no mode rebuild.
- Ascending from depth 1 is sealed (a log line, no transition).
- `main.py` passes `new_level=_new_game`; without it (some tests) descent is
  inert.
- **The hero's stats/equipment carry across; only position resets.**
  `world_from_level()` always builds a brand-new hero via `make_hero()`
  (`HERO_DEFAULTS`) — that's correct for *position* (the new level's arrival
  stair), but `_change_level` snapshots the old hero's `hp`/`max_hp`/
  `power`/`defense`/`gold`/`xp`/`level`/`weapon_level`/`armor_level`/
  `inventory` (`_HERO_CARRY_KEYS`) before releasing the old world, then
  `new_world.hero.update(carry_hero)`s them onto the freshly-placed hero.
  **Missing until 2026-09-14** — only `world.turn` was ever carried, so
  every level change silently reset hp/gold/xp and dropped the equipped
  sword/armor level and any carried potions. Chris caught it via the
  cd-dsc.4 rail: "I found a sword on level 1, but when I went to level 2 I
  didn't have it anymore." `test_scene.py`'s `Descent` class covers it now
  (`test_hero_stats_and_equipment_survive_a_level_change`).

## 6. Monsters + AI

Resolves bead `cd-e3p.4`. `Chapter_7/game/ai.py` — pure; `PlayMode._monster_turn`
calls `ai.take_turn(world, actor)` for each monster once per turn (§5.2).

### 6.1 State — on the actor dict

Monsters are plain dicts (§2.4). `take_turn` reads/writes two keys:

| key | |
|---|---|
| `actor["ai"]` | `"sleep"` \| `"hunt"` — defaults to `"sleep"` if absent |
| `actor["goal"]` | `(x, y)` last-known hero tile, while hunting |

### 6.2 Behaviours (4-way, §1.3)

- **sleep** — idle. `WANDER_CHANCE` (0.12) per turn to shuffle one tile.
  Wakes to **hunt** on line of sight to the hero within `SIGHT` (8, Chebyshev),
  setting `goal` to the hero's tile.
- **hunt** — if it still sees the hero, refresh `goal`. Step greedily toward
  `goal` — the axis with the larger remaining delta first, the other as a
  fallback if blocked (no real pathfinding in v1; greedy is enough for open
  rooms). Reaching `goal` without seeing the hero → back to **sleep**.

Stepping onto the hero's tile is a **bump** → `ai._step_toward` calls
`world.resolve_attack` (§7).

### 6.3 Line of sight

`world.los_clear(world, x0, y0, x1, y1)` — a Bresenham walk, endpoints
excluded, `False` on the first wall between. This is the *monster→hero* ray
only; the player's field of view (visible / explored / unseen) is the
separate, heavier `cd-e3p.6`.

### 6.4 RNG

`ai.py` uses the module `random` stream, continuing after level generation
(`LEVELGEN.md` §6). Deterministic given the run seed and the call order.
Tests set `ai.WANDER_CHANCE = 0` to drop the randomness.

## 7. Combat

Resolves bead `cd-e3p.5`. `world.resolve_attack(world, attacker, defender)` —
v1 is **hero ↔ monster only** (nothing else has `hp`/`power`).

- **Trigger:** a bump. `world.move_actor` returns `("bump", other)`; if `other`
  has an `hp` key, `_apply_player_action` / `ai._step_toward` call
  `resolve_attack` instead of moving, and the bump **spends the turn** (§1.2).
- **Damage:** `max(1, attacker.power - defender.defense)` — always at least 1.
- **Monster death:** removed from `world.actors`; a non-blocking corpse
  (`objects` tile `CORPSE_TILE`, `corpse=True`) takes its place; if the killer
  is the hero, `hero["xp"] += monster["xp"]`. The `corpse` flag keeps
  `resolve_turn` from ever handing it to the AI (§1.1).
- **Hero death:** `hp ≤ 0`, but the hero **stays at `actors[0]`** — no corpse.
  `engine.Game.run()` sees `not world.hero_alive()` and shows `GameOverMode`
  (§9.2). `resolve_turn` also `break`s its monster loop once the hero is dead,
  so a later monster doesn't swing at a corpse.
- **Messages:** `resolve_attack` calls `world.log.add(...)` ("You hit the rat
  for 4.", "The rat dies.", "The rat hits you for 2.", "You die.") — §11.
- **Sprites:** `world.roster_version` bumps on every add/remove;
  `PlayMode.tick` re-runs `_sync_actor_sprites()` when it changes.

*Open:* no level-up from xp (§9.1); no ranged attacks / to-hit roll (flat
"always hits"); a "dead" hero sprite (`ART.md` §8).

## 8. Field of view

Resolves bead `cd-e3p.6`. `Chapter_7/game/fov.py` — pure, no displayio/board.

- **Algorithm:** recursive shadowcasting, 8 octants (Björn Bergström /
  RogueBasin). `fov.compute(ox, oy, blocked, mark, radius=8)` calls
  `mark(x, y)` once per visible tile. `blocked(x, y)` must be total (out of
  bounds = blocked). Cost ≈ radius² per octant, run once per hero move
  (~1–4 ms on device); recursion depth ≤ radius.
- **`RADIUS = 8`** — matches the monster `SIGHT` (§6), so it's roughly
  symmetric: if the hero can see a tile, a monster there can see the hero.
  Monster AI still uses the cheaper `world.los_clear` single ray, not this.
- **State on `World`** — two **bit-packed** masks, `width·height` bits each
  (~288 B apiece at 48×48):
  - `world.visible` — recomputed from scratch every `world.refresh_fov()`
    (zeroed, then re-marked). `world.is_visible(x, y)`.
  - `world.explored` — only ever gains bits: fog-of-war memory. Reset when
    the level is rebuilt (levels regenerate on entry — §5.4 — so there's no
    cross-visit memory to keep). `world.is_explored(x, y)`.
- **When it runs:** `world_from_level()` and `PlayMode.load_world()` seed it;
  `resolve_turn()` calls `world.refresh_fov()` after upkeep (the hero may have
  moved). Both accessors bounds-check, so callers don't have to.
- **Rendering (`cd-oht.6`, dim tiles `cd-e17.5`):** `PlayMode._paint_terrain`
  draws a cell one of three ways: currently `is_visible` → its real tile;
  `is_explored` but not visible → the same tile index + `DIM_OFFSET` (8) —
  `terrain.bmp`'s second row, a darkened copy of every base tile generated
  from the palette's `fog_dim` ramp; never seen → `VOID_TILE` (index 6, a
  solid tile — was wall-top reused as a placeholder before `cd-e17.5`).
  So the dungeon reads as solid rock until FOV reveals it, then dims to
  "remembered" once the hero looks away, both permanently until the level
  regenerates. `_render` hides any actor sprite that isn't `world.is_visible`
  (monsters vanish when they leave sight). `PlayMode.tick` repaints the
  terrain after any resolved turn, not just on camera movement.

## 9. Player model

Resolves bead `cd-e3p.7`.

### 9.1 Stats — plain actor keys

The hero is `world.actors[0]`, an actor dict like any other. `world.make_hero()`
adds `world.HERO_DEFAULTS`:

| key | v1 | |
|---|---|---|
| `hp` / `max_hp` | 20 / 20 | health |
| `power` | 4 | damage dealt on a hit (`cd-e3p.5`) |
| `defense` | 1 | damage reduced |
| `gold` | 0 | for the status line |
| `xp` / `level` | 0 / 1 | tracked; **no level-up mechanic in v1** — a later polish (xp threshold → +max_hp/+power) |

Combat stats are just keys, so **any actor with `hp`/`power` can fight and
die** — monsters get theirs from the spawn tables (`LEVELGEN.md` §5).
`world.depth` (the dungeon level number) also lives on the `World`.

### 9.2 Death → game over

`world.hero_alive()` = `hero exists and hero.get("hp", 1) > 0` (a stat-less
hero counts as alive). Each loop pass, `engine.Game.run()` checks it right
after `stack.handle`; on death it calls `stack.show(self.gameover)` —
`GameOverMode`, a non-chord overlay the player can't dismiss. `CONFIRM` on it
calls the `restart` callback: `supervisor.reload()` on device (`main.py`),
a test hook off it. The world freezes behind the overlay (play isn't ticked).

*Open:* passive regen / status-effect ticks in `_upkeep` (§5.2) — none yet.

## 10. Inventory model

Resolves beads `cd-e3p.8` and `cd-dsc.4`. `Chapter_7/game/world.py`, right
after combat (§7), plus `Chapter_7/game/spawns.py` for level population.

- **Items are non-blocking actors** — `world.make_item(x, y, tile, kind,
  name, **extra)` builds one on the `objects` sheet, `item=True` flagged
  (mirrors the existing `corpse` flag: `resolve_turn`'s monster loop skips
  both — **true of the code since 2026-09-14**; between `cd-e3p.8` and
  `cd-dsc.4` this line described the intent but the loop only actually
  checked `corpse`, so spawned items got full monster AI turns and would
  wander/hunt/bump-attack the hero. No test caught it — `test_scene.py`'s
  harness sets `ai.WANDER_CHANCE = 0` globally, and no other test put an
  item through `resolve_turn`'s roster with `ai="hunt"`. Found in a real
  playtest; `test_combat.py`'s `test_item_never_gets_a_turn_and_never_chases_the_hero`
  covers it now.) `actor_at()` already only reports *blocking* actors — its
  own docstring calls out items alongside corpses — so an item never causes a
  bump; stepping onto one is just a normal move.
- **Pickup is automatic**, not a separate input: `_check_pickup(world)` runs
  right after a successful hero move (same spot `_check_transition` watches
  for stairs) and looks at any item actor on the hero's new tile. What
  happens next depends on the item's `kind`:
  - **Consumables** (`potion_red`, `potion_blue`, `scroll` — anything not in
    `EQUIP_SLOTS`) move into `hero["inventory"]`, same dict, relocated out
    of `world.actors`, nothing to convert. One item per tile.
  - **Weapon/armor** (`kind` in `EQUIP_SLOTS`) never enter the inventory at
    all — see "Leveled equipment" below. Either way the item actor is
    removed from the map on contact; it's either an upgrade or gone.
- **No selection UI for consumables** (`cd-oht.7`, deliberately not built —
  see below) — rather than build a choose-one-from-a-list screen, `use`
  acts on the first inventory item that qualifies:
  - `world.use_item(world, actor, item)` — consumes a potion/scroll whose
    `kind` is in `ITEM_EFFECTS` (`heal`, `buff_power`, `buff_defense`),
    logs a message, removed from inventory. `AUX_X` (X alone, not the X+Y
    chord) triggers "use the first item with an effect."
  - `world.drop_item(world, actor, item)` — removed from inventory, placed
    on the map at the actor's position. Built and tested; **no input
    binding** — dropping a *specific* item needs the selection UI this
    section deliberately avoided building early.

### 10.1 Leveled equipment — sword & armor (`cd-dsc.4`)

Swords and armor are **not carried items** — the hero always holds exactly
one of each, tracked as plain stats (`weapon_level`/`power`,
`armor_level`/`defense` — `EQUIP_SLOTS` maps `kind` to the pair). Finding
one auto-compares against what's equipped:

- `_try_equip_leveled(world, actor, item)` — if the found item's `level` is
  higher than the actor's current `*_level`, it replaces it: the actor's
  stat is adjusted by `-old_level + new_level` (so re-equipping is an
  unwind-then-apply, not additive) and a "You found a better sword! (level
  N)" message is logged.
- If the found level is **lower or equal**, nothing changes on the actor —
  just a rejection message: `"Your level N sword is better!"` (or armor).
  Either way the ground item is gone; there's nothing to carry or drop.
- This is why `cd-oht.7` (a dedicated inventory *screen*) was closed as
  superseded rather than built: with only two equipment slots and no
  selection to make (auto-equip-if-better is the whole interaction), a
  minimal always-on readout in the icon rail (`cd-oht.5`) covers it more
  cheaply than a toggle-mode screen would.
- `AUX_Y` (Y alone) is unbound — there's no "equip" action left to trigger;
  equipping happens on pickup, not on demand.

### 10.2 Spawn tables (`Chapter_7/game/spawns.py`, `cd-dsc.4`)

`world_from_level()` calls `spawns.populate(world, level["spawn_points"],
level["depth"])` right after placing the hero. `populate()` draws distinct
spawn points via `_pop_random` (swap the picked index to the end of the
list, then `pop()`) and draws from the same continuing global `random`
stream `generator.generate()` seeded (an optional `rng` param is the
hermetic escape hatch tests use — see `test_spawns.py`), matching the
determinism convention `ai.py` already established.

**Gotcha found on-device (2026-09-14):** `_pop_random` deliberately avoids
`random.shuffle()` — CircuitPython's built-in `random` module implements
only `choice`/`getrandbits`/`randint`/`random`/`randrange`/`seed`/`uniform`,
*not* `shuffle`. A hermetic `random.Random()` instance (what the desktop
tests use) has `shuffle`, so a shuffle-then-pop implementation passed all
222 off-device tests and then crashed with `AttributeError` on first boot.
Anything reaching for the global `random` stream should stick to that
smaller method set.

- **Monsters** — `MONSTERS` is a table of `(name, min_depth, max_depth, hp,
  power, defense, ..., xp)` tuples; `_eligible_monsters(depth)` filters to
  ones whose depth range covers the level, `_make_monster` picks one at
  random. Count scales with depth: `MONSTER_BASE=2 +
  MONSTER_PER_DEPTH=1 * (depth-1)`, capped at `MONSTER_CAP=8` and by however
  many spawn points exist.
- **Items** — one sword and one armor per level (if spawn points remain
  after monsters), each at `_item_level(depth, rng)` = `depth +
  randint(-ITEM_LEVEL_JITTER, +ITEM_LEVEL_JITTER)` (`ITEM_LEVEL_JITTER=2`),
  floored at level 1. This is the mechanic the hero's auto-equip compares
  against (§10.1) — deeper levels trend toward better gear, with enough
  jitter that a shallow level can still occasionally drop something worth
  upgrading to.
- **Gold** — `GOLD_PILES=2` per level (flat, not depth-scaled), each worth
  `_gold_amount(depth, rng)` = `randint(GOLD_MIN, GOLD_MAX) * depth`
  (`GOLD_MIN=5`, `GOLD_MAX=15`). Its `kind` is `"gold"`, not one of
  `ITEM_EFFECTS` or `EQUIP_SLOTS` — `_check_pickup` special-cases it a third
  way: adds straight to `hero["gold"]` and logs "You found N gold," never
  entering the inventory list (§10, `world.py`). Added 2026-09-14 — the
  status line (`cd-oht.3`) always had a Gold counter, but nothing dropped
  any until this.
- Tuning (`MONSTER_BASE`/`MONSTER_PER_DEPTH`/`MONSTER_CAP`/
  `ITEM_LEVEL_JITTER`/`GOLD_PILES`/`GOLD_MIN`/`GOLD_MAX`) is a first pass,
  not balanced against real playtesting yet.
## 11. Message log

Resolves bead `cd-e3p.9`. `Chapter_7/game/log.py` — pure. `world.log` is a
`Log`; engine code formats a sentence and calls `world.log.add(text)`.

| | |
|---|---|
| `add(text)` | append; drop the oldest past `CAP` (24); `seq += 1` |
| `latest()` | newest line (`""` when empty) |
| `tail(n)` / `all()` | recent-first slice / the whole list |
| `seq` | bumps on every add — **renderers watch this** and re-render when it changes |

`PlayMode._paint_message` (called after a turn) sets the message-line label to
`log.latest()` truncated to ~39 chars when `seq` moved. That's the minimum
viable line — **`cd-oht.4`** adds horizontal scroll for long lines and a
short multi-line history; **`cd-oht.7`** could show `all()` as a scrollback.

Writers so far: combat (§7). Later: item pickup/use (`cd-e3p.8`), descent
(`cd-e3p.10`), traps.
