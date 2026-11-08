# SPDX-License-Identifier: MIT
"""The ornament screen: a few ambient Christmas scenes that take turns -- cd-zw2.7, cd-342.37.

A separate top-level mode (no gameplay, no input expected) for when the device
hangs as an ornament on a real tree. Since cd-342.37 it gets the same art as
the rooms (doc/STYLE.md sec 6: DB16, comic halftone, Christmas Eve at night),
and has several scenes that cycle:

  tree    a big decorated tree out in the snowy yard: twinkling lights, a pulsing star
  candy   a gingerbread house with candy canes spinning round it
  sleigh  a sleigh flying across the moon over snowy rooftops, snow

Each scene is a backdrop (ornament_<scene>.bmp in the deployed art set, so a
restyled set can redo them, see art_sets/README.md) plus a few things that
move: vectorio lights and star, sprites from ornament_sprites.bmp, snow. The
backdrop goes in the room screen's one shared bitmap (backdrop.Backdrop) --
only one screen is up at a time -- so a scene costs a small sprite sheet, not
another 7.2 KB. app.py calls nav.refresh_backdrop() on the way back to the game.

A new scene on each entry to ornament mode, and every CYCLE_S of lit time.
While the ornament is handled (not still) everything dims and holds still.
Without art files the scenes still run, over the plain dark background.
"""
import math
import random

WIDTH = HEIGHT = 240

SCENES = ("tree", "candy", "sleigh")
CYCLE_S = 40.0  # lit seconds per scene
SPRITES = "ornament_sprites.bmp"  # 128x32: row 0 candy cane at 8 angles; row 1 sleigh x2
SHEET_W, SHEET_H, TILE = 128, 32, 16
_DIM = 0.45  # how far colours drop while handled


def file_name(scene):
    return "ornament_" + scene + ".bmp"


FILES = tuple(file_name(s) for s in SCENES) + (SPRITES,)  # what an art set must have

_BG_COLOR = 0x05050C
_INK = 0x140C1C
_STAR_BRIGHT = 0xDAD45E
_STAR_DIM = 0x8A6A20
_SNOW_COLOR = 0xDEEED6

_ORNAMENT_COLORS = (0xD04648, 0x597DCE, 0xDAD45E, 0xDEEED6)  # DB16 red, blue, yellow, white
_COLOR_HOLD_MIN = 0.5  # seconds a light keeps a color, picked at random
_COLOR_HOLD_MAX = 3.0

# The tree scene's lights go inside this triangle (screen px), a little inside
# the drawn tree (tools/build_backdrops.py ornament_tree: apex art (60, 18),
# base art y 92, 34 each side, at 2x).
_APEX = (120, 52)
_BASE_L = (66, 172)
_BASE_R = (174, 172)
_ORNAMENT_COUNT = 8
_ORNAMENT_RADIUS = 4
_ORNAMENT_MIN_GAP = 18  # px between centers, so they don't overlap or clump
_ORNAMENT_TOP_Y = 66  # placement band, clear of the star and the tree's base
_ORNAMENT_BOTTOM_Y = 164
_STAR_CENTER = (120, 34)
_STAR_OUTER = 13
_STAR_INNER = 5

# The candy scene: canes orbit the middle, each spinning as it goes.
_CANES = 10
_ORBIT_R = 84  # px from the centre to a cane's centre
_ORBIT_S = 16.0  # seconds per lap
_SPIN_S = 2.0  # seconds per turn of a cane

# The sleigh scene: a pass across the moon every _PASS_S.
_PASS_S = 12.0
_FLY_S = 9.0  # of which flying, the rest a pause
_SLEIGH_W = 3 * TILE * 2  # px, at 2x
_SLEIGH_Y = 62
_HOOF_S = 0.15

_SNOW_COUNT = 6
_SNOW_SPEED = 22  # px/second
# Longest time step one update can apply. Snow only updates in ornament mode, so
# without this, returning to the mode wraps every flake to y=0 on one tick and
# they fall as a single row from then on.
_SNOW_MAX_DT = 0.25  # seconds


