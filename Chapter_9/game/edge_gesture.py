# SPDX-License-Identifier: MIT
"""Edge-region gesture classification for room-to-room navigation -- cd-zw2.4.

touch.py's GestureTracker classifies a tap/swipe from displacement + duration
alone -- it has no idea where on screen a gesture happened. This module turns
those into rooms.py's up/down/left/right:

- A tap moves if it STARTS outside the centre disk (CENTER_RADIUS): the
  screen is round, so the ring around the centre is split into four wedges
  along the diagonals, and the wedge you tap is the way you go. The centre
  disk is for in-panel taps (critters, lures). No dead corners -- every
  point on the glass is either a direction or the centre (cd-342 feedback
  2026-11-06: the old 45px square-frame bands were thin slivers on the
  round glass and edge taps kept missing).
- A swipe drags the world, from anywhere on screen, the way a watch or phone
  does: swiping left brings in the room to the right (cd-342.22).

Ported from Chapter_8/game/edge_gesture.py (cd-45v.2's prototype) -- same
API. Chapter 8 used 45px bands along the square frame's edges; Chapter 9
switched to radial wedges, which fit the round panel.

Reuses touch.py's GestureTracker for the underlying tap/swipe classification.
Pure logic otherwise -- no displayio/board imports, runs under plain desktop
Python (see tests/test_edge_gesture.py). touch.py itself only needs
adafruit_cst8xx inside SafeTouch.poll(), so importing GestureTracker here
doesn't need real touch hardware either.
"""
from rooms import DOWN, LEFT, RIGHT, UP
from touch import GestureTracker

# The finger's direction -> the way the player goes, like dragging a page.
_SWIPE_MOVES = {"swipe_left": RIGHT, "swipe_right": LEFT, "swipe_up": DOWN, "swipe_down": UP}

CENTER_RADIUS = 60  # px -- taps inside this disk are centre taps; outside,
                    # the wedge decides the direction. The panel's radius is 120,
                    # so each wedge is 60px deep at its edge midpoint (the old
                    # band was 45px there and tapered to nothing).


def edge_of(x, y, width, height, center_radius=CENTER_RADIUS):
    """Which direction's wedge (x, y) falls in, or None inside the centre disk.

    Module-level (not just EdgeGestureTracker-internal) so a UI can show
    live "which zone is my finger in" feedback on every frame, not just the
    edge a *completed* gesture started from.
    """
    dx = x - width / 2
    dy = y - height / 2
    if dx * dx + dy * dy < center_radius * center_radius:
        return None
    if abs(dx) >= abs(dy):
        return LEFT if dx < 0 else RIGHT
    return UP if dy < 0 else DOWN


class EdgeGestureTracker:
    """Wraps GestureTracker; .update() -> a rooms.py direction, or None."""

    def __init__(self, width, height, center_radius=CENTER_RADIUS):
        self._tracker = GestureTracker()
        self._width = width
        self._height = height
        self._center_radius = center_radius
        self._start = None
        self.center_tapped = False  # True for the one tick a center tap completes
        self.gesture_done = False  # True for the one tick any gesture completes

    def update(self, point, now):
        """Call once per frame with the latest touch point (or None) and time.

        Returns a rooms.py direction the tick a qualifying gesture completes,
        else None -- same call shape as GestureTracker.update(). A tap inside the
        centre disk returns None and sets .center_tapped for that tick.
        """
        self.center_tapped = False
        self.gesture_done = False
        if point is not None and self._start is None:
            self._start = point

        gesture = self._tracker.update(point, now)
        if gesture is None:
            return None

        start, self._start = self._start, None
        if start is None:
            return None
        self.gesture_done = True
        if gesture != "tap":
            return _SWIPE_MOVES[gesture]
        direction = edge_of(start[0], start[1], self._width, self._height, self._center_radius)
        self.center_tapped = direction is None
        return direction
