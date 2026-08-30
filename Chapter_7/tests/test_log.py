# The MIT License (MIT)
#
# Copyright (c) 2026 Chris J Daly (github user cjdaly)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

#   python3 Chapter_7/tests/test_log.py

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "game"))

import log as log_mod  # noqa: E402


class LogTests(unittest.TestCase):
    def test_add_and_latest(self):
        lg = log_mod.Log()
        self.assertEqual(lg.latest(), "")
        lg.add("a")
        lg.add("b")
        self.assertEqual(lg.latest(), "b")
        self.assertEqual(lg.tail(2), ["a", "b"])
        self.assertEqual(lg.all(), ["a", "b"])
        self.assertEqual(len(lg), 2)

    def test_seq_bumps_on_every_add(self):
        lg = log_mod.Log()
        self.assertEqual(lg.seq, 0)
        lg.add("x")
        lg.add("y")
        self.assertEqual(lg.seq, 2)

    def test_cap_drops_oldest(self):
        lg = log_mod.Log(cap=3)
        for c in "abcde":
            lg.add(c)
        self.assertEqual(lg.all(), ["c", "d", "e"])
        self.assertEqual(len(lg), 3)
        self.assertEqual(lg.seq, 5)          # seq counts adds, not survivors

    def test_clear(self):
        lg = log_mod.Log()
        lg.add("x")
        s = lg.seq
        lg.clear()
        self.assertEqual(lg.all(), [])
        self.assertEqual(lg.latest(), "")
        self.assertGreater(lg.seq, s)

    def test_tail_zero_is_empty(self):
        lg = log_mod.Log()
        lg.add("x")
        self.assertEqual(lg.tail(0), [])


if __name__ == "__main__":
    unittest.main()
