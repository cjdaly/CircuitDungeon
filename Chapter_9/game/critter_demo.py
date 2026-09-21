# SPDX-License-Identifier: MIT
"""On-device look-test for animated critter candidates -- cd-342.3.

Not main.py: deploy it as the device's main.py with
`Chapter_9/tools/deploy.sh --demo critter_demo`, or `import critter_demo`
from a scratch main.py. Browses the 39 candidates in critter_candidates.py
(2-frame DawnLike creatures expanded 16x16 -> 32x32 by
tools/build_critter_candidates.py) so the best ones can be picked on the
real round panel, at the real size they'd have in the game.

  swipe left / right   previous / next candidate
  swipe up / down      next / previous group (dog, cat, owl, ...)
  tap, top half        flip the 16->32 expansion: nn (pixel-doubling) <-> epx
                       (Scale2x edge smoothing)
  tap, bottom half     toggle WALK MODE

Still view: each candidate shown twice -- 3x zoomed for inspection, and at
true 32x32 straddling a dark/light backdrop split (does the outline read on
both dark floors and pale snow/wood?). Frames flip every FRAME_PERIOD s.

Walk mode: the critter patrols a rectangle over a floor (with a light rug in
the middle) at true size, using walk.py. Position slides at WALK_SPEED; the
two frames step at STEP_PERIOD with a BOB_PX hop; it idles at each corner.
The art is drawn facing left, so the sprite is mirrored (flip_x) when it
heads right -- if a critter looks like it's moonwalking, it's drawn facing
right and needs the opposite flip, so note which ones. Front-facing critters
(owls, bats, penguins, robots) just hop. The WALK_*/STEP_*/BOB_* constants
are the things worth feeling out; note what looks right.

The current pick is echoed to serial so a session's favorites can be copied out.

STATUS: still view confirmed on ws-1 2026-09-21. Walk mode UNTESTED ON DEVICE;
tests/test_critter_demo.py drives both views against stubbed displayio to
catch wiring bugs. Assumes TileGrid.flip_x works on a 1x1-tile grid over an
OnDiskBitmap (documented displayio behaviour).
"""
import time

import displayio
import terminalio
import vectorio
from adafruit_display_text.bitmap_label import Label

import critter_candidates as cc
import hardware
import walk
from touch import GestureTracker

FRAME_PERIOD = 0.5  # seconds per animation frame at rest (DawnLike is 2-frame)
_ZOOM = 3

# Walk-mode tuning -- the things worth feeling out on the device.
WALK_SPEED = 40.0  # px / second
STEP_PERIOD = 0.2  # seconds per animation frame while walking
BOB_PX = 2  # hop height per step
WALK_PAUSE = 0.6  # seconds idling at each waypoint
# Top-left positions of a 32x32 walker; the corners keep the sprite inside the
# round bezel (worst corner is ~104px from centre, glass radius is 120).
_WAYPOINTS = ((30, 96), (178, 96), (178, 140), (30, 140))

_BG = 0x101018
_BACKDROP_DARK = 0x2A2A38
_BACKDROP_LIGHT = 0xE8DCC0
_FLOOR = 0x3A2E28
_RUG = 0x9A3030
_TEXT = 0xC0C0C0
_TEXT_DIM = 0x707080

_BIG_SIZE = cc.TILE * _ZOOM  # 96
_BIG_X = (hardware.WIDTH - _BIG_SIZE) // 2
_BIG_Y = 48
_BACKDROP_Y = 152
_BACKDROP_W, _BACKDROP_H = 96, 40
_SMALL_X = (hardware.WIDTH - cc.TILE) // 2
_SMALL_Y = _BACKDROP_Y + (_BACKDROP_H - cc.TILE) // 2

_METHODS = ("nn", "epx")


def _load(method):
    """(bitmap, palette) for one expansion method, index 0 made transparent."""
    bmp = displayio.OnDiskBitmap("/art/critters_{}.bmp".format(method))
    pal = bmp.pixel_shader
    pal.make_transparent(0)
    return bmp, pal


def _actor(bmp, pal):
    return displayio.TileGrid(
        bmp, pixel_shader=pal, width=1, height=1,
        tile_width=cc.TILE, tile_height=cc.TILE,
    )


def _rect(group, x, y, w, h, color):
    palette = displayio.Palette(1)
    palette[0] = color
    group.append(vectorio.Rectangle(pixel_shader=palette, x=x, y=y, width=w, height=h))


