# SPDX-License-Identifier: MIT
"""On-device tryout of rooms.py -- cd-45v.4 prototype.

Not main.py: run this standalone (rename to main.py or `import
room_nav_demo` from a scratch main.py) to try the navigation feel without
disturbing the Ch8 diagnostic HUD in main.py.

A tap or swipe starting near a screen edge attempts a move in that edge's
direction (edge_gesture.py, cd-45v.2) -- swipe direction itself doesn't
matter, only where the gesture started.

Visual design (testing aid, not necessarily the eventual Ch9 UI): the
current room's name sits persistently in the center (no toast/auto-hide --
"where am I" should never require having caught a message before it
vanished). A small circle at the midpoint of each edge's margin band shows,
live, whether that direction is a real exit right now: pulsing green if so,
dim/static if not. Touching a zone snaps its dot to gold (a live exit) or
red (blocked) immediately, on every frame -- not just once a gesture
completes -- so the margin feel and the room graph can both be judged by
eye. room_banner.py (cd-45v.3) is reused only for the transient "can't go
<direction>" flash on a blocked attempt, named-direction confirmation on
top of the red dot.

STATUS: on-device testing in progress, 2026-09-13 -- desk-checked against
hardware.py/touch.py/edge_gesture.py/room_banner.py's APIs; navigation feel
still being tried on the board.
"""
import math
import time

import displayio
import terminalio
import vectorio
from adafruit_display_text.bitmap_label import Label

import edge_gesture
import hardware
import rooms
from room_banner import RoomBanner

_BG_COLOR = 0x101018
_BLOCKED_FLASH_COLOR = 0xE04040

_ROOM_NAME_COLOR = 0xFFFFFF
_ROOM_NAME_Y = 100  # center-ish; clear of the edge markers' row/column

_BANNER_Y = 172  # "can't go <direction>" flash -- below the room name, above
                 # the DOWN marker

_MARKER_RADIUS = 9
_AVAILABLE_DIM = 0x1A4028
_AVAILABLE_BRIGHT = 0x40FF80
_BLOCKED_IDLE = 0x2A1A1A  # static, not pulsing -- reads as "don't bother"
_ACTIVE_GO_COLOR = 0xFFD040  # gold -- touching a zone that IS a live exit
_ACTIVE_BLOCKED_COLOR = 0xFF4040  # red -- touching a zone that is NOT
_PULSE_PERIOD = 1.4  # seconds per idle pulse cycle, available zones only

# Marker positions sit at each edge's margin-band midpoint -- literally where
# a gesture needs to start, matching edge_gesture.EDGE_MARGIN.
_MARGIN_MID = edge_gesture.EDGE_MARGIN // 2


def _edge_positions(width, height):
    return {
        rooms.UP: (width // 2, _MARGIN_MID),
        rooms.DOWN: (width // 2, height - _MARGIN_MID),
        rooms.LEFT: (_MARGIN_MID, height // 2),
        rooms.RIGHT: (width - _MARGIN_MID, height // 2),
    }


def _blend(color_a, color_b, t):
    """Linear-interpolate two 0xRRGGBB colors; t=0 -> a, t=1 -> b."""
    ar, ag, ab = (color_a >> 16) & 0xFF, (color_a >> 8) & 0xFF, color_a & 0xFF
    br, bg, bb = (color_b >> 16) & 0xFF, (color_b >> 8) & 0xFF, color_b & 0xFF
    r = int(ar + (br - ar) * t)
    g = int(ag + (bg - ag) * t)
    b = int(ab + (bb - ab) * t)
    return (r << 16) | (g << 8) | b


def _make_group(display):
    group = displayio.Group()
    display.root_group = group

    bg_bitmap = displayio.Bitmap(hardware.WIDTH, hardware.HEIGHT, 1)
    bg_palette = displayio.Palette(1)
    bg_palette[0] = _BG_COLOR
    group.append(displayio.TileGrid(bg_bitmap, pixel_shader=bg_palette))
    return group


def _make_edge_markers(group, width, height):
    """One circle per direction at its edge-margin midpoint."""
    markers = {}
    for direction, (x, y) in _edge_positions(width, height).items():
        palette = displayio.Palette(1)
        palette[0] = _BLOCKED_IDLE
        group.append(
            vectorio.Circle(pixel_shader=palette, x=x, y=y, radius=_MARKER_RADIUS)
        )
        markers[direction] = palette
    return markers


def _update_markers(markers, now, active_zone, live_exits):
    phase = (now % _PULSE_PERIOD) / _PULSE_PERIOD
    pulse = 0.5 + 0.5 * math.sin(2 * math.pi * phase)
    available_idle = _blend(_AVAILABLE_DIM, _AVAILABLE_BRIGHT, pulse)
    for direction, palette in markers.items():
        available = direction in live_exits
        if direction == active_zone:
            palette[0] = _ACTIVE_GO_COLOR if available else _ACTIVE_BLOCKED_COLOR
        elif available:
            palette[0] = available_idle
        else:
            palette[0] = _BLOCKED_IDLE


def main():
    display = hardware.init_display()
    i2c = hardware.init_i2c()
    touch = hardware.init_touch(i2c)
    tracker = edge_gesture.EdgeGestureTracker(hardware.WIDTH, hardware.HEIGHT)

    world = rooms.make_demo_world()

    group = _make_group(display)
    markers = _make_edge_markers(group, hardware.WIDTH, hardware.HEIGHT)
    l_room = Label(
        terminalio.FONT,
        text="",
        color=_ROOM_NAME_COLOR,
        scale=2,
        anchor_point=(0.5, 0.5),
        anchored_position=(hardware.WIDTH // 2, _ROOM_NAME_Y),
    )
    group.append(l_room)
    banner = RoomBanner(group, hardware.WIDTH, y=_BANNER_Y)

    live_exits = set()

    def enter_room():
        nonlocal live_exits
        l_room.text = world.room.name
        live_exits = set(world.live_exits())

    enter_room()
    print("Ch8 room-nav demo ready -- start: {}".format(world.current))

    while True:
        now = time.monotonic()
        point = touch.poll(now)
        active_zone = (
            edge_gesture.edge_of(point[0], point[1], hardware.WIDTH, hardware.HEIGHT)
            if point is not None
            else None
        )
        _update_markers(markers, now, active_zone, live_exits)

        direction = tracker.update(point, now)
        if direction is not None:
            if world.move(direction):
                enter_room()
                print("moved {} -> {}".format(direction, world.current))
            else:
                banner.show(
                    "can't go {}".format(direction), now, color=_BLOCKED_FLASH_COLOR
                )

        banner.update(now)
        time.sleep(0.05)


main()
