#!/usr/bin/env bash
# Copy Chapter_7/game/ onto a CircuitPython device (the PicoSystem).
# The CONTENTS of game/ go to the drive root — util.py loads tiles from /tiles/.
# See Chapter_7/doc/DEPLOY.md.
#
#   Chapter_7/tools/deploy.sh [--no-eject] [CIRCUITPY_PATH]
#
# Default target: /Volumes/CIRCUITPY
#
# CircuitPython soft-reboots on every filesystem write, so a multi-file copy
# would reboot the board mid-deploy into a half-written codebase. Two guards:
#   1. game/boot.py turns auto-reload OFF (deployed with everything else).
#   2. this script ejects the drive at the end, which forces the macOS FAT
#      write cache to flush. Re-mount by resetting / power-cycling the board;
#      it then runs the freshly-written code. Pass --no-eject to skip.

set -euo pipefail

EJECT=1
if [ "${1:-}" = "--no-eject" ]; then EJECT=0; shift; fi

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

# --- lib check (warn only) --- PicoSystem needs these; neopixel is not used
# on this board (RGB LED is 3 PWM pins, not a NeoPixel). adafruit_ticks is a
# dependency of adafruit_display_text.bitmap_label (util.py).
missing=()
for lib in adafruit_display_text adafruit_imageload; do
  [ -d "$TARGET/lib/$lib" ] || missing+=("$lib/")
done
[ -e "$TARGET/lib/adafruit_ticks.mpy" ] || [ -d "$TARGET/lib/adafruit_ticks" ] \
  || missing+=("adafruit_ticks")
if [ ${#missing[@]} -ne 0 ]; then
  echo
  echo "deploy: WARNING — missing from $TARGET/lib/ :  ${missing[*]}" >&2
  echo "        circup install adafruit_display_text adafruit_imageload adafruit_ticks" >&2
fi

sync
if [ "$EJECT" = 1 ] && command -v diskutil >/dev/null 2>&1; then
  echo "deploy: ejecting $TARGET (flushes the write cache)…"
  diskutil eject "$TARGET" >/dev/null
  echo "deploy: done. RESET / power-cycle the board to run the new code."
  echo "        (boot.py keeps auto-reload off; the drive re-mounts on reset.)"
else
  sync
  echo "deploy: done (no eject). If the board didn't reboot cleanly, eject"
  echo "        $TARGET in Finder before resetting.  watch:  screen /dev/tty.usbmodem*"
fi