def _label(group, y, color=_TEXT, scale=1):
    label = Label(
        terminalio.FONT, text="", color=color, scale=scale,
        anchor_point=(0.5, 0.5), anchored_position=(hardware.WIDTH // 2, y),
    )
    group.append(label)
    return label


def _group_starts():
    """Index of the first candidate of each group, in order."""
    starts, seen = [], None
    for i, (_id, group, _src) in enumerate(cc.CANDIDATES):
        if group != seen:
            starts.append(i)
            seen = group
    return starts


def main():
    display, _backlight = hardware.init_display()
    i2c = hardware.init_i2c()
    touch = hardware.init_touch(i2c)
    tracker = GestureTracker()

    root = displayio.Group()
    display.root_group = root
    bg = displayio.Bitmap(hardware.WIDTH, hardware.HEIGHT, 1)
    bg_pal = displayio.Palette(1)
    bg_pal[0] = _BG
    root.append(displayio.TileGrid(bg, pixel_shader=bg_pal))

    still_view = displayio.Group()  # zoomed + true-size on a dark/light split
    walk_view = displayio.Group()  # patrolling walker over a floor + rug
    root.append(still_view)
    root.append(walk_view)

    half = _BACKDROP_W // 2
    bx = (hardware.WIDTH - _BACKDROP_W) // 2
    _rect(still_view, bx, _BACKDROP_Y, half, _BACKDROP_H, _BACKDROP_DARK)
    _rect(still_view, bx + half, _BACKDROP_Y, half, _BACKDROP_H, _BACKDROP_LIGHT)

    _rect(walk_view, 10, 88, 220, 96, _FLOOR)
    _rect(walk_view, 88, 108, 64, 56, _RUG)

    bigs, smalls, walkers = {}, {}, {}
    for method in _METHODS:
        bmp, pal = _load(method)
        big_group = displayio.Group(scale=_ZOOM, x=_BIG_X, y=_BIG_Y)
        bigs[method] = _actor(bmp, pal)
        big_group.append(bigs[method])
        still_view.append(big_group)
        smalls[method] = _actor(bmp, pal)
        smalls[method].x, smalls[method].y = _SMALL_X, _SMALL_Y
        still_view.append(smalls[method])
        walkers[method] = _actor(bmp, pal)  # shares this method's bitmap/palette
        walk_view.append(walkers[method])

    l_id = _label(root, 26, _TEXT)
    l_src = _label(root, 38, _TEXT_DIM)
    _label(root, 196, _TEXT_DIM).text = "< > pick   ^ v group"
    _label(root, 208, _TEXT_DIM).text = "tap top: nn / epx"
    _label(root, 220, _TEXT_DIM).text = "tap bottom: walk"

    starts = _group_starts()
    count = len(cc.CANDIDATES)
    idx = 0
    method = "nn"
    frame = 0
    walking = False
    patrol = walk.Patrol(_WAYPOINTS, speed=WALK_SPEED, pause=WALK_PAUSE)
    moving = False
    last_point = None  # last live touch, so a tap knows top vs bottom half

    def show_frame():
        # Cheap: just tile indices -- runs every animation flip.
        for m in _METHODS:
            bigs[m][0, 0] = smalls[m][0, 0] = walkers[m][0, 0] = 2 * idx + frame

    def refresh():
        # Text + which method/view is visible -- only when a gesture changed
        # something (relabeling every flip would churn bitmap_label's heap).
        cid, group, src = cc.CANDIDATES[idx]
        l_id.text = "{}/{} {}".format(idx + 1, count, group)
        l_src.text = "{}  [{}]{}".format(src, method, " walk" if walking else "")
        still_view.hidden = walking
        walk_view.hidden = not walking
        for m in _METHODS:
            bigs[m].hidden = smalls[m].hidden = walkers[m].hidden = m != method
        show_frame()
        return cid

    print("critter_demo: {} candidates".format(count))
    print("showing", refresh())
    next_frame = time.monotonic() + FRAME_PERIOD

    while True:
        now = time.monotonic()
        changed = False

        point = touch.poll(now)
        if point is not None:
            last_point = point
        gesture = tracker.update(point, now)
        if gesture == "swipe_left":
            idx, changed = (idx + 1) % count, True
        elif gesture == "swipe_right":
            idx, changed = (idx - 1) % count, True
        elif gesture in ("swipe_up", "swipe_down"):
            step = 1 if gesture == "swipe_up" else -1
            # Jump to the start of the next/previous group.
            here = max(i for i, s in enumerate(starts) if s <= idx)
            idx, changed = starts[(here + step) % len(starts)], True
        elif gesture == "tap":
            if last_point is not None and last_point[1] >= hardware.HEIGHT // 2:
                walking = not walking
            else:
                method = _METHODS[(_METHODS.index(method) + 1) % len(_METHODS)]
            changed = True

        if changed:
            print("showing", refresh(), method, "walk" if walking else "still")

        if walking:
            x, y, moving, facing_right = patrol.update(now)
            w = walkers[method]
            w.x = x
            w.y = y - (walk.bob(now, STEP_PERIOD, BOB_PX) if moving else 0)
            # Art faces left: mirror it when heading right.
            w.flip_x = facing_right

        if now >= next_frame:
            frame ^= 1
            next_frame = now + (STEP_PERIOD if walking and moving else FRAME_PERIOD)
            show_frame()

        time.sleep(0.05)


main()
