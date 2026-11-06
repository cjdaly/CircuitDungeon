# SPDX-License-Identifier: MIT
"""Stand-ins for displayio & co. that really draw, for tools/preview.py -- cd-342.25.

Just the parts of displayio, vectorio, bitmaptools, adafruit_display_text's
bitmap_label and adafruit_bitmap_font that Chapter_9/game uses, written so a
Group tree can be rendered to a Pillow image on the desktop. install() puts them
in sys.modules; render(group) draws the 240x240 panel.

It's a preview, not an emulator: label placement can be a pixel or two off the
real bitmap_label, and only what the game calls is here. Desktop only, needs
Pillow (`/usr/bin/python3` on Chris's Mac).
"""
import os
import sys
import types

from PIL import Image

GAME_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "game"))


# --------------------------------------------------------------------------- #
# displayio

class Bitmap:
    def __init__(self, width, height, value_count):
        self.width, self.height = width, height
        self._pixels = bytearray(width * height)

    def __setitem__(self, index, value):
        if isinstance(index, tuple):
            index = index[1] * self.width + index[0]
        self._pixels[index] = value

    def __getitem__(self, index):
        if isinstance(index, tuple):
            index = index[1] * self.width + index[0]
        return self._pixels[index]

    def fill(self, value):
        self._pixels = bytearray([value]) * (self.width * self.height)


class Palette:
    def __init__(self, color_count, dither=False):
        self._colors = [0] * color_count
        self._transparent = set()

    def __len__(self):
        return len(self._colors)

    def __setitem__(self, index, color):
        self._colors[index] = color

    def __getitem__(self, index):
        return self._colors[index]

    def make_transparent(self, index):
        self._transparent.add(index)

    def make_opaque(self, index):
        self._transparent.discard(index)

    def is_transparent(self, index):
        return index in self._transparent


