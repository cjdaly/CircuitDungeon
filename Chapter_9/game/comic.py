# SPDX-License-Identifier: MIT
"""The comic overlay kit's drawing: caption, balloon, bubble, burst, emanata, ring
-- cd-342.9, doc/STYLE.md sec 3 and 8.

Stage builds every element once and hides it, then reuses them for each beat
(beats.py), since a new label per caption is what ran Chapter 7 out of memory
(cd-yl4). Its .group goes above the scene it decorates.
"""
import bitmaptools
import displayio
import vectorio
from adafruit_display_text.bitmap_label import Label

import clearance
import comic_fonts
import comic_shapes

MAX_EMANATA = 4

_INK = 0x140C1C
_PAPER = 0xDEEED6
_YELLOW = 0xDAD45E
_RED = 0xD04648

_LINE_OFFSET = 13  # a two-line text's lines sit this far above/below its middle
_LINE_HEIGHT = 26
_CAPTION_Y = 172
# Where a caption's middle can go, (one line, two lines), best first: the
# bottom, as it always was; the top, over the room name (hidden meanwhile);
# the middle. Each caption takes the one covering least of the scene (cd-342.46).
BOTTOM, TOP, MIDDLE = "bottom", "top", "middle"
_CAPTION_BANDS = ((BOTTOM, _CAPTION_Y, _CAPTION_Y), (TOP, 66, 76), (MIDDLE, 120, 120))
_BORDER = 2
_CAPTION_PAD_X = 6
_CAPTION_PAD_Y = 2
_BALLOON_PAD = 8
_TAIL_PX = 18  # from a balloon's side to its tail's tip
_RING_THICKNESS = 6
_THOUGHT_X = 120
_THOUGHT_Y = 88
_ICON_SCALE = 2
_EMANATA_SCALE = 2
_TILE = 16
_SHAKE_S = 0.35
_SHAKE_STEP_S = 0.05
_SHAKE_PX = 3


def _palette(*colors):
    palette = displayio.Palette(len(colors))
    for i, color in enumerate(colors):
        palette[i] = color
    return palette


def _hidden_group(parent, **kwargs):
    group = displayio.Group(**kwargs)
    group.hidden = True
    parent.append(group)
    return group


class _Lines:
    """Two reusable labels, centered on their own since bitmap_label can't center
    the lines of a proportional font. These fonts are capitals only."""

    def __init__(self, group, font, color):
        self._labels = []
        for _ in range(2):
            label = Label(font, text="", color=color, anchor_point=(0.5, 0.5),
                          anchored_position=(0, 0))
            group.append(label)
            self._labels.append(label)

    def show(self, text, x, y):
        """Draw one line, or two split by a newline. Returns (widest px, line count)."""
        lines = text.upper().split("\n")
        two = len(lines) > 1
        first, second = self._labels
        first.anchored_position = (x, y - _LINE_OFFSET if two else y)
        second.anchored_position = (x, y + _LINE_OFFSET)
        first.text = lines[0]
        second.text = lines[1] if two else ""
        return max(first.bounding_box[2], second.bounding_box[2]), len(lines)

    def move(self, x, y, count):
        """Re-place what show() drew, without redrawing the words."""
        first, second = self._labels
        first.anchored_position = (x, y - _LINE_OFFSET if count > 1 else y)
        second.anchored_position = (x, y + _LINE_OFFSET)


