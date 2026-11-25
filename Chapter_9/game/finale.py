# SPDX-License-Identifier: MIT
"""The finale's cutscenes as comic beats -- cd-342.6, doc/EPISODES.md sec 6.

After the last critter is home, every box pops at once: it's Christmas Eve
and they're all running flat. You lead the parade to the Odd Corner, they
stack into a tower to reach the batteries, and back at the tree each hops onto
its box, recharged; the reindeer finally flies a lap round the tree.

Like escape.py: each beat names a shot (finale_view draws it) and the words or
glyphs the comic kit puts over it. hunt.Hunt.cutscenes says which cutscene
plays before which of its messages; CUTSCENES says, for each, its beats and the
shot under the captions just before and just after it.

Where the critters are in the shots that move them about on the floor -- the
chaos and the parade -- is here too, as plain functions (cd-342.52): feet on
the floor, hopping, never flying; that's the reindeer's moment, in the lap.

Pure, so it runs under desktop Python (see tests/test_finale.py).
"""
import math

from beats import Beat

ALL_HOME = "all_home"  # everyone on their boxes, the calm before it
BURST = "burst"  # every box pops, every critter springs out
CHAOS = "chaos"  # bouncing round the panel, glitching
TOWER = "tower"  # tower<n>: n critters stacked under the shelf, the newest landing
GRAB = "grab"  # the top one takes the batteries off the shelf
TOP = "top"  # ...and holds them up
HOP = "hop"  # home: each critter hops onto its box
LIFTOFF = "liftoff"  # the reindeer's lap round the tree

MAX_TOWER = 5


def tower_shot(n):
    return "{}{}".format(TOWER, n)


SHOTS = (ALL_HOME, BURST, CHAOS, GRAB, TOP, HOP, LIFTOFF) + tuple(
    tower_shot(n) for n in range(MAX_TOWER + 1))

# Hearts either side of the boxes as they land (screen px, glyph top-left at 2x).
_HEARTS = (("heart", 40, 120), ("heart", 168, 120))
_GLITCH = (("question", 36, 128), ("bang", 172, 124))  # on the wall, over the hoppers
# HUP! to the left of the tower (finale_view's _TOWER_X 104), not over it: the
# word clears it; only the star's spike tips reach its edge (the panel's round).
_HUP_AT = (60, 120)

# Screen px: a critter's top-left x and its FEET y (32px at 1x; art to row 31).
# Every room's floor or ground is above feet y 186 (cd-342.51).
_FEET = 31
# The parade's spots, leader first: on the floor, right of the item in hand
# (bottom left, to x 84), the first ones clear of the Odd Corner's tower too.
_PARADE = ((178, 192), (150, 204), (122, 190), (94, 202), (164, 214))
_WANDER_PX = 18
_MIN_X = 88  # ...even wandering
# The chaos: each hops back and forth across the rug at its own pace.
_CHAOS_X, _CHAOS_MID = 104, 78
_CHAOS_FEET, _CHAOS_DEPTH = 198, 10


def parade_place(i):
    """Top-left of the i-th critter in the parade, standing still."""
    x, feet = _PARADE[i % len(_PARADE)]
    return x, feet - _FEET


def parade_at(i, t):
    """The i-th critter of the parade, `t` s into a room: wandering about its
    spot, hopping. (x, y top-left, heading right)."""
    x, y = parade_place(i)
    w = 1.6 + 0.35 * i
    a = w * t + 1.1 * i
    hop = (6 + 2 * (i % 3)) * abs(math.sin(math.pi * t / (0.32 + 0.04 * i)))
    return max(_MIN_X, int(x + _WANDER_PX * math.sin(a))), int(y - hop), math.cos(a) > 0


def chaos_place(i, t):
    """Top-left of critter i, t seconds into the chaos; and whether it's heading
    right. Back and forth across the rug, hopping, a little nearer or deeper."""
    wx, wy = 1.9 + 0.37 * i, 1.3 + 0.29 * i
    a = wx * t + 1.3 * i
    x = _CHAOS_X + _CHAOS_MID * math.sin(a)
    feet = _CHAOS_FEET + _CHAOS_DEPTH * math.sin(wy * t + 2.1 * i)
    hop = (10 + 2 * i) * abs(math.sin(math.pi * t / (0.3 + 0.05 * i)))
    return int(x), int(feet - _FEET - hop), math.cos(a) > 0


def burst():
    return [
        Beat(shot=BURST, burst="Pop!", shake=True, duration=1.0),
        Beat(shot=CHAOS, burst="Bzzt!", duration=1.2),
        Beat(shot=CHAOS, emanata=_GLITCH, duration=1.6),
    ]


def tower(n=MAX_TOWER):
    beats = [Beat(shot=tower_shot(i), burst="Hup!", burst_at=_HUP_AT, duration=0.9)
             for i in range(1, n + 1)]
    beats.append(Beat(shot=GRAB, duration=1.2))
    return beats


def hop():
    return [Beat(shot=HOP, emanata=_HEARTS, duration=3.4)]


def liftoff():
    # No burst: it would sit over the tree the reindeer is flying round.
    return [Beat(shot=LIFTOFF, duration=3.6)]


# Cutscene names, as in hunt.Hunt.cutscenes.
BURST_SCENE = "burst"
TOWER_SCENE = "tower"
HOP_SCENE = "hop"
LIFTOFF_SCENE = "liftoff"

# name -> (beats(n critters), shot under the captions before it, ...and after it)
CUTSCENES = {
    BURST_SCENE: (lambda n: burst(), ALL_HOME, CHAOS),
    TOWER_SCENE: (tower, tower_shot(0), TOP),
    HOP_SCENE: (lambda n: hop(), None, None),
    LIFTOFF_SCENE: (lambda n: liftoff(), None, None),
}
