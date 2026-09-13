#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Write/update a per-device DEVICE_ID in a CIRCUITPY drive's settings.toml
-- cd-89o.11.

Each PicoSystem unit needs a persistent DEVICE_ID (ps-1, ps-2, ...), set
once when a device is set up. settings.toml is CircuitPython's own config
file, read on-device with os.getenv() -- see doc/DEPLOY.md. deploy.sh never
touches it (it's excluded from the rsync --delete), so it survives every
later code deploy untouched.

Ported from Chapter_8/game/tools/set_device_config.py (cd-bp3.7) --
same read-modify-write approach, trimmed to just DEVICE_ID since the
PicoSystem's battery is a sealed, non-user-selected part (unlike Ch8's
Waveshare units, which each get a separately-sourced/wired battery worth
tracking), so there's no analogous BATTERY_PRODUCT/BATTERY_MAH concept
here.

This script only ever touches the DEVICE_ID line -- any other lines
already in settings.toml (comments, unrelated keys) are left exactly as
they are.

Usage:
    tools/set_device_config.py --id ps-1
    tools/set_device_config.py --id ps-2 [/Volumes/CIRCUITPY]
    tools/set_device_config.py --show [/Volumes/CIRCUITPY]
"""
import argparse
import re
import sys
from pathlib import Path

_KEY = "DEVICE_ID"


def _key_pattern():
    return re.compile(r"^\s*{}\s*=".format(re.escape(_KEY)))


def _parse(lines):
    """Return (line_index, value) for DEVICE_ID if found in lines, else None."""
    for i, line in enumerate(lines):
        if _key_pattern().match(line):
            return i, line.split("=", 1)[1].strip().strip('"')
    return None


def _format(value):
    return '{} = "{}"\n'.format(_KEY, value)


def update(path, device_id):
    """Read-modify-write settings.toml at `path`, setting only DEVICE_ID."""
    lines = path.read_text().splitlines(keepends=True) if path.exists() else []
    found = _parse(lines)

    if found is not None:
        lines[found[0]] = _format(device_id)
    else:
        if lines and not lines[-1].endswith("\n"):
            lines[-1] += "\n"
        lines.append(_format(device_id))

    path.write_text("".join(lines))


def show(path):
    if not path.exists():
        print("{}: no settings.toml".format(path))
        return
    found = _parse(path.read_text().splitlines(keepends=True))
    if found is None:
        print("{}: settings.toml has no {}".format(path, _KEY))
        return
    print("{} = {}".format(_KEY, found[1]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--id", dest="device_id", help="DEVICE_ID, e.g. ps-1")
    parser.add_argument("--show", action="store_true", help="print current config, don't write")
    parser.add_argument(
        "target", nargs="?", default="/Volumes/CIRCUITPY",
        help="mounted CIRCUITPY path (default: /Volumes/CIRCUITPY)",
    )
    args = parser.parse_args()

    target = Path(args.target)
    if not target.is_dir():
        print("set_device_config: target not found: {}".format(target), file=sys.stderr)
        sys.exit(1)
    if not (target / "boot_out.txt").exists():
        print(
            "set_device_config: {} has no boot_out.txt "
            "-- is that really a CircuitPython drive?".format(target),
            file=sys.stderr,
        )
        sys.exit(1)

    settings_path = target / "settings.toml"

    if args.show:
        show(settings_path)
        return

    if args.device_id is None:
        parser.error("nothing to do -- pass --id, or --show")

    update(settings_path, args.device_id)
    print("wrote {}:".format(settings_path))
    show(settings_path)


if __name__ == "__main__":
    main()