class _Caption:
    """Narration: black words in a small yellow box with a black border."""

    def __init__(self, parent, width):
        self._middle = width // 2
        self.group = _hidden_group(parent)
        self._border = vectorio.Rectangle(
            pixel_shader=_palette(_INK), width=1, height=1, x=0, y=0)
        self._fill = vectorio.Rectangle(
            pixel_shader=_palette(_YELLOW), width=1, height=1, x=0, y=0)
        self.group.append(self._border)
        self.group.append(self._fill)
        self._lines = _Lines(self.group, comic_fonts.caption(), _INK)

    def draw(self, text):
        """Draw the words, not placed yet. Kept tiny: bitmap_label goes five
        calls deep under it, and the board's pystack has little to spare (a
        fat frame here made the escape cutscene die with "pystack exhausted")."""
        self._widest, self._count = self._lines.show(text, self._middle, _CAPTION_Y)

    def bands(self):
        """Each band's rect for what draw() drew."""
        self._width = self._widest + 2 * _CAPTION_PAD_X
        self._height = self._count * _LINE_HEIGHT + 2 * _CAPTION_PAD_Y
        rects = []
        for _name, one, two in _CAPTION_BANDS:
            y = two if self._count > 1 else one
            x0 = self._middle - self._width // 2 - _BORDER
            y0 = y - self._height // 2 - _BORDER
            rects.append((x0, y0, x0 + self._width + 2 * _BORDER,
                          y0 + self._height + 2 * _BORDER))
        return rects

    def place(self, band):
        """Show what draw() drew in _CAPTION_BANDS[band]; returns its name."""
        name, one, two = _CAPTION_BANDS[band]
        y = two if self._count > 1 else one
        if y != _CAPTION_Y:
            self._lines.move(self._middle, y, self._count)
        width, height = self._width, self._height
        self._fill.width, self._fill.height = width, height
        self._fill.x = self._middle - width // 2
        self._fill.y = y - height // 2
        self._border.width = width + 2 * _BORDER
        self._border.height = height + 2 * _BORDER
        self._border.x = self._fill.x - _BORDER
        self._border.y = self._fill.y - _BORDER
        self.group.hidden = False
        return name


class _Balloon:
    """A critter talking: black words in a white balloon with a tail.

    The balloon sits beside its tail's tip, toward the middle of the panel: a
    tip near the left edge puts it to the tip's right, one near the top below
    it, and so on -- so a tail at an exit reads as a voice from beyond it."""

    def __init__(self, parent, width):
        self._middle = width // 2
        self.top = False  # the balloon is up over the room name
        self.group = _hidden_group(parent)
        placeholder = [(0, 0), (1, 0), (0, 1)]
        self._outline = vectorio.Polygon(
            pixel_shader=_palette(_INK), points=placeholder, x=0, y=0)
        self._fill = vectorio.Polygon(
            pixel_shader=_palette(_PAPER), points=placeholder, x=0, y=0)
        self.group.append(self._outline)
        self.group.append(self._fill)
        self._lines = _Lines(self.group, comic_fonts.caption(), _INK)

    def show(self, text, tail):
        widest, count = self._lines.show(text, self._middle, self._middle)
        width = widest + 2 * _BALLOON_PAD
        height = count * _LINE_HEIGHT + _BALLOON_PAD
        x, y = comic_shapes.balloon_middle(tail, width, height, _BORDER + _TAIL_PX)
        self._lines.move(x, y, count)
        self.top = y < self._middle
        self._outline.points = comic_shapes.balloon_points(
            x, y, width, height, tail, grow=_BORDER)
        self._fill.points = comic_shapes.balloon_points(x, y, width, height, tail)
        self.group.hidden = False


