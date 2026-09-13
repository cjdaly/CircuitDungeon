#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Check a CircuitPython board's serial console without a human at a
terminal -- cd-bp3.10.

Two modes:

  serial_check.py              # passive: read whatever's flowing, 3s, exit
  serial_check.py --reboot     # send ONE Ctrl-D (soft reboot), capture the
                                # boot log + traceback (if any), 8s, exit

Passive mode is always safe -- it never writes to the port, so it can't
trigger a reset or contribute to the I2C-bus-wedge quirk below. Use it
first to check whether the board is already sitting at a `Done` (crashed)
REPL prompt vs. a live `main.py`/demo -- the terminal-title escape sequence
CircuitPython emits (visible in the raw output) says which.

--reboot actually restarts the running code, which is the only way to see a
FRESH traceback (a crash's traceback prints once, at the moment it happens
-- if nothing was listening then, it's gone). Deliberately does exactly one
Ctrl-D and stops; it does not loop, retry, or send anything else.

Do not call --reboot repeatedly in a tight loop. Multiple quick resets
back-to-back is the documented trigger for wedging this board's shared I2C
bus (doc/HARDWARE.md "Touch controller" / "Power / battery") --
`RuntimeError: No pull up found on SDA or SCL` at the next I2C use.
`microcontroller.reset()` (or this script's Ctrl-D, which is a soft-reboot,
not a hardware reset, but has the same effect on the bus) does NOT clear
it once wedged -- only a real USB unplug/replug does. If --reboot's output
shows that RuntimeError, stop and ask for a physical unplug/replug rather
than trying again over serial.

Implementation note: use a plain os.open()/select()/os.read() loop, as
below. Putting the fd into raw mode first (tty.setraw()) was tried and
reproducibly returned nothing at all -- unexplained, but don't do it.
"""
import argparse
import glob
import os
import select
import sys
import time

_SOFT_REBOOT = b"\x04"  # Ctrl-D


def find_port():
    matches = glob.glob("/dev/cu.usbmodem*")
    if len(matches) == 1:
        return matches[0]
    if not matches:
        sys.exit("serial_check: no /dev/cu.usbmodem* found -- board plugged in?")
    sys.exit(
        "serial_check: multiple ports found, pass one explicitly: {}".format(matches)
    )


def read_for(fd, seconds):
    end = time.time() + seconds
    buf = b""
    while time.time() < end:
        r, _, _ = select.select([fd], [], [], 0.3)
        if r:
            try:
                buf += os.read(fd, 4096)
            except OSError:
                break
    return buf


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", help="default: auto-detect /dev/cu.usbmodem*")
    parser.add_argument(
        "--reboot", action="store_true",
        help="send one Ctrl-D soft-reboot before capturing (see warnings above)",
    )
    args = parser.parse_args()

    port = args.port or find_port()
    seconds = 8 if args.reboot else 3
    flags = os.O_RDWR if args.reboot else os.O_RDONLY
    fd = os.open(port, flags | os.O_NOCTTY)
    try:
        if args.reboot:
            os.write(fd, _SOFT_REBOOT)
        output = read_for(fd, seconds)
    finally:
        os.close(fd)

    text = output.decode(errors="replace")
    print(text)
    if "Traceback (most recent call last)" in text:
        print("--- traceback detected above ---", file=sys.stderr)
    if "No pull up found on SDA or SCL" in text:
        print(
            "--- I2C bus wedged -- unplug/replug the board, do NOT reset again ---",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
