# Chapter 8 — Scripted serial diagnostics

How to check what a board is doing over USB serial without a human
sitting at `screen`/a terminal — useful for an agent (or a quick script)
confirming a deploy actually ran, or capturing a crash traceback. `doc/
HARDWARE.md`'s intro mentions this board was originally probed via
"raw-REPL scripting" — this doc is that write-up, and the tool to go with
it.

## The tool

```
Chapter_8/tools/serial_check.py              # passive read, 3s
Chapter_8/tools/serial_check.py --reboot     # one soft-reboot + capture, 8s
```

Auto-detects `/dev/cu.usbmodem*` (pass `--port` if more than one board is
plugged in). Prints the raw output; flags a detected traceback or the
I2C-wedge `RuntimeError` (see below) to stderr.

**Passive mode is always safe.** It only reads — never writes to the port —
so it cannot trigger a reset or contribute to the I2C-wedge quirk. The
terminal-title escape sequence CircuitPython emits (visible in the raw
output, e.g. `]0;🐍main.py | 10.2.1\`) tells you what's currently running:
`main.py` (or a demo's filename) means it's alive and looping; `Done` means
the code already finished or crashed and it's sitting at the REPL.

**`--reboot` actually restarts the running code** — the only way to see a
*fresh* traceback, since a crash's traceback prints once, at the moment it
happens; if nothing was listening then, it's gone. It sends exactly one
Ctrl-D (`0x04`, CircuitPython's soft-reboot key) and stops. It does not
loop or retry.

## The one rule: don't reset repeatedly

Multiple quick resets back-to-back is the documented trigger for wedging
this board's shared I2C bus (`doc/HARDWARE.md` "Touch controller" / "Power
/ battery"): the next I2C use (`hardware.init_i2c()`, or any touch/IMU
call) raises `RuntimeError: No pull up found on SDA or SCL`.
`microcontroller.reset()` — and a serial soft-reboot has the same effect on
the bus — does **not** clear it once wedged. Only a **real USB
unplug/replug** does.

So: run `--reboot` at most once, look at the result, and if it shows that
`RuntimeError`, stop and unplug/replug rather than trying again over
serial. This was learned the hard way (2026-09-13) sending several
`--reboot`-equivalent soft-reboots back-to-back while iterating on a demo —
wedged the bus, cost a debugging detour to realize a totally unrelated
`ScreenBlanker` change wasn't actually the problem.

**On a battery-equipped unit, USB unplug/replug alone may not clear it** —
confirmed the same day: the battery keeps the board powered straight
through a USB disconnect, so nothing actually resets. Disconnect the
battery's MX1.25 connector too for a real power cycle. See `doc/
HARDWARE.md` "Power / battery".

## Implementation note (if hand-rolling instead of using the script)

A plain loop works reliably:

```python
import os, select, time
fd = os.open(port, os.O_RDWR | os.O_NOCTTY)
os.write(fd, b"\x04")  # omit this line for passive-only reading
end = time.time() + 8
buf = b""
while time.time() < end:
    r, _, _ = select.select([fd], [], [], 0.3)
    if r:
        buf += os.read(fd, 4096)
os.close(fd)
```

Putting the fd into raw mode first (`tty.setraw(fd)` / `termios`) was tried
and reproducibly returned nothing at all — unexplained, but don't do it.
`pyserial` isn't installed in this environment either; the plain
`os.open`/`select`/`os.read` approach above needs nothing beyond the
standard library.
