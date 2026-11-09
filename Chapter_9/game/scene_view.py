# SPDX-License-Identifier: MIT
"""Draws what's in the room to see and tap -- cd-342.26.

hunt.Hunt.scene() says what the current room holds (hunt.Scene); SceneView draws
it, in the middle of the panel where a tap lands on it (edge_gesture's centre
disk):

- a hiding critter peeks over its hiding spot, bobbing up and down, while the
  spot rustles with wiggle lines -- you see something and want to tap it
- once found, it stands in front of the spot, waiting for its lure
- a lure (or what hides it: a snowman, a dark room) sits in its room, bobbing
- the item in hand shows bottom left; a critter following you home, bottom right
- in the finale, the whole parade of critters trailing round the bottom, and
  the finale's cutscene shots (finale_view.py)

Everything is built once and shown/hidden or moved, never re-created, so a room
change allocates nothing (the cd-yl4 Label-churn lesson). The pictures come
from the deployed art set (art_sets/README.md): objects.bmp (props, 32x32
tiles in scene_art.NAMES order) and critters.bmp, both OnDiskBitmaps, so they
stay in flash; both are shown at 2x, the room art's pixel size (cd-342.38).
tools/preview.py renders this on the desktop for art review.
"""

import math

import displayio

import backdrop
import comic_shapes
import critter_candidates
import finale
import scene_art
from finale_view import FinaleView
from home_view import HomeView
from hunt import BOX_HOME, HIDING, SHELF
from walk import bob

OBJECTS = scene_art.OBJECTS
CRITTERS = scene_art.CRITTERS
_LEGACY_CRITTERS = "/art/critters_nn.bmp"  # before art sets carried critters
_ART_SCALE = 2  # objects.bmp's 32px tiles -> 64px, the critters' pixel size
_CRITTER_SCALE = 2  # the 32px nn sheet -> 64px
_ART_PX = scene_art.TILE * _ART_SCALE  # 64

# The middle object (spot or lure): 64x64, centred a little low, so a peeking
# critter's head still sits inside the tap disk (centre 120, radius 60).
_MIDDLE_X = 120 - _ART_PX // 2  # 88
_SPOT_Y = 112
_LURE_Y = 92
_WAIT_Y = 104  # a found critter, standing in front of its spot
_PEEK_PX = 42  # how much of a hiding critter shows over its spot, at the top of a bob
_PEEK_BOB_PX = 10
_PEEK_PERIOD = 2.4  # s for one peek up and back down
_RUSTLE_EVERY = 2.4  # s; the spot shakes for _RUSTLE_S of each
_RUSTLE_S = 0.5
_RUSTLE_STEP_S = 0.08
_WIGGLE_X = (_MIDDLE_X - 34, _MIDDLE_X + _ART_PX + 2)  # wiggle lines either side
_WIGGLE_Y = _SPOT_Y + 8
_LURE_BOB_PX = 3
_LURE_BOB_PERIOD = 1.6
# A lure up on the Odd Corner's high shelf (hunt.SHELF): 1x and still, its
# bottom row standing on the shelf (backdrop y 49, so 98 on screen), just
# under the room caption and above a standing critter's head.
_SHELF_X, _SHELF_Y, _SHELF_SCALE = 138, 68, 1

_IDLE_FRAME_S = 0.5  # critter frame flip at rest
_HOP_FRAME_S = 0.2  # ...and while hopping along behind you

# Bottom corners: the item in hand (left), a critter following you home (right).
_HELD_SCALE = 1
_HELD_X, _HELD_Y = 46, 158
_HELD_BACK = 0x241C2C
_HELD_BACK_RADIUS = 22
_FOLLOW_X, _FOLLOW_Y = 162, 156
_FOLLOW_HOP_PX = 3


def _palette():
    palette = displayio.Palette(len(scene_art.COLORS))
    for i, color in enumerate(scene_art.COLORS):
        palette[i] = color
    palette.make_transparent(0)
    return palette


def _open(path, fallback=None):
    """An OnDiskBitmap, or `fallback`'s, or None if neither is there."""
    for p in (path, fallback):
        if p is None:
            continue
        try:
            return displayio.OnDiskBitmap(p)
        except OSError:
            pass
    return None


def _art_grid(sheet, palette):
    return displayio.TileGrid(
        sheet, pixel_shader=palette, width=1, height=1,
        tile_width=scene_art.TILE, tile_height=scene_art.TILE,
    )


def _critter_grid(sheet, palette):
    tile = critter_candidates.TILE
    return displayio.TileGrid(
        sheet, pixel_shader=palette, width=1, height=1, tile_width=tile, tile_height=tile,
    )


