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
  log.py           # message log  (§11; cd-e3p.9)
  metrics.py       # RAM / flash / frame-time readout for DiagMode  (§4.1; cd-89o.6)
  generator.py     # Pure: seed -> level dict (grid/rooms/stairs/spawns).
                   #   No displayio/board.  (LEVELGEN.md; cd-dsc.2)
  world.py         # Pure core: grid, actors, movement, scheduler, turn loop,
                   #   combat, camera, line-of-sight. No displayio/board.
  hardware.py      # forked verbatim + X/Y face buttons wired for PicoSystem
  util.py          # forked verbatim (displayio helpers)
  level_loader.py  # forked verbatim; the `.lvl` Level type is a handy target
                   #   for the generator (cd-dsc) but nothing calls it yet
  tiles/           # terrain/creatures/heroes/objects .bmp + palette + tiles.json
Chapter_7/tests/
  test_{world,input,modes,turn,ai,combat,log,metrics,generator,scene}.py  # python3 <file>
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
  (§§5–7, §9, §11). Still missing: FOV (`cd-e3p.6`), inventory (`cd-e3p.8`),
  `_upkeep` regen, and the HUD content (`cd-oht.3`/`.4`/`.5`).
- `PlayMode` lays out the Option-G regions (`cd-oht.2`): a 13×13 terrain
  viewport with a hero-centred clamped camera, plus empty `status_group` /
  `rail_group` / `message_group` for `cd-oht.3` / `.5` / `.4` to fill.
- `main.py` now builds the level with `generator.generate(seed, depth)` →
  `world.world_from_level(level)` (hero on the up-stairs); `cd-dsc.5`. Seed is
  fixed (`RUN_SEED`) and monsters are three placeholders on `spawn_points`
  until `cd-dsc.4` reads the spawn tables and `cd-89o.1` owns seed/depth.
- No idle animation yet — the placeholder tile sheets are one frame each;
  it lands with the art (`cd-e17.*`) and the polish pass.
- No FOV — the whole camera window is drawn. `cd-e3p.6` hooks fog-of-war into
  `PlayMode._paint_terrain` / `_render`.
- `MenuMode` is a stub overlay — real screen is `cd-e3p.13`. `DiagMode` has
  INPUT + SYSTEM pages (§4.4, `cd-e3p.14` / `cd-89o.6`); the always-on
  diagnostic event-log ring buffer is still open (`cd-89o.10`).

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
- `trace()` / `snapshot()` expose input timing for the `cd-89o.6` diag page.

## 4. Screen / mode dispatch

Resolves bead `cd-e3p.12`. `Chapter_7/game/modes.py`.

### 4.1 Modes

A **mode** is an object with `tick(events, now)`, `render()`, and a `.group`
(its displayio scene). v1 modes:

| Mode | Class | Scene | switched by |
|---|---|---|---|
| play | `PlayMode` | Option-G scene: 13×13 terrain viewport + camera + actor layer + empty HUD region groups (`LAYOUT.md`, `cd-oht.2`) | — (base) |
| menu | `MenuMode` → `_StubOverlay` | centred label; real screen is `cd-e3p.13` | `A+B` chord |
| diag | `DiagMode` | two pages, `A` cycles (§4.4): **INPUT** — `chord_stats()` / held / trace (`cd-e3p.14`); **SYSTEM** — RAM / flash / frame-time / board+CP / actor counts (`cd-89o.6`) | `X+Y` chord |
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

`DiagMode` has two pages; `CONFIRM` (A) cycles, `CANCEL` (B) or the `X+Y`
chord exits. Assigning `Label.text` rebuilds the whole glyph bitmap and wants
a ~2 KB contiguous block — it OOM'd mid-game (`cd-yl4`). So the label is
rebuilt only when the rendered text *changes* (and at most every 4th render),
with a `gc.collect()` immediately before the allocation. The frame-time
readout is rounded to 10 ms so ordinary jitter doesn't count as a change.

- **INPUT** — `chord_stats()` (per-binding fired / missed / spread), held
  buttons, in-flight chord candidates, and the tail of the input trace.
  Built to evaluate the wait-chord bindings on real hardware (`cd-e3p.14`).
- **SYSTEM** — from `game/metrics.py` (pure: `gc` / `os` / `sys` / `time`):
  - **RAM** — `gc.mem_free()` / `gc.mem_alloc()` read *after* `gc.collect()`,
    since raw `mem_free()` counts not-yet-collected garbage as used. The
    engine loop calls `metrics.maybe_sample_ram(now)` every tick, but it
    only collects + reads on a ~0.5 Hz timer (`RAM_INTERVAL`) — `collect()`
    costs a few ms. `free_low` is the low-water mark since boot: the number
    that says how close to the edge you actually got.
  - **flash** — `os.statvfs("/")` free / total.
  - **frame time** — last and max ms (`metrics.note_frame`).
  - board id, CircuitPython version, actor / turn / depth counts.
  - Off-device (`gc` has no `mem_free`) the RAM fields read `None` → shown
    as `-`; `metrics` still runs, tested headless in `test_metrics.py`.

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

- Repeat-pause while a monster is in view (§1.3) waits on FOV (`cd-e3p.6`);
  the engine currently only pauses repeat for overlays.

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
  level state is persisted (RAM: one 64×64 level is enough).
- **Release the old level first.** `_change_level` nulls `self.world` /
  `play.world` / `diag.world` and `gc.collect()`s *before* calling
  `new_level` — the outgoing grid + `generate()`'s transient BFS buffers
  would otherwise peak together on an already-tight heap (`cd-yl4`).
- `PlayMode.load_world(world)` reuses the displayio scene (viewport, HUD
  groups) and just re-points + repaints — no mode rebuild.
- Ascending from depth 1 is sealed (a log line, no transition).
- `main.py` passes `new_level=_new_game`; without it (some tests) descent is
  inert.

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

## 8. Field of view  *(cd-e3p.6 — open)*

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

## 10. Inventory model  *(cd-e3p.8 — open)*
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
