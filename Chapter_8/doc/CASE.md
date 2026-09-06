# Chapter 8 — Custom backplate / case (`cd-bp3.6`)

Reference photos and measurement notes for a custom 3D-printed backplate:
more interior room for a bigger battery than the stock one fits, reusing the
same 4 screws, plus BOOT/RESET button access (see `cd-bp3.6` for the full
requirements, and `doc/HARDWARE.md` "Power / battery" for why button access
alone doesn't cover the I2C-bus-wedge recovery case).

## Reference photos — 2026-09-04

![The stock backplate's outer (convex) face next to a PCB ruler for scale, with its 4 screws removed to either side. A "RP2350-1.28 Touch" label sticker is centered on it.](../pics/backplate-outside.jpg)

![The stock backplate (left, outer face) next to the opened board (right), both beside the ruler. The board shows the round LCD/touch module on its FPC connector at top, BOOT and RESET buttons flanking it, the QMI8658 IMU can (orange square), the USB-C port at bottom, and the BAT (MX1.25) connector.](../pics/board-open-outside-backplate.jpg)

![The same pairing, but showing the backplate's inner (concave) face -- ribbed/textured, thin -- next to the open board.](../pics/board-open-inside-backplate.jpg)

![Close-up on two of the backplate's 4 screw holes against the ruler, with one of the stock screws (small flat/countersunk head) resting beside them.](../pics/screw-holes-closeup-1.jpg)

![Same close-up, ruler repositioned for a clearer read of the hole spacing.](../pics/screw-holes-closeup-2.jpg)

## Design note from Chris (2026-09-04)

The stock backplate is uniformly **flat/thin** — that's how the 4 screws
(short, reaching fixed-height standoffs on the board) end up flush. If the
new backplate just adds depth everywhere for more battery room, the screws
won't reach the standoffs anymore. So the 4 mounting points need to stay
**recessed bosses** at the original stock depth (screw holes on small raised
pads reaching in to the same height the stock screws expect), while the
surrounding shell bulges outward around them for the bigger cavity. Capture
this as a real constraint in the `.scad` model, not just an afterthought.

## Measurement conventions (Chris, 2026-09-06)

Orientation terms for the caliper notes, looking at the **outer (convex,
label) face**:

- **Bottom** — the edge that lines up with the USB-C connector and the
  bottom of the round display. Straight across the middle, curving away at
  the rounded sides.
- **Top** — the opposite edge, also straight across the middle, with a
  small **notch** (stepped tab) protruding outward at its center. Clearest
  in `../pics/screw-holes-closeup-1.jpg` / `-2.jpg`.
- **Top–bottom axis** = the line between those two straight edges.
  **Left / right** = the perpendicular (rounded) sides.

So the plate outline is a **disc with two parallel flats** (top and
bottom), not a full circle. In `../cad/stock_backplate.scad`, `plate_od`
as a plain circle has to become circle ∩ slab, with the notch added at
top center.

## Caliper readings — 2026-09-06

| feature | reading | model value | notes |
|---|---|---|---|
| top flat → bottom flat (excl. notch) | 42.4 mm | **42.0** | flatted axis (Y) |
| left → right overall width | 46.5 mm | **46.5** | widest point of the curved sides (X) |
| top / bottom straight-edge length | 19.15 mm | (derived ≈20) | falls out of circle(46.5) ∩ slab(42); check on the print |
| wall thickness (outer → inner face) | 2.15 mm | **2.0** | uniform; stock plate is flat, no crown per photos |
| notch protrusion past top flat | ~1.0 mm | **1.0** | notch tip → bottom flat ≈ 43 mm |
| notch width along top edge | 4.8 mm | **4.5** | centered on the top edge; modeled as a plain rect tab (closeups hint at a step/slot — unmodeled) |
| mounting-hole pattern | TRUE rectangle | — | confirmed symmetric |
| hole c-c, top pair = bottom pair (X) | ~25 mm | **25.0** | |
| hole c-c, left pair = right pair (Y) | ~33 mm | **33.0** | diagonal ≈ 41.4 mm |
| hole profile | cone, no throat | **d 4.0 → 2.0** | 4 mm at outer face tapering to 2 mm at inner face, straight through |
| inner-face ribs | 9 gaps = 18.9 mm | pitch **2.1**, depth 0.3 (est) | shallow grooves running along Y (top–bottom); cosmetic, don't affect fit |

### Still open (needed before the *custom* part, not the clone)

- Inner locating lip / rim on the concave face — exists? size? (clone models it as **absent**)
- Standoff gap: outer face of plate → PCB underside when screwed down (the
  stock battery's available thickness; the number the custom part must beat)
- Screw: head dia, thread dia (looks M2), thread length, overall length;
  self-tap into plastic standoffs or brass inserts?
- Any raised boss around each hole on the inner face (clone: none)
- USB-C / MX1.25 / SH1.0-GPIO connector positions vs. a hole → shell cutouts

## Measurement checklist (calipers — pending, target: this weekend)

From the chat discussion: LiDAR/photogrammetry (Scaniverse/Polycam on the
iPhone 17 Pro) is fine for a general sense of shape but not trustworthy for
the screw-hole tolerances that matter here. Filling this in with real
caliper numbers once Chris has borrowed one.

**Screw holes**
- [ ] Hole diameter (all 4)
- [ ] Bolt-circle diameter (or adjacent/diagonal hole-to-hole distances if
      not evenly spaced)
- [ ] Distance from each hole to the nearest board edge
- [ ] Screw diameter and length
- [ ] Standoff height (how far the screw threads into the board)

**Board & stock backplate**
- [ ] Overall board diameter (or length×width)
- [ ] PCB thickness
- [~] Stock backplate: wall thickness **2.15 mm** (using 2.0); top–bottom
      **42.4 mm** excl. notch (using 42.0) + notch **~1.0 mm**. Still need:
      left–right width, side-arc radius, internal cavity depth. See the
      "Caliper readings" table above.
- [ ] Total assembled thickness, front glass to back of case

**Buttons (BOOT/RESET) — for extender design**
- [ ] Each button's X/Y position relative to a fixed reference point
- [ ] Button diameter, recess depth below the board's top surface, and
      travel distance

**Ports/connectors the case must clear**
- [ ] USB-C port position + size
- [ ] 6-pin SH1.0 GPIO connector position + size
- [ ] MX1.25 battery connector position + size
- [ ] Anything else (speaker hole, SD slot, etc.)

**Battery (once purchased)**
- [ ] Length × width × thickness — the actual driver of how much bigger the
      cavity needs to be
