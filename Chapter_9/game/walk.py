# SPDX-License-Identifier: MIT
"""Critter walking motion: waypoint patrol + facing + hop bob -- cd-342.3.

The candidate art is 2-frame and side-on only, so "walking" is built from
three cheap things layered together (see doc/CRITTERS.md, *Showing movement*):

  1. **Position** slides between waypoints at a constant speed (Patrol).
  2. **Facing** is a mirror: the sprites are drawn facing left, so heading
     right sets flip_x (displayio.TileGrid.flip_x). Facing sticks through
     vertical legs and pauses -- a critter that walks down the screen keeps
     the side it was last heading, as top-down games with side-view sprites do.
  3. **Step cadence + bob**: the caller flips the 2 animation frames faster
     while moving than at rest, and bob() lifts the sprite a pixel or two in
     time with the steps so it hops instead of gliding.

Pure logic, no displayio/board imports -- runs under plain desktop Python
(see tests/test_walk.py). Used by critter_demo.py's walk mode now; meant to
be reused when critters really move around rooms. come_in() is a follower
walking in behind you (scene_view, cd-342.50).
"""
import math

from rooms import DOWN, LEFT, RIGHT, UP

DEFAULT_SPEED = 40.0  # px / second
DEFAULT_PAUSE = 0.6  # seconds standing still at each waypoint
_MAX_DT = 0.25  # clamp a long gap between updates so a hiccup doesn't teleport


class Patrol:
    """Loops through `waypoints` ((x, y) top-left positions) forever.

    .update(now) -> (x, y, moving, facing_right); x, y are ints. The first
    call places the walker on waypoint 0 and starts toward waypoint 1.
    """

    def __init__(self, waypoints, speed=DEFAULT_SPEED, pause=DEFAULT_PAUSE):
        if len(waypoints) < 2:
            raise ValueError("a patrol needs at least 2 waypoints")
        self._wps = [(float(x), float(y)) for x, y in waypoints]
        self._speed = speed
        self._pause = pause
        self._x, self._y = self._wps[0]
        self._target = 1
        self._last = None
        self._pause_until = 0.0
        self.facing_right = False  # sprites are drawn facing left

    def update(self, now):
        if self._last is None:
            self._last = now
            return int(self._x), int(self._y), False, self.facing_right
        dt = min(now - self._last, _MAX_DT)
        self._last = now

        moving = False
        if now >= self._pause_until:
            tx, ty = self._wps[self._target]
            dx, dy = tx - self._x, ty - self._y
            dist = math.sqrt(dx * dx + dy * dy)
            step = self._speed * dt
            if dx > 0:
                self.facing_right = True
            elif dx < 0:
                self.facing_right = False
            if dist <= step:
                self._x, self._y = tx, ty
                self._target = (self._target + 1) % len(self._wps)
                self._pause_until = now + self._pause
            else:
                self._x += dx / dist * step
                self._y += dy / dist * step
                moving = True
        return int(round(self._x)), int(round(self._y)), moving, self.facing_right


def come_in(edge, home, t, seconds, size=64, width=240):
    """Where a critter coming in by `edge` (rooms.LEFT, ...) is, `t` s after
    the room appeared, on its way to `home` (its top-left): from just off the
    panel at that edge, slowing as it arrives, there at `seconds`.
    Returns (x, y, moving)."""
    hx, hy = home
    sx, sy = hx, hy  # no allocation per frame: this runs every tick
    if edge == LEFT:
        sx = -size
    elif edge == RIGHT:
        sx = width
    elif edge == UP:
        sy = -size
    elif edge == DOWN:
        sy = width
    u = min(max(t / seconds, 0.0), 1.0)
    u = 1 - (1 - u) * (1 - u)
    return int(sx + (hx - sx) * u), int(sy + (hy - sy) * u), t < seconds


def bob(now, step_period, px):
    """Pixels to lift a walking sprite: 0..px, one hop per animation step."""
    return int(round(px * abs(math.sin(math.pi * now / step_period))))
