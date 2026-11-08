# SPDX-License-Identifier: MIT
"""Look-test for the comic overlay kit -- cd-342.9.

Cycles through every element by itself, first on the game's dark background, then
on a brighter one standing in for room art, where the black ink shows up. Tap to
skip ahead. Run it with:  tools/deploy.sh --demo overlay_demo
"""
import comic_shapes
from beats import Beat

_DARK = 0x101018
_ART_STAND_IN = 0x597DCE

_YARN = (
    "................",
    ".....######.....",
    "...##rrrrrr##...",
    "..#rrwwrrrrrr#..",
    ".#rrwrrwwrrrrr#.",
    ".#rwrrrrrwwrrr#.",
    "#rrwrrwwrrrwrrr#",
    "#rwrrwrrwrrrwrr#",
    "#rwrwrrrrwrrwrr#",
    "#rrwrrrwwrrwrrr#",
    ".#rrrwwrrrwrrr#.",
    ".#rrrrrrwwrrrr#.",
    "..#rrrrrrrrrr#..",
    "...##rrrrrr##...",
    ".....######.....",
    "................",
)


def beats(yarn_icon):
    """Every element once, with the same text budget the game has."""
    names = list(comic_shapes.EMANATA)
    glyph_rows = []
    for i in range(0, len(names), 4):
        row = names[i:i + 4]
        glyph_rows.append(tuple(
            (name, 40 + (column % 2) * 128 - 8, 56 + (column // 2) * 96)
            for column, name in enumerate(row)
        ))
    return [
        Beat(caption="Chirpy escaped!"),
        Beat(caption="Chirpy loves\nfresh air!"),
        Beat(speech="Meow! I like\nit out here", tail=(120, 200)),
        Beat(speech="You found me!", tail=(120, 40)),
        Beat(thought=yarn_icon),
        Beat(burst="Rattle!", duration=1.5),
        Beat(burst="Pop!", duration=1.5),
        Beat(burst="Bonk!", shake=True, duration=1.5),
    ] + [Beat(emanata=row) for row in glyph_rows]


def main():
    import displayio
    import time

    import comic
    import comic_fonts
    import hardware
    from beats import BeatPlayer
    from room_banner import RoomLabel
    from touch import GestureTracker

    display, _backlight = hardware.init_display()
    hardware.reset_touch()
    touch = hardware.init_touch(hardware.init_i2c())

    root = displayio.Group()
    background = displayio.Palette(1)
    background[0] = _DARK
    root.append(displayio.TileGrid(
        displayio.Bitmap(hardware.WIDTH, hardware.HEIGHT, 1), pixel_shader=background,
    ))
    scene = displayio.Group()
    root.append(scene)
    RoomLabel(scene, hardware.WIDTH, comic_fonts.title(), y=45).show(
        "Living Room"
    )
    stage = comic.Stage(hardware.WIDTH, hardware.HEIGHT, shake_target=scene)
    root.append(stage.group)
    display.root_group = root

    yarn = displayio.Bitmap(16, 16, len(comic_shapes.COLORS))
    comic.draw_rows(yarn, _YARN)
    palette = displayio.Palette(len(comic_shapes.COLORS))
    for i, color in enumerate(comic_shapes.COLORS):
        palette[i] = color
    palette.make_transparent(0)

    player = BeatPlayer(stage)
    tracker = GestureTracker()
    bright = False
    print("overlay demo ready")
    while True:
        now = time.monotonic()
        if not player.active:
            background[0] = _ART_STAND_IN if bright else _DARK
            bright = not bright
            player.play(beats((yarn, palette, 0, 16)), now)  # one 16px tile
        if tracker.update(touch.poll(now), now):
            player.tap(now)
        player.update(now)
        stage.update(now)
        time.sleep(0.05)


if __name__ == "__main__":
    main()
