# Chapter 8 — Demo scripts

Ch8 is prototyping, not a game (see `../../README.md`), so most code lands
here `UNTESTED ON DEVICE`. This directory is the walkthrough series that
closes that gap: one numbered file per demo (or small batch of demos meant
to be tried together), written for whoever has the board in hand — steps to
deploy, what to physically do, what you should see, and a place to mark
pass/fail.

## Running a demo

Each `*_demo.py` in `game/` is written to run standalone as `main.py`
(that's what its own docstring says). Rather than hand-editing files on the
device, use `deploy.sh --demo NAME`:

```bash
Chapter_8/tools/deploy.sh --demo sprite_scale_demo
```

This deploys `game/` as usual, then overwrites the **device's** `main.py`
with `game/NAME.py` — the checked-in `main.py` (the diagnostic HUD) is
untouched on desktop. Reset the board to run it. To put the HUD back:

```bash
Chapter_8/tools/deploy.sh
```

## The series

| # | File | Demo module(s) | Beads |
|---|------|-----------------|-------|
| 01 | [`01-sprite-scale.md`](01-sprite-scale.md) | `sprite_scale_demo` | `cd-45v.1` |
| 02 | [`02-room-nav.md`](02-room-nav.md) | `room_nav_demo` (+ `rooms`, `edge_gesture`, `room_banner`) | `cd-45v.2`, `cd-45v.3`, `cd-45v.4` |
| 03 | [`03-ornament.md`](03-ornament.md) | `ornament_demo` (+ `stillness`) | `cd-45v.5` |
| 04 | [`04-fonts.md`](04-fonts.md) | `font_demo` (+ `fonts/*.bdf`) | `cd-bp3.11` |

New batch of features → new numbered file, added to this table.

## Template for a new entry

```markdown
# NN — <short name>

Beads: `cd-...` · Module(s): `game/....py`

## Deploy

    Chapter_8/tools/deploy.sh --demo <module_name>

(note any one-time setup beyond the standard doc/DEPLOY.md steps)

## Walkthrough

- [ ] Step: do this — expect: this
- [ ] Step: do this — expect: this

## Notes

(fill in during/after the on-device run: what worked, what felt off,
threshold/timing tweaks needed, whether the bead(s) above are ready to
close)
```

## After running one

Update the relevant bead's notes with what you saw (`bd update <id> --notes
"..."` or ask Claude to), and close it if the feature checks out. If it
doesn't, leave the bead open with what needs to change — the walkthrough
file stays as-is for the next attempt.
