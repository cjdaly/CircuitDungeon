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

Pure data, so it runs under desktop Python (see tests/test_finale.py).
"""
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
_GLITCH = (("question", 48, 64), ("bang", 164, 72))


def burst():
    return [
        Beat(shot=BURST, burst="Pop!", shake=True, duration=1.0),
        Beat(shot=CHAOS, burst="Bzzt!", duration=1.2),
        Beat(shot=CHAOS, emanata=_GLITCH, duration=1.6),
    ]


def tower(n=MAX_TOWER):
    beats = [Beat(shot=tower_shot(i), burst="Hup!", duration=0.9) for i in range(1, n + 1)]
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