def make_background(group, width=WIDTH, height=HEIGHT, color=_BG_COLOR):
    """A solid background: a shape, not a bitmap (one costs ~7.7 KB even in one colour)."""
    import vectorio

    group.append(vectorio.Rectangle(pixel_shader=_solid(color), width=width, height=height,
                                    x=0, y=0))


def _solid(color):
    import displayio

    palette = displayio.Palette(1)
    palette[0] = color
    return palette


def _blend(color_a, color_b, t):
    """Linear-interpolate two 0xRRGGBB colors; t=0 -> a, t=1 -> b."""
    ar, ag, ab = (color_a >> 16) & 0xFF, (color_a >> 8) & 0xFF, color_a & 0xFF
    br, bg, bb = (color_b >> 16) & 0xFF, (color_b >> 8) & 0xFF, color_b & 0xFF
    r = int(ar + (br - ar) * t)
    g = int(ag + (bg - ag) * t)
    b = int(ab + (bb - ab) * t)
    return (r << 16) | (g << 8) | b


def _star_points(center, outer, inner):
    """Outline of a 5-point star with one tip straight up: tip, notch, tip, ..."""
    points = []
    for i in range(10):
        radius = inner if i % 2 else outer
        angle = math.radians(i * 36 - 90)
        points.append(
            (
                center[0] + int(round(radius * math.cos(angle))),
                center[1] + int(round(radius * math.sin(angle))),
            )
        )
    return points


def _scatter_positions(count=_ORNAMENT_COUNT, randint=random.randint):
    """Random ornament centers inside the tree, kept apart where possible."""
    positions = []
    apex_x, apex_y = _APEX
    tree_half = _BASE_R[0] - apex_x
    tree_height = _BASE_R[1] - apex_y
    for _ in range(count):
        best = None
        best_gap2 = -1
        for _attempt in range(30):
            y = randint(_ORNAMENT_TOP_Y, _ORNAMENT_BOTTOM_Y)
            half = (y - apex_y) * tree_half // tree_height - _ORNAMENT_RADIUS - 1
            x = randint(apex_x - half, apex_x + half)
            gap2 = min(
                ((x - px) ** 2 + (y - py) ** 2 for px, py in positions),
                default=_ORNAMENT_MIN_GAP ** 2,
            )
            if gap2 > best_gap2:
                best, best_gap2 = (x, y), gap2
            if gap2 >= _ORNAMENT_MIN_GAP ** 2:
                break
        positions.append(best)
    return positions


def _next_color_index(current, count=len(_ORNAMENT_COLORS), randint=random.randint):
    """A random color index that always differs from `current`."""
    index = randint(0, count - 2)
    return index + 1 if index >= current else index


class _Light:
    def __init__(self, palette, ink, shape, color_index):
        self.palette = palette
        self.ink = ink
        self.shape = shape
        self.color_index = color_index
        self.next_change = 0.0


