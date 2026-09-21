
# CircuitDungeon - Chapter 9 - Christmas Critters

TODO ...

The game for the Waveshare RP2350-Touch-LCD-1.28 (round display), building on
techniques proved out in [Chapter 8](../Chapter_8) (all five `cd-45v`
prototypes -- sprite scales, edge-gesture navigation, room banners, room
graph, ornament mode -- verified on real hardware 2026-09-13). Tracked in
beads under `cd-zw2` (the building blocks, done) and `cd-342` (the playable
build); design notes will land in `doc/` as they solidify. To run it on a
board see [`doc/DEPLOY.md`](doc/DEPLOY.md).

## What's here

* **Room-graph model** (`game/rooms.py`, `cd-zw2.1`) -- ported from
  Chapter 8's `cd-45v.4` prototype, same `Room`/`World` API. Pure data +
  movement logic, no hardware deps. Off-device tests in `tests/`.
* **Room roster** (`rooms.make_world()`, `cd-zw2.6`) -- the real Ch9
  content: 10 rooms (Living Room start, Kitchen, Basement, Entryway,
  Bedroom, Kids' Bedroom, Yard, Pond, Tree House, Cave). Only the Living
  Room has detailed `items` content so far (tree, fireplace, cookies/milk,
  presents) -- the rest are placeholder rooms pending further content/art.
  Tests check every exit has a matching return exit and every room is
  reachable from the start, not just the specific room content.
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
* **Mixed sprite-scale rendering** (`game/sprite_scale.py`, `cd-zw2.2`) --
  generic helpers for a 16x16 scenery `TileGrid` from a tile sheet + layout,
  and free-positioned 32x32 actor sprites kept clear of the round bezel
  (`clamp_actor_position`). Generalized from Chapter 8's `cd-45v.1`
  prototype (which hardcoded one demo scene) into reusable building blocks
  -- no room content or actual hero/critter art lives here, that's separate
  content/art work. `clamp_actor_position` is pure arithmetic and unit
  tested; the `TileGrid`-building functions need displayio (lazy-imported,
  same trick as `touch.py`'s `adafruit_cst8xx`) so they're desk-checked
  only.
* **Ornament mode** (`game/ornament.py`, `game/stillness.py`,
  `game/screen_blanker.py`, `cd-zw2.7`) -- a non-interactive ambient scene
  (tree, pulsing star, twinkling ornaments, drifting snow) for hanging the
  device on a real tree, no gameplay/input expected. Ported from Chapter
  8's `cd-45v.5` prototype (confirmed on real hardware 2026-09-13).
  `stillness.StillnessDetector` tells "hanging still" apart from "being
  handled" from IMU jerk alone; `screen_blanker.ScreenBlanker` (also ported,
  general-purpose, not ornament-specific) blanks the backlight after a long
  idle stretch and wakes on being handled. `ornament.py` is the scene only
  -- no `main()`/hardware calls; wiring it all together into an actual
  on-device entry point is future integration work.
* **Critter mechanic** (`game/critters.py`, `cd-zw2.3`) -- `Critter` state
  machine (`in_box` -> `hiding` -> `returned`, `returned` is terminal) and
  `CritterRoster` (lookup by name / by current room). Retrieval requires
  finding the critter in the right room AND holding its preferred item
  together, not either alone. New design work, not a Ch8 port -- no prior
  prototype existed. Deliberately doesn't decide the escape *trigger*
  (time-based? player-action-based? -- still unspecified per the design
  notes) or "holding an item" (`try_retrieve` takes any `held_items`
  collection, decoupled from `rooms.py`'s `Room.items`); those are left to
  a future game loop. No real critter roster (names/preferred items)
  either -- placeholder critters only exist in tests, same as room content
  waited for `cd-zw2.6` once the room model existed. Fully unit tested, 15
  tests, pure state logic.

* **On-device entry point** (`game/main.py`, `game/app.py`,
  `game/nav_view.py`, `game/modes.py`, `cd-342.1`/`cd-342.2`) -- the first
  runnable Ch9 build. `main.py` is just hardware bootstrap
  (`hardware.py`/`imu.py`/`boot.py` are copied unchanged from Chapter 8);
  `app.run()` is the loop, taking its hardware as arguments so it can be
  smoke-tested off-device. Interactive mode is room navigation
  (`nav_view.NavView`: persistent room label, live edge-exit markers,
  blocked-move flash -- the Ch8 `room_nav_demo.py` UI, made reusable) over
  the real 10-room world. `modes.ModeController` switches to ornament mode
  when the device has been untouched AND still (IMU) for 30s, and back on
  any touch -- BOOT can't be a toggle on RP2350 (`cd-bp3.9`). A touch that
  wakes the device (from ornament or a blanked screen) is swallowed along
  with the rest of that finger-down. Screen blanking is per-mode (2 min of
  no touch interactive, 5 min of stillness ornament). No critters, items or
  art yet -- see the `cd-342` epic. `modes.py` is unit tested;
  `tests/test_app_smoke.py` drives `app.run()` through navigation, blocked
  moves, and both mode switches against stubbed `displayio`, which catches
  wiring bugs but says nothing about how it looks. **Not yet run on real
  hardware.**

## Layout

```
game/      deployed to CIRCUITPY by tools/deploy.sh; mostly plain Python
           modules testable off-device (rooms.py, touch.py's
           GestureTracker, edge_gesture.py, sprite_scale.py's
           clamp_actor_position, stillness.py, screen_blanker.py,
           critters.py, modes.py); room_banner.py, nav_view.py,
           sprite_scale.py's TileGrid builders, and ornament.py need
           displayio so they're desk-checked only (app.py is exercised
           against stubbed displayio by tests/test_app_smoke.py)
tools/     deploy.sh -- see doc/DEPLOY.md
doc/       DEPLOY.md
tests/     off-device unit tests -- `python3 tests/test_<name>.py`, no
           hardware or CircuitPython needed
```

(`cad/` etc. will show up here as this chapter grows, mirroring Chapter
7/8's layout.)

