# SPDX-License-Identifier: MIT
"""Outlines and glyphs for the comic overlay kit -- cd-342.9.

Plain numbers and strings with no display code, so tests/test_beats.py can check
that everything fits on the round panel under desktop Python. comic.py draws them.
"""
import math

# How far each spike of an SFX burst reaches, as a share of its radius, so the
# star looks hand-inked rather than regular.
_SPIKES = (1.0, 0.82, 0.95, 0.78, 1.0, 0.86, 0.95, 0.8, 1.0, 0.84, 0.92, 0.8)
BURST_WAIST = 0.62  # the inner points; a burst's word has to fit inside these


def burst_points(cx, cy, rx, ry, grow=0):
    """A jagged star's corners. `grow` widens it, for its black outline."""
    points = []
    corners = len(_SPIKES) * 2
    for i in range(corners):
        reach = BURST_WAIST if i % 2 else _SPIKES[i // 2]
        angle = 2 * math.pi * i / corners
        points.append((
            int(cx + ((rx * reach) + grow) * math.cos(angle)),
            int(cy + ((ry * reach) + grow) * math.sin(angle)),
        ))
    return points


def burst_radii(word_width):
    """The (rx, ry) of a burst that holds a word this wide, kept on the panel."""
    return min((word_width // 2 + 8) / BURST_WAIST, 110), 52


def balloon_points(cx, cy, width, height, tail, grow=0, chamfer=6):
    """A speech balloon's corners: a box with cut corners and a tail to `tail`."""
    left, right = cx - width // 2 - grow, cx + width // 2 + grow
    top, bottom = cy - height // 2 - grow, cy + height // 2 + grow
    tip_x, tip_y = tail
    base = max(left + chamfer + 8, min(tip_x, right - chamfer - 8))
    if tip_y > cy:  # tail hangs from the bottom edge
        tip = (tip_x, tip_y + grow)
        return [
            (left + chamfer, top), (right - chamfer, top),
            (right, top + chamfer), (right, bottom - chamfer),
            (right - chamfer, bottom), (base + 8, bottom), tip, (base - 8, bottom),
            (left + chamfer, bottom), (left, bottom - chamfer), (left, top + chamfer),
        ]
    tip = (tip_x, tip_y - grow)
    return [
        (left + chamfer, top), (base - 8, top), tip, (base + 8, top),
        (right - chamfer, top), (right, top + chamfer), (right, bottom - chamfer),
        (right - chamfer, bottom), (left + chamfer, bottom), (left, bottom - chamfer),
        (left, top + chamfer),
    ]


def ring_spans(size, thickness):
    """(y, x0, x1) spans covering a ring just inside a round panel `size` across.

    x1 is exclusive. A row entirely outside the inner circle is one span; a row
    crossing it is two, one each side.
    """
    inner = size // 2 - thickness
    middle = size // 2
    spans = []
    for y in range(size):
        dy = abs(y + 0.5 - middle)
        if dy >= inner:
            spans.append((y, 0, size))
        else:
            half = int(math.sqrt(inner * inner - dy * dy))
            spans.append((y, 0, middle - half))
            spans.append((y, middle + half, size))
    return spans


# Emanata, 16x16. '.' is see-through and '#' is black ink; the rest index COLORS.
INK_INDEX = {".": 0, "#": 1, "w": 2, "y": 3, "r": 4, "b": 5}
COLORS = (0x000000, 0x140C1C, 0xDEEED6, 0xDAD45E, 0xD04648, 0x597DCE)  # DB16

EMANATA = {
    "wiggle": (
        "...##.....##....",
        "..#ww#...#ww#...",
        "..#ww#...#ww#...",
        "...#ww#...#ww#..",
        "....#ww#...#ww#.",
        "....#ww#...#ww#.",
        "...#ww#...#ww#..",
        "..#ww#...#ww#...",
        "..#ww#...#ww#...",
        "...#ww#...#ww#..",
        "....#ww#...#ww#.",
        "....#ww#...#ww#.",
        "...#ww#...#ww#..",
        "..#ww#...#ww#...",
        "..#ww#...#ww#...",
        "...##.....##....",
    ),
    "bang": (
        "......####......",
        ".....#yyyy#.....",
        ".....#yyyy#.....",
        ".....#yyyy#.....",
        ".....#yyyy#.....",
        "......#yy#......",
        "......#yy#......",
        "......#yy#......",
        "......#yy#......",
        "......#yy#......",
        ".......##.......",
        "......####......",
        ".....#yyyy#.....",
        ".....#yyyy#.....",
        "......####......",
        "................",
    ),
    "question": (
        "....########....",
        "...#yyyyyyyy#...",
        "..#yyy####yyy#..",
        "..#yy#....#yyy#.",
        "...##.....#yyy#.",
        "........##yyy#..",
        ".......#yyyy#...",
        "......#yyy##....",
        "......#yy#......",
        "......#yy#......",
        ".......##.......",
        "......####......",
        ".....#yyyy#.....",
        ".....#yyyy#.....",
        "......####......",
        "................",
    ),
    "heart": (
        "................",
        "...###....###...",
        "..#rrr#..#rrr#..",
        ".#rrrrr##rrrrr#.",
        ".#rrrrrrrrrrrr#.",
        ".#rrrrrrrrrrrr#.",
        ".#rrrrrrrrrrrr#.",
        "..#rrrrrrrrrr#..",
        "...#rrrrrrrr#...",
        "....#rrrrrr#....",
        ".....#rrrr#.....",
        "......#rr#......",
        ".......##.......",
        "................",
        "................",
        "................",
    ),
    "zzz": (
        "..........######",
        "..........#wwww#",
        "............#w#.",
        "...........#w#..",
        "..........#wwww#",
        "..........######",
        "....#####.......",
        "....#www#.......",
        "......#w#.......",
        ".....#w#........",
        "....#www#.......",
        "....#####.......",
        "#####...........",
        "#www#...........",
        ".#w#............",
        "#####...........",
    ),
    "sweat": (
        "........##......",
        ".......#bb#.....",
        ".......#bb#.....",
        "......#bbbb#....",
        "......#bbbb#....",
        ".....#bbbbbb#...",
        ".....#bwbbbb#...",
        "....#bwwbbbbb#..",
        "....#bwbbbbbb#..",
        "....#bbbbbbbb#..",
        "....#bbbbbbbb#..",
        ".....#bbbbbb#...",
        "......######....",
        "................",
        "................",
        "................",
    ),
    "dust": (
        "................",
        "......####......",
        "....##wwww##....",
        "...#wwwwwwww#...",
        ".###wwwwwwww###.",
        "#wwwwwwwwwwwwww#",
        "#wwwwwwwwwwwwww#",
        "#wwwwwwwwwwwwww#",
        ".#wwwwwwwwwwww#.",
        "..###wwwwww###..",
        "....#wwwwww#....",
        ".....######.....",
        "...##......##...",
        "..#ww#....#ww#..",
        "...##......##...",
        "................",
    ),
    "speed": (
        "................",
        "..############..",
        "..#wwwwwwwwww#..",
        "..############..",
        "................",
        "#########.......",
        "#wwwwwww#.......",
        "#########.......",
        "................",
        ".....###########",
        ".....#wwwwwwwww#",
        ".....###########",
        "................",
        "...##########...",
        "...#wwwwwwww#...",
        "...##########...",
    ),
}