class OnDiskBitmap(Bitmap):
    """Loads an indexed BMP. A path starting with "/" is the device's root, the game dir."""

    def __init__(self, path):
        if path.startswith("/"):
            path = os.path.join(GAME_DIR, path[1:])
        image = Image.open(path)
        if image.mode != "P":
            raise ValueError("preview only handles indexed BMPs: " + path)
        super().__init__(image.width, image.height, 256)
        self._pixels = bytearray(image.tobytes())
        flat = image.getpalette()
        self.pixel_shader = Palette(len(flat) // 3)
        for i in range(len(flat) // 3):
            r, g, b = flat[3 * i:3 * i + 3]
            self.pixel_shader[i] = (r << 16) | (g << 8) | b


class TileGrid:
    def __init__(self, bitmap, *, pixel_shader, width=1, height=1, tile_width=None,
                 tile_height=None, default_tile=0, x=0, y=0):
        self.bitmap, self.pixel_shader = bitmap, pixel_shader
        self.width, self.height = width, height
        self.tile_width = tile_width or bitmap.width
        self.tile_height = tile_height or bitmap.height
        self._tiles = [default_tile] * (width * height)
        self.x, self.y = x, y
        self.hidden = False
        self.flip_x = self.flip_y = False

    def __setitem__(self, index, tile):
        if isinstance(index, tuple):
            index = index[1] * self.width + index[0]
        self._tiles[index] = tile

    def __getitem__(self, index):
        if isinstance(index, tuple):
            index = index[1] * self.width + index[0]
        return self._tiles[index]


class Group(list):
    def __init__(self, *, scale=1, x=0, y=0):
        super().__init__()
        self.scale, self.x, self.y = scale, x, y
        self.hidden = False


# --------------------------------------------------------------------------- #
# vectorio

class _Shape:
    def __init__(self, *, pixel_shader, x=0, y=0, color_index=0, **kwargs):
        self.pixel_shader, self.x, self.y = pixel_shader, x, y
        self.color_index = color_index
        self.hidden = False
        self.__dict__.update(kwargs)


class Circle(_Shape):
    def covers(self, px, py):
        return px * px + py * py <= self.radius * self.radius


class Rectangle(_Shape):
    def covers(self, px, py):
        return 0 <= px < self.width and 0 <= py < self.height


class Polygon(_Shape):
    def covers(self, px, py):
        inside = False
        points = self.points
        j = len(points) - 1
        for i, (xi, yi) in enumerate(points):
            xj, yj = points[j]
            if (yi > py) != (yj > py) and px < (xj - xi) * (py - yi) / (yj - yi) + xi:
                inside = not inside
            j = i
        return inside


def fill_region(bitmap, x1, y1, x2, y2, value):
    for y in range(y1, y2):
        for x in range(x1, x2):
            bitmap[x, y] = value


# --------------------------------------------------------------------------- #
# Fonts and labels

class _Glyph:
    def __init__(self, dwidth, width, height, dx, dy, rows):
        self.shift_x = dwidth
        self.width, self.height, self.dx, self.dy = width, height, dx, dy
        self.rows = rows  # list of ints, MSB first


class BdfFont:
    def __init__(self, path):
        full = path if os.path.isabs(path) else os.path.join(GAME_DIR, path)
        self._glyphs = {}
        self._box = (0, 0, 0, 0)
        with open(full) as handle:
            lines = iter(handle.read().splitlines())
        for line in lines:
            if line.startswith("FONTBOUNDINGBOX"):
                self._box = tuple(int(v) for v in line.split()[1:5])
            elif line.startswith("STARTCHAR"):
                code = dwidth = None
                bbx = (0, 0, 0, 0)
                for line in lines:
                    if line.startswith("ENCODING"):
                        code = int(line.split()[1])
                    elif line.startswith("DWIDTH"):
                        dwidth = int(line.split()[1])
                    elif line.startswith("BBX"):
                        bbx = tuple(int(v) for v in line.split()[1:5])
                    elif line == "BITMAP":
                        rows = [int(next(lines), 16) for _ in range(bbx[1])]
                        self._glyphs[code] = _Glyph(dwidth, *bbx, rows)
                        break

    def get_bounding_box(self):
        return self._box

    def get_glyph(self, code):
        return self._glyphs.get(code)

    def load_glyphs(self, glyphs):
        pass


class Label:
    """bitmap_label.Label: text in one color, placed by its anchor point."""

    def __init__(self, font, *, text="", color=0xFFFFFF, anchor_point=None,
                 anchored_position=None, scale=1, x=0, y=0, background_color=None,
                 **_ignored):
        self.font, self.color, self.scale = font, color, scale
        self.anchor_point, self.anchored_position = anchor_point, anchored_position
        self.background_color = background_color
        self.x, self.y = x, y
        self.hidden = False
        self.text = text

    @property
    def bounding_box(self):
        width = 0
        for ch in self.text:
            glyph = self.font.get_glyph(ord(ch))
            if glyph is not None:
                width += glyph.shift_x
        _, height, _, _ = self.font.get_bounding_box()
        return (0, 0, width, height)

    def pixels(self):
        """(x, y) offsets of every inked pixel, from the label's top-left."""
        _, box_h, _, box_dy = self.font.get_bounding_box()
        baseline = box_h + box_dy
        cursor = 0
        for ch in self.text:
            glyph = self.font.get_glyph(ord(ch))
            if glyph is None:
                continue
            top = baseline - glyph.dy - glyph.height
            span = ((glyph.width + 7) // 8) * 8
            for row, bits in enumerate(glyph.rows):
                for col in range(glyph.width):
                    if bits >> (span - 1 - col) & 1:
                        yield cursor + glyph.dx + col, top + row
            cursor += glyph.shift_x

    def origin(self):
        if self.anchor_point is None or self.anchored_position is None:
            return self.x, self.y
        _, _, width, height = self.bounding_box
        ax, ay = self.anchor_point
        px, py = self.anchored_position
        return round(px - ax * width * self.scale), round(py - ay * height * self.scale)


# --------------------------------------------------------------------------- #

def install():
    """Put the fakes in sys.modules and make the game dir importable and current."""
    displayio = types.ModuleType("displayio")
    displayio.Bitmap, displayio.Palette, displayio.Group = Bitmap, Palette, Group
    displayio.TileGrid, displayio.OnDiskBitmap = TileGrid, OnDiskBitmap
    vectorio = types.ModuleType("vectorio")
    vectorio.Circle, vectorio.Rectangle, vectorio.Polygon = Circle, Rectangle, Polygon
    bitmaptools = types.ModuleType("bitmaptools")
    bitmaptools.fill_region = fill_region
    text_pkg = types.ModuleType("adafruit_display_text")
    bitmap_label = types.ModuleType("adafruit_display_text.bitmap_label")
    bitmap_label.Label = Label
    text_pkg.bitmap_label = bitmap_label
    font_pkg = types.ModuleType("adafruit_bitmap_font")
    font_mod = types.ModuleType("adafruit_bitmap_font.bitmap_font")
    font_mod.load_font = BdfFont
    font_pkg.bitmap_font = font_mod
    sys.modules.update({
        "displayio": displayio, "vectorio": vectorio, "bitmaptools": bitmaptools,
        "adafruit_display_text": text_pkg, "adafruit_display_text.bitmap_label": bitmap_label,
        "adafruit_bitmap_font": font_pkg, "adafruit_bitmap_font.bitmap_font": font_mod,
    })
    if GAME_DIR not in sys.path:
        sys.path.insert(0, GAME_DIR)
    os.chdir(GAME_DIR)  # fonts load by relative path, as on the device


def _rgb(color):
    return (color >> 16) & 0xFF, (color >> 8) & 0xFF, color & 0xFF


def render(root, size=240, round_panel=True):
    """Draw `root` (a Group) into a new RGB image, the way the panel would show it."""
    image = Image.new("RGB", (size, size), (0, 0, 0))
    canvas = image.load()

    def plot(x, y, color):
        if 0 <= x < size and 0 <= y < size:
            canvas[x, y] = _rgb(color)

    def draw(node, ox, oy, scale):
        if getattr(node, "hidden", False):
            return
        x0 = ox + node.x * scale
        y0 = oy + node.y * scale
        if isinstance(node, Group):
            for child in node:
                draw(child, x0, y0, scale * node.scale)
        elif isinstance(node, TileGrid):
            draw_tilegrid(node, x0, y0, scale)
        elif isinstance(node, _Shape):
            draw_shape(node, x0, y0, scale)
        elif isinstance(node, Label):
            draw_label(node, ox, oy, scale)

    def draw_tilegrid(grid, x0, y0, scale):
        tw, th = grid.tile_width, grid.tile_height
        across = grid.bitmap.width // tw
        palette = grid.pixel_shader
        for gy in range(grid.height):
            for gx in range(grid.width):
                tile = grid[gx, gy]
                sx0, sy0 = (tile % across) * tw, (tile // across) * th
                for ty in range(th):
                    for tx in range(tw):
                        sx = tw - 1 - tx if grid.flip_x else tx
                        sy = th - 1 - ty if grid.flip_y else ty
                        index = grid.bitmap[sx0 + sx, sy0 + sy]
                        if palette.is_transparent(index):
                            continue
                        color = palette[index]
                        px = x0 + (gx * tw + tx) * scale
                        py = y0 + (gy * th + ty) * scale
                        for dy in range(scale):
                            for dx in range(scale):
                                plot(px + dx, py + dy, color)

    def draw_shape(shape, x0, y0, scale):
        if shape.pixel_shader.is_transparent(shape.color_index):
            return
        color = shape.pixel_shader[shape.color_index]
        if isinstance(shape, Circle):
            r = shape.radius
            box = (-r, -r, r + 1, r + 1)
        elif isinstance(shape, Rectangle):
            box = (0, 0, shape.width, shape.height)
        else:
            xs = [p[0] for p in shape.points]
            ys = [p[1] for p in shape.points]
            box = (min(xs), min(ys), max(xs) + 1, max(ys) + 1)
        for py in range(box[1], box[3]):
            for px in range(box[0], box[2]):
                if shape.covers(px, py):
                    for dy in range(scale):
                        for dx in range(scale):
                            plot(x0 + px * scale + dx, y0 + py * scale + dy, color)

    def draw_label(label, ox, oy, scale):
        lx, ly = label.origin()
        s = scale * label.scale
        if label.background_color is not None:
            _, _, width, height = label.bounding_box
            for py in range(height * s):
                for px in range(width * s):
                    plot(ox + lx * scale + px, oy + ly * scale + py, label.background_color)
        for px, py in label.pixels():
            for dy in range(s):
                for dx in range(s):
                    plot(ox + lx * scale + px * s + dx, oy + ly * scale + py * s + dy, label.color)

    draw(root, 0, 0, 1)
    if round_panel:
        middle = size / 2
        for y in range(size):
            for x in range(size):
                if (x + 0.5 - middle) ** 2 + (y + 0.5 - middle) ** 2 > middle * middle:
                    canvas[x, y] = (40, 40, 44)
    return image