class _TreeScene:
    """Twinkling lights and a pulsing star over the drawn tree."""

    snow = True

    def __init__(self, displayio, vectorio):
        self.group = displayio.Group()
        ink = _solid(_INK)
        self._star_palette = _solid(_STAR_BRIGHT)
        self.group.append(vectorio.Polygon(pixel_shader=ink, points=_star_points(
            _STAR_CENTER, _STAR_OUTER + 3, _STAR_INNER + 2)))
        self.group.append(vectorio.Polygon(pixel_shader=self._star_palette, points=_star_points(
            _STAR_CENTER, _STAR_OUTER, _STAR_INNER)))
        self._lights = []
        for i, (x, y) in enumerate(_scatter_positions()):
            color_index = i % len(_ORNAMENT_COLORS)
            palette = _solid(_ORNAMENT_COLORS[color_index])
            ring = vectorio.Circle(pixel_shader=ink, x=x, y=y, radius=_ORNAMENT_RADIUS + 1)
            shape = vectorio.Circle(pixel_shader=palette, x=x, y=y, radius=_ORNAMENT_RADIUS)
            self.group.append(ring)
            self.group.append(shape)
            self._lights.append(_Light(palette, ring, shape, color_index))

    def enter(self, now):
        """A new layout of lights each time the scene comes round."""
        for light, (x, y) in zip(self._lights, _scatter_positions()):
            light.shape.x = light.ink.x = x
            light.shape.y = light.ink.y = y

    def update(self, now, lit):
        if not lit:
            self._star_palette[0] = _STAR_DIM
            return
        phase = (now % 2.0) / 2.0  # slow star pulse between dim and bright gold
        self._star_palette[0] = _blend(_STAR_DIM, _STAR_BRIGHT, 0.6 + 0.4 * abs(1 - 2 * phase))
        hold_range = _COLOR_HOLD_MAX - _COLOR_HOLD_MIN
        for light in self._lights:
            if now >= light.next_change:
                light.color_index = _next_color_index(light.color_index)
                light.palette[0] = _ORNAMENT_COLORS[light.color_index]
                light.next_change = now + _COLOR_HOLD_MIN + random.random() * hold_range


def cane_place(i, now, width=WIDTH, height=HEIGHT):
    """(x, y, frame) for cane i: its sprite's top-left at 2x, and which of 8 angles."""
    angle = 2 * math.pi * (i / _CANES + now / _ORBIT_S)
    cx = width // 2 + int(_ORBIT_R * math.cos(angle))
    cy = height // 2 + int(_ORBIT_R * math.sin(angle))
    turn = (i / _CANES + now / _SPIN_S) % 1.0
    return cx - TILE, cy - TILE, int(turn * 8) % 8


def sleigh_place(now, start, width=WIDTH):
    """(x, y, frame) of the sleigh, or None between passes."""
    t = (now - start) % _PASS_S
    if t >= _FLY_S:
        return None
    x = -_SLEIGH_W + int((width + _SLEIGH_W) * t / _FLY_S)
    y = _SLEIGH_Y + int(6 * math.sin(t * 2.2))
    return x, y, int(now / _HOOF_S) % 2


class _CandyScene:
    """Candy canes spinning round the big peppermint."""

    snow = False

    def __init__(self, displayio, sheet, palette):
        self.group = displayio.Group()
        self._canes = []
        for _ in range(_CANES):
            g = displayio.Group(scale=2)
            grid = displayio.TileGrid(sheet, pixel_shader=palette, width=1, height=1,
                                      tile_width=TILE, tile_height=TILE)
            g.append(grid)
            self.group.append(g)
            self._canes.append((g, grid))

    def enter(self, now):
        self.update(now, True)

    def update(self, now, lit):
        if not lit:
            return  # hold still while handled
        for i, (g, grid) in enumerate(self._canes):
            g.x, g.y, frame = cane_place(i, now)
            grid[0] = frame


class _SleighScene:
    """The sleigh crosses the moon now and then."""

    snow = True

    def __init__(self, displayio, sheet, palette):
        self.group = displayio.Group()
        self._g = displayio.Group(scale=2)
        self._grid = displayio.TileGrid(sheet, pixel_shader=palette, width=3, height=1,
                                        tile_width=TILE, tile_height=TILE)
        self._g.append(self._grid)
        self._g.hidden = True
        self.group.append(self._g)
        self._start = 0.0

    def enter(self, now):
        self._start = now - 1.0  # already on its way in
        self.update(now, True)

    def update(self, now, lit):
        if not lit:
            return
        place = sleigh_place(now, self._start)
        self._g.hidden = place is None
        if place is None:
            return
        self._g.x, self._g.y, frame = place
        base = 8 + 3 * frame  # row 1 of the sheet: frame A tiles 8-10, frame B 11-13
        for k in range(3):
            self._grid[k] = base + k


