# SPDX-License-Identifier: MIT
"""The gift tag before the title: FOR <PLAYER>, FROM CHRIS -- cd-342.44.

A close-up of a present's corner: wrapping paper filling the screen, a ribbon
crossing under a bow, and the tag tied on with a string. It says who the board
is for (settings.toml PLAYER), so a reset tells you which board is which. It
shows for SHOW_S (settings.toml TAG_SECONDS overrides it), or until a tap, then the title comes up (app.py).

Everything is drawn in code, no art files: the paper is one 24x24 pattern tile
repeated, the rest is vectorio shapes and two fonts' labels. The look -- paper,
ribbon and tag colours -- moves on to the next one at every reset: main.py
keeps a turn counter in the last byte of microcontroller.nvm (next_turn; the
drain log's 12-byte records stop 4 bytes short of the end). Each board starts
the cycle at its own number (settings.toml DEVICE_ID, ws-01 .. ws-10), so
boards reset side by side still differ; a board without one starts by name.
"""

SHOW_S = 10.0  # from when it goes up, while the rest of the game loads
MIN_LIVE_S = 1.0  # at least this long after the loop starts, so a tap can skip it
FROM = "CHRIS"

_INK = 0x140C1C
_TILE = 24  # the paper pattern repeats every 24 px

# DB16 colours (doc/STYLE.md), plus a kraft brown for the paper tag.
_WHITE, _RED, _DARK_RED = 0xDEEED6, 0xD04648, 0x442434
_GREEN, _LEAF, _GOLD, _ORANGE = 0x346524, 0x6DAA2C, 0xDAD45E, 0xD27D2C
_NAVY, _BLUE, _BROWN = 0x30346D, 0x597DCE, 0x854C30
_KRAFT = 0xC9A26B

# Papers: (pattern, colours for its values 0..3).
PAPERS = (
    ("stripes", (_WHITE, _RED, _RED, _WHITE)),
    ("dots", (_GREEN, _WHITE, _LEAF, _GREEN)),
    ("flakes", (_NAVY, _WHITE, _BLUE, _NAVY)),
    ("plaid", (_RED, _DARK_RED, _GOLD, 0x8C2D3A)),
    ("stars", (_RED, _GOLD, _ORANGE, _RED)),
    ("trees", (_WHITE, _GREEN, _RED, _BROWN)),
)
# Ribbons: (face, edge).
_RIBBON_GOLD, _RIBBON_GREEN, _RIBBON_RED = (_GOLD, _ORANGE), (_LEAF, _GREEN), (_RED, _DARK_RED)
_RIBBON_WHITE = (_WHITE, 0x8595A1)
# Tags: (fill, inner line, small words, name).
_TAG_KRAFT = (_KRAFT, _BROWN, _DARK_RED, _RED)
_TAG_WHITE = (_WHITE, _RED, _INK, _GREEN)
_TAG_RED = (_RED, _GOLD, _GOLD, _WHITE)
_TAG_GREEN = (_GREEN, _GOLD, _GOLD, _WHITE)
_TAG_GOLD = (_GOLD, _RED, _DARK_RED, _RED)

# The looks: (paper index, ribbon, tag), picked so nothing clashes. Ten, one per
# gift board ws-01 .. ws-10, ordered so neighbouring boards differ.
STYLES = (
    (0, _RIBBON_GREEN, _TAG_KRAFT),
    (1, _RIBBON_RED, _TAG_WHITE),
    (2, _RIBBON_GOLD, _TAG_RED),
    (3, _RIBBON_GOLD, _TAG_GREEN),
    (4, _RIBBON_GREEN, _TAG_WHITE),
    (5, _RIBBON_RED, _TAG_GOLD),
    (2, _RIBBON_WHITE, _TAG_KRAFT),
    (0, _RIBBON_GOLD, _TAG_GREEN),
    (1, _RIBBON_GOLD, _TAG_RED),
    (3, _RIBBON_WHITE, _TAG_KRAFT),
)

# Layout (240x240 round panel). The tag points left, where its hole is; the bow
# sits up and left where the ribbons cross, and the string runs down to the hole.
_RIBBON_X, _RIBBON_Y, _RIBBON_W = 74, 48, 28  # band centres, width
_KNOT = (_RIBBON_X, _RIBBON_Y)
_TAG_TOP, _TAG_BOTTOM = 70, 190
_TAG_TIP, _TAG_BODY, _TAG_RIGHT, _TAG_CHAMFER = 14, 50, 220, 12
_HOLE = (40, 130)
_HOLE_R, _RING_R = 6, 10
_TEXT_X = 132  # the words' centre: the tag body's, nudged clear of the hole
_NAME_MAX_W = 150  # widest name that fits between the hole and the bezel
_FOR_Y, _NAME_Y, _FROM_Y = 96, 131, 166


