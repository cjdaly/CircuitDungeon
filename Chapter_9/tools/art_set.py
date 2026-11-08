#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Room art sets: several versions of the backdrops in the repo, one on a board -- cd-342.35.

    python3 Chapter_9/tools/art_set.py list
    python3 Chapter_9/tools/art_set.py show NAME
    python3 Chapter_9/tools/art_set.py compose NAME DEST_DIR
    python3 Chapter_9/tools/art_set.py add NAME ROOM SRC.bmp --note "how it was made"

Each set is Chapter_9/art_sets/<name>/ with a set.json and rooms/*.bmp
(backdrop.file_name(room) names). A set may be partial: `base` names the set
its missing rooms come from (the hand-drawn set, `drawn`, has none and must
cover every room). compose() writes the resolved files, plus SET.txt naming the
set, into one folder -- deploy.sh puts exactly that on a board as /art/rooms,
so the board only ever holds one set, and game code doesn't know sets exist.

set.json:
    {"name": ..., "description": ..., "base": "drawn" or null,
     "made_by": how the set is produced (tool, settings),
     "rooms": {"sewing_nook.bmp": {"note": where this one came from}, ...}}
"""
import argparse
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SETS_DIR = os.path.normpath(os.path.join(HERE, "..", "art_sets"))
DEFAULT = "drawn"
MARKER = "SET.txt"  # in the composed folder / on the board: the set's name


def names():
    return sorted(d for d in os.listdir(SETS_DIR)
                  if os.path.isfile(os.path.join(SETS_DIR, d, "set.json")))


def manifest(name):
    path = os.path.join(SETS_DIR, name, "set.json")
    if not os.path.isfile(path):
        raise KeyError("no art set {!r} (have: {})".format(name, ", ".join(names())))
    with open(path) as f:
        return json.load(f)


def rooms_dir(name):
    return os.path.join(SETS_DIR, name, "rooms")


def own_files(name):
    d = rooms_dir(name)
    if not os.path.isdir(d):
        return {}
    return {f: os.path.join(d, f) for f in sorted(os.listdir(d)) if f.endswith(".bmp")}


def files(name, _seen=()):
    """file name -> path, this set's own files over its base chain's."""
    if name in _seen:
        raise ValueError("art set base loop: {}".format(" -> ".join(_seen + (name,))))
    base = manifest(name).get("base")
    resolved = files(base, _seen + (name,)) if base else {}
    resolved.update(own_files(name))
    return resolved


def compose(name, dest):
    """Fill `dest` (made empty first) with the resolved set and its SET.txt."""
    resolved = files(name)
    if os.path.isdir(dest):
        shutil.rmtree(dest)
    os.makedirs(dest)
    for f, src in resolved.items():
        shutil.copyfile(src, os.path.join(dest, f))
    with open(os.path.join(dest, MARKER), "w") as f:
        f.write(name + "\n")
    return resolved


def add(name, room_file, src, note):
    """Copy one backdrop into a set and record where it came from."""
    path = os.path.join(SETS_DIR, name, "set.json")
    data = manifest(name)
    os.makedirs(rooms_dir(name), exist_ok=True)
    shutil.copyfile(src, os.path.join(rooms_dir(name), room_file))
    data.setdefault("rooms", {})[room_file] = {"note": note}
    with open(path, "w") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    p = sub.add_parser("show")
    p.add_argument("name")
    p = sub.add_parser("compose")
    p.add_argument("name")
    p.add_argument("dest")
    p = sub.add_parser("add")
    p.add_argument("name")
    p.add_argument("room", help='a room name ("Sewing Nook") or its file (sewing_nook.bmp)')
    p.add_argument("src")
    p.add_argument("--note", required=True)
    args = ap.parse_args(argv)
    try:
        if args.cmd == "list":
            for n in names():
                m = manifest(n)
                print("{:16} {:3} own, base {:8} {}".format(
                    n, len(own_files(n)), m.get("base") or "-", m.get("description", "")))
        elif args.cmd == "show":
            own = own_files(args.name)
            for f, path in files(args.name).items():
                print("{:22} {}".format(f, "own" if f in own else "from " + os.path.basename(
                    os.path.dirname(os.path.dirname(path)))))
        elif args.cmd == "compose":
            n = len(compose(args.name, args.dest))
            print("art set {}: {} rooms -> {}".format(args.name, n, args.dest))
        elif args.cmd == "add":
            room_file = args.room if args.room.endswith(".bmp") else (
                args.room.lower().replace("'", "").replace(" ", "_") + ".bmp")
            add(args.name, room_file, args.src, args.note)
            print("added {} to {}".format(room_file, args.name))
    except (KeyError, ValueError) as e:
        sys.exit("art_set: {}".format(e.args[0]))


if __name__ == "__main__":
    main(sys.argv[1:])