class Show:
    """The ornament screen. enter(now) on switching to ornament mode, then
    update(now, lit) each lit tick; `lit` tracks stillness (bright when still)."""

    def __init__(self, group, backdrop, width=WIDTH, height=HEIGHT, scenes=SCENES,
                 cycle_s=CYCLE_S):
        import displayio
        import vectorio

        import scene_art
        from backdrop import COLORS, load, make_palette, scale_color

        make_background(group, width, height)
        self._backdrop = backdrop
        self._colors = COLORS
        self._scale_color = scale_color
        self._view_palette = make_palette(displayio)
        self._view = backdrop.view(self._view_palette)
        self._view.hidden = True
        group.append(self._view)

        sheet = displayio.Bitmap(SHEET_W, SHEET_H, 17)
        self._sheet_colors = scene_art.COLORS[:17]
        self._sheet_palette = displayio.Palette(17)
        for i, rgb in enumerate(self._sheet_colors):
            self._sheet_palette[i] = rgb
        self._sheet_palette.make_transparent(0)
        have_sprites = load(sheet, backdrop.root + "/" + SPRITES, SHEET_W, SHEET_H)

        makers = {
            "tree": lambda: _TreeScene(displayio, vectorio),
            "candy": lambda: _CandyScene(displayio, sheet, self._sheet_palette),
            "sleigh": lambda: _SleighScene(displayio, sheet, self._sheet_palette),
        }
        self._order = list(scenes)
        self._scenes = {}
        for name in self._order:
            scene = makers[name]()
            scene.group.hidden = True
            if name != "tree" and not have_sprites:
                scene.group.append(displayio.Group())  # nothing to draw; still cycles
            group.append(scene.group)
            self._scenes[name] = scene
        self._snow_group = displayio.Group()
        group.append(self._snow_group)
        self._snow = Snow(self._snow_group, width, height)
        self._cycle_s = cycle_s
        self._index = -1
        self._since = 0.0
        self._lit = True
        self.scene = None  # the name of the scene up now

    def enter(self, now):
        """Switching to ornament mode: the next scene."""
        self._show((self._index + 1) % len(self._order), now)

    def _show(self, index, now):
        self._index = index
        self.scene = self._order[index]
        for name, scene in self._scenes.items():
            scene.group.hidden = name != self.scene
        current = self._scenes[self.scene]
        self._view.hidden = not self._backdrop.show_file(file_name(self.scene))
        self._snow_group.hidden = not current.snow
        self._since = now
        current.enter(now)

    def update(self, now, lit):
        if lit and now - self._since >= self._cycle_s:
            self._show((self._index + 1) % len(self._order), now)
        if lit != self._lit:
            self._lit = lit
            k = 1.0 if lit else _DIM
            for i, rgb in enumerate(self._colors):
                self._view_palette[i] = self._scale_color(rgb, k)
            for i in range(1, len(self._sheet_colors)):
                self._sheet_palette[i] = self._scale_color(self._sheet_colors[i], k)
        current = self._scenes[self.scene]
        current.update(now, lit)
        if current.snow:
            self._snow.update(now)


class Snow:
    """Drifting snow dots. .update(now) drives them regardless of `lit`."""

    def __init__(self, group, width=WIDTH, height=HEIGHT):
        import vectorio

        self._width = width
        self._height = height
        self._palette = _solid(_SNOW_COLOR)
        self._flakes = []
        for _ in range(_SNOW_COUNT):
            x = random.randint(10, width - 10)
            y = random.randint(0, height)
            flake = vectorio.Circle(pixel_shader=self._palette, x=x, y=y, radius=2)
            group.append(flake)
            self._flakes.append(flake)
        self._last_update = None

    def update(self, now):
        if self._last_update is None:
            self._last_update = now
            return
        dt = min(now - self._last_update, _SNOW_MAX_DT)
        self._last_update = now
        step = _SNOW_SPEED * dt
        for flake in self._flakes:
            flake.y = int(flake.y + step)
            if flake.y > self._height:
                flake.y = 0
                flake.x = random.randint(10, self._width - 10)
