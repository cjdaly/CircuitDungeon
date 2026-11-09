# SPDX-License-Identifier: MIT
"""Draws the finale -- cd-342.6, finale.py, doc/EPISODES.md sec 6.

Out of the shots (finale.py) it draws:

  burst     every critter springs up out of its box
  chaos     ...and bounces round the panel, glitching (flickering out)
  tower<n>  in the Odd Corner, n critters stacked under the shelf, the newest
            dropping on; the batteries still up on the shelf
  grab      the top one takes the batteries
  top       ...and holds them up
  hop       home: each critter, in turn, hops from the parade onto its box
  liftoff   the reindeer's lap round the tree, then back onto its box

and, with no shot, the parade: every loose critter trailing round the bottom
of the panel, hopping, in whatever room you're in. ("all_home", everyone on
their boxes before the burst, is just the presents: SceneView draws it.)

The critters are 1x (32px), like the one following you home in the hunt, and
come from scene_view's sheets; the presents are home_view's, whose sitters
this hides while their critter is in the air. Everything is built once.
"""
import math

import displayio

import critter_candidates
import finale
import scene_art
from home_view import SLOTS, first_frame

_ON_BOX = 24  # home_view's: a critter at home sits this far up from its box's top
_FRAME_S = 0.2

# The parade: an arc round the bottom right of the panel (the item in hand is
# bottom left), leader first.
_PARADE_R = 78
_PARADE_DEG = (20, 42, 64, 86, 108)
_PARADE_HOP_PX = 3

# The tower in the Odd Corner, under the shelf (scene_view's _SHELF_*).
_TOWER_X, _TOWER_Y = 104, 150  # the bottom critter's top-left
_TOWER_STEP = 22  # each one stands this far up the one below
_TOWER_DROP_PX, _TOWER_DROP_S = 40, 0.25
_SHELF_X, _SHELF_Y = 138, 68  # the batteries, up on it
_GRAB_X, _GRAB_Y = 116, 66  # ...and in the top critter's paws
_GRAB_S = 0.5

# The burst and the chaos: every critter on its own wobbly loop round the panel.
_BURST_S = 0.8
_CHAOS_X, _CHAOS_Y = 70, 56  # how far each loop swings
_GLITCH_EVERY, _GLITCH_S = 1.7, 0.15  # each flickers out now and then: running flat

# Home: each critter hops onto its box in turn; then the reindeer's lap.
_HOP_EVERY, _HOP_S, _HOP_PX = 0.55, 0.45, 36
_LAP_S = 3.2
_LAP_CX, _LAP_CY = 104, 100  # round the tree (the sprite's top-left), under the room name
_LAP_RX, _LAP_RY = 76, 38


def parade_place(i):
    """Top-left of the i-th critter in the parade."""
    a = math.radians(_PARADE_DEG[i % len(_PARADE_DEG)])
    return (int(120 + _PARADE_R * math.cos(a)) - 16, int(120 + _PARADE_R * math.sin(a)) - 16)


def tower_place(k):
    """Top-left of the k-th critter up the tower (0 at the bottom)."""
    return _TOWER_X, _TOWER_Y - k * _TOWER_STEP


def chaos_place(i, t):
    """Top-left of critter i, t seconds into the chaos; and whether it's heading right."""
    wx, wy = 1.9 + 0.37 * i, 2.6 + 0.29 * i
    px, py = 1.3 * i, 0.7 + 2.1 * i
    x = 104 + _CHAOS_X * math.sin(wx * t + px)
    y = 100 + _CHAOS_Y * math.sin(wy * t + py)
    return int(x), int(y), math.cos(wx * t + px) > 0


def lap_place(t):
    """The reindeer's top-left, t into its lap; and whether it's heading right."""
    u = min(max(t / _LAP_S, 0.0), 1.0)
    a = math.pi / 2 - 2 * math.pi * u  # from the bottom, clockwise round the tree
    return (int(_LAP_CX + _LAP_RX * math.cos(a)), int(_LAP_CY + _LAP_RY * math.sin(a)),
            math.sin(a) < 0)


