# SPDX-License-Identifier: MIT
"""The escape cutscene as comic beats -- cd-342.10, doc/STYLE.md sec 4.

Each beat names a home_view shot (what the scene shows) and the words or
glyphs the comic kit puts over it. nav_view splices these into an episode's
opening captions, after the hour and before "<NAME> ESCAPED!". Every beat can
be tapped past, like any caption.

Pure data (the shot names are plain strings), so it runs under desktop Python
(see tests/test_escape.py).
"""
from beats import Beat
from rooms import DOWN, LEFT, RIGHT, UP

CALM = "calm"
RATTLE = "rattle"
CLOSEUP = "closeup"
POP = "pop"
PEEK = "peek"
NAME = "name"
BOLT = "bolt"
CLOSE_SHOTS = (CLOSEUP, POP, PEEK, NAME)  # cut in: no room name or edge markers

# "!" over the close-up box (screen px, the glyph's top-left at 2x).
_BANG = (("bang", 104, 52),)

# The bolt (cd-342.49, Chris 2026-11-24): not a straight dash but a show -- a
# Z around the Living Room, then out the way it went. It starts by running AWAY
# from its exit, so a critter whose box is on that side still takes a walkabout.
# Waypoints are the runner's top-left (a 32px sprite), each on the round panel;
# the last is off it, past the exit's edge.
_ROUTES = {
    RIGHT: ((28, 112), (176, 84), (72, 150), (260, 118)),
    LEFT: ((180, 112), (32, 84), (136, 150), (-52, 118)),
    UP: ((180, 140), (30, 104), (176, 52), (104, -52)),
    DOWN: ((30, 70), (180, 96), (40, 128), (104, 260)),
}
# Its legs, (seconds, easing): out of the box, slowing into the first turn;
# two zigzags, slowing into each corner; a stop to look back; then a dash
# that speeds up all the way out. PAUSE and DASH are indexes into this.
_OUT, _ZIG, _STAY, _IN = "out", "zig", "stay", "in"
_LEGS = ((0.6, _OUT), (0.8, _ZIG), (0.75, _ZIG), (0.45, _STAY), (0.7, _IN))
PAUSE, DASH = 3, 4
BOLT_S = sum(seconds for seconds, _ease in _LEGS) + 0.3  # a moment after it's gone


def _ease(kind, u):
    if kind == _OUT:
        return 1 - (1 - u) * (1 - u)
    if kind == _ZIG:
        return u * u * (3 - 2 * u)
    if kind == _IN:
        return u * u
    return 0.0


def bolt_at(start, direction, t):
    """Where the bolting critter is `t` s into the bolt shot, from its box's
    `start` (x, y), leaving by `direction`: (x, y, ux, uy, leg). (ux, uy) is the
    way it's facing, roughly a unit vector; `leg` indexes _LEGS (PAUSE, DASH)."""
    route = _ROUTES.get(direction, _ROUTES[LEFT])
    points = (start, route[0], route[1], route[2], route[2], route[3])
    leg = 0
    while leg < len(_LEGS) - 1 and t >= _LEGS[leg][0]:
        t -= _LEGS[leg][0]
        leg += 1
    seconds, kind = _LEGS[leg]
    u = _ease(kind, min(t / seconds, 1.0))
    (x0, y0), (x1, y1) = points[leg], points[leg + 1]
    if leg == PAUSE:  # standing still, looking back from where it's about to dash
        (fx, fy), (tx, ty) = points[leg + 2], points[leg + 1]
        size = max(abs(tx - fx), abs(ty - fy), 1)
        return (x0, y0, (tx - fx) / size, (ty - fy) / size, leg)
    dx, dy = x1 - x0, y1 - y0
    size = max(abs(dx), abs(dy), 1)
    return (int(x0 + dx * u), int(y0 + dy * u), dx / size, dy / size, leg)


def cutscene():
    """The beats from a box starting to rattle to its critter bolting."""
    return [
        Beat(shot=RATTLE, burst="Rattle!", duration=1.6),
        Beat(shot=CLOSEUP, emanata=_BANG, duration=1.2),
        Beat(shot=POP, burst="Pop!", duration=0.7),
        Beat(shot=PEEK, duration=1.3),
        Beat(shot=NAME, duration=1.6),
        Beat(shot=BOLT, duration=BOLT_S),
    ]
