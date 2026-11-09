# SPDX-License-Identifier: MIT
"""The title screen: CHRISTMAS CRITTERS, this playthrough's critters hopping
on their presents, until a tap starts the game -- cd-342.34.

It's the interactive screen until the first tap (app.py), so it blanks, goes
to deep idle and drops into the ornament scenes exactly like the game screen
does: no new way to stay lit on battery.

The backdrop is the art set's title.bmp (art_sets/README.md), shown in the
room screen's shared bitmap like the ornament scenes, so show() (re)loads it.
The presents and critters come from the same sprite sheets as the game
(SceneView.sheets()), each present in its own critter's colours: they're the
boxes under the tree the critters are about to escape from.
"""
import math

FILE = "title.bmp"

_SIGN_Y = (62, 94)  # the two title lines' centres
_SIGN_PAD_X, _SIGN_PAD_Y = 10, 6
_SIGN_BORDER = 3
_SIGN_FILL = 0xDAD45E  # DB16 yellow, the room captions' box
_INK = 0x140C1C
_RED = 0xD04648
_GREEN = 0x346524
_BOX_Y = 162  # presents' top
_BOX_X0, _BOX_STEP = 28, 36  # five 32px presents across
_ON_BOX = 26  # a critter's top sits this far above its box's top
_HOP_PX = 16
_HOP_S = 0.9  # one hop
_HOP_LAG = 0.18  # s between neighbours: a wave along the row
_FRAME_S = 0.25
_TAP_Y = 214
_BLINK_S = 0.6


def hop_height(i, now):
    """How high critter i is off its box (px) at `now`: a wave of hops."""
    return int(_HOP_PX * abs(math.sin(math.pi * (now - i * _HOP_LAG) / _HOP_S)))


class TitleView:
    """Owns `.group`. show() when it comes up; update(now) every frame."""

    def __init__(self, backdrop, sheets, cast, width=240, height=240):
        """`backdrop`: the shared backdrop.Backdrop. `sheets`: SceneView.sheets().
        `cast`: (species, sprite id) for each critter, in present order."""
        import displayio
        import vectorio
        from adafruit_display_text.bitmap_label import Label

        import comic_fonts
        import ornament
        from home_view import box_palette, first_frame

        self.group = displayio.Group()
        self._backdrop = backdrop
        bg = displayio.Palette(1)
        bg[0] = 0x101018
        self.group.append(vectorio.Rectangle(pixel_shader=bg, width=width, height=height,
                                             x=0, y=0))
        self._view = backdrop.view()
        self.group.append(self._view)
        self._snow = ornament.Snow(self.group, width, height)

        objects, objects_palette, critters, critter_palette, tile_of = sheets
        self._critters = []
        for i, (species, sprite) in enumerate(cast):
            x = _BOX_X0 + i * _BOX_STEP
            box = displayio.TileGrid(objects, pixel_shader=box_palette(objects_palette, species),
                                     width=1, height=1, tile_width=32, tile_height=32,
                                     default_tile=tile_of["present"], x=x, y=_BOX_Y)
            critter = displayio.TileGrid(critters, pixel_shader=critter_palette, width=1,
                                         height=1, tile_width=32, tile_height=32,
                                         default_tile=first_frame(sprite), x=x,
                                         y=_BOX_Y - _ON_BOX)
            self.group.append(critter)  # behind its box: it stands in it
            self.group.append(box)
            self._critters.append((critter, first_frame(sprite)))

        # The sign: two lines on a yellow comic caption box with an ink border.
        font = comic_fonts.title()
        lines = [Label(font, text=text, color=color, anchor_point=(0.5, 0.5),
                       anchored_position=(width // 2, y))
                 for text, color, y in (("CHRISTMAS", _RED, _SIGN_Y[0]),
                                        ("CRITTERS", _GREEN, _SIGN_Y[1]))]
        w = max(line.bounding_box[2] for line in lines) + 2 * _SIGN_PAD_X
        h = _SIGN_Y[1] - _SIGN_Y[0] + lines[0].bounding_box[3] + 2 * _SIGN_PAD_Y
        top = (_SIGN_Y[0] + _SIGN_Y[1]) // 2 - h // 2
        ink, fill = displayio.Palette(1), displayio.Palette(1)
        ink[0], fill[0] = _INK, _SIGN_FILL
        b = _SIGN_BORDER
        self.group.append(vectorio.Rectangle(pixel_shader=ink, width=w + 2 * b, height=h + 2 * b,
                                             x=width // 2 - w // 2 - b, y=top - b))
        self.group.append(vectorio.Rectangle(pixel_shader=fill, width=w, height=h,
                                             x=width // 2 - w // 2, y=top))
        for line in lines:
            self.group.append(line)
        self._tap = Label(comic_fonts.caption(), text="TAP TO START", color=_INK,
                          anchor_point=(0.5, 0.5), anchored_position=(width // 2, _TAP_Y))
        self.group.append(self._tap)

    def show(self):
        """Put the title art in the shared bitmap (after another screen used it)."""
        self._view.hidden = not self._backdrop.show_file(FILE)

    def update(self, now):
        for i, (critter, frame) in enumerate(self._critters):
            critter.y = _BOX_Y - _ON_BOX - hop_height(i, now)
            critter[0] = frame + int(now / _FRAME_S) % 2
        self._tap.hidden = int(now / _BLINK_S) % 2 == 1
        self._snow.update(now)
