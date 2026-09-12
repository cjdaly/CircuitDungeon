# SPDX-License-Identifier: MIT
"""On-device tryout of rooms.py -- cd-45v.4 prototype.

Not main.py: run this standalone (rename to main.py or `import
room_nav_demo` from a scratch main.py) to try the navigation feel without
disturbing the Ch8 diagnostic HUD in main.py.

A tap or swipe starting near a screen edge attempts a move in that edge's
direction (edge_gesture.py, cd-45v.2) -- swipe direction itself doesn't
matter, only where the gesture started. The room name + live exits show as
a toast banner (room_banner.py, cd-45v.3) on entry and auto-hide; a blocked
attempt flashes "can't go <direction>" in the same banner.

STATUS: UNTESTED ON DEVICE as of 2026-09-12 -- written and desk-checked
against hardware.py/touch.py/edge_gesture.py/room_banner.py's APIs, not yet
run on the board.
"""
import time

import displayio

import edge_gesture
import hardware
import rooms
from room_banner import RoomBanner

_BG_COLOR = 0x101018
_BLOCKED_COLOR = 0xE04040

_BANNER_Y = 60  # inset from the top -- see doc/HARDWARE.md "Display" (round bezel)


def _make_group(display):
    group = displayio.Group()
    display.root_group = group

    bg_bitmap = displayio.Bitmap(hardware.WIDTH, hardware.HEIGHT, 1)
    bg_palette = displayio.Palette(1)
    bg_palette[0] = _BG_COLOR
    group.append(displayio.TileGrid(bg_bitmap, pixel_shader=bg_palette))
    return group


def main():
    display = hardware.init_display()
    i2c = hardware.init_i2c()
    touch = hardware.init_touch(i2c)
    tracker = edge_gesture.EdgeGestureTracker(hardware.WIDTH, hardware.HEIGHT)

    world = rooms.make_demo_world()

    group = _make_group(display)
    banner = RoomBanner(group, hardware.WIDTH, y=_BANNER_Y)

    def announce_room(now):
        exits = ", ".join(world.live_exits()) or "none"
        banner.show("{}  (exits: {})".format(world.room.name, exits), now)

    start_now = time.monotonic()
    announce_room(start_now)
    print("Ch8 room-nav demo ready -- start: {}".format(world.current))

    while True:
        now = time.monotonic()
        point = touch.poll(now)
        direction = tracker.update(point, now)

        if direction is not None:
            if world.move(direction):
                announce_room(now)
                print("moved {} -> {}".format(direction, world.current))
            else:
                banner.show("can't go {}".format(direction), now, color=_BLOCKED_COLOR)

        banner.update(now)
        time.sleep(0.05)


main()
