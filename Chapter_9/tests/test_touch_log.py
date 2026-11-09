# SPDX-License-Identifier: MIT
"""touch_log.TouchLog: one line per stroke -- cd-342.24."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "game"))

from touch_log import TouchLog  # noqa: E402


class TestTouchLog(unittest.TestCase):
    def setUp(self):
        self.lines = []
        self.log = TouchLog(out=self.lines.append)

    def test_a_stroke_counts_its_points_and_the_quiet_reads_inside_it(self):
        self.log.sample(1.0, None, True)  # quiet before the stroke: not part of it
        self.log.sample(1.1, (200, 120), False)
        self.log.sample(1.15, None, True)
        self.log.sample(1.2, (205, 121), False)
        self.log.sample(1.25, None, False)
        self.log.end(1.25, "move right")
        self.assertEqual(self.lines, [
            "t=1.1 touch 200,120 -> 205,121 0.10s pts=2 quiet=1 gap=0.05s: move right"])
        self.assertFalse(self.log.stroke_open)

    def test_the_report_totals_every_poll_then_starts_again(self):
        for point, quiet in ((None, True), ((1, 2), False), (None, False)):
            self.log.sample(0.0, point, quiet)
        self.assertEqual(self.log.report(), "touch polls=3 quiet=1 points=1")
        self.assertEqual(self.log.report(), "touch polls=0 quiet=0 points=0")

    def test_ending_with_no_stroke_prints_nothing(self):
        self.log.end(2.0, "nothing")
        self.assertEqual(self.lines, [])


if __name__ == "__main__":
    unittest.main()
