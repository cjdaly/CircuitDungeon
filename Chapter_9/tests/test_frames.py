# SPDX-License-Identifier: MIT
# The board's Python stack, checked on the desktop -- cd-342.47.5,
# doc/ARCHITECTURE.md sec 1 and 5.
#
#   python3 Chapter_9/tests/test_frames.py        (-v prints each path's size)
#
# CircuitPython runs the game on a 1536-byte Python stack (pystack). Every
# call holds a frame there -- about 28 bytes plus 4 per local and per value
# stack slot -- and drawing a label's text goes 5 calls deeper inside the
# library. Run out and the call raises "pystack exhausted": on 2026-11-22 that
# silently skipped the escape cutscene. CPython has no such limit, so every
# other test passes regardless.
#
# This test estimates each frame from CPython's code objects (locals + cells +
# value stack: a stand-in for MicroPython's, not the same numbers) and adds up
# the frames along each path that draws text, from main() down to the
# library. The library's share is calibrated from the board (_SET_TEXT,
# _NEW_LABEL). Each path must leave room for _SPARE_CALLS more small calls.
#
# The paths are written out by hand below: when one changes (a call added, a
# function renamed or moved), update it here -- a name that no longer exists
# fails the test. tools/device_run.py --depth is the real measurement.

import os
import sys
import types
import unittest

_GAME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "game")

PYSTACK = 1536  # CircuitPython's default CIRCUITPY_PYSTACK_SIZE
_FRAME_BYTES = 28
_SLOT_BYTES = 4
_SPARE_CALLS = 4  # each path leaves room for this many more small calls
_SMALL_CALL = 4  # slots in a small call (tools/device_run.py's deeper())

# What the library itself takes below the game's last frame, in this test's
# estimated bytes, calibrated on ws-1 (CP 10.3.1) with tools/device_run.py
# --depth on 2026-11-22 (e98c607). device_run runs the game under its go()
# (10 slots) and depth+1 deeper() frames instead of main():
# - Setting a label's text (bitmap_label's text setter). The game survived
#   --depth 11 and failed at 12 on the caption path (772 bytes from app.run):
#   12 x 44 + 68 + 772 + lib fits and 13 x 44 + ... doesn't, so 124 < lib <= 168.
_SET_TEXT = 168
# - Building a new label (its constructor lays out the text, deeper still).
#   Start-up survived 8 and failed at 9 on the gift tag path (752 bytes from
#   app.run): 276 < lib <= 320.
_NEW_LABEL = 320
# Checked against older code: at 6be05de (app.run's 90-slot frame under the
# title tap's caption) this predicts 4 calls to spare and the board had 3.
# Big frames cost a little more on the board than estimated, so the estimate
# is good to about one call; _SPARE_CALLS covers that.

# Every path starts at main() and runs down the loop.
_LOOP = ("main:main", "app:run", "app:Game.tick", "app:Game._play",
         "screens:GameScreen.update", "nav_view:NavView.update")
_BEAT = _LOOP + ("beats:BeatPlayer.update", "beats:BeatPlayer._next",
                 "nav_view:_Director.show")

# name -> (the game's frames, outermost first; what the library does at the end)
PATHS = {
    # The comic's words, from a beat starting at update().
    "caption": (_BEAT + ("comic:Stage.show", "comic:_Caption.draw", "comic:_Lines.show"),
                _SET_TEXT),
    "balloon": (_BEAT + ("comic:Stage.show", "comic:_Balloon.show", "comic:_Lines.show"),
                _SET_TEXT),
    "burst": (_BEAT + ("comic:Stage.show", "comic:_Burst.show"), _SET_TEXT),
    # The escape's ZOOM! and the critter's name, set as a shot starts.
    "escape title": (_BEAT + ("scene_view:SceneView.shot", "home_view:HomeView.shot",
                              "home_view:HomeView._set_title"), _SET_TEXT),
    # The room's name, on arriving.
    "room name": (_LOOP + ("room_banner:RoomLabel.show",), _SET_TEXT),
    # Start-up: the gift tag's words, built under Game.__init__.
    "gift tag": (("main:main", "app:run", "app:Game.__init__", "app:Game._gift_tag",
                  "gift_tag:GiftTag.__init__", "gift_tag:GiftTag._words",
                  "gift_tag:GiftTag._name_labels",
                  "gift_tag:GiftTag._name_labels.<listcomp>"), _NEW_LABEL),
}


def _codes(module):
    """{qualified name: code object} for every function in game/<module>.py."""
    path = os.path.join(_GAME, module + ".py")
    with open(path) as f:
        top = compile(f.read(), path, "exec")
    found = {}

    def walk(code, prefix):
        for const in code.co_consts:
            if isinstance(const, types.CodeType):
                name = prefix + const.co_name
                found[name] = const
                walk(const, name + ".")

    walk(top, "")
    return found


_CACHE = {}


def slots(where):
    """Estimated frame slots of "module:Qual.name"."""
    module, name = where.split(":")
    if module not in _CACHE:
        _CACHE[module] = _codes(module)
    code = _CACHE[module].get(name)
    if code is None:
        raise KeyError("{} is on a drawing path in tests/test_frames.py but isn't in "
                       "game/{}.py: update PATHS".format(name, module))
    return code.co_nlocals + len(code.co_cellvars) + code.co_stacksize


def frame_bytes(n_slots):
    return _FRAME_BYTES + _SLOT_BYTES * n_slots


def path_bytes(path):
    return sum(frame_bytes(slots(where)) for where in path)


def spare_calls(name):
    """How many more small calls PATHS[name] leaves room for."""
    path, library = PATHS[name]
    left = PYSTACK - path_bytes(path) - library
    return left // frame_bytes(_SMALL_CALL)


class TestFrames(unittest.TestCase):
    def test_every_drawing_path_leaves_room_to_spare(self):
        for name in PATHS:
            with self.subTest(path=name):
                spare = spare_calls(name)
                if "-v" in sys.argv:
                    print("  {}: {} bytes + library, {} calls to spare".format(
                        name, path_bytes(PATHS[name][0]), spare))
                self.assertGreaterEqual(
                    spare, _SPARE_CALLS,
                    "{} is too deep for the board's pystack: shrink a frame on it "
                    "(doc/ARCHITECTURE.md sec 1) and check with tools/device_run.py "
                    "--depth".format(name))

    def test_loop_level_frames_stay_small(self):
        # They sit under every call the game makes.
        for where in _LOOP:
            with self.subTest(frame=where):
                self.assertLessEqual(slots(where), 24, where)

    def test_every_name_on_a_path_exists(self):
        for path, _library in PATHS.values():
            for where in path:
                slots(where)  # raises KeyError naming it if not


if __name__ == "__main__":
    unittest.main()
