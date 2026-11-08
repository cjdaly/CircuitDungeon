# SPDX-License-Identifier: MIT
"""Scene art: lures, hiding spots, props -- what they are, not what they look like.
cd-342.26, cd-342.38.

The pictures themselves are in each art set's objects.bmp (art_sets/README.md):
32x32 tiles in NAMES order, 8-bit, index = COLORS index (0 see-through; 17-19
are a present's paper/shade/ribbon, swapped per critter). tools/build_sprites.py
builds them; the hand-drawn originals (16x16 character rows) are in
tools/scene_art_src.py, kept off the board because their strings cost ~15 KB
of RAM. scene_view.py reads the sheet from flash and shows it at 2x, the same
pixel size as the room art.
"""

COLORS = (
    0x000000,  # 0  see-through
    0x140C1C,  # 1  # ink
    0x442434,  # 2  p plum
    0x30346D,  # 3  n navy
    0x4E4A4E,  # 4  d dark grey
    0x854C30,  # 5  o brown
    0x346524,  # 6  G dark green
    0xD04648,  # 7  r red
    0x757161,  # 8  g grey
    0x597DCE,  # 9  b blue
    0xD27D2C,  # 10 O orange
    0x8595A1,  # 11 s steel
    0x6DAA2C,  # 12 l leaf green
    0xD2AA99,  # 13 k skin / tan
    0x6DC2CA,  # 14 c cyan
    0xDAD45E,  # 15 y yellow
    0xDEEED6,  # 16 w white
    0xD04648,  # 17 X a present's paper  } stand-ins: each box swaps these
    0x442434,  # 18 x ...its shade       } three for its own (BOX_COLORS)
    0xDAD45E,  # 19 R ...its ribbon      }
)
KEY = {
    ".": 0, "#": 1, "p": 2, "n": 3, "d": 4, "o": 5, "G": 6, "r": 7, "g": 8,
    "b": 9, "O": 10, "s": 11, "l": 12, "k": 13, "c": 14, "y": 15, "w": 16,
    "X": 17, "x": 18, "R": 19,
}
BOX_INDEXES = (17, 18, 19)  # paper, shade, ribbon

# Each critter's present: (paper, shade, ribbon), all DB16.
BOX_COLORS = {
    "cat": (0xD04648, 0x442434, 0xDAD45E),
    "dog": (0x597DCE, 0x30346D, 0xD04648),
    "squirrel": (0x6DAA2C, 0x346524, 0xDEEED6),
    "reindeer": (0xD27D2C, 0x854C30, 0x6DAA2C),
    "robot": (0x6DC2CA, 0x8595A1, 0xD04648),
}

TILE = 32  # px, in objects.bmp (shown at 2x)
OBJECTS = "objects.bmp"  # in the deployed art set (/art/rooms), next to the backdrops
CRITTERS = "critters.bmp"

# Sheet order: tile i of objects.bmp is NAMES[i].
NAMES = (
    'ball of yarn',
    'squeaky ball',
    'walnuts',
    'carrot',
    'oil can',
    'batteries',
    'snowman',
    'potted plant',
    'snowy bush',
    'cardboard box',
    'leaf pile',
    'chimney',
    'present',
    'present open',
    'lid',
    'present tipped',
)

# Where each episode's critter hides (episodes.Episode.hide_room -> art).
HIDING_SPOTS = {
    "Sun Porch": "potted plant",
    "Yard": "snowy bush",
    "Basement": "cardboard box",
    "Tree House": "leaf pile",
    "Roof": "chimney",
}
