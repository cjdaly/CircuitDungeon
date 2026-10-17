# Christmas Critters — visual style (DRAFT)

Living doc, started 2026-10-16 from Chris's direction: a **comic-book**
style, driven by the device itself — a tiny (240px) round screen — and a
**first-person** view with **no hero sprite**. Everything here is a
proposal to react to; decisions get marked **DECIDED** as they land.

## 1. The screen is one comic panel

- **The circle is the panel.** Every screen is a single panel; the bezel is
  its border. Draw a thick black "ink" ring just inside the visible edge —
  it reads as a panel border and also hides the round-panel clipping margin
  (`Chapter_8/doc/HARDWARE.md`).
- **Cuts, not camera moves.** Comics jump between shots; they don't pan.
  That suits displayio, whose `Group.scale` is integer-only: there's no
  smooth zoom, but a hard cut from 1x to 3x is exactly a comic "smash cut".
- **Three shot sizes** (all built from the same 16x16 / 32x32 art):
  - *Wide* — a room's establishing panel (1x–2x art).
  - *Close-up* — one subject filling the middle (2x–3x): a rattling box, a
    hiding spot, a found critter.
  - *Extreme close-up* — a critter's face/upper body at 4x+ for the big
    beats (escape, found, home).
- **Pulse** = emphasis: bump a subject's scale n -> n+1 -> n for a beat or
  two (the "strobe larger/smaller" idea). Use sparingly so it stays loud.
- **Iris transitions** between rooms — a black circle closing to a point
  and reopening is the old-cartoon iris wipe, and it's native to a round
  screen. (Cheap: one 1-bit 240x240 overlay bitmap, 7.2KB, with the outside
  of a shrinking circle filled row by row.)

## 2. First person, no hero

- The player *is* the viewer. Presence is implied by what you can touch:
  edge exits (already built, `nav_view.py`) and tap targets in a panel
  (search a bush, tap a box, pick up an item).
