#!/usr/bin/env bash
# Copy Chapter_8/game/ onto a CircuitPython device (the Waveshare RP2350-Touch-LCD-1.28).
# The CONTENTS of game/ go to the drive root. See Chapter_8/doc/DEPLOY.md.
#
#   Chapter_8/tools/deploy.sh [--no-eject] [--demo NAME] [CIRCUITPY_PATH]
#
# Default target: /Volumes/CIRCUITPY
#
# CircuitPython soft-reboots on every filesystem write, so a multi-file copy
# would reboot the board mid-deploy into a half-written codebase. Two guards
# (same pattern as Chapter_7/tools/deploy.sh):
#   1. game/boot.py turns auto-reload OFF (deployed with everything else).
#   2. this script ejects the drive at the end, which forces the macOS FAT
#      write cache to flush. Re-mount by resetting / power-cycling the board;
#      it then runs the freshly-written code. Pass --no-eject to skip.
#
# --demo NAME deploys game/ as usual, then overwrites the DEVICE's main.py
# with game/NAME.py (e.g. --demo sprite_scale_demo) so a *_demo.py prototype
# runs on reset instead of the diagnostic HUD. The desktop copy of main.py is
# untouched -- re-run deploy.sh with no --demo to put the HUD back on the
# device. See doc/demos/ for the walkthrough that goes with each demo.

set -euo pipefail

EJECT=1
DEMO=""
while [ $# -gt 0 ]; do
  case "$1" in
    --no-eject) EJECT=0; shift ;;
    --demo) DEMO="$2"; shift 2 ;;
    *) break ;;
  esac
done

TARGET="${1:-/Volumes/CIRCUITPY}"
HERE="$(cd "$(dirname "$0")/.." && pwd)"   # Chapter_8/
SRC="$HERE/game"

if [ -n "$DEMO" ] && [ ! -f "$SRC/$DEMO.py" ]; then
  echo "deploy: no such demo: $SRC/$DEMO.py" >&2
  exit 1
fi

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
# settings.toml, sd/) and the macOS FAT turds (.Trashes, .fseventsd, ...).
rsync -rtv --delete \
  --exclude '__pycache__/' --exclude '*.pyc' --exclude '.*' \
  --exclude '/lib/' --exclude '/boot_out.txt' --exclude '/settings.toml' \
  --exclude '/sd/' \
  "$SRC"/ "$TARGET"/

if [ -n "$DEMO" ]; then
  cp "$SRC/$DEMO.py" "$TARGET/main.py"
  echo "deploy: running demo '$DEMO' as main.py (desktop main.py unchanged)"
fi

# --- lib check (warn only) ---
# adafruit_ticks is a dependency of adafruit_display_text.bitmap_label.
# qmi8658c is vendored (not in the Adafruit bundle) -- copy it straight from
# Chapter_8/vendor/, not via circup. See doc/HARDWARE.md.
missing=()
for lib in adafruit_display_text adafruit_register; do
  [ -d "$TARGET/lib/$lib" ] || missing+=("$lib/")
done
for mpy in adafruit_cst8xx adafruit_gc9a01a adafruit_ticks; do
  [ -e "$TARGET/lib/$mpy.mpy" ] || missing+=("$mpy")
done
[ -e "$TARGET/lib/qmi8658c.py" ] || missing+=("qmi8658c.py (vendored, not circup)")
if [ ${#missing[@]} -ne 0 ]; then
  echo
  echo "deploy: WARNING — missing from $TARGET/lib/ :  ${missing[*]}" >&2
  echo "        circup install adafruit_cst8xx adafruit_gc9a01a adafruit_register adafruit_display_text adafruit_ticks" >&2
  echo "        cp $HERE/vendor/qmi8658c.py $TARGET/lib/" >&2
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
