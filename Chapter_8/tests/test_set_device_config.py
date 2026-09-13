# SPDX-License-Identifier: MIT
# Off-device tests for tools/set_device_config.py -- pure file I/O, no
# hardware or CircuitPython needed. Exercises it against a fake mounted
# CIRCUITPY drive (a temp dir with a boot_out.txt).
#
#   python3 Chapter_8/tests/test_set_device_config.py

import contextlib
import io
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))

import set_device_config as sdc  # noqa: E402


class TestUpdate(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.settings = Path(self._tmp.name) / "settings.toml"

    def test_creates_file_with_given_keys(self):
        sdc.update(self.settings, {"DEVICE_ID": "ws-1"})
        self.assertEqual(
            sdc._parse(self.settings.read_text().splitlines(keepends=True)),
            {"DEVICE_ID": (0, "ws-1")},
        )

    def test_updates_existing_key_in_place(self):
        sdc.update(self.settings, {"DEVICE_ID": "ws-1"})
        sdc.update(self.settings, {"DEVICE_ID": "ws-2"})
        found = sdc._parse(self.settings.read_text().splitlines(keepends=True))
        self.assertEqual(found["DEVICE_ID"][1], "ws-2")
        # still exactly one DEVICE_ID line, not appended a second time
        lines = self.settings.read_text().splitlines()
        self.assertEqual(sum(1 for l in lines if l.startswith("DEVICE_ID")), 1)

    def test_setting_one_key_leaves_others_untouched(self):
        sdc.update(self.settings, {"DEVICE_ID": "ws-1", "BATTERY_MAH": "420"})
        sdc.update(self.settings, {"BATTERY_PRODUCT": "adafruit-4236"})
        found = sdc._parse(self.settings.read_text().splitlines(keepends=True))
        self.assertEqual(found["DEVICE_ID"][1], "ws-1")
        self.assertEqual(found["BATTERY_MAH"][1], "420")
        self.assertEqual(found["BATTERY_PRODUCT"][1], "adafruit-4236")

    def test_preserves_unrelated_lines_and_comments(self):
        self.settings.write_text(
            '# some unrelated setting\nCIRCUITPY_WIFI_SSID = "home"\n'
        )
        sdc.update(self.settings, {"DEVICE_ID": "ws-monica"})
        text = self.settings.read_text()
        self.assertIn("# some unrelated setting", text)
        self.assertIn('CIRCUITPY_WIFI_SSID = "home"', text)
        self.assertIn('DEVICE_ID = "ws-monica"', text)

    def test_appends_without_trailing_newline_in_prior_file(self):
        self.settings.write_text('CIRCUITPY_WIFI_SSID = "home"')  # no trailing \n
        sdc.update(self.settings, {"DEVICE_ID": "ws-1"})
        lines = self.settings.read_text().splitlines()
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[1], 'DEVICE_ID = "ws-1"')


class TestMainCli(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.target = Path(self._tmp.name)
        (self.target / "boot_out.txt").write_text("Adafruit CircuitPython 10.2.1\n")

    def _run(self, argv):
        old_argv = sys.argv
        sys.argv = ["set_device_config.py"] + argv
        out = io.StringIO()
        try:
            with contextlib.redirect_stdout(out):
                sdc.main()
        finally:
            sys.argv = old_argv
        return out.getvalue()

    def test_rejects_target_without_boot_out_txt(self):
        not_circuitpy = Path(self._tmp.name) / "not_circuitpy"
        not_circuitpy.mkdir()
        with self.assertRaises(SystemExit):
            self._run(["--id", "ws-1", str(not_circuitpy)])

    def test_writes_id_and_battery_fields(self):
        self._run(
            [
                "--id", "ws-monica",
                "--battery-product", "adafruit-4236",
                "--battery-mah", "420",
                str(self.target),
            ]
        )
        text = (self.target / "settings.toml").read_text()
        self.assertIn('DEVICE_ID = "ws-monica"', text)
        self.assertIn('BATTERY_PRODUCT = "adafruit-4236"', text)
        self.assertIn('BATTERY_MAH = "420"', text)

    def test_show_reports_current_values_without_writing(self):
        self._run(["--id", "ws-2", str(self.target)])
        before = (self.target / "settings.toml").read_text()
        printed = self._run(["--show", str(self.target)])
        after = (self.target / "settings.toml").read_text()
        self.assertIn("DEVICE_ID = ws-2", printed)
        self.assertEqual(before, after)

    def test_no_flags_is_an_error(self):
        with self.assertRaises(SystemExit):
            self._run([str(self.target)])


if __name__ == "__main__":
    unittest.main()
