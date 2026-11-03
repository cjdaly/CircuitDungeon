# SPDX-License-Identifier: MIT
"""Edge-region gesture classification for room-to-room navigation -- cd-zw2.4.

touch.py's GestureTracker classifies a tap/swipe from displacement + duration
alone -- it has no idea where on screen a gesture happened. This module turns
those into rooms.py's up/down/left/right:

- A tap only moves if it STARTS inside one edge's margin: tapping near the left
  edge means "go left". A start inside two margins at once (a corner) is
  ambiguous and dropped rather than guessed.
- A swipe drags the world, from anywhere on screen, the way a watch or phone
  does: swiping left brings in the room to the right (cd-342.22).

Ported from Chapter_8/game/edge_gesture.py (cd-45v.2's prototype) -- same
API, including EDGE_MARGIN already tuned to 45px after on-device feel
testing 2026-09-13 found the original 30px too narrow to hit reliably.

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

EDGE_MARGIN = 45  # px from a frame edge -- see doc/HARDWARE.md-equivalent
                  # bezel-inset guidance; tuned up from an initial 30px
                  # after on-device testing (Chapter_8's cd-45v.2).


def edges_within(x, y, width, height, margin=EDGE_MARGIN):
    """Every edge whose margin (x, y) falls in -- 0, 1, or 2 (a corner)."""
    edges = []
    if x < margin:
        edges.append(LEFT)
    if x > width - margin:
        edges.append(RIGHT)
    if y < margin:
        edges.append(UP)
    if y > height - margin:
        edges.append(DOWN)
    return edges


def edge_of(x, y, width, height, margin=EDGE_MARGIN):
    """Which single edge margin (x, y) falls in, or None if it's in none/two.

    Module-level (not just EdgeGestureTracker-internal) so a UI can show
    live "which zone is my finger in" feedback on every frame, not just the
    edge a *completed* gesture started from.
    """
    edges = edges_within(x, y, width, height, margin)
    return edges[0] if len(edges) == 1 else None


class EdgeGestureTracker:
    """Wraps GestureTracker; .update() -> a rooms.py direction, or None."""

    def __init__(self, width, height, margin=EDGE_MARGIN):
        self._tracker = GestureTracker()
        self._width = width
        self._height = height
        self._margin = margin
        self._start = None
        self.center_tapped = False  # True for the one tick a center tap completes
        self.gesture_done = False  # True for the one tick any gesture completes

    def update(self, point, now):
        """Call once per frame with the latest touch point (or None) and time.

        Returns a rooms.py direction the tick a qualifying gesture completes,
        else None -- same call shape as GestureTracker.update(). A tap outside
        every edge margin returns None and sets .center_tapped for that tick.
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
        if not edges_within(start[0], start[1], self._width, self._height, self._margin):
            self.center_tapped = True
        return edge_of(start[0], start[1], self._width, self._height, self._margin)