- Narration addresses the player directly ("You hear scratching under the
  porch..."). Critters talk *to* the player in speech balloons.
- The 32x32 "hero" scale from the original sketch goes away; 32x32 is now
  the critter scale only.

## 3. Comic vocabulary, ranked for a tiny screen

Best value first — the top ones are tiny, read instantly, and need no text.

| Element | Use | Cost |
|---|---|---|
| **Emanata** — wiggle lines, `!`, `?`, hearts, `zzz`, sweat drop, dust puff, speed lines | something is shaking / alarmed / hiding / happy / fleeing | one small glyph sheet (8x8 and 16x16 tiles) |
| **SFX burst** — jagged starburst + one shouted word | RATTLE! POP! ZOOM! SQUEAK! FOUND! | `vectorio.Polygon` + a label |
| **Caption box** — yellow rectangle, black border | narration, room story, clues | rect + label |
| **Speech balloon** (with tail) | a critter talks | rounded rect/ellipse + tail polygon + label |
| **Thought bubble** (cloud + little circles) | critter wants its item — show the *item icon*, no words | a few `vectorio.Circle`s + one 16x16 icon |
| **Room title** | first entry to a room | label |
| **Halftone (Ben-Day) dots** background | the "printed comic" texture | one dither tile — **try on device first**, may just be noise at this size |

**Fonts** (both all-caps, both confirmed on hardware in `cd-bp3.11/.12`):
- **Luckiest Guy** — room titles and SFX words (big, upright, shouty).
- **Bangers** — captions, speech, narration (condensed, so more fits).
  This finally gives Bangers its job (the missing half of `cd-bp3.13`).

**Text budget.** Measured from the on-device picks (`*-spaced45-24.bdf`,
24px + 45 units letter-spacing, `cd-bp3.11/.12`): Bangers caps average
~11px/char, Luckiest Guy ~15px. The panel is ~220px wide at the middle but
only ~170–180px in a band 80px above or below centre, so:
- Bangers: ~14 chars per line in a top/bottom band, max **2 lines**.
- Luckiest Guy: ~13 chars across the middle, ~11 in a band, **1 line**
  (titles/SFX only).
- One idea per balloon/caption. Longer story = a *sequence* of captions,
  each tap-to-advance, auto-dismissing after ~2s + a little per char.
- Bangers: `SPARKY ESCAPED!` = 152px (one line, just fits a band);
  `SPARKY LOVES TO SWIM!` = 214px, so it needs two lines.
  Luckiest Guy: `KIDS' BEDROOM` = 171px, the longest room name, so it
  barely fits a band.

**Colour.** Comic printing = flat colours + black ink. Stay in DawnLike's
DB16 palette (the critters already use it) with black outlines. Rooms get a
colour key by zone: indoor warm (reds/browns/lamp yellow), outdoor cold
(night blue, snow white), underground dark (near-black with glowing eyes).
Nearest-neighbour (`nn`) expansion keeps the 2px black outlines crisp and
inky; `epx` softens them. **DECIDED 2026-10-17: `nn`.**

## 4. The escape — storyboard

Each beat is a panel. Taps skip ahead; otherwise it plays through
(~8–10s total).

1. **Wide: the tree.** Tree, lights, presents underneath (reuse the
   ornament-mode tree). Calm. One box starts to **rock** (x-jitter of a
   couple of px, alternating) with **wiggle lines** either side.
   Small SFX: `RATTLE!`
2. **Cut to close-up** on that box (3x). It **pulses** bigger/smaller. A `!`
   pops above it.
3. **`POP!`** burst — the lid flies up and off the top of the panel. Two
   eyes peek over the rim (critter sprite layered *between* the box's back
   and front, so the box front hides its lower half).
4. **Extreme close-up** of the critter (animated 2-frame idle), name as a
   title: `SPARKY!`
5. **It bolts.** The box **tips over** (a pre-rotated frame made at build
   time), the critter dashes for an edge with **speed lines** and a
   **dust puff**: `ZOOM!`
6. **Caption:** `SPARKY ESCAPED!` — then a second caption, the **clue**:
   `SPARKY LOVES TO SWIM!`
7. **Back to the wide shot.** That box now sits tipped over, lid off,
   empty — a persistent "who's missing" display with no HUD.

## 5. Clues

> **Superseded 2026-10-17.** Chris widened this. Clues go wherever they
> make sense, as text by default or as an image when there's a fitting one.
> They're paired with per-critter map gating. See `EPISODES.md` §4. The
> split below survives only as one pattern among several.

### Original proposal: the clue split

Two kinds of clue, so the two-part fetch has two little mysteries:

- **Where it went** — given at escape time, as a *habit*:
  `SPARKY LOVES TO SWIM!` -> Pond. (`LOVES THE DARK` -> Cave,
  `LIKES TO CLIMB` -> Tree House...)
- **What lures it back** — revealed when you *find* it, as a **thought
  bubble with the item's icon** (no text). Then you go fetch the item.

This answers CRITTERS.md open question 3 with option (a), and makes the
escape caption do real work instead of just announcing.

## 6. Rooms as splash panels

The original sketch had rooms as 16x16 tile floorplans. In first person
that becomes a **tableau**: each room is one composed panel of 1–3 *iconic*
objects that say what the room is, drawn big (16x16/32x32 art at 2x–3x),
over the room's colour key — not a map you walk around in.

- Living Room: tree, presents, fireplace, cookies + milk.
- Kitchen: fridge, oven, cookie jar. Pond: frozen water, reeds, a log.
  Cave: dark, dripping, two glowing eyes. (Etc. — per-room list to come.)
- **Room name stays on screen**, as a comic *location caption* ("THE
  KITCHEN" in a small box), not a flash. Ch8 hardware testing already
  found that a transient toast is a poor answer to "what room am I in"
  (`cd-45v.3`, `cd-zw2.5`). That's why `nav_view.RoomLabel` is persistent
  today, at y=100, which is dead centre. The change here is only *where*
  it sits: centre is now where the art goes, so the label moves into a
  top caption box. Check on the device that it still reads, and that it
  doesn't collide with the UP edge marker.
- **First visit:** iris in, then 1–2 captions of story/flavour. **Revisits:**
  iris in, location caption only.
- **A hiding critter** is never fully visible: a tail sticking out from
  behind the log, eyes glowing in the dark, a bush with wiggle lines.
  Tap it -> `FOUND!` burst -> the critter pops out -> thought bubble.
- **Home again:** back under the tree, the critter hops in, the lid drops,
  a bow appears: `SPARKY'S HOME!`

## 7. What the extra animals are for

**DECIDED 2026-10-17:** the 39 look-test animals were culled to 15
(`CRITTERS.md` *Cull*). Five species escape: dog, cat, squirrel, reindeer,
robot. Each playthrough uses a random sprite from that species' variants.
The **birds and the owl are wild**. They're ambience where they help fill
out a scene (owl in the Tree House, birds in the Yard), and they make
"tap the thing that's moving" a real search rather than a giveaway.
Keeping them is nearly free: the sheet is read with `OnDiskBitmap`, so it
lives in flash (38KB of 16MB) and costs almost no RAM.

## 8. Technical notes

- **Layers** (displayio `Group`s, bottom to top): scene -> actors ->
  emanata -> balloons/captions/SFX -> iris -> nav edge markers.
- Integer `Group.scale` for shot sizes and pulses; no runtime rotation —
  tipped/rocked frames are made at build time by the tools script.
- Comic overlays should be one reusable module (caption, balloon, thought,
  burst, emanata) with a small "sequence player" that runs a list of timed
  beats with tap-to-skip — the escape, found, and home scenes are then
  just data.
- RAM to watch: each text label allocates its own bitmap; reuse a few
  labels rather than creating one per caption. This is the Ch7 lesson from
  `cd-yl4` (Label churn -> MemoryError) and `critter_demo.py` already
  avoids relabelling for the same reason.

## 9. Constraints from what's already built

- **Touch zones.** Edge navigation (`edge_gesture.EDGE_MARGIN` = 45px,
  tuned on hardware) claims everything within 45px of the square frame's
  edges, leaving a **150x150 centre square** for in-panel taps. So:
  - *Tap targets* (a bush to search, a box, an item) must sit in that
    centre square.
  - *Captions* in a top/bottom band sit inside an edge zone. While any
    caption or balloon is up, **a tap anywhere advances or dismisses it,
    and navigation is suspended** until the overlay clears. Otherwise
    tapping a bottom caption would walk you out of the room.
- **Edge-exit markers** (`nav_view`, colour-coded, confirmed on device)
  stay. They're the "which exits are live" answer from the original
  design. They and the location caption must share the top of the panel.
- **Actor placement** (`sprite_scale.clamp_actor_position`, 20px bezel
  margin) still applies to critters. The tableau art at 2x–3x is built
  with the existing `make_scenery_grid` (16x16 tiles), just on a scaled
  `Group`.
- **Not yet on hardware:** the Ch9 entry point (`cd-342.1`/`.2`) and the
  critter walk mode (`cd-342.3`) have only been run off-device. Run them
  on ws-1 before stacking the comic layer on top, so we don't debug both
  at once.

## 10. Where this lands in beads

| Bead | Relation to this doc |
|---|---|
| `cd-342.9` (new) | Comic overlay kit, sec 3/8, plus the nav-suspend rule in sec 9 |
| `cd-bp3.13` | Font port + RoomLabel font swap. **First step** of `cd-342.9` (blocks it) |
| `cd-342.10` (new) | Escape storyboard, sec 4. Needs `cd-342.9` + roster (`cd-342.3`); *triggered* by `cd-342.4` |
| `cd-342.11` (new) | Iris + location caption + first-visit story, sec 1/6. Changes `nav_view`'s label placement (`cd-342.2`) |
| `cd-342.3` | Roster: drop list from the look-test, `nn`/`epx`, clue text per critter (sec 5) |
| `cd-342.4` | Escape *trigger*, tap-to-find hidden critters, thought-bubble reveal, inventory (sec 5/6) |
| `cd-342.5` | Re-scoped: no hero sprite; tableau rooms + zone colours; extras as ambient wildlife (sec 6/7) |
| `cd-342.6` | Ending can reuse the overlay kit and the "home again" beat (sec 6); end game = whole map unlocked (`EPISODES.md` §6) |
| `cd-342.12` (new) | Per-critter episodes + map gating, `EPISODES.md`; closed exits show as blocked, with a reason on bump |
| `cd-342.13` (new) | Clue system, `EPISODES.md` §4 (supersedes sec 5 here) |
| `cd-342.8` | Its idle "critters stirring" idea = the rattling box from sec 4 beat 1 |
| `cd-342.7` | Playtest adds: caption legibility on the panel, overlay RAM (`gc.mem_free`) |
| `cd-zw2.2`, `cd-zw2.5`, `cd-45v.1/.3` (closed) | Source of the constraints in sec 9; nothing reopened |