def clean_name(name):
    """The name in the fonts' letters: upper case, unknown characters dropped."""
    import comic_fonts

    text = "".join(ch for ch in name.upper().replace("-", " ") if ch in comic_fonts.GLYPHS)
    return " ".join(text.split())


def board_number(device_id):
    """The number at the end of a DEVICE_ID ("ws-07" -> 7), or None."""
    digits = ""
    for ch in reversed(device_id or ""):
        if not ch.isdigit():
            break
        digits = ch + digits
    return int(digits) if digits else None


def style_for(name, device_id=None, turn=0):
    """The look for this board on this `turn`: its own start, then on round."""
    number = board_number(device_id)
    if number:
        start = number - 1
    else:
        start = 0
        for ch in name:
            start = (start * 31 + ord(ch)) % 65521
    return STYLES[(start + (turn or 0)) % len(STYLES)]


def next_turn(nvm):
    """This boot's turn, counted in nvm's last byte, which is moved on for the next.

    Erased flash (0xFF) or anything out of range starts again at 0.
    """
    at = len(nvm) - 1
    turn = nvm[at]
    if turn >= len(STYLES):
        turn = 0
    nvm[at] = (turn + 1) % len(STYLES)
    return turn


def name_layout(widths):
    """How to letter the name, given (title width, caption width) at scale 1.

    Returns ("title" | "caption", scale), the biggest that fits _NAME_MAX_W,
    or None when even the caption font is too wide for one line.
    """
    title_w, caption_w = widths
    if 2 * title_w <= _NAME_MAX_W:
        return ("title", 2)
    if title_w <= _NAME_MAX_W:
        return ("title", 1)
    if caption_w <= _NAME_MAX_W:
        return ("caption", 1)
    return None


