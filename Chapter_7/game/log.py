# SPDX-FileCopyrightText: 2026 Chris J Daly (github user cjdaly)
#
# SPDX-License-Identifier: MIT

# The message log (bead cd-e3p.9). Pure — engine code (combat, item use,
# descent, …) formats a sentence and calls `world.log.add(text)`. The message
# line (cd-oht.4) watches `.seq` and shows `.tail()`; a full-scrollback view
# (cd-oht.7) can show `.all()`.
#
# Governed by doc/ENGINE.md §11.

CAP = 24   # lines kept; older ones fall off


class Log:
    def __init__(self, cap=CAP):
        self._cap = cap
        self._lines = []
        self.seq = 0            # bumped on every add — renderers watch this

    def add(self, text):
        self._lines.append(text)
        if len(self._lines) > self._cap:
            del self._lines[0]
        self.seq += 1

    def tail(self, n=1):
        """The `n` most recent lines, oldest-first."""
        return self._lines[-n:] if n else []

    def latest(self):
        """The newest line, or "" when empty."""
        return self._lines[-1] if self._lines else ""

    def all(self):
        return list(self._lines)

    def clear(self):
        self._lines = []
        self.seq += 1

    def __len__(self):
        return len(self._lines)