class _Thought:
    """What a critter wants: an icon, no words, in a cloud with trailing circles."""

    # (x, y, radius) from the cloud's middle.
    _CLOUD = ((-20, -8, 22), (20, -8, 22), (-20, 12, 20), (20, 12, 20), (0, 0, 32))
    _TRAIL_R = (7, 4)
    # Where the cloud can go, best first (cd-342.46): its middle, and its trail's
    # two circles from there, pointing back at the thinker -- above a critter in
    # the middle, or beside one that has danced off to the other side.
    SPOTS = (
        ((_THOUGHT_X, _THOUGHT_Y), ((6, 44), (12, 58))),
        ((172, 146), ((-52, 8), (-64, 12))),
        ((68, 146), ((52, 8), (64, 12))),
    )

    def __init__(self, parent):
        self.group = _hidden_group(parent, x=_THOUGHT_X, y=_THOUGHT_Y)
        ink = _palette(_INK)
        paper = _palette(_PAPER)
        self._trail = []
        for palette, grow in ((ink, _BORDER), (paper, 0)):
            for x, y, radius in self._CLOUD:
                self.group.append(vectorio.Circle(
                    pixel_shader=palette, x=x, y=y, radius=radius + grow))
            for radius in self._TRAIL_R:
                puff = vectorio.Circle(pixel_shader=palette, x=0, y=0, radius=radius + grow)
                self.group.append(puff)
                self._trail.append(puff)
        offset = -_TILE * _ICON_SCALE // 2
        self._icon = displayio.Group(scale=_ICON_SCALE, x=offset, y=offset)
        self.group.append(self._icon)

    @classmethod
    def rects(cls, spot=0):
        """Screen rects the cloud and its trail cover at SPOTS[spot]."""
        (cx, cy), trail = cls.SPOTS[spot]
        cloud = cls._CLOUD
        out = [(cx + min(x - r for x, _y, r in cloud) - _BORDER,
                cy + min(y - r for _x, y, r in cloud) - _BORDER,
                cx + max(x + r for x, _y, r in cloud) + _BORDER,
                cy + max(y + r for _x, y, r in cloud) + _BORDER)]
        puffs = [(x, y, r) for (x, y), r in zip(trail, cls._TRAIL_R)]
        out.append((cx + min(x - r for x, _y, r in puffs) - _BORDER,
                    cy + min(y - r for _x, y, r in puffs) - _BORDER,
                    cx + max(x + r for x, _y, r in puffs) + _BORDER,
                    cy + max(y + r for _x, y, r in puffs) + _BORDER))
        return out

    def show(self, icon, spot=0):
        """`icon` is (sheet, palette, tile index, tile px), from SceneView.icon();
        `spot` an index into SPOTS."""
        (cx, cy), trail = self.SPOTS[spot]
        self.group.x, self.group.y = cx, cy
        for i, puff in enumerate(self._trail):
            puff.x, puff.y = trail[i % 2]
        sheet, palette, tile, size = icon
        if len(self._icon):
            self._icon.pop()
        self._icon.scale = max(1, _TILE * _ICON_SCALE // size)  # always 32px across
        offset = -size * self._icon.scale // 2
        self._icon.x = self._icon.y = offset
        self._icon.append(displayio.TileGrid(sheet, pixel_shader=palette, width=1, height=1,
                                             tile_width=size, tile_height=size, default_tile=tile))
        self.group.hidden = False


class _Burst:
    """A shouted sound: one word on a jagged yellow star, across the middle."""

    def __init__(self, parent, width, height):
        self._x, self._y = width // 2, height // 2
        self.group = _hidden_group(parent)
        placeholder = [(0, 0), (1, 0), (0, 1)]
        self._outline = vectorio.Polygon(
            pixel_shader=_palette(_INK), points=placeholder, x=0, y=0)
        self._fill = vectorio.Polygon(
            pixel_shader=_palette(_YELLOW), points=placeholder, x=0, y=0)
        self.group.append(self._outline)
        self.group.append(self._fill)
        self._label = Label(comic_fonts.title(), text="", color=_RED,
                            anchor_point=(0.5, 0.5), anchored_position=(self._x, self._y))
        self.group.append(self._label)

    def show(self, word):
        self._label.text = word.upper()
        rx, ry = comic_shapes.burst_radii(self._label.bounding_box[2])
        self._outline.points = comic_shapes.burst_points(self._x, self._y, rx, ry, grow=3)
        self._fill.points = comic_shapes.burst_points(self._x, self._y, rx, ry)
        self.group.hidden = False


class _Emanata:
    """Up to MAX_EMANATA glyphs from one shared sheet, placed in screen pixels."""

    def __init__(self, parent):
        self.group = _hidden_group(parent, scale=_EMANATA_SCALE)
        names = list(comic_shapes.EMANATA)
        self._tile_of = {name: i for i, name in enumerate(names)}
        sheet, palette = glyph_sheet(names)
        self._grids = []
        for _ in range(MAX_EMANATA):
            grid = displayio.TileGrid(
                sheet, pixel_shader=palette, width=1, height=1,
                tile_width=_TILE, tile_height=_TILE,
            )
            grid.hidden = True
            self.group.append(grid)
            self._grids.append(grid)

    def show(self, glyphs):
        for i, grid in enumerate(self._grids):
            grid.hidden = i >= len(glyphs)
            if i < len(glyphs):
                name, x, y = glyphs[i]
                grid[0] = self._tile_of[name]
                grid.x, grid.y = x // _EMANATA_SCALE, y // _EMANATA_SCALE
        self.group.hidden = False


def glyph_sheet(names):
    """comic_shapes.EMANATA glyphs as one sheet of 16px tiles, in `names`
    order, and its palette (index 0 see-through): (bitmap, palette)."""
    sheet = displayio.Bitmap(_TILE * len(names), _TILE, len(comic_shapes.COLORS))
    for i, name in enumerate(names):
        draw_rows(sheet, comic_shapes.EMANATA[name], i * _TILE)
    palette = _palette(*comic_shapes.COLORS)
    palette.make_transparent(0)
    return sheet, palette


def draw_rows(bitmap, rows, x=0):
    """Paint `rows` of comic_shapes.INK_INDEX characters into `bitmap` at column x."""
    for row, text in enumerate(rows):
        for column, character in enumerate(text):
            bitmap[x + column, row] = comic_shapes.INK_INDEX[character]


def _make_ring(width, height):
    """The ink ring at the panel's rim. It reads as the comic panel's border.

    The ring is symmetric, so one quarter is drawn and shown four times,
    mirrored: a quarter of the RAM of a full-screen bitmap (~2 KB, not ~8).
    """
    qw, qh = width // 2, height // 2
    bitmap = displayio.Bitmap(qw, qh, 2)
    for y, x0, x1 in comic_shapes.ring_spans(width, _RING_THICKNESS):
        if y < qh and x0 < qw:
            bitmaptools.fill_region(bitmap, x0, y, min(x1, qw), y + 1, 1)
    palette = _palette(0x000000, _INK)
    palette.make_transparent(0)
    group = displayio.Group()
    for flip_x in (False, True):
        for flip_y in (False, True):
            grid = displayio.TileGrid(bitmap, pixel_shader=palette,
                                      x=qw if flip_x else 0, y=qh if flip_y else 0)
            grid.flip_x = flip_x
            grid.flip_y = flip_y
            group.append(grid)
    return group


class Stage:
    """Everything a beat can show. `shake_target` is the Group a shake moves."""

    def __init__(self, width, height, shake_target=None):
        self.group = displayio.Group()
        self.group.append(_make_ring(width, height))
        self._caption = _Caption(self.group, width)
        self._balloon = _Balloon(self.group, width)
        self._thought = _Thought(self.group)
        self._burst = _Burst(self.group, width, height)
        self._emanata = _Emanata(self.group)
        self._shake_target = shake_target
        self._shake_started = None
        self.caption_band = None  # where the caption up now went (BOTTOM, TOP, ...)

    @property
    def over_name(self):
        """A caption or balloon is up where the room name is: hide the name."""
        return self.caption_band == TOP or (
            not self._balloon.group.hidden and self._balloon.top)

    def show(self, beat, now, things=(), dancers=()):
        """Show a beat. `things` are the scene's clearance rects, for the caption
        and thought bubble to keep off; `dancers` the (x, y, size) of critters
        out in the open, who need somewhere clear to dance (SceneView.avoid).
        Returns the rects the caption and thought bubble cover.

        Few locals here, and the words drawn before the layout search: drawing
        text is the deepest call the game makes, so the frames under it must
        stay small (see _Caption.draw)."""
        self.clear()
        if beat.caption:
            self._caption.draw(beat.caption)
        if beat.speech:
            self._balloon.show(beat.speech, beat.tail)
        if beat.burst:
            self._burst.show(beat.burst)
        if beat.emanata:
            self._emanata.show(beat.emanata)
        if beat.shake and self._shake_target is not None:
            self._shake_started = now
        return self._arrange(beat, things, dancers)

    def _arrange(self, beat, things, dancers):
        """Show the caption and thought bubble where clearance.layout() says;
        returns the rects they cover. Draws no text (see show)."""
        captions = self._caption.bands() if beat.caption else [None]
        clouds = ([_Thought.rects(spot) for spot in range(len(_Thought.SPOTS))]
                  if beat.thought else [None])
        spot, band, covers = clearance.layout(captions, clouds, things, dancers)
        if spot is not None:
            self._thought.show(beat.thought, spot)
        if band is not None:
            self.caption_band = self._caption.place(band)
        return covers

    def clear(self):
        self.caption_band = None
        for element in (self._caption, self._balloon, self._thought, self._burst,
                        self._emanata):
            element.group.hidden = True
        self._stop_shake()

    def update(self, now):
        """Call once per frame; runs any shake."""
        if self._shake_started is None:
            return
        elapsed = now - self._shake_started
        if elapsed >= _SHAKE_S:
            self._stop_shake()
        else:
            step = int(elapsed / _SHAKE_STEP_S)
            self._shake_target.x = _SHAKE_PX if step % 2 else -_SHAKE_PX

    def _stop_shake(self):
        if self._shake_started is not None:
            self._shake_started = None
            self._shake_target.x = 0
