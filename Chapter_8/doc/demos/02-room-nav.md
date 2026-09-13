# 02 — Room navigation: edge gesture + room banner + room graph

Beads: `cd-45v.2` (edge gesture), `cd-45v.3` (room banner), `cd-45v.4` (room
graph) · Module: `game/room_nav_demo.py` (+ `rooms.py`, `edge_gesture.py`,
`room_banner.py`)

One demo, three prototypes: a tap/swipe that **starts** near a screen edge
moves you through a small 4-room graph in that edge's direction. The
current room's name sits persistently in the center; 4 small dots at the
edge-margin midpoints show live which directions are real exits right now.

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
Room`. The screen should show `Living Room` centered, with the left and
right dots pulsing green (live exits) and the up/down dots dim/static
(blocked).

## Walkthrough

Edge-gesture reminder: a tap or swipe **starting** within ~45px of one edge
moves that direction, regardless of swipe direction. Starting near a corner
(inside two edges' margins at once) is ambiguous and does nothing. Touching
a zone snaps its dot to **gold** if it's a live exit or **red** if it's
blocked, live, on every frame — you don't need to complete the gesture to
see which zone you're in.

- [ ] **Startup state** — `Living Room` centered; left/right dots pulsing
  green, up/down dots dim.
- [ ] **Touching a dot highlights it correctly** — touch near the right
  edge: that dot goes gold (it's a live exit). Touch near the top edge:
  that dot goes red (blocked here).
- [ ] **Right → Entryway** — complete a tap/swipe starting near the right
  edge; center text updates to `Entryway`, and its dots update: left/down
  pulse green, up/right go dim.
- [ ] **Down → Yard** — from Entryway, gesture starting near the bottom
  edge; center text → `Yard`, only the up dot pulses green, the other 3 dim.
- [ ] **Blocked directions** — from Yard, touch/gesture left or right: dot
  goes red, banner flashes `can't go left`/`can't go right`, room name does
  NOT change.
- [ ] **Up → back to Entryway** — confirms the graph round-trips.
- [ ] **Left → Living Room, then left again → Kitchen** — two hops back
  through the start room; Kitchen should show only its right dot green.
- [ ] **Kitchen is a dead end except right** — try up/down/left from
  Kitchen: all blocked (red dot + banner flash); only right returns to
  Living Room.
- [ ] **Corner start is ignored** — a gesture starting near a corner
  (within margin of two edges at once) produces no move, no dot highlight,
  and no red flash — just silently does nothing.
- [ ] **45px margin feels right** — does the zone feel comfortably easy to
  hit now (bumped from 30px 2026-09-13), or does it need to go bigger
  still / feel like it's triggering by accident from more central touches?
  (`EDGE_MARGIN` in `edge_gesture.py`.)
- [ ] **Room name + dots legible over the round bezel** — nothing clipped,
  readable at a glance.
- [ ] **No crash / no traceback** — a couple minutes of poking around,
  serial stays quiet.

## Notes

_(fill in after running on the board — does swipe vs. tap feel more
natural for triggering a move? does the margin need to change further?
anything to flag for cd-zw2.1 / cd-zw2.4 / cd-zw2.5)_
