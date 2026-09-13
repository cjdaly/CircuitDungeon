# 04 — Custom font: terminalio vs. Bangers vs. Luckiest Guy

Beads: `cd-bp3.11`, `cd-bp3.12` (both settled) · Module: `game/font_demo.py`
(+ `game/fonts/*.bdf`)

Ch9's text overlays all use `terminalio.FONT` today. Chris wants a
comic-book look instead. Two candidates compared here, both at 24px with
+45 font-unit extra letter-spacing: **Bangers** (superhero-comics
lettering, SIL OFL) and **Luckiest Guy** (rounder/bolder, Apache 2.0 —
not OFL, a correction from `cd-bp3.11`'s original research). See
`doc/FONTS.md` for the full research, tuning history, and how the `.bdf`
files were made.

## One-time setup beyond doc/DEPLOY.md

`adafruit_bitmap_font` needs to be in `lib/` — not required by any other
demo, so it's easy to have missed:

    circup --path /Volumes/CIRCUITPY install adafruit_bitmap_font

`deploy.sh` will warn if it's missing.

## Deploy

    Chapter_8/tools/deploy.sh --demo font_demo

Reset the board. Serial prints `Ch8 font demo ready`. Static scene, no
touch/IMU input.

## Walkthrough

- [x] **No crash / no traceback** — confirmed 2026-09-13 (ws-1).
- [x] **terminalio row** — "terminalio (today)" at normal size.
- [x] **Bangers row** — "LIVING ROOM", slanted, more horizontally compact.
- [x] **Luckiest Guy row** — "LIVING ROOM", upright, bolder/thicker.
- [x] **Legible over the round bezel** — nothing clipped.
- [x] **Verdict** — both read well; not a single winner, a role split (see
  Notes).

## Notes

**Confirmed 2026-09-13 (ws-1), Chris's call**: both fonts work, and the
visual difference suggests different jobs rather than picking one —
**Luckiest Guy for titles/names** (room names, `RoomLabel`/`cd-zw2.5`) and
**Bangers for in-character dialogue** (a "I'll find you!"-style
critter-speech UI — doesn't exist as a mechanic yet, so Bangers' role is
aspirational until it does). Neither is wired into real Ch9 code yet —
follow-up once `RoomLabel` gets its font swap, and once/if a dialogue
system exists.
