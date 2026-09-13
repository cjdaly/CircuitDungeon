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

#   python3 Chapter_7/tests/test_set_device_config.py

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

    def test_creates_file_with_device_id(self):
        sdc.update(self.settings, "ps-1")
        self.assertEqual(sdc._parse(self.settings.read_text().splitlines(keepends=True)), (0, "ps-1"))

    def test_updates_existing_key_in_place(self):
        sdc.update(self.settings, "ps-1")
        sdc.update(self.settings, "ps-2")
        found = sdc._parse(self.settings.read_text().splitlines(keepends=True))
        self.assertEqual(found[1], "ps-2")
        lines = self.settings.read_text().splitlines()
        self.assertEqual(sum(1 for l in lines if l.startswith("DEVICE_ID")), 1)

    def test_preserves_unrelated_lines_and_comments(self):
        self.settings.write_text('# some unrelated setting\nCIRCUITPY_WIFI_SSID = "home"\n')
        sdc.update(self.settings, "ps-1")
        text = self.settings.read_text()
        self.assertIn("# some unrelated setting", text)
        self.assertIn('CIRCUITPY_WIFI_SSID = "home"', text)
        self.assertIn('DEVICE_ID = "ps-1"', text)

    def test_appends_without_trailing_newline_in_prior_file(self):
        self.settings.write_text('CIRCUITPY_WIFI_SSID = "home"')  # no trailing \n
        sdc.update(self.settings, "ps-1")
        lines = self.settings.read_text().splitlines()
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[1], 'DEVICE_ID = "ps-1"')


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
            self._run(["--id", "ps-1", str(not_circuitpy)])

    def test_writes_device_id(self):
        self._run(["--id", "ps-1", str(self.target)])
        text = (self.target / "settings.toml").read_text()
        self.assertIn('DEVICE_ID = "ps-1"', text)

    def test_show_reports_current_value_without_writing(self):
        self._run(["--id", "ps-1", str(self.target)])
        before = (self.target / "settings.toml").read_text()
        printed = self._run(["--show", str(self.target)])
        after = (self.target / "settings.toml").read_text()
        self.assertIn("DEVICE_ID = ps-1", printed)
        self.assertEqual(before, after)

    def test_no_flags_is_an_error(self):
        with self.assertRaises(SystemExit):
            self._run([str(self.target)])


if __name__ == "__main__":
    unittest.main()
