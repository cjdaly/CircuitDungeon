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

### Still open

- Inner locating lip / rim on the concave face — exists? size? (models treat it as **absent**)
- Standoff gap: outer face of plate → PCB underside when screwed down. NOT
  actually needed to *add* depth (the deep model keeps the screw path
  unchanged and just adds a well above the head), but it's the reference
  for "how much battery room did we start with".
- Screw: head dia, thread dia (looks M2), thread length, overall length;
  self-tap into plastic standoffs or brass inserts? — and whether a #0/#00
  driver reaches the head down the ~7 mm well (`well_d` opens to 4.5 if tight)
- USB-C / MX1.25 / SH1.0-GPIO connector positions vs. a hole → cutout in the
  deep shell for the battery lead + the Adafruit 3922 pigtail
- Deep part: does any back-side PCB component foul the seat-plane ring or the
  6 bosses? (all held at Z ≤ stock inner face, so no worse than stock — but
  unverified)

## Battery plan (Chris, 2026-09-06; parts confirmed 2026-09-12; wired + solder-tested 2026-09-13)

**Superseded 2026-09-13**: the Adafruit 1317 (150mAh) originally planned
below was swapped out before wiring -- what Chris actually has on hand and
has soldered is three batteries, all JST-PH (2-pin), which the board's
onboard MX1.25 BAT connector doesn't accept directly:

- [Adafruit 4236](https://www.adafruit.com/product/4236) — 3.7V 420mAh,
  35 × 24 × 5.2mm, 25mm lead. **Fits `deep_backplate_20mm.scad`** — printed
  and confirmed 2026-09-12, the biggest of the three the case has been sized
  around. Wired to `ws-2`.
- [Adafruit 1570](https://www.adafruit.com/product/1570) — 3.7V, listed as
  100mAh on the product title but the pack itself is printed **105mAh**
  (Chris confirmed by eye on the physical unit -- go with 105). Wired to
  `ws-1`. **Dimensions not yet checked against `deep_backplate_6mm.scad`**
  (that model was sized around the now-superseded 1317's 19.75 × 26.02 ×
  3.8mm, not the 1570's — needs calipers before assuming it fits).
- [Adafruit 4237](https://www.adafruit.com/product/4237) — 3.7V 350mAh.
  Currently a spare (not wired to a device). No case variant sized for it
  yet.

Adapter: [Adafruit 3922](https://www.adafruit.com/product/3922) — a 200mm,
28AWG **Molex PicoBlade (1.25mm pitch)** cable, connector on one end, bare
leads on the other (a short-cable 3922 is fine too since the leads get cut
to splice anyway). **Confirmed 2026-09-12: the 3922's connector plugs
straight into the board's BAT input** — no re-termination needed on that
side. **Polarity confirmed against the board's silkscreen: red = +, black =
-.** **Solder work DONE 2026-09-13**: all three batteries have a 3922
spliced/soldered on (red-to-red/black-to-black, JST-PH connector bypassed
entirely). Test-fired on both `ws-1` and `ws-2` — powered up, no smoke/fire.
This was cd-bp3.6.1's blocker; that bead is now unblocked for the on-device
divider-ratio calibration.

`extra_depth` is fixed at two variants rather than a single tunable knob:
`deep_backplate_6mm.scad` (sized for the now-superseded 1317 — fit against
the 1570 not yet confirmed) and `deep_backplate_20mm.scad` (sized for the
4236, confirmed 2026-09-12).

## BOOT / RESET on the deep part

The flat-part poke-holes would open straight into the battery compartment,
so `deep_backplate_6mm.scad`/`deep_backplate_20mm.scad` run each button hole up a sealed poke-tube from
the outer face, `btn_tube_up` past the seat plane toward the PCB (clears a
nearby connector).

**Printed push-rod extenders** (`button_extender_6mm.scad`) — working design as
of 2026-09-10, after one reverted attempt:

- First attempt used a retention flange riding in a counterbore + a "-"
  press tab — didn't fit when printed, scrapped.
- **Current design:** the bore is round Ø`btn_hole_d` for the first
  `btn_bore_lip` (1mm) at the back face, then widens to a D shape
  (`btn_bore_wide_d`, keyed by a flat) the rest of the way to the tube top.
  The rod matches: a narrow D **tip** (fits the round lip, pokes
  `tip_out` past the back surface — this is just the external press nub,
  it doesn't affect reach) then a wider D **body** (slides the wide bore,
  runs `over` mm past the tube top toward the switch — this sets the actual
  contact point). The tip→body shoulder can't pass back through the round
  lip, so the rod is self-captured: drop it into the tube from the cavity
  side before the PCB goes on.
- Reach is tuned via `over` (contact point) and `tip_out` (external nub),
  independently. **Two variants confirmed working 2026-09-10** (both in
  `button_extender_6mm.scad`'s `variants` list): one lands snug/exact, the
  other has slight play but actuates fine. Kept both as-is for now.

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
- [~] Each button's X/Y position: **5.0 mm toward the bottom (−Y) and
      1.5 mm toward center (X) from its neighbouring top screw hole.**
      With the 25×33 hole pattern that puts the centers at (±11.0, +11.5),
      i.e. 5.22 mm from the top screw hole, 9.5 mm from the top flat.
      Access holes modeled at Ø3.0 straight-through in
      `../cad/custom_backplate.scad` (pass 1) — pending print-test.
- [ ] Button diameter, recess depth below the board's top surface, and
      travel distance (only needed if we go to printed extenders)

**Ports/connectors the case must clear**
- [ ] USB-C port position + size
- [ ] 6-pin SH1.0 GPIO connector position + size
- [ ] MX1.25 battery connector position + size
- [ ] Anything else (speaker hole, SD slot, etc.)

**Battery (once purchased)**
- [ ] Length × width × thickness — the actual driver of how much bigger the
      cavity needs to be
