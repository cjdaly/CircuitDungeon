# Chapter 7 — Button Input Model

Resolves bead `cd-e3p.11`. Implemented in `Chapter_7/game/input.py`, tested by
`Chapter_7/tests/test_input.py`. Sits above `hardware.read_buttons()` and
feeds the mode dispatch (`cd-e3p.12`), the turn loop (`cd-e3p.3`), menus
(`cd-e3p.13`), and the diagnostics input page (`cd-89o.6`).

## Contract

```python
m = InputModel(chords=None, repeat_delay=0.28, repeat_interval=0.13)

events = m.tick(buttons, now)   # buttons: read_buttons() dict; now: monotonic s
                               # -> list of event strings produced this tick
ev = m.get()                   # pop oldest queued event, or None
```

The engine calls `tick()` once per loop pass (~20 fps) and pulls **one**
event per pass with `get()` (`ENGINE.md` §1.5). Pure module — no `displayio`,
no `board`, no `time`; the caller supplies `now`.

## Button map

| Hardware | Event | Notes |
|---|---|---|
| D-pad Up | `MOVE_N` | edge on press, then auto-repeat while held |
| D-pad Down | `MOVE_S` | " |
| D-pad Left | `MOVE_W` | " |
| D-pad Right | `MOVE_E` | " |
| A | `CONFIRM` | fires once per press; **no** long-press / repeat |
| B | `CANCEL` | " |
| X | `AUX_X` | " |
| Y | `AUX_Y` | " |

Movement is 4-way (`ENGINE.md` §1.3) — no diagonal input. Face-button events
are semantic (`CONFIRM`/`CANCEL`), not physical, so menu/UI code doesn't
hard-code "A".

## Chord table

Simultaneous button pairs, edge-triggered, **fire once per hold** (release
one member to re-arm). The model emits the bound *name* verbatim — it doesn't
know what "diag" or "menu" do.

| Chord | Name | Consumer |
|---|---|---|
| X + Y | `diag` | enter on-device diagnostics (`cd-89o.6`) |
| A + B | `menu` | enter main menu / settings (`cd-e3p.13`) |

The table is passed to the constructor and is extensible — the turn loop or a
UI screen can add bindings (e.g. `Up+A` → something). `DEFAULT_CHORDS` in
`input.py` holds the two above.

### How chords stay reliable

Any button that appears in a chord holds its single-press for `CHORD_WINDOW`
(50 ms ≈ one tick):

- both members go down within the window → **chord fires**, both pending
  singles are cancelled.
- window passes with only one member down → the **single** fires; that button
  is now "singled" for the rest of the hold and can't join a chord until
  released. (So "hold A, then press B a second later" is `CONFIRM` then
  `CANCEL`, not `menu`.)
- a member is tapped and released inside the window → the single still fires
  (a fast tap isn't lost).

D-pad buttons are never in a chord, so they never incur the delay.

## Timing

| Param | Default | Meaning |
|---|---|---|
| `repeat_delay` | 0.28 s | held d-pad: press → first repeat |
| `repeat_interval` | 0.13 s | between repeats (~7.5/s) |
| `CHORD_WINDOW` | 0.05 s | single-press hold for chord-eligible buttons |

`repeat_delay` / `repeat_interval` are **instance attributes**, retunable live
by the settings screen (`cd-e3p.13`). `m.repeat_paused = True` suppresses
repeats — the engine sets it each tick while a monster is in view
(`ENGINE.md` §1.3) or a non-play mode is up.

## Output queue

Bounded at **4**, drop-oldest. If the player out-runs turn resolution, stale
inputs are discarded rather than banked (turn-based — a 2-second-old move is
noise).

## Instrumentation (for `cd-89o.6`)

Always recording from construction; kept tiny.

```python
m.trace()      # -> list of (t_ms, kind, detail), oldest first, ring of 32
               #    kind in {press, release, repeat, chord, single}
m.snapshot()   # -> {"held": [...], "hold_ms": {btn: ms},
               #     "chord_candidates": [[a,b], ...],   # partially-held chords
               #     "chord_fired": [...], "queue_depth": n}
```

`t_ms` is `int(now*1000)` masked to 24 bits (wraps every ~4.6 h — fine for a
scrolling debug view).
