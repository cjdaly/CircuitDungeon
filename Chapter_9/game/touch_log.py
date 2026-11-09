# SPDX-License-Identifier: MIT
"""A touch diagnostic log, on with settings.toml TOUCH_LOG = "1" -- cd-342.24.

Playtests say moves are hit or miss, and need 2 or 3 tries. To see why, this
prints one line per stroke: where the finger went down and came up, how long it
was down, how many readings the chip gave during it, how many reads it refused
(quiet NACKs) mid-stroke, and what the game made of it. Every 10s report also
gets the chip's overall read counts.

Plain logic (no hardware), so it runs under desktop Python
(tests/test_touch_log.py).
"""


class TouchLog:
    def __init__(self, out=print):
        self._out = out
        self.polls = self.quiet = self.points = 0
        self._stroke = None  # [t0, first point, last point, last t, points, quiet]

    def sample(self, now, point, quiet):
        """Every poll: its point (or None), and whether the chip refused the read."""
        self.polls += 1
        if quiet:
            self.quiet += 1
        if point is not None:
            self.points += 1
            if self._stroke is None:
                self._stroke = [now, point, point, now, 1, 0]
            else:
                self._stroke[2] = point
                self._stroke[3] = now
                self._stroke[4] += 1
        elif quiet and self._stroke is not None:
            self._stroke[5] += 1

    @property
    def stroke_open(self):
        return self._stroke is not None

    def end(self, now, outcome):
        """The finger is up (or the reads say so): print the stroke and what it did."""
        if self._stroke is None:
            return
        t0, first, last, last_t, points, quiet = self._stroke
        self._stroke = None
        self._out("t={:.1f} touch {},{} -> {},{} {:.2f}s pts={} quiet={} gap={:.2f}s: {}".format(
            t0, first[0], first[1], last[0], last[1], last_t - t0, points, quiet,
            now - last_t, outcome))

    def report(self):
        """The 10s summary, and start counting again."""
        line = "touch polls={} quiet={} points={}".format(self.polls, self.quiet, self.points)
        self.polls = self.quiet = self.points = 0
        return line
