# SPDX-License-Identifier: MIT
"""The Living Room's presents and the escape cutscene -- cd-342.27, cd-342.10.

The wide shot is drawn at 2x (doc/STYLE.md sec 1, "Wide"): a present for every
critter under the tree, each in its own colours. The tree itself is part of the
room's backdrop (living_room.bmp, tools/build_backdrops.py), like
every room's static art; this view draws only what changes with the game. A present tells
you who's where with no HUD -- closed with a bow, its critter hasn't got out
yet; tipped over and empty, it's out now; its critter sitting on top, it's home.

The escape (STYLE.md sec 4) is a run of comic beats whose `shot` this view
draws, while the comic kit draws their words on top:

  calm     the wide shot, with the escaping critter's box still shut
  rattle   ...that box rocking, wiggle lines either side (RATTLE!)
  closeup  cut in to the box at 4x, pulsing (!)
  pop      its lid flies off (POP!)
  peek     two eyes come up over the rim
  name     the critter big, and its name
  bolt     back to the wide shot: it dashes out of the tipped box toward the
           way it went, speed lines behind it

The close-up shots cover the room with a plain backdrop; nav_view hides the
edge markers and room name under them (escape.CLOSE_SHOTS). Everything is built once
and reused; the critter sprites share scene_view's OnDiskBitmap.
"""
import displayio
import vectorio
from adafruit_display_text.bitmap_label import Label

import comic_fonts
import comic_shapes
import critter_candidates
import scene_art
from escape import BOLT, CALM, CLOSE_SHOTS, CLOSEUP, NAME, PEEK, POP, RATTLE
from rooms import DOWN, LEFT, RIGHT, UP

_BACKDROP = 0x101018  # nav_view's background, so a cut reads as the same panel
_TITLE_COLOR = 0xDAD45E
_TITLE_Y = 196  # the critter's name, under its close-up
_ZOOM_Y = 92  # ZOOM! during the bolt, over the tree

# Wide shot, screen px. (The tree, in the backdrop, is at (80, 62), 80x104.)
_WIDE = 1  # objects.bmp's 32px presents at 1x: 32px, as the 16px ones were at 2x
# Each present's top-left, in CAST order, in an arc in front of the tree.
SLOTS = ((40, 168), (72, 160), (104, 172), (136, 160), (168, 168))
_ON_BOX = 24  # a critter at home sits this far up from its box's top
_ROCK_STEP_S = 0.09
_ROCK_PX = 2

# Close-ups, screen px: the box at 2x (64px), the critter at 2x.
_CLOSE = 2
_PULSE_HOP_PX = 4  # the shut box jumps a little, on the beat
_BOX_X, _BOX_Y = 88, 100
_PULSE_STEP_S = 0.2
_RIM_Y = _BOX_Y + 12 * _CLOSE  # the open box's rim ("present open" row 12 of 32)
_PEEK_PX = 40
_PEEK_RISE_S = 0.5
_LID_FLY_S = 0.5
_LID_RISE_PX = 200
_LID_DRIFT_PX = 30
_NAME_SCALE = 3  # the critter big: 96px
_NAME_X, _NAME_Y = 72, 64
_FRAME_S = 0.3

_BOLT_S = 0.9  # time to reach the edge
_BOLT_PX = 130


def first_frame(sprite):
    for i, candidate in enumerate(critter_candidates.CANDIDATES):
        if candidate[0] == sprite:
            return 2 * i
    raise ValueError("no such critter sprite: {}".format(sprite))


def _solid(color):
    palette = displayio.Palette(1)
    palette[0] = color
    return palette


def box_palette(base, species):
    """scene_art's palette with this critter's present colours swapped in."""
    palette = displayio.Palette(len(scene_art.COLORS))
    for i in range(len(scene_art.COLORS)):
        palette[i] = base[i]
    for index, color in zip(scene_art.BOX_INDEXES, scene_art.BOX_COLORS[species]):
        palette[index] = color
    palette.make_transparent(0)
    return palette


class _Grid:
    """One tile of a sheet in its own scaled Group, so it can be moved and swapped."""

    def __init__(self, parent, sheet, palette, tile, scale):
        self.group = displayio.Group(scale=scale)
        self.grid = displayio.TileGrid(
            sheet, pixel_shader=palette, width=1, height=1, tile_width=tile, tile_height=tile)
        self.group.append(self.grid)
        self.group.hidden = True
        parent.append(self.group)

    def place(self, x, y, tile=None):
        self.group.x, self.group.y = x, y
        if tile is not None:
            self.grid[0] = tile
        self.group.hidden = False

    def hide(self):
        self.group.hidden = True


