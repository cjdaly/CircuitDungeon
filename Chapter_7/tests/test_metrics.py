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

#   python3 Chapter_7/tests/test_metrics.py

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "game"))

import metrics as metrics_mod  # noqa: E402


class _FakeGC:
    """Just the CircuitPython gc surface metrics.py touches."""

    def __init__(self, free_series):
        self._series = list(free_series)
        self.collects = 0

    def collect(self):
        self.collects += 1

    def mem_free(self):
        return self._series[min(self.collects - 1, len(self._series) - 1)]

    def mem_alloc(self):
        return 200_000 - self.mem_free()


class RamSampling(unittest.TestCase):
    def _with_fake_gc(self, free_series):
        real = metrics_mod.gc
        fake = _FakeGC(free_series)
        metrics_mod.gc = fake
        self.addCleanup(lambda: setattr(metrics_mod, "gc", real))
        return fake

    def test_sample_populates_free_alloc_and_heap(self):
        self._with_fake_gc([120_000])
        m = metrics_mod.Metrics()
        m.sample_ram()
        self.assertEqual(m.free, 120_000)
        self.assertEqual(m.alloc, 80_000)
        self.assertEqual(m.heap, 200_000)
        self.assertEqual(m.free_low, 120_000)
        self.assertEqual(m.ram_samples, 1)
        self.assertGreaterEqual(m.collect_ms, 0.0)

    def test_free_low_tracks_the_minimum_across_samples(self):
        self._with_fake_gc([100_000, 90_000, 95_000, 82_000, 88_000])
        m = metrics_mod.Metrics(ram_interval=1.0)
        for i in range(5):
            m.maybe_sample_ram(float(i))
        self.assertEqual(m.ram_samples, 5)
        self.assertEqual(m.free, 88_000)        # last reading
        self.assertEqual(m.free_low, 82_000)    # low-water

    def test_maybe_sample_is_throttled_by_the_interval(self):
        self._with_fake_gc([120_000])
        m = metrics_mod.Metrics(ram_interval=10.0)
        m.maybe_sample_ram(0.0)          # first call always samples
        self.assertEqual(m.ram_samples, 1)
        m.maybe_sample_ram(1.0)          # inside the window — no-op
        m.maybe_sample_ram(9.9)
        self.assertEqual(m.ram_samples, 1)
        m.maybe_sample_ram(10.0)         # window elapsed
        self.assertEqual(m.ram_samples, 2)

    def test_off_device_gc_has_no_mem_free_so_fields_are_none(self):
        # real CPython gc — no mem_free/mem_alloc
        m = metrics_mod.Metrics()
        m.sample_ram()
        self.assertIsNone(m.free)
        self.assertIsNone(m.alloc)
        self.assertIsNone(m.heap)
        self.assertIsNone(m.free_low)
        self.assertEqual(m.ram_samples, 1)      # still counts the attempt


class Frame(unittest.TestCase):
    def test_note_frame_tracks_last_and_max(self):
        m = metrics_mod.Metrics()
        m.note_frame(0.010)
        self.assertAlmostEqual(m.frame_ms, 10.0)
        m.note_frame(0.040)
        self.assertAlmostEqual(m.frame_ms, 40.0)
        self.assertAlmostEqual(m.frame_ms_max, 40.0)
        m.note_frame(0.005)
        self.assertAlmostEqual(m.frame_ms, 5.0)
        self.assertAlmostEqual(m.frame_ms_max, 40.0)   # max sticks


class FlashAndEnvironment(unittest.TestCase):
    def test_flash_returns_a_consistent_pair(self):
        free, total = metrics_mod.Metrics().flash()
        if free is None or total is None:
            self.assertIsNone(free)
            self.assertIsNone(total)
        else:
            self.assertIsInstance(free, int)
            self.assertIsInstance(total, int)
            self.assertGreater(total, 0)
            self.assertLessEqual(free, total)

    def test_environment_is_a_dotted_version_and_a_name(self):
        ver, osname = metrics_mod.Metrics().environment()
        self.assertRegex(ver, r"^\d+\.\d+\.\d+$")
        self.assertTrue(osname)


if __name__ == "__main__":
    unittest.main()