def _first_frame(sprite):
    """The critter sheet's frame 0 for a sprite id; frame 1 is the next tile."""
    for i, candidate in enumerate(critter_candidates.CANDIDATES):
        if candidate[0] == sprite:
            return 2 * i
    raise ValueError("no such critter sprite: {}".format(sprite))


class SceneView:
    """Owns `.group`; call show(scene) on any change, and update(now) every frame."""

    def __init__(self, art_root="/art/rooms"):
        import vectorio

        self.group = displayio.Group()
        self._palette = _palette()
        self._tile_of = {name: i for i, name in enumerate(scene_art.NAMES)}
        self._sheet = _open(art_root + "/" + OBJECTS)
        if self._sheet is None:  # no art deployed: the props just don't show
            self._sheet = displayio.Bitmap(scene_art.TILE * len(scene_art.NAMES), scene_art.TILE, 2)
        spots = [self._tile_of[spot] for spot in scene_art.HIDING_SPOTS.values()]
        tops = backdrop.tile_tops(art_root + "/" + OBJECTS, scene_art.TILE, spots)
        self._spot_tops = {name: tops.get(self._tile_of[name], 0)
                           for name in scene_art.HIDING_SPOTS.values()}

        critters = _open(art_root + "/" + CRITTERS, _LEGACY_CRITTERS)
        if critters is None:
            tile = critter_candidates.TILE
            critters = displayio.Bitmap(tile * critter_candidates.TILES_WIDE, tile * 3, 2)
            critter_palette = _palette()
        else:
            critter_palette = critters.pixel_shader
            critter_palette.make_transparent(0)
        self._critter_sheet, self._critter_palette = critters, critter_palette

        # Back to front: a peeking critter, its spot, wiggles, the lure, a found critter.
        self._behind = displayio.Group(scale=_CRITTER_SCALE)
        self._spot_layer = displayio.Group(scale=_ART_SCALE, x=_MIDDLE_X, y=_SPOT_Y)
        self._spot = _art_grid(self._sheet, self._palette)
        self._spot_layer.append(self._spot)
        self._wiggles = displayio.Group(scale=2)
        self._wiggle_grids = []
        wiggle_sheet = displayio.Bitmap(16, 16, len(comic_shapes.COLORS))
        for y, row in enumerate(comic_shapes.EMANATA["wiggle"]):
            for x, ch in enumerate(row):
                wiggle_sheet[x, y] = comic_shapes.INK_INDEX[ch]
        wiggle_palette = displayio.Palette(len(comic_shapes.COLORS))
        for i, color in enumerate(comic_shapes.COLORS):
            wiggle_palette[i] = color
        wiggle_palette.make_transparent(0)
        for x in _WIGGLE_X:
            grid = displayio.TileGrid(wiggle_sheet, pixel_shader=wiggle_palette,
                                      x=x // 2, y=_WIGGLE_Y // 2)
            self._wiggles.append(grid)
            self._wiggle_grids.append(grid)
        self._lure_layer = displayio.Group(scale=_ART_SCALE, x=_MIDDLE_X, y=_LURE_Y)
        self._lure = _art_grid(self._sheet, self._palette)
        self._lure_layer.append(self._lure)
        self._front = displayio.Group(scale=_CRITTER_SCALE)
        self._critter = _critter_grid(critters, critter_palette)

        self._held_layer = displayio.Group()
        back = displayio.Palette(1)
        back[0] = _HELD_BACK
        half = scene_art.TILE * _HELD_SCALE // 2
        self._held_layer.append(vectorio.Circle(
            pixel_shader=back, radius=_HELD_BACK_RADIUS, x=_HELD_X + half, y=_HELD_Y + half))
        held_icon = displayio.Group(scale=_HELD_SCALE, x=_HELD_X, y=_HELD_Y)
        self._held = _art_grid(self._sheet, self._palette)
        held_icon.append(self._held)
        self._held_layer.append(held_icon)

        self._follow_layer = displayio.Group(x=_FOLLOW_X, y=_FOLLOW_Y)
        self._follower = _critter_grid(critters, critter_palette)
        self._follow_layer.append(self._follower)

        self._home = HomeView(self._sheet, self._palette, self._tile_of, critters,
                              critter_palette)
        self.group.append(self._home.group)
        for layer in (self._behind, self._spot_layer, self._wiggles, self._lure_layer,
                      self._front, self._held_layer, self._follow_layer):
            layer.hidden = True
            self.group.append(layer)
        self._finale = FinaleView(self._sheet, self._palette, self._tile_of, critters,
                                  critter_palette, self._home)
        self.group.append(self._finale.group)
        self._boxes = None  # the scene's presents, to put back after a finale shot
        self._finale_shot = False

        self._pose = None
        self._held_shown = False
        self._lure_high = False
        self._critter_frame = 0
        self._follower_frame = 0
        self._spot_top = 0
        self._shown_at = 0.0

    def show(self, scene, now=0.0):
        """Show a hunt.Scene: call it whenever the room or what's in it changes."""
        self._shown_at = now
        self._boxes = scene.boxes
        self._home.show(scene.boxes)
        self._finale.show(scene.parade)
        self._spot_layer.hidden = scene.spot is None
        if scene.spot is not None:
            self._spot[0] = self._tile_of[scene.spot]
            self._spot_top = _SPOT_Y + self._spot_tops.get(scene.spot, 0) * _ART_SCALE

        self._pose = scene.pose if scene.critter is not None else None
        for layer in (self._behind, self._front):
            if len(layer):
                layer.pop()
            layer.hidden = True
        if self._pose is not None:
            self._critter_frame = _first_frame(scene.critter)
            layer = self._behind if self._pose == HIDING else self._front
            layer.append(self._critter)
            layer.hidden = False
            layer.x = _MIDDLE_X
            layer.y = _WAIT_Y
        self._wiggles.hidden = True

        self._lure_layer.hidden = scene.lure is None
        if scene.lure is not None:
            self._lure[0] = self._tile_of[scene.lure]
        self._lure_high = scene.lure_at == SHELF
        layer = self._lure_layer
        if self._lure_high:
            layer.scale, layer.x, layer.y = _SHELF_SCALE, _SHELF_X, _SHELF_Y
        else:
            layer.scale, layer.x = _ART_SCALE, _MIDDLE_X

        self._held_layer.hidden = scene.held is None or self._finale_shot
        self._held_shown = scene.held is not None
        if scene.held is not None:
            self._held[0] = self._tile_of[scene.held]

        self._follow_layer.hidden = scene.follower is None
        if scene.follower is not None:
            self._follower_frame = _first_frame(scene.follower)
        self.update(now)

    def sheets(self):
        """(objects, its palette, critters, its palette, tile index by name), to share."""
        return (self._sheet, self._palette, self._critter_sheet, self._critter_palette,
                self._tile_of)

    def icon(self, name):
        """(sheet, palette, tile, tile px) of one picture, for comic thought bubbles."""
        return self._sheet, self._palette, self._tile_of[name], scene_art.TILE

    def set_escape(self, escape):
        """The critter the next escape cutscene is about (a hunt.Escape)."""
        self._home.set_escape(escape)

    def shot(self, name, now):
        """Draw one cutscene shot (home_view's escape shots or finale.SHOTS), or None."""
        in_finale = name in finale.SHOTS
        self._home.shot(None if in_finale else name, now)
        self._finale.shot(name if in_finale else None, now)
        if name == finale.ALL_HOME and self._boxes:  # the calm before the burst
            self._home.show(tuple((species, BOX_HOME, sprite)
                                  for species, _state, sprite in self._boxes))
        elif in_finale or self._finale_shot:
            self._home.show(self._boxes)  # as the scene has them (and every sitter back)
        self._finale_shot = in_finale
        if in_finale:
            self._held_layer.hidden = True  # the finale draws its own batteries
        elif self._held_shown:
            self._held_layer.hidden = False

    def parade_size(self):
        """How many critters the finale has (for its tower's beats)."""
        return self._finale.size

    def update(self, now):
        self._home.update(now)
        self._finale.update(now)
        t = now - self._shown_at
        if self._pose is not None:
            self._critter[0] = self._critter_frame + int(t / _IDLE_FRAME_S) % 2
            if self._pose == HIDING:
                rise = 0.5 - 0.5 * math.cos(2 * math.pi * t / _PEEK_PERIOD)
                self._behind.y = self._spot_top - _PEEK_PX + int(_PEEK_BOB_PX * (1 - rise))
                rustling = (t % _RUSTLE_EVERY) < _RUSTLE_S
                jiggle = (1 if int(t / _RUSTLE_STEP_S) % 2 else -1) if rustling else 0
                self._spot_layer.x = _MIDDLE_X + jiggle
                self._wiggles.hidden = not rustling
            else:
                self._spot_layer.x = _MIDDLE_X
        else:
            self._spot_layer.x = _MIDDLE_X
        if not self._lure_layer.hidden and not self._lure_high:
            self._lure_layer.y = _LURE_Y - bob(t, _LURE_BOB_PERIOD, _LURE_BOB_PX)
        if not self._follow_layer.hidden:
            self._follower[0] = self._follower_frame + int(t / _HOP_FRAME_S) % 2
            self._follow_layer.y = _FOLLOW_Y - bob(t, _HOP_FRAME_S, _FOLLOW_HOP_PX)
