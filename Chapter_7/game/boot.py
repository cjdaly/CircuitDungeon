# SPDX-FileCopyrightText: 2026 Chris J Daly (github user cjdaly)
#
# SPDX-License-Identifier: MIT

# Runs once at hard reset, before the USB workflow starts — the right place to
# turn OFF auto-reload. Without this, CircuitPython soft-reboots on every file
# write, so a multi-file `deploy.sh` reboots the board mid-copy and it runs a
# half-written codebase. With it: deploy the whole project, THEN press reset
# (or Ctrl-C + Ctrl-D in the serial REPL) to run the new code.
#
# See Chapter_7/doc/DEPLOY.md. Delete this file (or the line) for live-reload.

import supervisor

try:
    supervisor.runtime.autoreload = False        # CircuitPython 8+
except AttributeError:
    supervisor.disable_autoreload()              # CircuitPython <= 7

print("boot.py: autoreload OFF — deploy fully, then reset to run")
