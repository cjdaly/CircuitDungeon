#!/usr/bin/env bash
# Copy Chapter_7/game/ onto a CircuitPython device (the PicoSystem).
# The CONTENTS of game/ go to the drive root — util.py loads tiles from /tiles/.
# See Chapter_7/doc/DEPLOY.md.
#
#   Chapter_7/tools/deploy.sh [CIRCUITPY_PATH]
#
# Default target: /Volumes/CIRCUITPY

set -euo pipefail

TARGET="${1:-/Volumes/CIRCUITPY}"
HERE="$(cd "$(dirname "$0")/.." && pwd)"   # Chapter_7/
SRC="$HERE/game"

if [ ! -d "$TARGET" ]; then
  echo "deploy: target not found: $TARGET" >&2
  echo "        mount the device, or pass the path: deploy.sh /Volumes/CIRCUITPY" >&2
  exit 1
fi
if [ ! -f "$TARGET/boot_out.txt" ]; then
  echo "deploy: $TARGET has no boot_out.txt — is that really a CircuitPython drive?" >&2
  exit 1
fi

echo "deploy: $SRC/  ->  $TARGET/"
# --delete removes stale game modules from a prior deploy, but the anchored
# excludes protect everything CircuitPython owns (lib/, boot_out.txt,
# settings.toml) and the macOS FAT turds (.Trashes, .fseventsd, ...).
rsync -rtv --delete \
  --exclude '__pycache__/' --exclude '*.pyc' --exclude '.*' \
  --exclude '/lib/' --exclude '/boot_out.txt' --exclude '/settings.toml' \
  "$SRC"/ "$TARGET"/

# --- lib check (warn only) --- PicoSystem needs just these two;
# neopixel is not used on this board (RGB LED is 3 PWM pins, not a NeoPixel).
missing=()
for lib in adafruit_display_text adafruit_imageload; do
  [ -d "$TARGET/lib/$lib" ] || missing+=("$lib/")
done
if [ ${#missing[@]} -ne 0 ]; then
  echo
  echo "deploy: WARNING — missing from $TARGET/lib/ :  ${missing[*]}" >&2
  echo "        circup install adafruit_display_text adafruit_imageload" >&2
fi

sync
echo "deploy: done. watch it:  screen /dev/tty.usbmodem*   (Ctrl-D restarts)"
