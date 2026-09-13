# 04 — Custom font: terminalio vs. Bangers (comic-book style)

Beads: `cd-bp3.11` (settled), `cd-bp3.12` (trying other fonts, follow-up)
Module: `game/font_demo.py` (+ `game/fonts/*.bdf`)

Ch9's text overlays all use `terminalio.FONT` today. Chris wants a
comic-book look instead — **Bangers** (a Google Fonts face built for
superhero-comics lettering, OFL-licensed) is the first candidate tried.
See `doc/FONTS.md` for the full research, the on-device tuning history,
and how the `.bdf` files were made.

## One-time setup beyond doc/DEPLOY.md

`adafruit_bitmap_font` needs to be in `lib/` — not required by any other
demo, so it's easy to have missed:

    circup --path /Volumes/CIRCUITPY install adafruit_bitmap_font

`deploy.sh` will warn if it's missing.

## Deploy

    Chapter_8/tools/deploy.sh --demo font_demo

Reset the board. Serial prints `Ch8 font demo ready`. Static scene, no
touch/IMU input.

## Walkthrough (settled configuration)

This now shows the settled comparison: `terminalio.FONT` vs. Bangers at
24px with +45 font-unit extra letter-spacing (`bangers-spaced45-24.bdf`) —
the on-device pick after trying 16px (too cramped), 24px default spacing
(readable but tight), and +90 spacing (too much). See `doc/FONTS.md` for
that full history if re-litigating the spacing amount.

- [x] **No crash / no traceback** — confirmed 2026-09-13 (ws-1).
- [x] **terminalio row** — "terminalio.FONT (today)" at normal size.
- [x] **Bangers row** — "LIVING ROOM" reads well at a glance; the
  all-caps-only look (Bangers has no true lowercase) is fine for a room
  name.
- [x] **Legible over the round bezel** — nothing clipped.
- [ ] **Wire into Ch9** — swap `terminalio.FONT` for this Bangers config in
  Ch9's `RoomLabel`/`RoomBanner` (`cd-zw2.5`)? Or hold until `cd-bp3.12`
  compares other font families first?

## Notes

Confirmed 2026-09-13 (ws-1): 24px + 45 extra letter-spacing units is the
current pick for Bangers specifically. Not yet compared against other
font families (`cd-bp3.12`) or wired into Ch9's actual overlay code
(`cd-zw2.5`) — both open follow-ups, not blockers on this demo itself.