def _ease(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


class FinaleView:
    """Owns `.group`. show(parade) on any scene change; shot(name, now); update(now)."""

    def __init__(self, objects, objects_palette, tile_of, critters, critter_palette, home):
        self.group = displayio.Group()
        self._home = home
        tile = critter_candidates.TILE
        self._grids = []
        for _ in range(finale.MAX_TOWER):
            grid = displayio.TileGrid(critters, pixel_shader=critter_palette, width=1, height=1,
                                      tile_width=tile, tile_height=tile)
            grid.hidden = True
            self.group.append(grid)
            self._grids.append(grid)
        self._batteries = displayio.TileGrid(objects, pixel_shader=objects_palette, width=1,
                                             height=1, tile_width=scene_art.TILE,
                                             tile_height=scene_art.TILE,
                                             default_tile=tile_of["batteries"])
        self._batteries.hidden = True
        self.group.append(self._batteries)
        self._parade = ()
        self._frames = ()
        self._walking = False
        self._shot = None
        self._shot_at = 0.0

    def show(self, parade):
        """The critters following you (hunt.Scene.parade), or None. The last
        parade is kept: the ending's shots play after they're all home."""
        self._walking = bool(parade)
        if parade:
            self._parade = tuple(parade)[:len(self._grids)]
            self._frames = tuple(first_frame(sprite) for _, sprite in self._parade)

    @property
    def size(self):
        """How many critters the finale has (the last parade)."""
        return len(self._parade)

    def shot(self, name, now):
        """Start drawing a finale shot; None goes back to just the parade."""
        self._shot = name
        self._shot_at = now

    def update(self, now):
        t = now - self._shot_at
        shot = self._shot
        self._batteries.hidden = True
        for grid in self._grids:
            grid.hidden = True
            grid.flip_x = False
        step = int(now / _FRAME_S) % 2
        if shot is None or shot == finale.ALL_HOME:
            if shot is None and self._walking:
                self._draw_parade(now, step)
        elif shot == finale.BURST:
            self._draw_burst(t, step)
        elif shot == finale.CHAOS:
            self._draw_chaos(t + _BURST_S, step)
        elif shot.startswith(finale.TOWER) or shot in (finale.GRAB, finale.TOP):
            self._draw_tower(shot, t, step)
        elif shot == finale.HOP:
            self._draw_hop(t, step)
        elif shot == finale.LIFTOFF:
            self._draw_lap(t, step)

    # ------------------------------------------------------------------ #

    def _place(self, i, x, y, frame, right=False):
        grid = self._grids[i]
        grid.x, grid.y = x, y
        grid[0] = frame
        grid.flip_x = right  # the sprites face left
        grid.hidden = False

    def _home_spot(self, species):
        """Where this critter sits on its box, or None if it has no box showing."""
        slot = self._home.slot_of(species)
        if slot is None:
            return None, None
        x, y = SLOTS[slot]
        return slot, (x, y - _ON_BOX)

    def _draw_parade(self, now, step):
        for i, frame in enumerate(self._frames):
            x, y = parade_place(i)
            hop = int(_PARADE_HOP_PX * abs(math.sin(math.pi * (now + 0.13 * i) / 0.4)))
            self._place(i, x, y - hop, frame + step)

    def _draw_burst(self, t, step):
        u = _ease(t / _BURST_S)
        for i, (species, _) in enumerate(self._parade):
            _slot, spot = self._home_spot(species)
            sx, sy = spot if spot else parade_place(i)
            cx, cy, right = chaos_place(i, 0.0)
            arc = int(40 * math.sin(math.pi * u))  # up out of the box first
            self._place(i, int(sx + (cx - sx) * u), int(sy + (cy - sy) * u) - arc,
                        self._frames[i] + step, right)

    def _draw_chaos(self, t, step):
        for i, frame in enumerate(self._frames):
            x, y, right = chaos_place(i, t)
            self._place(i, x, y, frame + step, right)
            if (t + 0.61 * i) % _GLITCH_EVERY < _GLITCH_S:
                self._grids[i].hidden = True  # flickers out: running flat

    def _draw_tower(self, shot, t, step):
        if shot in (finale.GRAB, finale.TOP):
            stacked = len(self._frames)
        else:
            stacked = min(int(shot[len(finale.TOWER):]), len(self._frames))
        for i, frame in enumerate(self._frames):
            if i < stacked:
                x, y = tower_place(i)
                if i == stacked - 1 and shot.startswith(finale.TOWER):
                    y -= int(_TOWER_DROP_PX * (1 - min(t / _TOWER_DROP_S, 1.0)))
                self._place(i, x, y, frame + (step if i == stacked - 1 else 0))
            else:  # still waiting in the parade
                x, y = parade_place(i - stacked)
                self._place(i, x, y, frame + step)
        self._batteries.hidden = False
        if shot == finale.GRAB:
            u = _ease(t / _GRAB_S)
        else:
            u = 1.0 if shot == finale.TOP else 0.0
        self._batteries.x = int(_SHELF_X + (_GRAB_X - _SHELF_X) * u)
        self._batteries.y = int(_SHELF_Y + (_GRAB_Y - _SHELF_Y) * u)

    def _draw_hop(self, t, step):
        for i, (species, _) in enumerate(self._parade):
            slot, spot = self._home_spot(species)
            if slot is None:
                continue
            u = (t - i * _HOP_EVERY) / _HOP_S
            landed = u >= 1.0
            self._home.sitter_visible(slot, landed)
            if landed:
                continue
            sx, sy = parade_place(i)
            u = max(u, 0.0)
            x = int(sx + (spot[0] - sx) * u)
            y = int(sy + (spot[1] - sy) * u - _HOP_PX * math.sin(math.pi * u))
            self._place(i, x, y, self._frames[i] + step, spot[0] > sx)

    def _draw_lap(self, t, step):
        for i, (species, _) in enumerate(self._parade):
            if species != "reindeer":
                continue
            slot, spot = self._home_spot(species)
            if slot is None:
                return
            flying = t < _LAP_S
            self._home.sitter_visible(slot, not flying)
            if not flying:
                return
            x, y, right = lap_place(t)
            # Ease off the box and back onto it at either end of the lap.
            near = min(t / 0.5, (_LAP_S - t) / 0.5, 1.0)
            x = int(spot[0] + (x - spot[0]) * near)
            y = int(spot[1] + (y - spot[1]) * near)
            self._place(i, x, y, self._frames[i] + int(t / 0.1) % 2, right)
            return
