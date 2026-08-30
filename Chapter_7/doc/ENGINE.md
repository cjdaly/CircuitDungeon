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
`wait` chord (Left+Right / Up+Down / Down+B, provisional; `cd-e3p.14`).

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
  world.py         # Pure core: grid, actors, movement, scheduler. No
                   #   displayio/board/time — runs and is tested off-device.
  hardware.py      # forked verbatim + X/Y face buttons wired for PicoSystem
  util.py          # forked verbatim (displayio helpers)
  level_loader.py  # forked verbatim; the `.lvl` Level type is a handy target
                   #   for the generator (cd-dsc) but nothing calls it yet
  tiles/           # terrain/creatures/heroes/objects .bmp + palette + tiles.json
Chapter_7/tests/
  test_world.py test_input.py test_modes.py   # off-device: python3 <file>
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

- The hero moves and turns advance (§5), but `monster_turn` and `_upkeep`
  are no-ops — monster AI is **`cd-e3p.4`**, player stats / death are
  **`cd-e3p.7`**, and a bump becomes an attack at **`cd-e3p.5`**.
- `PlayMode` is one full-bleed world group. Status / map-viewport / inventory
  bands are **`cd-oht.2`** (geometry from `cd-oht.1`).
- The hardcoded `_test_room()` in `main.py` is a placeholder until the
  generator (**`cd-dsc`**) hands back a `World`.
- No idle animation yet — the placeholder tile sheets are one frame each;
  it lands with the art (`cd-e17.*`) and the polish pass.
- `MenuMode` is a stub overlay — real screen is `cd-e3p.13`. `DiagMode`
  shows a live input page (`cd-e3p.14`); RAM/flash/timing pages are
  `cd-89o.6`.

### 2.4 Actor representation

Actors are **plain dicts in `world.actors`**, not classes (CircuitPython has
no `__slots__`; Ch6 `PLAN.md` "State"). `actors[0]` is the hero. Shape:
`{"x", "y", "sheet", "tile", "blocks", ...}` — `make_actor()` builds one.
Sprites are a parallel list in `PlayMode`, re-synced by `_sync_actor_sprites()`
when the roster changes.

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

| Mode | Class | Scene |
|---|---|---|
| play | `PlayMode` | terrain grid + actor sprites (moved here from the `cd-e3p.2` `Game`) |
| menu | `MenuMode` → `_StubOverlay` | centred label; real screen is `cd-e3p.13` |
| diag | `DiagMode` | live input page — `chord_stats()` / held state / trace (`cd-e3p.14`); RAM/flash/timing pages are `cd-89o.6` |

`tick()` returns `"exit"` to ask the stack to drop back to play (both overlays
do this on `CANCEL`); anything else returns `None`.

### 4.2 ModeStack

`ModeStack(base, {"menu": …, "diag": …})` — `base` (play) is always at the
bottom; at most one overlay sits on top (never two).

- `handle(events, now)` — the `"menu"` / `"diag"` **chord events are consumed
  here** and toggle their overlay (same chord again, or a `tick()` `"exit"`,
  returns to play). Every other event is passed to `top.tick()`.
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
    events = input.tick(read_buttons(), now)
    stack.handle(events, now)
    input.repeat_paused = stack.overlay_active()   # no d-pad repeat in a menu
    stack.render(screen); screen.refresh()
```

## 5. Turn loop

Resolves bead `cd-e3p.3`. The loop body lives in `world.py` (pure, tested in
`tests/test_turn.py`); `modes.PlayMode` maps input to actions and renders.

### 5.1 Action

`PlayMode.tick(events, now)` takes the first play-mode event and maps it to an
**action** tuple:

| Event | Action | |
|---|---|---|
| `MOVE_N/S/E/W` | `("move", dx, dy)` | 4-way, ±1 |
| `wait` | `("wait",)` | passes a turn in place — chord: Left+Right / Up+Down / Down+B (provisional, `cd-e3p.14`) |
| `CONFIRM` / `CANCEL` / `AUX_X` / `AUX_Y` | — | belong to later beads (inventory, look); pass no turn |

At most one action per tick — extra events are dropped (auto-repeat is already
rate-capped in `input.py`, so >1 move per ~50 ms tick is nearly impossible).

### 5.2 `world.resolve_turn(world, scheduler, action, monster_turn)`

```
if not _apply_player_action(world, action):   # move → move_actor(); "moved" spends
    return False                              #   a turn, "blocked"/"bump"/None don't
for actor in scheduler.actors_for_turn():     # §1.1 — round-robin, hero first
    if actor is world.hero: continue
    monster_turn(world, actor)                # per-monster AI — cd-e3p.4 (no-op now)
_upkeep(world)                                # status ticks / regen — empty until cd-e3p.7
world.turn += 1
return True
```

- **A failed move (wall/edge) or a `bump` onto an actor passes no turn.** Bump
  becomes an attack (and *does* spend the turn) at `cd-e3p.5`; inert for now.
- `monster_turn` and `_upkeep` are the seams for `cd-e3p.4` / `cd-e3p.7`.
- Movement is an instant snap — `PlayMode.render()` repositions sprites from
  `world.actors` on the next frame (§1.4). No tween.
- `world.turn` counts real turns; `PlayMode.cycle` is the wall-clock pulse.

### 5.3 What's still open

- The three `wait` chord bindings are provisional (`cd-e3p.14`) — narrow to
  the one that proves reliable on hardware, using `DiagMode`'s stats.
- Repeat-pause while a monster is in view (§1.3) waits on FOV (`cd-e3p.6`);
  the engine currently only pauses repeat for overlays.

## 6. Monsters + AI  *(cd-e3p.4 — open)*
## 7. Combat  *(cd-e3p.5 — open)*
## 8. Field of view  *(cd-e3p.6 — open)*
## 9. Player model  *(cd-e3p.7 — open)*
## 10. Inventory model  *(cd-e3p.8 — open)*
## 11. Message log API  *(cd-e3p.9 — open)*
