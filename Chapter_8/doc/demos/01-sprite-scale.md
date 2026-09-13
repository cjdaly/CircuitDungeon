# 01 — Mixed sprite-scale rendering

Beads: `cd-45v.1` · Module: `game/sprite_scale_demo.py`

Proves two `TileGrid`s at different tile scales can share the round screen:
a 16×16 scenery grid (floor/wall/rug) under two hand-drawn 32×32 "actor"
placeholders (no real Ch9 art yet), kept clear of the round bezel.

## Deploy

    Chapter_8/tools/deploy.sh --demo sprite_scale_demo

Reset the board. Serial should print `Ch8 sprite-scale demo ready`. No
touch or IMU involved — this one's just a static scene + a slow bob, so no
input to give it.

## Walkthrough

- [ ] **Scenery grid** — a 15×15 tile floor/wall grid fills the screen:
  darker "wall" tiles form a one-tile border around the edge, plain "floor"
  tiles everywhere else, and a reddish diamond "rug" tile dead center.
  Expect: the four corners get clipped by the round bezel — that's fine,
  it's background.
- [ ] **Two actors visible** — a red-bodied/tan-headed "hero" blob on the
  left and a blue round "critter" blob on the right, both roughly
  vertically centered, both fully inside the round bezel (not clipped).
- [ ] **Edge margin holds** — eyeball the gap between each actor and the
  screen's curved edge. Should look like a clean ~20px clearance, not
  tight/clipped. This is the number to revisit if it looks off
  (`_EDGE_MARGIN` in the module).
- [ ] **Bob animation** — both actors drift up/down slowly and smoothly
  (~2.4s per cycle), moving in opposite phase (one up while the other's
  down). No stutter, no tearing over the tile grid underneath.
- [ ] **No crash / no traceback** — let it run a minute or two; check
  serial stays quiet (no exceptions).

## Notes

_(fill in after running on the board — placeholder shapes read okay?
margin feel right? anything to flag for cd-zw2.2)_
