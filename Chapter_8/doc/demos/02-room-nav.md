# 02 — Room navigation: edge gesture + room banner + room graph

Beads: `cd-45v.2` (edge gesture), `cd-45v.3` (room banner), `cd-45v.4` (room
graph) · Module: `game/room_nav_demo.py` (+ `rooms.py`, `edge_gesture.py`,
`room_banner.py`)

One demo, three prototypes: a tap/swipe that **starts** near a screen edge
moves you through a small 4-room graph in that edge's direction; a toast
banner announces the room + live exits on arrival, or flashes red on a
blocked move.

The demo world (`rooms.make_demo_world()`):

```
             [Yard]
               ^ up from Entryway / down from Entryway
[Kitchen] <--right-- [Living Room] --right--> [Entryway]
   (only exit: right, back to Living Room)     (only exits: left, down)
```
Start room: **Living Room** (exits: left→Kitchen, right→Entryway).

## Deploy

    Chapter_8/tools/deploy.sh --demo room_nav_demo

Reset the board. Serial prints `Ch8 room-nav demo ready -- start: Living
Room`, and the banner should immediately show `Living Room  (exits: left,
right)` for ~2.5s.

## Walkthrough

Edge-gesture reminder: a tap or swipe **starting** within ~30px of one edge
moves that direction, regardless of swipe direction. Starting near a corner
(inside two edges' margins at once) is ambiguous and should do nothing.

- [ ] **Startup banner** — on boot, banner shows `Living Room  (exits:
  left, right)`, auto-hides after ~2.5s.
- [ ] **Right → Entryway** — gesture starting near the right edge moves you;
  banner updates to `Entryway  (exits: left, down)`.
- [ ] **Down → Yard** — from Entryway, gesture starting near the bottom
  edge; banner updates to `Yard  (exits: up)`.
- [ ] **Blocked directions flash red** — from Yard, try left or right
  (no exit that way): banner flashes `can't go left` / `can't go right` in
  red, room does NOT change.
- [ ] **Up → back to Entryway** — confirms the graph round-trips.
- [ ] **Left → Living Room, then left again → Kitchen** — two hops back
  through the start room.
- [ ] **Kitchen is a dead end except right** — try up/down/left from
  Kitchen: all blocked (red flash); only right returns to Living Room.
- [ ] **Corner start is ignored** — a gesture starting near a corner
  (within margin of two edges at once) produces no move and no red flash —
  just silently does nothing. (Hardest one to eyeball; try a few corners.)
- [ ] **Edge margin feels right** — does ~30px from the edge feel like the
  natural "I meant to swipe from the edge" zone, or does it trigger by
  accident from more central touches / feel too narrow to hit reliably?
  This is the number to revisit (`EDGE_MARGIN` in `edge_gesture.py`).
- [ ] **Banner legible over the round bezel** — text + bar fully inside the
  visible round area, no clipping, readable at a glance.
- [ ] **No crash / no traceback** — a couple minutes of poking around,
  serial stays quiet.

## Notes

_(fill in after running on the board — does swipe vs. tap feel more
natural for triggering a move? does the margin need to change? anything to
flag for cd-zw2.1 / cd-zw2.4 / cd-zw2.5)_