def split_name(text):
    """Two lines for a long name, broken at the space nearest the middle."""
    spaces = [i for i, ch in enumerate(text) if ch == " "]
    if not spaces:
        half = len(text) // 2
        return text[:half], text[half:]
    cut = min(spaces, key=lambda i: abs(i - len(text) // 2))
    return text[:cut], text[cut + 1:]


def paint_pattern(bitmap, pattern):
    """Draw one _TILE x _TILE tile of `pattern` into `bitmap` (values 0..3)."""
    n = _TILE
    for y in range(n):
        for x in range(n):
            bitmap[x, y] = _pattern_value(pattern, x, y)


def _pattern_value(pattern, x, y):
    n = _TILE
    if pattern == "stripes":  # candy stripes, down to the right
        return 1 if (x + y) % 12 < 5 else 0
    if pattern == "dots":  # big dots on a half-drop grid, small ones between
        for cx, cy, r2, value in ((6, 6, 10, 1), (18, 18, 10, 1), (18, 6, 2, 2), (6, 18, 2, 2)):
            if (x - cx) ** 2 + (y - cy) ** 2 <= r2:
                return value
        return 0
    if pattern == "flakes":  # six-armed flakes and specks
        for cx, cy in ((6, 6), (18, 18)):
            dx, dy = x - cx, y - cy
            if abs(dx) <= 4 and abs(dy) <= 4 and (dx == 0 or dy == 0 or abs(dx) == abs(dy)):
                return 1 if abs(dx) + abs(dy) < 7 else 2
        if (x, y) in ((18, 5), (5, 18), (12, 12)):
            return 2
        return 0
    if pattern == "plaid":
        bar_x, bar_y = x % n in (3, 4, 5, 6), y % n in (3, 4, 5, 6)
        if x % n == 15 or y % n == 15:
            return 2
        if bar_x and bar_y:
            return 1
        if bar_x or bar_y:
            return 3
        return 0
    if pattern == "stars":  # five-ish point stars from a plus and an x
        for cx, cy, big in ((6, 6, True), (18, 18, False)):
            dx, dy = abs(x - cx), abs(y - cy)
            reach = 4 if big else 3
            if (dx == 0 and dy <= reach) or (dy == 0 and dx <= reach) or (
                    dx == dy and dx <= reach - 2) or (dx + dy <= 2):
                return 1 if big else 2
        return 0
    if pattern == "trees":  # little trees with a trunk, red berries between
        for cx, top in ((6, 1), (18, 13)):
            row = y - top
            if 0 <= row < 8 and abs(x - cx) <= row // 2:
                return 1
            if row in (8, 9) and x == cx:
                return 3
        if (x, y) in ((17, 4), (18, 5), (5, 16), (6, 17)):
            return 2
        return 0
    return 0


def _tag_points(inset):
    """The tag's outline, `inset` px in from the outer edge."""
    i = inset
    top, bottom = _TAG_TOP + i, _TAG_BOTTOM - i
    mid = (_TAG_TOP + _TAG_BOTTOM) // 2
    body, right, chamfer = _TAG_BODY + i // 2, _TAG_RIGHT - i, _TAG_CHAMFER
    return [(_TAG_TIP + 2 * i, mid), (body, top), (right - chamfer, top), (right, top + chamfer),
            (right, bottom - chamfer), (right - chamfer, bottom), (body, bottom)]


def _line_points(a, b, width):
    """A straight line from a to b, `width` px thick, as a polygon."""
    import math

    dx, dy = b[0] - a[0], b[1] - a[1]
    length = math.sqrt(dx * dx + dy * dy) or 1.0
    ox, oy = -dy / length * width / 2, dx / length * width / 2
    return [(int(a[0] + ox), int(a[1] + oy)), (int(b[0] + ox), int(b[1] + oy)),
            (int(b[0] - ox), int(b[1] - oy)), (int(a[0] - ox), int(a[1] - oy))]


def _ellipse_points(cx, cy, rx, ry, tilt, steps=14):
    import math

    c, s = math.cos(tilt), math.sin(tilt)
    points = []
    for k in range(steps):
        a = 2 * math.pi * k / steps
        x, y = rx * math.cos(a), ry * math.sin(a)
        points.append((int(cx + x * c - y * s), int(cy + x * s + y * c)))
    return points


class GiftTag:
    """Owns `.group`. done(now) says when it has shown long enough."""

    def __init__(self, name, sender=FROM, width=240, height=240, now=0.0, device_id=None,
                 turn=0, show_s=SHOW_S):
        import displayio
        import vectorio
        from adafruit_display_text.bitmap_label import Label

        import comic_fonts

        self.name = clean_name(name)
        self.shown_at = now
        self.until = now + show_s
        paper_index, ribbon, tag = style_for(self.name, device_id, turn)
        pattern, paper_colors = PAPERS[paper_index]
        self.style = (pattern, ribbon, tag)

        def solid(color):
            palette = displayio.Palette(1)
            palette[0] = color
            return palette

        self.group = displayio.Group()
        group = self.group

        # The paper: one tile, repeated over the whole screen.
        tile = displayio.Bitmap(_TILE, _TILE, 4)
        paint_pattern(tile, pattern)
        paper = displayio.Palette(4)
        for i, color in enumerate(paper_colors):
            paper[i] = color
        group.append(displayio.TileGrid(tile, pixel_shader=paper, width=width // _TILE + 1,
                                        height=height // _TILE + 1, tile_width=_TILE,
                                        tile_height=_TILE))

        # The ribbons: a band down and a band across, each with darker edges.
        face, edge = solid(ribbon[0]), solid(ribbon[1])
        half = _RIBBON_W // 2
        for vertical in (True, False):
            for shader, grow in ((edge, 0), (face, -3)):
                if vertical:
                    group.append(vectorio.Rectangle(pixel_shader=shader,
                                                    width=_RIBBON_W + 2 * grow, height=height,
                                                    x=_RIBBON_X - half - grow, y=0))
                else:
                    group.append(vectorio.Rectangle(pixel_shader=shader, width=width,
                                                    height=_RIBBON_W + 2 * grow,
                                                    x=0, y=_RIBBON_Y - half - grow))

        # The tag: ink edge, fill, a thin inner line, then the words.
        fill, line, words, name_color = tag
        ink = solid(_INK)
        for shader, inset in ((ink, 0), (solid(fill), 3), (solid(line), 7), (solid(fill), 9)):
            group.append(vectorio.Polygon(pixel_shader=shader, points=_tag_points(inset)))

        caption = comic_fonts.caption()
        names = self._name_labels(Label, comic_fonts, name_color)
        spread = 6 if len(names) > 1 else 0  # a two-line name needs more room
        group.append(Label(caption, text="FOR", color=words, anchor_point=(0.5, 0.5),
                           anchored_position=(_TEXT_X, _FOR_Y - spread)))
        group.append(Label(caption, text="FROM " + clean_name(sender), color=words,
                           anchor_point=(0.5, 0.5),
                           anchored_position=(_TEXT_X, _FROM_Y + spread)))
        for label in names:
            group.append(label)

        # The string, from under the bow down to the hole: ink, then twine.
        twine = solid(_WHITE if fill != _WHITE else _RED)
        group.append(vectorio.Polygon(pixel_shader=ink, points=_line_points(_KNOT, _HOLE, 5)))
        group.append(vectorio.Polygon(pixel_shader=twine, points=_line_points(_KNOT, _HOLE, 3)))
        # The hole's reinforcing ring, and the hole showing the paper's colour.
        group.append(vectorio.Circle(pixel_shader=ink, radius=_RING_R + 1, x=_HOLE[0], y=_HOLE[1]))
        group.append(vectorio.Circle(pixel_shader=solid(line), radius=_RING_R, x=_HOLE[0],
                                     y=_HOLE[1]))
        group.append(vectorio.Circle(pixel_shader=ink, radius=_HOLE_R + 1, x=_HOLE[0],
                                     y=_HOLE[1]))
        group.append(vectorio.Circle(pixel_shader=solid(paper_colors[0]), radius=_HOLE_R,
                                     x=_HOLE[0], y=_HOLE[1]))
        group.append(vectorio.Polygon(pixel_shader=twine, points=_line_points(
            (_HOLE[0] - 1, _HOLE[1] - _HOLE_R - 2), (_HOLE[0] + 2, _HOLE[1]), 3)))

        # The bow over the knot: two loops, two tails, the knot.
        kx, ky = _KNOT
        for points in (
                [(kx - 4, ky), (kx - 22, ky + 34), (kx - 12, ky + 30), (kx - 8, ky + 38), (kx + 2, ky)],
                [(kx + 4, ky), (kx + 24, ky + 32), (kx + 14, ky + 29), (kx + 12, ky + 38), (kx - 2, ky)]):
            group.append(vectorio.Polygon(pixel_shader=ink, points=_grow(points, kx, ky + 18, 2)))
            group.append(vectorio.Polygon(pixel_shader=face, points=points))
        for side in (-1, 1):
            cx, cy, tilt = kx + side * 22, ky - 6, side * -0.35
            group.append(vectorio.Polygon(pixel_shader=ink, points=_ellipse_points(
                cx, cy, 25, 15, tilt)))
            group.append(vectorio.Polygon(pixel_shader=face, points=_ellipse_points(
                cx, cy, 22, 12, tilt)))
            group.append(vectorio.Polygon(pixel_shader=edge, points=_ellipse_points(
                cx + side * 2, cy - 1, 12, 5, tilt)))
        group.append(vectorio.Circle(pixel_shader=ink, radius=11, x=kx, y=ky))
        group.append(vectorio.Circle(pixel_shader=face, radius=8, x=kx, y=ky))
        group.append(vectorio.Circle(pixel_shader=edge, radius=3, x=kx - 2, y=ky - 2))

    def _name_labels(self, Label, comic_fonts, color):
        """The name, as big as fits: one line if it can, else two."""
        fonts = {"title": comic_fonts.title(), "caption": comic_fonts.caption()}

        def width(font, text):
            return Label(font, text=text).bounding_box[2]

        layout = name_layout((width(fonts["title"], self.name),
                              width(fonts["caption"], self.name)))
        if layout is not None:
            font, scale = layout
            return [Label(fonts[font], text=self.name, color=color, scale=scale,
                          anchor_point=(0.5, 0.5), anchored_position=(_TEXT_X, _NAME_Y))]
        lines = split_name(self.name)
        font = fonts["title"]
        if max(width(font, line) for line in lines) > _NAME_MAX_W:
            font = fonts["caption"]
        return [Label(font, text=line, color=color, anchor_point=(0.5, 0.5),
                      anchored_position=(_TEXT_X, _NAME_Y + dy))
                for line, dy in zip(lines, (-13, 13))]

    def done(self, now):
        return now >= self.until


def _grow(points, cx, cy, by):
    """`points` pushed `by` px further out from (cx, cy): a rough outline."""
    import math

    grown = []
    for x, y in points:
        dx, dy = x - cx, y - cy
        d = math.sqrt(dx * dx + dy * dy) or 1.0
        grown.append((int(x + dx / d * by), int(y + dy / d * by)))
    return grown
