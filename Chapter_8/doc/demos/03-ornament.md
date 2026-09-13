# 03 — Ornament / idle-mode ambient scene

Beads: `cd-45v.5` · Module: `game/ornament_demo.py` (+ `stillness.py`)

A non-interactive ambient scene (tree, pulsing star, twinkling ornaments,
drifting snow — all `vectorio` primitives, no bitmap art) that dims while
the board is being handled and lights up once it's been quiet for a few
seconds, standing in for "actually hanging on the tree."

## Deploy

    Chapter_8/tools/deploy.sh --demo ornament_demo

Reset the board. Serial prints `Ch8 ornament demo ready`. Leave it flat on
the desk or hold it steady to start.

## Walkthrough

- [ ] **Scene renders** — a green triangular tree with a brown trunk, a
  star at the apex, 5 ornament dots, and 6 falling snow dots, all inside
  the round bezel (nothing clipped by the curve).
- [ ] **Starts "handled"** — on boot, tree/star should render dim, bottom
  debug line reads `handled`. (Starts this way on purpose — see
  `stillness.py`.)
- [ ] **Goes "still" after ~3s of no motion** — set the board down flat and
  don't touch it; after about 3 seconds, debug line flips to `still`, tree
  brightens, star starts a slow pulse, and the 5 ornaments begin cycling
  through colors on a staggered ~1.6s beat.
- [ ] **Picking it up flips back to "handled"** — pick the board up / give
  it a nudge: debug line flips back to `handled` immediately, tree dims,
  star goes flat dim, ornaments stop cycling.
- [ ] **Snow keeps falling either way** — the 6 snow dots drift downward
  continuously in both "handled" and "still" states, wrapping to the top
  when they reach the bottom.
- [ ] **Threshold feel** — is `STILL_JERK_MAX` (2.0 m/s²) forgiving enough
  that just *resting* the board (tiny desk vibration, breathing near it)
  doesn't count as "handled"? Is 3s the right hold time, or does it feel
  laggy/twitchy switching modes? These are the numbers to revisit
  (`stillness.py`).
- [ ] **Debug line placement** — bottom debug text (`handled`/`still`) is
  legible and not clipped by the round bezel at the bottom edge.
- [ ] **No crash / no traceback** — a few minutes of alternating
  still/handled, serial stays quiet. Also watch for an `OSError` burst from
  the IMU read (the demo should just hold the last mode, not crash — see
  `except (OSError, ValueError, RuntimeError)` in the main loop).

## Notes

_(fill in after running on the board — do the thresholds need tuning? does
hanging by an actual hook (once cd-bp3.6.2 exists) still read as "still"
given whatever residual sway there is? anything to flag for cd-zw2.7)_