class HomeView:
    """Owns `.group`. show(boxes) for the room; shot(name, now) during the escape."""

    def __init__(self, art_sheet, art_palette, tile_of, critters, critter_palette):
        self.group = displayio.Group()
        self._tile_of = tile_of
        self._species_slot = {}
        tile = critter_candidates.TILE

        # The wide shot.
        self._wide = displayio.Group()
        self.group.append(self._wide)
        self._boxes = []
        self._sitters = []
        species_order = tuple(scene_art.BOX_COLORS)
        self._palettes = {
            species: box_palette(art_palette, species) for species in species_order
        }
        for _ in SLOTS:
            self._boxes.append(_Grid(self._wide, art_sheet, art_palette, scene_art.TILE, _WIDE))
        for _ in SLOTS:
            self._sitters.append(_Grid(self._wide, critters, critter_palette, tile, 1))
        self._runner = _Grid(self._wide, critters, critter_palette, tile, 1)
        self._speed = self._emanata("speed")
        self._wiggles = (self._emanata("wiggle"), self._emanata("wiggle"))

        # The close-ups, over a plain backdrop.
        self._close = displayio.Group()
        self._close.hidden = True
        self.group.append(self._close)
        self._close.append(vectorio.Rectangle(
            pixel_shader=_solid(_BACKDROP), width=240, height=240, x=0, y=0))
        self._close_critter = _Grid(self._close, critters, critter_palette, tile, 2)
        self._close_box = _Grid(self._close, art_sheet, art_palette, scene_art.TILE, _CLOSE)
        self._lid = _Grid(self._close, art_sheet, art_palette, scene_art.TILE, _CLOSE)
        self._big = _Grid(self._close, critters, critter_palette, tile, _NAME_SCALE)
        self._title = Label(comic_fonts.title(), text="", color=_TITLE_COLOR,
                            anchor_point=(0.5, 0.5), anchored_position=(120, _TITLE_Y))
        self.group.append(self._title)

        self._shown = ()
        self._normal_tile = []
        self._sitter_frame = [0] * len(SLOTS)
        self._escape = None
        self._shot = None
        self._shot_at = 0.0

    def _emanata(self, name):
        sheet = displayio.Bitmap(16, 16, len(comic_shapes.COLORS))
        for y, row in enumerate(comic_shapes.EMANATA[name]):
            for x, ch in enumerate(row):
                sheet[x, y] = comic_shapes.INK_INDEX[ch]
        palette = displayio.Palette(len(comic_shapes.COLORS))
        for i, color in enumerate(comic_shapes.COLORS):
            palette[i] = color
        palette.make_transparent(0)
        return _Grid(self._wide, sheet, palette, 16, 2)

    # ------------------------------------------------------------------ #

    def show(self, boxes):
        """The presents, as hunt.Scene.boxes; None hides the whole room."""
        import hunt

        self.group.hidden = boxes is None
        self._shown = boxes or ()
        self._normal_tile = []
        self._species_slot = {}
        for i, (species, state, sprite) in enumerate(self._shown):
            self._species_slot[species] = i
            box, sitter = self._boxes[i], self._sitters[i]
            if box.grid.pixel_shader is not self._palettes[species]:
                box.grid.pixel_shader = self._palettes[species]
            x, y = SLOTS[i]
            art = "present tipped" if state == hunt.BOX_EMPTY else "present"
            self._normal_tile.append(self._tile_of[art])
            box.place(x, y, self._normal_tile[i])
            if state == hunt.BOX_HOME:
                self._sitter_frame[i] = first_frame(sprite)
                sitter.place(x, y - _ON_BOX, self._sitter_frame[i])
            else:
                sitter.hide()
        self._draw_shot(0.0)

    def set_escape(self, escape):
        """The critter the next escape cutscene is about (a hunt.Escape)."""
        self._escape = escape

    def shot(self, name, now):
        """Start drawing an escape shot; None goes back to the plain room."""
        self._shot = name
        self._shot_at = now
        self._draw_shot(0.0)

    def update(self, now):
        if self.group.hidden:
            return
        t = now - self._shot_at
        step = int(now / (_FRAME_S * 2)) % 2  # a slow idle, critters at home
        for i, sitter in enumerate(self._sitters):
            if not sitter.group.hidden:
                sitter.grid[0] = self._sitter_frame[i] + step
        if self._shot is not None:
            self._draw_shot(t)

    # ------------------------------------------------------------------ #

    def _set_title(self, text, y=_TITLE_Y):
        """Change the title only when it changes: each new text rebuilds its bitmap."""
        if self._title.text != text:
            self._title.anchored_position = (120, y)
            self._title.text = text

    def _escape_slot(self):
        if self._escape is None:
            return None
        return self._species_slot.get(self._escape.species)

    def _draw_shot(self, t):
        if not self._shown:
            return
        shot = self._shot
        slot = self._escape_slot()
        close = shot in CLOSE_SHOTS and self._escape is not None
        self._close.hidden = not close
        self._wide.hidden = close
        for grid in (self._runner, self._speed) + self._wiggles:
            grid.hide()
        if shot not in (BOLT, NAME):
            self._set_title("")
        if slot is not None:
            x, y = SLOTS[slot]
            box = self._boxes[slot]
            if shot in (CALM, RATTLE):
                box.place(x, y, self._tile_of["present"])
            elif shot == BOLT:
                box.place(x, y, self._tile_of["present tipped"])
            else:
                box.place(x, y, self._normal_tile[slot])
            if shot == RATTLE:
                box.group.x = x + (_ROCK_PX if int(t / _ROCK_STEP_S) % 2 else -_ROCK_PX)
                self._wiggles[0].place(x - 30, y)
                self._wiggles[1].place(x + 30, y)
            if shot == BOLT:
                self._draw_bolt(t, x, y)
        if close:
            self._draw_close(shot, t)

    def _draw_bolt(self, t, x, y):
        direction = self._escape.direction or LEFT
        dx, dy = {LEFT: (-1, 0), RIGHT: (1, 0), UP: (0, -1), DOWN: (0, 1)}[direction]
        travel = min(t / _BOLT_S, 1.0) * _BOLT_PX
        rx, ry = int(x + dx * travel), int(y - 8 + dy * travel)
        frame = first_frame(self._escape.sprite) + int(t / 0.1) % 2
        self._runner.place(rx, ry, frame)
        self._runner.grid.flip_x = dx > 0  # the sprites face left
        if t < _BOLT_S:
            self._speed.place(rx - dx * 34, ry - dy * 34)
        self._set_title("ZOOM!", _ZOOM_Y)

    def _draw_close(self, shot, t):
        escape = self._escape
        palette = self._palettes[escape.species]
        frame = first_frame(escape.sprite)
        box, lid, critter, big = self._close_box, self._lid, self._close_critter, self._big
        if box.grid.pixel_shader is not palette:  # setting it redraws the lot
            box.grid.pixel_shader = palette
            lid.grid.pixel_shader = palette
        for grid in (box, lid, critter, big):
            grid.hide()
        if shot == CLOSEUP:
            if box.group.scale != _CLOSE:
                box.group.scale = _CLOSE
            hop = _PULSE_HOP_PX if int(t / _PULSE_STEP_S) % 2 else 0
            half = scene_art.TILE * _CLOSE // 2
            box.place(120 - half, _BOX_Y + 32 - half - hop, self._tile_of["present"])
        elif shot in (POP, PEEK):
            if box.group.scale != _CLOSE:
                box.group.scale = _CLOSE
            box.place(_BOX_X, _BOX_Y, self._tile_of["present open"])
            if shot == POP:
                fly = min(t / _LID_FLY_S, 1.0)
                lid.place(_BOX_X + int(_LID_DRIFT_PX * fly), _BOX_Y - int(_LID_RISE_PX * fly),
                          self._tile_of["lid"])
            else:
                rise = min(t / _PEEK_RISE_S, 1.0)
                # Built before the box, so it's behind the box's front.
                critter.place(_BOX_X, _RIM_Y - int(_PEEK_PX * rise),
                              frame + int(t / _FRAME_S) % 2)
        elif shot == NAME:
            big.place(_NAME_X, _NAME_Y, frame + int(t / _FRAME_S) % 2)
            self._set_title(escape.name.upper() + "!")
