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

# Parser for the `.lvl` format (see Chapter_6/PLAN.md). Pure text handling —
# no displayio, no board — so it runs and is testable off-device.

DEFAULT_CHARS = '(_)"[#]RGBYOoX^CDEF'
DEFAULT_WALLS = '"[#]RGBYOoX^CDEF'

_SECTIONS = ("meta", "terrain", "grid", "exits", "events")


class Level:
    def __init__(self):
        self.name, self.title, self.subtitle = None, None, None
        self.chars, self.walls = DEFAULT_CHARS, DEFAULT_WALLS
        self.grid, self.exits, self.events = [], {}, {}
        self.scroll = False


class LevelParseError(ValueError):
    def __init__(self, path, lineno, line, reason):
        super().__init__("{}:{}: {} ({!r})".format(path, lineno, reason, line))


def _kv(line):
    key, _, value = line.partition(":")
    return key.strip().lower(), value.strip()


def _parse_meta(level, key, value):
    if key == "name":
        level.name = value
    elif key == "title":
        level.title = value
    elif key == "subtitle":
        level.subtitle = value
    elif key == "scroll":
        level.scroll = value.strip().lower() in ("yes", "true", "1")


def _parse_terrain(level, key, value):
    if key == "chars":
        level.chars = value
    elif key == "walls":
        level.walls = value


def _parse_exit(level, path, lineno, line):
    left, sep, right = line.partition("->")
    if not sep:
        raise LevelParseError(path, lineno, line, "malformed [exits] line, expected 'col,row -> mapname @ col,row'")
    col, row = (int(n) for n in left.strip().split(","))
    mapname, sep, dest = right.partition("@")
    if not sep:
        raise LevelParseError(path, lineno, line, "malformed [exits] line, missing '@ dest_col,dest_row'")
    dcol, drow = (int(n) for n in dest.strip().split(","))
    level.exits[(col, row)] = {"map": mapname.strip(), "dest": (dcol, drow)}


def _parse_event(level, path, lineno, line):
    left, sep, rest = line.partition("!")
    if not sep:
        raise LevelParseError(path, lineno, line, "malformed [events] line, expected 'col,row ! event_type [args]'")
    left = left.rstrip()
    repeat = left.endswith("*")
    if repeat:
        left = left[:-1].rstrip()
    col, row = (int(n) for n in left.split(","))
    parts = rest.strip().split(None, 1)
    if not parts:
        raise LevelParseError(path, lineno, line, "malformed [events] line, missing event_type")
    event_type = parts[0]
    args = parts[1] if len(parts) > 1 else ""
    level.events.setdefault((col, row), []).append({"type": event_type, "args": args, "repeat": repeat})


def _pad_grid(grid, fill_char):
    if not grid:
        return grid
    cols = max(len(row) for row in grid)
    return [row + fill_char * (cols - len(row)) for row in grid]


def load(path):
    """Parse a `.lvl` file at `path` into a Level."""
    level = Level()
    grid_rows = []
    section = None

    with open(path) as f:
        for lineno, raw_line in enumerate(f, start=1):
            line = raw_line.rstrip("\r\n")

            if line.strip() == "":
                continue

            stripped = line.strip()
            if stripped.startswith("[") and stripped.endswith("]") and stripped[1:-1] in _SECTIONS:
                section = stripped[1:-1]
                continue

            if section != "grid" and stripped.startswith("#"):
                continue

            if section == "meta":
                _parse_meta(level, *_kv(line))
            elif section == "terrain":
                _parse_terrain(level, *_kv(line))
            elif section == "grid":
                grid_rows.append(line)
            elif section == "exits":
                _parse_exit(level, path, lineno, line)
            elif section == "events":
                _parse_event(level, path, lineno, line)
            # content before the first recognized section header is ignored

    fill_char = level.chars[0] if level.chars else " "
    level.grid = _pad_grid(grid_rows, fill_char)

    if level.name is None:
        stem = path.rsplit("/", 1)[-1]
        if stem.endswith(".lvl"):
            stem = stem[: -len(".lvl")]
        level.name = stem

    return level
