# The MIT License (MIT)
#
# Copyright (c) 2026 Chris J Daly (github user cjdaly)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

# Chapter 7 engine — the top-level Game object and the non-blocking main loop.
# Forked from Chapter_6/game/engine.py (bead cd-e3p.2) and stripped of the
# real-time frame loop; the scene + game logic moved out to world.py and
# modes.py as the turn model took shape.
#
# Game owns: the input model, the mode stack, and the loop. Each mode owns its
# own displayio scene and per-tick behaviour (modes.py). Pure game state lives
# in world.py.
#
# Governed by doc/ENGINE.md.

import time

import input as im
import modes


# doc/ENGINE.md section 1.5: a modest fixed tick so idle animation and button
# auto-repeat have a clock while the game waits for input. Upper bound only —
# a slow refresh() just runs at its own pace. Does NOT pace movement (one tile
# per turn; turns advance only on input), unlike Ch6's TARGET_TICK_SECONDS.
TICK_SECONDS = 1 / 20


class Game:
    def __init__(self, display, world):
        self.display = display          # a hardware.GameDisplay
        self.world = world              # a world.World
        self.input = im.InputModel()    # chords: X+Y -> "diag", A+B -> "menu"

        self.play = modes.PlayMode(display, world)
        self.stack = modes.ModeStack(
            self.play,
            {
                "menu": modes.MenuMode(display),
                "diag": modes.DiagMode(display, self.input),
            },
        )

        display.screen.auto_refresh = False
        self.stack.render(display.screen)   # sets root_group to the play scene

    def run(self):
        screen = self.display.screen
        buttons = self.display.read_buttons
        while True:
            t0 = time.monotonic()

            events = self.input.tick(buttons(), t0)
            self.stack.handle(events, t0)
            # no d-pad auto-repeat while an overlay (menu/diag) is up
            self.input.repeat_paused = self.stack.overlay_active()

            self.stack.render(screen)
            screen.refresh()

            slack = TICK_SECONDS - (time.monotonic() - t0)
            if slack > 0:
                time.sleep(slack)
