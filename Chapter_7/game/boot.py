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

# Runs once at hard reset, before the USB workflow starts — the right place to
# turn OFF auto-reload. Without this, CircuitPython soft-reboots on every file
# write, so a multi-file `deploy.sh` reboots the board mid-copy and it runs a
# half-written codebase. With it: deploy the whole project, THEN press reset
# (or Ctrl-C + Ctrl-D in the serial REPL) to run the new code.
#
# See Chapter_7/doc/DEPLOY.md. Delete this file (or the line) for live-reload.

import supervisor

try:
    supervisor.runtime.autoreload = False        # CircuitPython 8+
except AttributeError:
    supervisor.disable_autoreload()              # CircuitPython <= 7

print("boot.py: autoreload OFF — deploy fully, then reset to run")
