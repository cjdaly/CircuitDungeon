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

import gc
import time

import input as im
import metrics as metrics_mod
import modes


# doc/ENGINE.md section 1.5: a modest fixed tick so idle animation and button
# auto-repeat have a clock while the game waits for input. Upper bound only —
# a slow refresh() just runs at its own pace. Does NOT pace movement (one tile
# per turn; turns advance only on input), unlike Ch6's TARGET_TICK_SECONDS.
TICK_SECONDS = 1 / 20


def _mem_free():
    """gc.mem_free() on CircuitPython, -1 on desktop CPython (no such attr)."""
    fn = getattr(gc, "mem_free", None)
    return fn() if fn else -1


class Game:
    def __init__(self, display, world, restart=None, new_level=None):
        self.display = display          # a hardware.GameDisplay
        self.world = world              # a world.World
        # new_level(depth, start) -> a fresh World for that depth (cd-e3p.10);
        # None disables descent (some tests don't need it).
        self._new_level = new_level
        self.input = im.InputModel()    # chords: X+Y -> "diag", A+B -> "menu"
        self.metrics = metrics_mod.Metrics()

        self.play = modes.PlayMode(display, world)
        self.gameover = modes.GameOverMode(display, restart or (lambda: None))
        self.diag = modes.DiagMode(display, self.input, self.metrics, world)
        self.stack = modes.ModeStack(
            self.play,
            {"menu": modes.MenuMode(display), "diag": self.diag},
        )

        display.screen.auto_refresh = False
        self.stack.render(display.screen)   # sets root_group to the play scene

    def _change_level(self, direction):
        """Hero stepped onto stairs (world.transition). Build the next level
        and swap it in. Regenerate-on-entry: generator.generate(seed, depth)
        is deterministic, so re-entering a depth gives the same layout with
        fresh monsters (ENGINE.md §5.4)."""
        world = self.world
        world.transition = None
        if self._new_level is None:
            return
        if direction == "up" and world.depth <= 1:
            world.log.add("The way out has sealed behind you.")
            self.play._paint_message()
            return
        depth = world.depth + (1 if direction == "down" else -1)
        arrive = "up" if direction == "down" else "down"
        carry_turn = world.turn             # turn count is a running total, not per-level
        verb = "descend" if direction == "down" else "climb"

        # Release the old level before building the new one. Its grid plus
        # generator.generate()'s transient BFS buffers would otherwise peak
        # together on a heap that's already tight (cd-yl4). load_world() sets
        # play/diag.world again a few lines down — nothing runs in between.
        world = None
        self.world = None
        self.play.world = None
        self.diag.world = None
        gc.collect()
        before = _mem_free()

        new_world = self._new_level(depth, arrive)
        new_world.turn = carry_turn
        new_world.log.add("You %s to depth %d." % (verb, depth))
        self.world = new_world
        self.play.load_world(new_world)
        self.diag.world = new_world

        # cd-dsc.6: watch this across a long run — if `after` trends down
        # descent-over-descent, something is retained per level. (Device only;
        # -1 off-device where gc.mem_free() doesn't exist.)
        gc.collect()
        after = _mem_free()
        if after >= 0:
            print("Ch7 %-7s depth %d   free %d -> %d" % (verb, depth, before, after))

    def run(self):
        screen = self.display.screen
        buttons = self.display.read_buttons
        while True:
            t0 = time.monotonic()
            self.metrics.maybe_sample_ram(t0)   # ~0.5 Hz gc.collect() + read

            events = self.input.tick(buttons(), t0)
            self.stack.handle(events, t0)
            if self.stack.top is self.play and not self.world.hero_alive():
                self.stack.show(self.gameover)   # ENGINE.md §9
            elif self.world.transition:
                self._change_level(self.world.transition)   # ENGINE.md §5.4
            # no d-pad auto-repeat while an overlay (menu/diag) is up
            self.input.repeat_paused = self.stack.overlay_active()

            self.stack.render(screen)
            screen.refresh()

            dt = time.monotonic() - t0
            self.metrics.note_frame(dt)
            slack = TICK_SECONDS - dt
            if slack > 0:
                time.sleep(slack)
