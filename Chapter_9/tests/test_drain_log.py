# SPDX-License-Identifier: MIT
# Off-device tests for game/drain_log.py -- pure logic, no hardware needed.
#
#   python3 Chapter_9/tests/test_drain_log.py

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "game"))

from drain_log import KIND_BOOT, KIND_SAMPLE, SIZE, DrainLog, records  # noqa: E402


def _blank(slots=8):
    return bytearray(b"\xff" * (SIZE * slots))


class _Adc:
    def __init__(self):
        self.value = 40000

    def __call__(self):
        self.value -= 100
        return self.value


class TestDrainLog(unittest.TestCase):
    def test_blank_flash_has_no_records(self):
        self.assertEqual(records(_blank()), [])

    def test_boot_writes_a_boot_record(self):
        nvm = _blank()
        DrainLog(nvm, _Adc(), 600, 0.0)
        (rec,) = records(nvm)
        self.assertEqual(rec[0], KIND_BOOT)
        self.assertEqual(rec[4], 0)  # minutes
        self.assertEqual(rec[5], 39900)

    def test_samples_every_interval_with_time_split(self):
        nvm = _blank()
        log = DrainLog(nvm, _Adc(), 600, 0.0)
        for i in range(1, 601):  # 600 s of 1 s ticks: lit, then dark, then asleep
            t = float(i)
            log.tick(t, lit=t <= 150, asleep=t > 300)
        recs = records(nvm)
        self.assertEqual([r[0] for r in recs], [KIND_BOOT, KIND_SAMPLE])
        kind, lit, deep, seq, minutes, raw = recs[1]
        self.assertEqual((lit, deep, seq, minutes), (25, 50, 1, 10))

    def test_a_new_boot_continues_after_the_old_log(self):
        nvm = _blank()
        log = DrainLog(nvm, _Adc(), 60, 0.0)
        log.tick(60.0, True, False)
        DrainLog(nvm, _Adc(), 60, 5.0)
        kinds = [r[0] for r in records(nvm)]
        seqs = [r[3] for r in records(nvm)]
        self.assertEqual(kinds, [KIND_BOOT, KIND_SAMPLE, KIND_BOOT])
        self.assertEqual(seqs, [0, 1, 2])

    def test_ring_drops_the_oldest_when_full(self):
        nvm = _blank(slots=4)
        log = DrainLog(nvm, _Adc(), 60, 0.0)
        for i in range(1, 7):
            log.tick(60.0 * i, False, True)
        seqs = [r[3] for r in records(nvm)]
        self.assertEqual(seqs, [3, 4, 5, 6])

    def test_a_failed_write_stops_logging_without_raising(self):
        class _ReadOnly(bytearray):
            def __setitem__(self, key, value):
                raise OSError(30, "read-only")

        log = DrainLog(_ReadOnly(_blank()), _Adc(), 60, 0.0)
        self.assertIsNotNone(log.failed)
        log.tick(120.0, True, False)  # quietly does nothing
        self.assertEqual(log.writes, 0)


if __name__ == "__main__":
    unittest.main()
