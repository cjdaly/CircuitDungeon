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
_BORDER = 2
_CAPTION_PAD_X = 6
_CAPTION_PAD_Y = 2
_BALLOON_PAD = 8
_BALLOON_Y_ABOVE = 72  # balloon's middle when its tail points down the screen
_BALLOON_Y_BELOW = 168
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

    def show(self, text):
        widest, count = self._lines.show(text, self._middle, _CAPTION_Y)
        width = widest + 2 * _CAPTION_PAD_X
        height = count * _LINE_HEIGHT + 2 * _CAPTION_PAD_Y
        self._fill.width, self._fill.height = width, height
        self._fill.x = self._middle - width // 2
        self._fill.y = _CAPTION_Y - height // 2
        self._border.width = width + 2 * _BORDER
        self._border.height = height + 2 * _BORDER
        self._border.x = self._fill.x - _BORDER
        self._border.y = self._fill.y - _BORDER
        self.group.hidden = False


class _Balloon:
    """A critter talking: black words in a white balloon with a tail."""

    def __init__(self, parent, width):
        self._middle = width // 2
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
        y = _BALLOON_Y_ABOVE if tail[1] > 120 else _BALLOON_Y_BELOW
        widest, count = self._lines.show(text, self._middle, y)
        width = widest + 2 * _BALLOON_PAD
        height = count * _LINE_HEIGHT + _BALLOON_PAD
        self._outline.points = comic_shapes.balloon_points(
            self._middle, y, width, height, tail, grow=_BORDER)
        self._fill.points = comic_shapes.balloon_points(self._middle, y, width, height, tail)
        self.group.hidden = False


class _Thought:
    """What a critter wants: an icon, no words, in a cloud with trailing circles."""

    # (x, y, radius) from the cloud's middle; the last two are the trail.
    _PUFFS = ((-20, -8, 22), (20, -8, 22), (-20, 12, 20), (20, 12, 20), (0, 0, 32),
              (6, 44, 7), (12, 58, 4))

    def __init__(self, parent):
        self.group = _hidden_group(parent, x=_THOUGHT_X, y=_THOUGHT_Y)
        ink = _palette(_INK)
        paper = _palette(_PAPER)
        for x, y, radius in self._PUFFS:
            self.group.append(vectorio.Circle(
                pixel_shader=ink, x=x, y=y, radius=radius + _BORDER))
        for x, y, radius in self._PUFFS:
            self.group.append(vectorio.Circle(pixel_shader=paper, x=x, y=y, radius=radius))
        offset = -_TILE * _ICON_SCALE // 2
        self._icon = displayio.Group(scale=_ICON_SCALE, x=offset, y=offset)
        self.group.append(self._icon)

    def show(self, icon):
        """`icon` is (sheet, palette, tile index, tile px), from SceneView.icon()."""
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
        sheet = displayio.Bitmap(_TILE * len(names), _TILE, len(comic_shapes.COLORS))
        for i, name in enumerate(names):
            draw_rows(sheet, comic_shapes.EMANATA[name], i * _TILE)
        palette = _palette(*comic_shapes.COLORS)
        palette.make_transparent(0)
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

    def show(self, beat, now):
        self.clear()
        if beat.caption:
            self._caption.show(beat.caption)
        if beat.speech:
            self._balloon.show(beat.speech, beat.tail)
        if beat.thought:
            self._thought.show(beat.thought)
        if beat.burst:
            self._burst.show(beat.burst)
        if beat.emanata:
            self._emanata.show(beat.emanata)
        if beat.shake and self._shake_target is not None:
            self._shake_started = now

    def clear(self):
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
