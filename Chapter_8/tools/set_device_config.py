#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Write/update per-device identity + battery info in a CIRCUITPY drive's
settings.toml -- cd-bp3.7.

Each Waveshare RP2350-Touch-LCD-1.28 unit needs a persistent DEVICE_ID
(ws-1, ws-2, ws-monica, ...) and battery details (Adafruit product number +
mAh capacity), set once when a device is unboxed. settings.toml is
CircuitPython's own config file, read on-device with os.getenv() -- see
doc/DEPLOY.md. deploy.sh never touches it (it's excluded from the rsync
--delete), so it survives every later code deploy untouched.

This script only ever touches the three keys it knows about (DEVICE_ID,
BATTERY_PRODUCT, BATTERY_MAH), and only the ones given on the command line
-- any other lines already in settings.toml (comments, unrelated keys) are
left exactly as they are. Safe to re-run to update just one field, e.g.
swapping a battery without re-entering the device id.

Usage:
    tools/set_device_config.py --id ws-monica \\
        --battery-product adafruit-4236 --battery-mah 420
    tools/set_device_config.py --id ws-2 [/Volumes/CIRCUITPY]
    tools/set_device_config.py --show [/Volumes/CIRCUITPY]
"""
import argparse
import re
import sys
from pathlib import Path

_KEYS = ("DEVICE_ID", "BATTERY_PRODUCT", "BATTERY_MAH")


def _key_pattern(key):
    return re.compile(r"^\s*{}\s*=".format(re.escape(key)))


def _parse(lines):
    """Return {key: (line_index, value)} for recognized keys found in lines."""
    found = {}
    for i, line in enumerate(lines):
        for key in _KEYS:
            if _key_pattern(key).match(line):
                value = line.split("=", 1)[1].strip().strip('"')
                found[key] = (i, value)
    return found


def _format(key, value):
    return '{} = "{}"\n'.format(key, value)


def update(path, updates):
    """Read-modify-write settings.toml at `path`, changing only `updates`."""
    lines = path.read_text().splitlines(keepends=True) if path.exists() else []
    existing = _parse(lines)

    appended = []
    for key, value in updates.items():
        if key in existing:
            lines[existing[key][0]] = _format(key, value)
        else:
            appended.append(_format(key, value))

    if appended:
        if lines and not lines[-1].endswith("\n"):
            lines[-1] += "\n"
        lines.extend(appended)

    path.write_text("".join(lines))


def show(path):
    if not path.exists():
        print("{}: no settings.toml".format(path))
        return
    found = _parse(path.read_text().splitlines(keepends=True))
    if not found:
        print("{}: settings.toml has none of {}".format(path, ", ".join(_KEYS)))
        return
    for key in _KEYS:
        if key in found:
            print("{} = {}".format(key, found[key][1]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--id", dest="device_id", help="DEVICE_ID, e.g. ws-1 or ws-monica")
    parser.add_argument("--battery-product", help='e.g. "adafruit-4236"')
    parser.add_argument("--battery-mah", type=int, help="battery capacity in mAh")
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

    updates = {}
    if args.device_id is not None:
        updates["DEVICE_ID"] = args.device_id
    if args.battery_product is not None:
        updates["BATTERY_PRODUCT"] = args.battery_product
    if args.battery_mah is not None:
        updates["BATTERY_MAH"] = str(args.battery_mah)

    if not updates:
        parser.error("nothing to do -- pass --id/--battery-product/--battery-mah, or --show")

    update(settings_path, updates)
    print("wrote {}:".format(settings_path))
    show(settings_path)


if __name__ == "__main__":
    main()
