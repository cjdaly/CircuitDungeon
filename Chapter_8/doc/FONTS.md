# Chapter 8 — Custom fonts for text overlays (cd-bp3.11)

Ch9's text overlays (room names, banners, HUD text) all use CircuitPython's
built-in `terminalio.FONT` today — plain, small, monospace. Chris wants a
comic-book-style look instead. This doc is the research + the actual
conversion recipe used to get a working font onto the device.

## How CircuitPython loads a custom font

`adafruit_bitmap_font.bitmap_font.load_font(path)` loads a BDF or PCF
bitmap font file and returns a font object that's a drop-in replacement for
`terminalio.FONT` anywhere `adafruit_display_text.bitmap_label.Label` is
already used — no other code changes needed. The library ships in the
standard Adafruit CircuitPython bundle already vendored in this project
(`downloads/adafruit-circuitpython-bundle-10.x-mpy-20260820/lib/
adafruit_bitmap_font/`).

**RAM**: `terminalio.FONT` is frozen into firmware (effectively free). A
loaded BDF's glyphs don't all have to live in RAM at once — both the BDF
and PCF font classes support `load_glyphs(code_points)`, loading only the
specified characters. Since this project's overlays use a small, mostly
fixed character set (room names, short messages), pre-declaring exactly
which glyphs are needed keeps the RAM cost proportional to what's actually
used, not the whole font file. `font_demo.py` does this.

## The font: Bangers

