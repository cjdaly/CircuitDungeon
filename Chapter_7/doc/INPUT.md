# Chapter 7 — Button Input Model

Beads `cd-e3p.11` (model) and `cd-e3p.14` (wait chords + diagnostics).
Implemented in `Chapter_7/game/input.py`, tested by
`Chapter_7/tests/test_input.py`. Sits above `hardware.read_buttons()` and
feeds the mode dispatch (`cd-e3p.12`), the turn loop (`cd-e3p.3`), menus
(`cd-e3p.13`), and the diagnostics input page (`cd-89o.6`).

## PicoSystem controls

D-pad on the left; four face buttons in a diamond on the right. GPIO map from
Pimoroni's SDK (`A=18 B=19 X=17 Y=16 UP=23 DOWN=20 LEFT=22 RIGHT=21`). The
**physical face-button positions** (Chris's unit):

```
      X (top)
Y (left)   A (right)
      B (bottom)
```

So `CONFIRM = A` is the right button, `CANCEL = B` the bottom one, and the
`Down + B` wait chord is "both thumbs pressing *down*". No centre button is
exposed to CircuitPython.

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

| Chord | Name | Consumer | |
|---|---|---|---|
| X + Y | `diag` | on-device diagnostics (`cd-89o.6`) | |
| A + B | `menu` | main menu / settings (`cd-e3p.13`) | |
| Left + Right | `wait` | pass a turn (`world.resolve_turn`) | *provisional* |
| Up + Down | `wait` | " | *provisional* |
| Down + B | `wait` | " | *provisional*, Chris's pick |

`DEFAULT_CHORDS` in `input.py` holds these; the table is passed to the
constructor and is extensible.

**The three `wait` bindings are an experiment (`cd-e3p.14`).** Opposing d-pad
squeezes may or may not register cleanly on the real rocker; `Down + B` should
be the most reliable. The diagnostics input page (`DiagMode`) shows
`chord_stats()` — fire / miss counts and press-spread per binding — so the
losers can be dropped after a hardware session.

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

**With the `wait` bindings, every d-pad direction is chord-eligible**, so
every move press now takes the 50 ms deferral (previously d-pad fired
immediately). Imperceptible in a turn game, but revisit if the `wait`
bindings are narrowed to just `Down + B` — then Up/Left/Right could fire
immediately again.

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

## Instrumentation

Always recording from construction; kept tiny. Rendered by `DiagMode`
(`modes.py`) — flip to it with the `X + Y` chord.

```python
m.trace()        # -> list of (t_ms, kind, detail), oldest first, ring of 32
                 #    kind in {press, release, repeat, chord, single, miss}
m.snapshot()     # -> {"held": [...], "hold_ms": {btn: ms},
                 #     "chord_candidates": ["a+b", ...],  # partially-held chords
                 #     "chord_armed": [...], "queue_depth": n}
m.chord_stats()  # -> one row per binding:
                 #    {"combo": "b+down", "name": "wait",
                 #     "fired": n, "missed": n, "last_spread_ms": ms}
```

- **`fired`** — the chord landed.
- **`missed`** — both members were held but one had already fired its
  single-press (the d-pad rocked / the squeeze was too slow). Counted once per
  attempt.
- **`last_spread_ms`** — gap between the two members' press timestamps on the
  last fire. Small = the hardware registers them near-simultaneously.

`t_ms` is `int(now*1000)` masked to 24 bits (wraps every ~4.6 h — fine for a
scrolling debug view).
