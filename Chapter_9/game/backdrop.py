# SPDX-License-Identifier: MIT
"""Room backdrops: background art behind each room's scene -- cd-342.35.

Each room with art has a 120x120 BMP in /art/rooms/, shown at 2x under
everything else. Which version of the art that is -- the hand-drawn set or
another one -- is picked at deploy time (art_sets/README.md, deploy.sh
--art-set); /art/rooms/SET.txt names it, and `Backdrop.art_set` reads it. There is ONE
backdrop bitmap, made at start-up and refilled from flash on each room change,
so the RAM cost is the same however many rooms get art: 120x120 at 16 colours
is 4 bits a pixel, 7.2 KB.

Why not draw straight from flash with OnDiskBitmap, as the critter sheet does:
measured on ws-10 (2026-11-07), that made every frame ~14% slower (74 vs 65 ms
median) because a bobbing critter redraws over it; a RAM bitmap costs nothing
per frame and refilling it takes ~11 ms.

The BMPs are 8-bit indexed, index i = DB16 colour i (scene_art.COLORS[i + 1]:
a backdrop needs no see-through slot), with no row padding since 120 is a
multiple of 4. A room without a file, or a file that isn't that, just hides
the backdrop and the plain background shows.
"""
import struct

import scene_art

SIZE = 120
SCALE = 2
COLORS = scene_art.COLORS[1:17]  # DB16, without scene_art's see-through slot 0


def file_name(room):
    """"Kids' Bedroom" -> "kids_bedroom.bmp"."""
    return room.lower().replace("'", "").replace(" ", "_") + ".bmp"


def _blitter():
    try:
        from bitmaptools import arrayblit
    except ImportError:
        arrayblit = None
    if arrayblit is None:
        def arrayblit(bitmap, data, x1, y1, x2, y2):  # desktop stand-ins lack it
            for x in range(x1, x2):
                bitmap[x, y1] = data[x - x1]
    return arrayblit


def load(bitmap, path, size=SIZE, height=None):
    """Fill `bitmap` from the 8-bit BMP at `path`, `size` wide and `height` (default:
    `size`) tall; False if it's missing or not that."""
    height_want = height or size
    try:
        f = open(path, "rb")
    except OSError:
        return False
    with f:
        head = f.read(54)
        if len(head) < 54 or head[:2] != b"BM":
            return False
        offset = struct.unpack_from("<I", head, 10)[0]
        width, height = struct.unpack_from("<ii", head, 18)
        bits = struct.unpack_from("<H", head, 28)[0]
        if width != size or abs(height) != height_want or bits != 8:
            return False
        blit = _blitter()
        f.seek(offset)
        row = bytearray((size + 3) & ~3)  # BMP rows pad to 4 bytes
        rows = abs(height)
        for i in range(rows):
            if f.readinto(row) != len(row):
                return False
            y = rows - 1 - i if height > 0 else i  # positive height = bottom-up rows
            blit(bitmap, row, 0, y, size, y + 1)
    return True


def read_set_name(root):
    """The art set deployed at `root` (its SET.txt), or None."""
    try:
        with open(root + "/SET.txt") as f:
            return f.read().strip() or None
    except OSError:
        return None


class Backdrop:
    """Owns `.group` (hidden when the room has no art); call show(room) on entering one.

    The one 120x120 bitmap is shared: the ornament screen shows its own art in
    it too (view() + show_file()), since only one screen is up at a time. So
    after another screen has used it, show(room) reloads the room's art.
    """

    def __init__(self, root="/art/rooms"):
        import displayio  # here, so the build tool can import this module

        self._displayio = displayio
        self.root = root
        self.bitmap = displayio.Bitmap(SIZE, SIZE, len(COLORS))
        self.palette = make_palette(displayio)
        self.group = displayio.Group(scale=SCALE)
        self.group.append(displayio.TileGrid(self.bitmap, pixel_shader=self.palette))
        self.group.hidden = True
        self.room = None
        self.loaded = None  # the file now in the bitmap, whoever asked for it
        self.ok = False  # ...and whether it loaded
        self.art_set = read_set_name(root)

    def show(self, room):
        self.room = room
        self.group.hidden = not self.show_file(file_name(room))

    def show_file(self, name):
        """Load /art/rooms/<name> into the shared bitmap (if it isn't there already)."""
        if name != self.loaded:
            self.loaded = name
            self.ok = load(self.bitmap, self.root + "/" + name)
        return self.ok

    def view(self, palette=None):
        """Another 2x view of the shared bitmap, for another screen's group."""
        group = self._displayio.Group(scale=SCALE)
        group.append(self._displayio.TileGrid(self.bitmap, pixel_shader=palette or self.palette))
        return group


def make_palette(displayio, dim=1.0):
    """The 16 DB16 colours, scaled by `dim` (1.0 = as drawn)."""
    palette = displayio.Palette(len(COLORS))
    for i, rgb in enumerate(COLORS):
        palette[i] = scale_color(rgb, dim)
    return palette


def scale_color(rgb, k):
    if k == 1.0:
        return rgb
    return ((int(((rgb >> 16) & 255) * k) << 16) | (int(((rgb >> 8) & 255) * k) << 8)
            | int((rgb & 255) * k))
