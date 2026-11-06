#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Render game screens to PNG on the desktop, for art review -- cd-342.25.

    /usr/bin/python3 Chapter_9/tools/preview.py [OUT_DIR] [--only NAME]

Builds the game's real NavView (fake_display.py stands in for displayio and
draws for real), walks it through a list of moments, and writes each as a PNG
at 2x, plus contact.png with them all side by side. The default OUT_DIR is
Chapter_9/preview/ (gitignored). Needs Pillow.

Scenes are set up through the same calls app.py makes, so what you see is what
the game would draw -- give or take a pixel on label placement.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fake_display  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_OUT = os.path.normpath(os.path.join(HERE, "..", "preview"))
ZOOM = 2


ORDER = ["cat", "dog", "robot", "squirrel", "reindeer"]


def _game(first):
    """A fresh world, roster and hunt, the way app.run() builds them."""
    import critters
    import hunt as hunt_mod
    import rooms

    world = rooms.make_world()
    roster = critters.make_roster(choice=lambda options: options[0])
    order = [first] + [species for species in ORDER if species != first]
    hunt = hunt_mod.Hunt(world, roster, order=order)
    return world, hunt


class Session:
    """Drives a NavView like app.py does, without touch or timing."""

    def __init__(self, first="cat"):
        import nav_view

        self.world, self.hunt = _game(first)
        self.nav = nav_view.NavView(240, 240)
        self.now = 0.0
        self.hunt.start()
        self._refresh()

    def _refresh(self, messages=(), event=None):
        self.nav.show_room(self.world.room.name, self.world.live_exits())
        self.nav.show_scene(self.hunt.scene(), self.now)
        want = self.hunt.critter.preferred_item if self.hunt.critter else None
        self.nav.say(list(messages), self.now, event, want)

    def jump(self, room):
        """Teleport, for a quick look at a room (the gate still applies to moves)."""
        self.world.current = room
        self.hunt.entered()
        self._refresh()
        return self

    def go(self, *directions):
        for direction in directions:
            if not self.world.move(direction):
                raise ValueError("can't go {} from {}".format(direction, self.world.current))
            self.hunt.entered()
        self._refresh()
        return self

    def tap(self, show_messages=False):
        messages = self.hunt.tapped()
        if show_messages:
            self._refresh(messages, self.hunt.event)
        else:
            self._refresh()
        return messages

    def at(self, seconds, zone=None):
        """Let time pass (animations), then render."""
        self.now += seconds
        self.nav.update(self.now, zone)
        return fake_display.render(self.nav.group)


def scenes():
    """(name, image) for every moment worth looking at."""
    from rooms import DOWN, LEFT, RIGHT, UP

    s = Session()
    yield "01_home_start", s.at(0.1)
    s.go(RIGHT, RIGHT, RIGHT)
    yield "02_cat_hiding", s.at(0.1)
    yield "03_cat_hiding_peek", s.at(0.45)
    s.tap()
    yield "04_cat_found", s.at(0.1)
    s.go(LEFT, LEFT, UP)
    yield "05_yarn", s.at(0.1)
    s.tap()
    yield "06_holding_yarn", s.at(0.1)
    s.go(DOWN, RIGHT, RIGHT)
    s.tap()
    yield "07_cat_follows", s.at(0.1)
    s.go(LEFT)
    yield "08_following_in_kitchen", s.at(0.3)

    s = Session()
    s.go(RIGHT, RIGHT, RIGHT)
    s.tap(show_messages=True)
    s.at(0.1)  # the FOUND! burst
    yield "09_found_burst", s.at(0.1)
    yield "10_found_thought", s.at(1.0)

    # Every other episode's hiding spot (at the top of a peek) and lure.
    for species in ORDER[1:]:
        s = Session(species)
        episode = s.hunt.episode
        s.jump(episode.hide_room)
        yield "{}_hiding".format(species), s.at(1.2)
        s.tap()
        yield "{}_found".format(species), s.at(0.1)
        s.hunt._found = False  # back to "not found yet", to see the locked lure
        s.hunt._locked = episode.unlock is not None
        if not (episode.unlock and episode.unlock.blocked_exit):
            s.jump(episode.lure_room)
            yield "{}_lure_locked".format(species), s.at(0.1)
        s.hunt._locked = False
        s.jump(episode.lure_room)
        yield "{}_lure".format(species), s.at(0.1)
    s.jump("Odd Corner")
    yield "odd_corner", s.at(0.1)


def main(argv):
    out = DEFAULT_OUT
    only = None
    args = list(argv)
    if "--only" in args:
        i = args.index("--only")
        only = args[i + 1]
        del args[i:i + 2]
    if args:
        out = os.path.abspath(args[0])
    fake_display.install()
    os.makedirs(out, exist_ok=True)
    from PIL import Image, ImageDraw

    shots = [(name, image) for name, image in scenes() if only is None or only in name]
    for name, image in shots:
        image.resize((240 * ZOOM, 240 * ZOOM), Image.NEAREST).save(os.path.join(out, name + ".png"))
    columns = 4
    rows = (len(shots) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * 250, rows * 266), (24, 24, 28))
    draw = ImageDraw.Draw(sheet)
    for i, (name, image) in enumerate(shots):
        x, y = (i % columns) * 250 + 5, (i // columns) * 266 + 5
        sheet.paste(image, (x, y))
        draw.text((x, y + 243), name, fill=(200, 200, 200))
    sheet.save(os.path.join(out, "contact.png"))
    print("wrote {} screens to {}".format(len(shots), out))


if __name__ == "__main__":
    main(sys.argv[1:])
