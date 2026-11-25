# SPDX-License-Identifier: MIT
"""The escape cutscene as comic beats -- cd-342.10, doc/STYLE.md sec 4.

Each beat names a home_view shot (what the scene shows) and the words or
glyphs the comic kit puts over it. nav_view splices these into an episode's
opening captions, after the hour and before "<NAME> ESCAPED!". Every beat can
be tapped past, like any caption.

Pure data (the shot names are plain strings), so it runs under desktop Python
(see tests/test_escape.py).
"""
import math

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

# The bolt (cd-342.49; on the floor, cd-342.51 -- Chris 2026-11-25: flying
# belongs to the reindeer's finale). A show, not a straight dash: the critter
# hops out of its box onto the rug, hops across to the far side of the room,
# back again, stops to look back, then dashes out the way it went -- off the
# side, or for the way up (into the back of the house) behind the tree. It
# stays on the floor the whole time: it only moves up and down the screen as
# it goes deeper into the room or comes forward, plus its hops.
# Screen px, the runner's top-left x and its FEET y (a 32px sprite at 1x, its
# art down to row 31): the Living Room's plank floor starts at y 162 and the
# rug runs to about 210 (art_sets' living_room.bmp, both sets).
_FEET = 31
_FAR_LEFT, _FAR_RIGHT, _MIDDLE = 28, 180, 104
_RUN_UP = {LEFT: 160, RIGHT: 48}  # where the dash starts from: across from the exit
_ON_RUG = 206  # landing, out of the box
_FAR_FEET, _BACK_FEET = 196, 210  # the two runs, a little deeper and nearer
_TREE = (104, 162)  # the tree's foot: the way up goes behind it
_EXITS = {LEFT: (-48, 204), RIGHT: (260, 204), DOWN: (104, 290), UP: _TREE}
# Its legs, (seconds, hop px, hops -- whole, so it lands at every turn): out of
# the box in one big hop; two runs of small hops, slowing into each turn; a
# stop; a dash of quick low hops. _SEGMENTS: which of _route()'s points each
# leg goes from and to.
_LEGS = ((0.45, 24, 1), (0.9, 9, 4), (0.85, 9, 4), (0.45, 0, 0), (0.7, 5, 5))
_SEGMENTS = ((0, 1), (1, 2), (2, 3), (3, 3), (3, 4))
OUT, PAUSE, DASH, GONE = 0, 3, 4, 5  # leg indexes; GONE: done (behind the tree, or off)
BOLT_S = sum(leg[0] for leg in _LEGS) + 0.3  # a moment after it's gone


def _route(start, direction):
    """(x, feet y) of the box, then each turn, then the way out."""
    sx = start[0]
    if sx < _MIDDLE or (sx == _MIDDLE and direction == RIGHT):
        far = _FAR_RIGHT
    else:
        far = _FAR_LEFT  # away from its box: a box by the exit still gets a walkabout
    back = _RUN_UP.get(direction, _FAR_RIGHT + _FAR_LEFT - far)
    if (back > _MIDDLE) == (far > _MIDDLE):
        back = _MIDDLE  # not back to the side it just ran to
    return ((sx, start[1] + _FEET), (sx, _ON_RUG), (far, _FAR_FEET), (back, _BACK_FEET),
            _EXITS.get(direction, _EXITS[LEFT]))


def _ease(leg, u):
    if leg == OUT:
        return u
    if leg == DASH:
        return u * u  # speeding up all the way out
    return u * u * (3 - 2 * u)  # slowing into each turn


def bolt_at(start, direction, t):
    """Where the bolting critter is `t` s into the bolt shot, from its box's
    `start` (the runner's top-left), leaving by `direction`: (x, y, ux, uy,
    leg), y its top. (ux, uy) is the way it's facing, roughly a unit vector;
    `leg` is OUT, 1, 2, PAUSE, DASH, or GONE once it's out of sight."""
    points = _route(start, direction)
    leg = 0
    while leg < len(_LEGS) and t >= _LEGS[leg][0]:
        t -= _LEGS[leg][0]
        leg += 1
    if leg == GONE:
        x, feet = points[-1]
        return x, feet - _FEET, 0.0, 0.0, GONE
    seconds, hop_px, hops = _LEGS[leg]
    a, b = _SEGMENTS[leg]
    (x0, f0), (x1, f1) = points[a], points[b]
    if leg == PAUSE:  # standing, looking back, away from where it's about to dash
        dx = x1 - points[-1][0]
        return x1, f1 - _FEET, (1.0 if dx > 0 else -1.0), 0.0, leg
    u = _ease(leg, min(t / seconds, 1.0))
    hop = abs(math.sin(math.pi * hops * t / seconds))
    dx, dy = x1 - x0, f1 - f0
    size = max(abs(dx), abs(dy), 1)
    x = int(x0 + dx * u)
    y = int(f0 + dy * u - hop_px * hop) - _FEET
    return x, y, dx / size, dy / size, leg


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
