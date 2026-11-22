# SPDX-License-Identifier: MIT
"""The game's settings.toml keys, read in one place -- cd-342.47.2.

Each board's settings.toml (doc/DEPLOY.md) is left alone by deploys. The keys
the game reads are all here, read once at start-up. The bootstrap's own keys
stay with it: LIGHT_SLEEP (hardware.py) and POWER_LOG (main.py).
"""
import os

import episodes

_YES = ("1", "true", "yes")


class Settings:
    def __init__(self, getenv=os.getenv):
        # Who this board is for: the gift tag and the finale's MERRY CHRISTMAS.
        self.player = getenv("PLAYER")
        self.device_id = getenv("DEVICE_ID")
        # How much the clues help: easy, medium (the default) or hard (cd-342.40).
        self.difficulty = episodes.difficulty(getenv("DIFFICULTY"))
        # How long the gift tag stays up, in seconds; None for gift_tag's own.
        self.tag_seconds = _seconds(getenv("TAG_SECONDS"))
        # Review switches: every room open; start at the finale. Never on a gift.
        self.open_all_rooms = getenv("OPEN_ALL_ROOMS") in _YES
        self.finale_now = getenv("FINALE_NOW") in _YES
        # Diagnostic: print every stroke (touch_log.py).
        self.touch_log = getenv("TOUCH_LOG") in _YES


def _seconds(text):
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None
