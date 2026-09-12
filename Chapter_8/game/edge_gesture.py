# SPDX-License-Identifier: MIT
"""Edge-region gesture classification for room-to-room navigation -- cd-45v.2
prototype (relates to Ch9's cd-zw2.4).

touch.py's GestureTracker classifies a tap/swipe from displacement + duration
alone -- it has no idea where on screen a gesture happened. room_nav_demo.py
(cd-45v.4) used that directly as a placeholder, treating any swipe direction
as a move attempt no matter where the finger started. This module adds the
missing piece: only a gesture that STARTS inside one edge's margin counts,
and the resulting direction is fixed by *which edge*, not by swipe
direction -- a tap or swipe starting near the left edge always means "go
left", matching rooms.py's up/down/left/right. A start inside two edges'
margins at once (a corner) is ambiguous and dropped rather than guessed.

Reuses touch.py's GestureTracker for the underlying tap/swipe classification.
Pure logic otherwise -- no displayio/board imports, runs under plain desktop
Python (see tests/test_edge_gesture.py). touch.py itself only needs
adafruit_cst8xx inside SafeTouch.poll(), so importing GestureTracker here
doesn't need real touch hardware either.

STATUS: UNTESTED ON DEVICE as of 2026-09-12 -- the classification logic is
unit-tested, but hooking this into room_nav_demo.py in place of its current
whole-screen-swipe placeholder hasn't been tried on the board yet.
"""
from rooms import DOWN, LEFT, RIGHT, UP
from touch import GestureTracker

EDGE_MARGIN = 30  # px from a frame edge -- matches the round-panel bezel
                  # inset noted in doc/HARDWARE.md ("Display"): content much
                  # closer to the edge than this is already clipped anyway.


class EdgeGestureTracker:
    """Wraps GestureTracker; .update() -> a rooms.py direction, or None."""

    def __init__(self, width, height, margin=EDGE_MARGIN):
        self._tracker = GestureTracker()
        self._width = width
        self._height = height
        self._margin = margin
        self._start = None

    def update(self, point, now):
        """Call once per frame with the latest touch point (or None) and time.

        Returns a rooms.py direction the tick a qualifying gesture completes,
        else None -- same call shape as GestureTracker.update().
        """
        if point is not None and self._start is None:
            self._start = point

        gesture = self._tracker.update(point, now)
        if gesture is None:
            return None

        start, self._start = self._start, None
        return self._edge_of(*start) if start is not None else None

    def _edge_of(self, x, y):
        edges = []
        if x < self._margin:
            edges.append(LEFT)
        if x > self._width - self._margin:
            edges.append(RIGHT)
        if y < self._margin:
            edges.append(UP)
        if y > self._height - self._margin:
            edges.append(DOWN)
        return edges[0] if len(edges) == 1 else None
