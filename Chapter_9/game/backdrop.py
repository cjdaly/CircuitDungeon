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


def load(bitmap, path, size=SIZE):
    """Fill `bitmap` from the BMP at `path`; False if it's missing or not a backdrop."""
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
        if width != size or abs(height) != size or bits != 8:
            return False
        blit = _blitter()
        f.seek(offset)
        row = bytearray(size)
        for i in range(size):
            if f.readinto(row) != size:
                return False
            y = size - 1 - i if height > 0 else i  # positive height = bottom-up rows
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
    """Owns `.group` (hidden when the room has no art); call show(room) on entering one."""

    def __init__(self, root="/art/rooms"):
        import displayio  # here, so the build tool can import this module

        self._root = root
        self._bitmap = displayio.Bitmap(SIZE, SIZE, len(COLORS))
        palette = displayio.Palette(len(COLORS))
        for i, rgb in enumerate(COLORS):
            palette[i] = rgb
        self.group = displayio.Group(scale=SCALE)
        self.group.append(displayio.TileGrid(self._bitmap, pixel_shader=palette))
        self.group.hidden = True
        self.room = None
        self.art_set = read_set_name(root)

    def show(self, room):
        if room == self.room:
            return
        self.room = room
        self.group.hidden = not load(self._bitmap, self._root + "/" + file_name(room))