[Bangers](https://fonts.google.com/specimen/Bangers) (Google Fonts,
[SIL Open Font License 1.1](https://github.com/googlefonts/bangers/blob/main/OFL.txt))
— built specifically in the style of mid-20th-century superhero comics
cover lettering. Free for commercial use; OFL requires including the
license text when redistributing (see `game/fonts/bangers-OFL.txt`).

One real constraint: **Bangers is effectively all-caps** — lowercase input
renders in the same caps style, there's no true lowercase glyph design.
Fine for short room-name/banner text (this project's actual use case), not
suited to anything needing real mixed-case.

`Luckiest Guy` (also Google Fonts, but **Apache License 2.0, not OFL** --
see "A second candidate" below, this was wrong in the original research)
was tried too — rounder, bolder, upright, more a 1950s-advertisement look
than comic-lettering specifically. Now used alongside Bangers rather than
as a fallback -- see "On-device verdict" below.

## Converting TTF -> BDF

CircuitPython needs a bitmap font (BDF/PCF), not the TTF outline font
Google Fonts distributes. FontForge does the conversion, but bitmap fonts
are fixed-size — one BDF per pixel size wanted.

**FontForge isn't installed on this Mac.** Rather than installing it
locally, this used **arc-1** (the rpi-fleet Raspberry Pi already set up for
Ch8's OpenSCAD/CAD work, see `../rpi-fleet/INVENTORY.md` and
`cad/README.md` for that precedent) — `sudo apt-get install -y fontforge`,
then a headless script over SSH. Recorded in `../rpi-fleet/INVENTORY.md`
as a capability of arc-1 now, alongside its OpenSCAD install.

FontForge's Python bindings on arc-1's packaged version
(`1:20230101~dfsg-4+b1`) have a broken `font.bitmapSizes` setter — every
input shape (`int`, list, tuple) raised a `SystemError` from the C
extension. Worked around by using FontForge's older native `.pe` scripting
language instead (`fontforge -script file.pe ...`), which doesn't hit the
same broken binding. Note for future font work: try the `.pe` path first
on this box, don't assume the Python API is a safe default.

The actual recipe used (subsetting to only the characters these overlays
need — space, digits, A-Z, a few punctuation marks — keeps the file small;
capital `M` must stay in the subset or `adafruit_display_text` miscalculates
line height):

```
# on arc-1, with Bangers-Regular.ttf fetched from
# https://github.com/googlefonts/bangers (OFL.txt confirmed present)

Open($1)
SelectNone()
SelectMore(32)   # space
SelectMore(33)   # !
SelectMore(39)   # '
SelectMore(44)   # ,
SelectMore(46)   # .
SelectMore(63)   # ?
# ...loop SelectMore over 48-57 (0-9) and 65-90 (A-Z)...
SelectInvert()
Clear()                        # drop everything not selected above
BitmapsAvail([16, 24])         # generate bitmap strikes at these pixel sizes
BitmapsRegen([16, 24])
Generate($2, "bdf")
```

Run once per output size wanted via
`fontforge -script make_bdf.pe Bangers-Regular.ttf bangers-16.bdf` etc.

**Letter-spacing**: Bangers' default advance width read as too cramped at
small bitmap sizes (see "On-device results" below). To add extra spacing,
widen each *kept* glyph's advance width **before** the invert+`Clear()`
step above (widening after, with a fresh `SelectAll()`, re-selects the
*entire original* glyph set including everything `Clear()` only emptied
rather than removed — produced a 5.8MB "BDF" with 65k+ glyph entries the
one time this was gotten backwards; don't call `SelectAll()` again after
`Clear()`):

```
Open($1)
SelectNone()
SelectMore(32)  # ...build the keep-set exactly as above...
foreach
  SetWidth(GlyphInfo("Width") + 45)   # +45 font units = the on-device pick
endloop
SelectInvert()
Clear()
BitmapsAvail([24])
BitmapsRegen([24])
Generate($2, "bdf")
```

`GlyphInfo("Width")` / `SetWidth(n)` only work with exactly one glyph
selected at a time (hence the `foreach` loop, which FontForge's `.pe`
language iterates one glyph per pass over whatever's currently selected).

## On-device results (2026-09-13, ws-1/ws-2)

Tried, in order: 16px (font's default spacing) — too cramped to read
comfortably. 24px default spacing — readable but felt tight. +90 font-unit
extra advance width at 24px — felt like too much. **+45 (half of that) at
24px — the pick.** 28px/32px (default spacing, no extra width) were also
generated and briefly compared but not against the 24px+45 configuration
specifically — an open question if 24px+spacing doesn't hold up in Ch9's
actual UI later (see `cd-bp3.12`, which also covers trying other font
families beyond Bangers).

Final files kept in `game/fonts/`: `bangers-24.bdf` (default spacing,
kept as a reference baseline) and `bangers-spaced45-24.bdf` (the winner,
7.9KB / 42 glyphs). The 16px and +90-spacing variants were deleted once
+45 was picked — the `.pe` recipe above reproduces any of them again if
needed.

## A second candidate: Luckiest Guy (`cd-bp3.12`)

Same 24px+45 recipe applied to
[Luckiest Guy](https://fonts.google.com/specimen/Luckiest+Guy) — rounder,
bolder, upright (not slanted like Bangers). **License correction**:
`cd-bp3.11`'s desk research assumed OFL like Bangers; Google's own download
manifest (`fonts.google.com/download/list?family=Luckiest+Guy`) says
**Apache License 2.0** instead — still fully free/permissive, just a
different license text to ship (`fonts/LuckiestGuy-LICENSE.txt`, not
`OFL.txt`). Not every Google Font is OFL; check per-font next time rather
than assuming.

The TTF wasn't reachable at the `github.com/googlefonts/<name>` or
`github.com/google/fonts/ofl/<name>` paths that worked for Bangers (404 on
both) — Google's font family/version naming doesn't map predictably to
either repo layout. Fetched instead via Google's own download-manifest API
(`fonts.google.com/download/list?family=<Name>`), which returns a JSON
manifest with text-file contents inline and a `fileRefs` array of
`{filename, url}` for the actual binary font files (served from
`fonts.gstatic.com`) — more reliable than guessing repo paths.

## On-device verdict (2026-09-13, ws-1)

Both read well — this became a **role split, not a single winner**:
Bangers is slanted and more horizontally compact (reads as "shouted",
comic-speech-bubble energy); Luckiest Guy is thicker/bolder and upright
(reads more like signage/a title). Chris's call: **Luckiest Guy for
titles/names** (room names — `RoomLabel`, `cd-zw2.5`) and **Bangers for
in-character dialogue** (a "I'll find you!"-style critter-speech UI that
doesn't exist yet as its own mechanic). Neither is wired into real Ch9
code yet — that's future integration work once/if a dialogue system exists
to need Bangers' role at all.

## Trying it on-device

`font_demo.py` (`deploy.sh --demo font_demo`) shows `terminalio.FONT`,
Bangers, and Luckiest Guy together (all 24px+45) on the real round panel —
see `doc/demos/04-fonts.md` for the walkthrough. Needs
`adafruit_bitmap_font` in `lib/` (`doc/DEPLOY.md` step 2).

## Status

Confirmed on-device 2026-09-13: both Bangers and Luckiest Guy at 24px with
+45 extra letter-spacing read well on the real round panel. Design
decision made (see "On-device verdict" above); neither is wired into real
Ch9 code yet -- follow-up once `RoomLabel` (cd-zw2.5) gets its font swap,
and once/if a dialogue mechanic exists for Bangers' role.
