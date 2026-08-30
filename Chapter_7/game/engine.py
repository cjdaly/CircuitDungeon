# SPDX-FileCopyrightText: 2026 Chris J Daly (github user cjdaly)
#
# SPDX-License-Identifier: MIT

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
    def __init__(self, display, world, restart=None):
        self.display = display          # a hardware.GameDisplay
        self.world = world              # a world.World
        self.input = im.InputModel()    # chords: X+Y -> "diag", A+B -> "menu"

        self.play = modes.PlayMode(display, world)
        self.gameover = modes.GameOverMode(display, restart or (lambda: None))
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
            if self.stack.top is self.play and not self.world.hero_alive():
                self.stack.show(self.gameover)   # ENGINE.md §9
            # no d-pad auto-repeat while an overlay (menu/diag) is up
            self.input.repeat_paused = self.stack.overlay_active()

            self.stack.render(screen)
            screen.refresh()

            slack = TICK_SECONDS - (time.monotonic() - t0)
            if slack > 0:
                time.sleep(slack)
