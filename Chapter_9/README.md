
# CircuitDungeon - Chapter 9 - Christmas Critters

TODO ...

The game for the Waveshare RP2350-Touch-LCD-1.28 (round display), building on
techniques proved out in [Chapter 8](../Chapter_8) (all five `cd-45v`
prototypes -- sprite scales, edge-gesture navigation, room banners, room
graph, ornament mode -- verified on real hardware 2026-09-13). Tracked in
beads under `cd-zw2`; design notes will land in `doc/` as they solidify.

## What's here

* **Room-graph model** (`game/rooms.py`, `cd-zw2.1`) -- ported from
  Chapter 8's `cd-45v.4` prototype, same `Room`/`World` API. Pure data +
  movement logic, no hardware deps. Off-device tests in `tests/`.
* **Edge-gesture navigation** (`game/touch.py`, `game/edge_gesture.py`,
  `cd-zw2.4`) -- ported from Chapter 8's `cd-45v.2` prototype (touch
  controller wrapper + tap/swipe classifier + edge-margin gesture
  classification). `EDGE_MARGIN` already carries the 45px tuning found on
  real hardware 2026-09-13 (bumped up from an initial 30px that felt too
  narrow). `touch.py`'s hardware bits (`SafeTouch`) aren't unit-tested (need
  real I2C), but `GestureTracker`/`edge_gesture.py` are, in `tests/`.
* **Room-name display + move feedback** (`game/room_banner.py`, `cd-zw2.5`)
  -- `RoomLabel` (persistent centered room-name text) and `RoomBanner`
  (transient "can't go `<direction>`" flash on a blocked move). Ported from
  Chapter 8's `cd-45v.3`, updated for what on-device testing there actually
  found: a toast is a poor way to answer "what room am I in", so that's now
  `RoomLabel` (persistent), while `RoomBanner` (the original toast) is kept
  for genuinely transient messages. Font is plain `terminalio.FONT` for
  now -- see `cd-bp3.11` (investigating a comic-book-style font instead).

## Layout

```
game/      copied to CIRCUITPY once on-device code exists; for now, plain
           Python modules testable off-device (rooms.py, touch.py's
           GestureTracker, edge_gesture.py); room_banner.py needs displayio
           so it's desk-checked only, not unit-tested
tests/     off-device unit tests -- `python3 tests/test_<name>.py`, no
           hardware or CircuitPython needed
```

(`doc/`, `cad/`, `tools/` etc. will show up here as this chapter grows,
mirroring Chapter 7/8's layout.)

