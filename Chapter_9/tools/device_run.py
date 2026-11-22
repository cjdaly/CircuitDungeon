#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Run the real game on a board with scripted taps, and report what it printed
-- cd-342.47.5, doc/ARCHITECTURE.md sec 5.

    /usr/bin/python3 Chapter_9/tools/device_run.py SERIAL [--seconds 60]
        [--tap-every 43] [--depth 0]

SERIAL is the board's USB serial number (boot_out.txt's UID, or the list
this prints when it can't find it). The board is reset, stopped at the REPL,
and sent a small script over serial in paste mode -- not as a file on the
drive, because macOS caches writes to CIRCUITPY and the board can read a
half-written file. The script brings up the hardware itself (importing
main.py would start the game) and runs app.run with a touch wrapper that taps
the middle of the screen for 3 polls in every --tap-every, once 8 s have
passed: that skips the gift tag, starts the game past the title, and steps
through every caption of the escape cutscene.

--depth N runs the game under N extra nested calls, to measure how much of
the Python stack (pystack) is to spare: find the smallest N that fails.

--push FILE... sends game modules over serial first and loads them into the
board's memory in place of the ones on its flash, so a change can be tried
without the drive (when macOS won't mount it). The flash is untouched: the
reset at the end puts the board back on what's deployed. List the files in
import order (a module before the ones that import it).

Exit status 1 if the board printed a traceback. The board is reset again at
the end, so it goes back to running main.py.

Before each reset the board's drive (found by the UID in its boot_out.txt)
is unmounted: a reset with the drive still mounted is, to macOS, a USB stick
pulled out, and on 2026-11-22 a run of those left the Mac's disk service
(diskarbitrationd) stuck until a restart. If the unmount fails, nothing is
reset.
"""
import argparse
import glob
import os
import subprocess
import sys
import time

import serial
import serial.tools.list_ports

_SCRIPT = '''
import time
import app
import hardware
import imu as imu_gestures


class Tapper:
    def __init__(self, touch, every):
        self.touch = touch
        self.every = every
        self.t0 = time.monotonic()
        self.n = 0

    def poll(self, now):
        self.touch.poll(now)
        if now - self.t0 < 8:
            return None
        self.n += 1
        return (120, 120) if self.n % self.every < 3 else None

    def __getattr__(self, name):
        return getattr(self.touch, name)


display, backlight = hardware.init_display()
hardware.reset_touch()
hardware.clock_out_bus()
i2c = hardware.init_i2c()
imu = hardware.init_imu(i2c)
touch = Tapper(hardware.init_touch(i2c), {every})


def go():
    app.run(display, backlight, touch, imu_gestures.ImuGestures(imu), hardware.WIDTH,
            hardware.HEIGHT, max_ticks={ticks}, title={title})


def deeper(n):
    if n:
        deeper(n - 1)
    else:
        go()


deeper({depth})
print("DEVICE_RUN " + "DONE")
'''


def _port(serial_number):
    for port in serial.tools.list_ports.comports():
        if port.serial_number == serial_number:
            return port.device
    return None


def _unmount(serial_number):
    """Unmount the board's drive, if macOS has it mounted."""
    for volume in glob.glob("/Volumes/CIRCUITPY*"):
        try:
            with open(os.path.join(volume, "boot_out.txt")) as f:
                if "UID:" + serial_number not in f.read():
                    continue
        except OSError:
            continue  # not mounted (a leftover folder), or not readable
        try:
            done = subprocess.run(["diskutil", "unmount", volume], capture_output=True,
                                  text=True, timeout=20)
        except subprocess.TimeoutExpired:
            raise SystemExit("diskutil unmount {} hung: the Mac's disk service is stuck, "
                             "so the board is left alone (doc/ARCHITECTURE.md sec 5)"
                             .format(volume))
        if done.returncode != 0:
            raise SystemExit("couldn't unmount {}: {}".format(volume, done.stderr.strip()))


def _reset(conn, serial_number):
    _unmount(serial_number)
    conn.write(b"\x03\x03")
    time.sleep(1.0)
    conn.write(b"\r\nimport microcontroller; microcontroller.reset()\r\n")
    time.sleep(0.3)
    try:
        conn.close()
    except (OSError, serial.SerialException):
        pass


def _reopen(serial_number, wait=20.0):
    end = time.time() + wait
    while time.time() < end:
        device = _port(serial_number)
        if device:
            try:
                return serial.Serial(device, 115200, timeout=0.3)
            except serial.SerialException:
                pass
        time.sleep(0.5)
    raise SystemExit("board {} didn't come back after a reset".format(serial_number))


def _raw_exec(conn, code, wait, echo=False):
    """Run `code` in the raw REPL (it must be in raw mode); returns (stdout,
    stderr). With `echo`, prints stdout as it comes."""
    data = code.encode()
    for i in range(0, len(data), 256):
        conn.write(data[i:i + 256])
        time.sleep(0.01)
    conn.write(b"\x04")
    reply = b""
    end = time.time() + 10
    while not reply.endswith(b"OK") and time.time() < end:
        reply += conn.read(1)
    if not reply.endswith(b"OK"):
        raise SystemExit("raw REPL didn't take the code: {!r}".format(reply[-200:]))
    out = b""
    end = time.time() + wait
    while out.count(b"\x04") < 2 and time.time() < end:
        chunk = conn.read(4000)
        if echo and chunk:
            text = chunk.split(b"\x04")[0] if b"\x04" not in out else b""
            for line in text.decode(errors="replace").splitlines(True):
                if " ticks=" not in line:
                    sys.stdout.write(line)
            sys.stdout.flush()
        out += chunk
    stdout, _, rest = out.partition(b"\x04")
    stderr = rest.partition(b"\x04")[0]
    return stdout.decode(errors="replace"), stderr.decode(errors="replace")


def _push(conn, path):
    """Load one module's source into sys.modules, under its file's name."""
    import os

    name = os.path.splitext(os.path.basename(path))[0]
    with open(path) as f:
        source = f.read()
    # CircuitPython can't make module objects from Python, but import takes
    # whatever sys.modules holds: run the source in a dict, then hand import
    # an object carrying its names. (Fine for these modules: nothing outside
    # one reads a module-level variable that it later reassigns.)
    code = ("import sys, gc\ng = {{'__name__': {n!r}, '__file__': {f!r}}}\n"
            "exec(compile({s!r}, {f!r}, 'exec'), g)\n"
            "class Pushed:\n    pass\n"
            "m = Pushed()\nfor k in g:\n    setattr(m, k, g[k])\n"
            "sys.modules[{n!r}] = m\ndel g, m, k\ngc.collect()\n"
            "print('pushed', {n!r})\n").format(n=name, f=name + ".py", s=source)
    stdout, stderr = _raw_exec(conn, code, 60)
    if stderr.strip():
        raise SystemExit("push {} failed:\n{}".format(path, stderr))
    print(stdout.strip())


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("serial_number")
    parser.add_argument("--seconds", type=float, default=60.0)
    parser.add_argument("--tap-every", type=int, default=43, help="polls between taps")
    parser.add_argument("--depth", type=int, default=0, help="extra nested calls")
    parser.add_argument("--no-title", action="store_true",
                        help="straight into the game: no gift tag or title (to measure the "
                             "game's own stack headroom when start-up runs out first)")
    parser.add_argument("--push", nargs="+", default=[], metavar="FILE",
                        help="game modules to load over serial first, in import order")
    args = parser.parse_args()

    device = None
    end = time.time() + 20  # it may still be coming back from a reset
    while device is None and time.time() < end:
        device = _port(args.serial_number)
        if device is None:
            time.sleep(0.5)
    if device is None:
        boards = [(p.serial_number, p.device) for p in serial.tools.list_ports.comports()
                  if p.serial_number]
        raise SystemExit("no board {}; plugged in: {}".format(args.serial_number, boards))

    _reset(serial.Serial(device, 115200, timeout=0.5), args.serial_number)
    time.sleep(10)  # the game starts again; stop it at the REPL
    conn = _reopen(args.serial_number)
    conn.write(b"\x03\x03")
    time.sleep(1.5)
    conn.write(b"\r\n")
    time.sleep(0.5)
    conn.read(20000)

    conn.write(b"\r\x01")  # raw REPL: code in, output back, no echo
    time.sleep(0.5)
    banner = conn.read(2000)
    if b"raw REPL" not in banner:
        raise SystemExit("no raw REPL: {!r}".format(banner[-200:]))
    for path in args.push:
        _push(conn, path)
    script = _SCRIPT.format(every=args.tap_every, depth=args.depth,
                            ticks=int(args.seconds / 0.05), title=not args.no_title)
    stdout, stderr = _raw_exec(conn, script, args.seconds * 2 + 30, echo=True)
    if stderr.strip():
        print(stderr)
    conn.write(b"\x02")  # back to the normal REPL
    text = stdout + stderr
    _reset(conn, args.serial_number)
    failed = "Traceback" in text
    print("device_run: {} (depth {})".format("TRACEBACK" if failed else "clean", args.depth))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
