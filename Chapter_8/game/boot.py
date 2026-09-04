# SPDX-License-Identifier: MIT
"""Runs once at hard reset, before the USB workflow starts.

Turns auto-reload OFF so a multi-file deploy.sh rsync doesn't soft-reboot the
board mid-copy into a half-written codebase. See Chapter_8/doc/DEPLOY.md
(mirrors the Chapter_7 game/boot.py pattern).
"""
import supervisor

supervisor.runtime.autoreload = False
print("boot.py: autoreload OFF -- deploy fully, then reset to run")
