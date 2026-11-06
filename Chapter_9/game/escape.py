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


def cutscene():
    """The beats from a box starting to rattle to its critter bolting."""
    return [
        Beat(shot=RATTLE, burst="Rattle!", duration=1.6),
        Beat(shot=CLOSEUP, emanata=_BANG, duration=1.2),
        Beat(shot=POP, burst="Pop!", duration=0.7),
        Beat(shot=PEEK, duration=1.3),
        Beat(shot=NAME, duration=1.6),
        Beat(shot=BOLT, duration=1.2),
    ]
