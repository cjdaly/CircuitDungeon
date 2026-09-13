# SPDX-License-Identifier: MIT
"""Edge-region gesture classification for room-to-room navigation -- cd-zw2.4.

touch.py's GestureTracker classifies a tap/swipe from displacement + duration
alone -- it has no idea where on screen a gesture happened. This module adds
the missing piece: only a gesture that STARTS inside one edge's margin
counts, and the resulting direction is fixed by *which edge*, not by swipe
direction -- a tap or swipe starting near the left edge always means "go
left", matching rooms.py's up/down/left/right. A start inside two edges'
margins at once (a corner) is ambiguous and dropped rather than guessed.

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
        if start is None:
            return None
        return edge_of(start[0], start[1], self._width, self._height, self._margin)
