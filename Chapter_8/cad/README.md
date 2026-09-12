# Chapter 8 — CAD (`cd-bp3.6`)

OpenSCAD models for the custom backplate / case work.

| file | what |
|---|---|
| `stock_backplate.scad` | Parametric model of the **stock** Waveshare RP2350-Touch-LCD-1.28 backplate. Baseline for the custom part. Body + hole pattern + notch are **caliper-measured** (2026-09-06, see `../doc/CASE.md`); inner lip, standoff gap, and screw dims still TBD. Verified: printed replica screws on cleanly. |
| `custom_backplate.scad` | Flat stock body + BOOT/RESET Ø3 through-holes. Button positions **print-tested & confirmed** 2026-09-06 (`btn_down` 5.0→6.0). `include`s `stock_backplate.scad`. |
| `deep_backplate_6mm.scad` | The bigger-battery part, 6mm-deep variant. `include`s `custom_backplate.scad`; pushes the interior floor out by `extra_depth` (6mm), wraps it in a `shell`-thick (3mm) box, holds the 4 screws at the stock plane via recessed `well_d` (4.2) counterbores. BOOT/RESET bore: round Ø`btn_hole_d` for the first `btn_bore_lip` (1mm) at the back face, then a wider D (`btn_bore_wide_d` 4.5, keyed by a flat) the rest of the way, to fit `button_extender_6mm.scad` rods. STL: `deep_backplate_6mm.stl`. **Print outer-face-down (cavity up), no supports.** Body confirmed screw-fitted 2026-09-07; extender bore **confirmed working with both extender variants 2026-09-10.** Not yet: battery-connector cutout, power-cut feature. |
| `button_extender_6mm.scad` | Printed BOOT/RESET push-rods for the 6mm-deep backplate: a narrow D tip (fits the round lip, pokes out the back to press) + a wider D body (slides the wide bore; the tip→body shoulder can't pass back through the lip, so it's captured — drop in from the cavity side). `include`s `deep_backplate_6mm.scad` for the shared `d2d()` profile + fit dims. **Both current variants (`variants` list) print-tested and confirmed working 2026-09-10** — A snug/exact, B has slight play but works. STL: `button_extender_6mm.stl`. |
| `deep_backplate_20mm.scad` | Same part as `deep_backplate_6mm.scad`, just `extra_depth`=20mm instead of 6 — everything else (`include`s, screw wells, poke-tubes) is identical, only the derived Z values shift. STL: `deep_backplate_20mm.stl`. Renders clean (manifold) on `arc-1` 2026-09-12 but **not yet printed/screw-fitted** — deeper counterbore may need a longer driver shaft to reach it, untested. |
| `button_extender_20mm.scad` | Same rod design as `button_extender_6mm.scad`, `include`s `deep_backplate_20mm.scad` instead — the printed rod length auto-scales with `extra_depth` (body is ~14mm longer than the 6mm version), so the `variants` list is carried over unchanged as a starting point. STL: `button_extender_20mm.stl`. Renders clean 2026-09-12 but **not yet print-tested at this depth** — expect the same one-or-two round tuning the 6mm rods needed. |

## Rendering — done on `arc-1` (a networked Linux box)

`arc-1.local` has `openscad` **2021.01** (Debian trixie) + `xvfb` (installed
2026-09-05; OpenSCAD needs an X server for PNG export, none for STL).

Rendering runs on a separate networked Linux box over SSH. The connection
setup (host, user, SSH key) is local machine config, not part of this repo.
`arc1.local.env` (gitignored, next to this file) holds the `ARC1_HOST` /
`ARC1_USER` vars the commands below `source`; key auth is already configured,
so `ssh`/`scp` need no password. **If you cloned CircuitDungeon just for the
games, skip this section** — none of it is needed to build or run them.

```bash
source Chapter_8/cad/arc1.local.env   # sets ARC1_USER / ARC1_HOST
scp stock_backplate.scad "$ARC1_USER@$ARC1_HOST:~/cad/"
ssh "$ARC1_USER@$ARC1_HOST"

cd ~/cad
# STL (headless, ~18s on the Pi 5):
openscad -o stock_backplate.stl stock_backplate.scad
# PNG preview (needs xvfb):
xvfb-run -a openscad -o preview.png --imgsize=1100,1100 \
  --colorscheme=Tomorrow --viewall --autocenter --projection=o \
  --camera=0,0,0,55,0,25,0 stock_backplate.scad
```

## Status

- 2026-09-05: toolchain validated end-to-end (author on macOS → render on
  arc-1).
- 2026-09-06: `stock_backplate.scad` rebuilt from Chris's caliper readings —
  flatted disc (46.5 L-R × 42 T-B × 2), true-rectangle hole pattern 25 × 33,
  cone holes 4→2, notch + inner ribs. Printed replica **screws on cleanly.**
- 2026-09-06: `custom_backplate.scad` — BOOT/RESET Ø3 holes at (±11, +10.5).
  Printed, alignment **confirmed good.**
- 2026-09-06: `deep_backplate_6mm.scad` — first deep pass, `extra_depth`=6mm,
  `shell`=3mm. Poke-tubes then lengthened `btn_tube_up`=2mm toward the PCB.
- 2026-09-07: deep part **printed and screw-fitted — everything lines up.**
  `extra_depth` still expected to move (3–8mm) once the battery + Adafruit
  3922 pigtail are in hand.
- 2026-09-10: first extender attempt (flange + counterbore + slot) **didn't
  fit — reverted.** Replaced with a simpler two-diameter bore (round lip +
  wider D) and a matching two-diameter rod (`button_extender_6mm.scad`), tuned
  over two print rounds. **Both current variants confirmed working** — one
  snug/exact-length, one with slight play but functional. Still open
  (`../doc/CASE.md`): standoff gap, inner lip, battery-connector cutout,
  power-cut feature.
- 2026-09-12: renamed `button_extender.scad`→`button_extender_6mm.scad` and
  `deep_backplate.scad`→`deep_backplate_6mm.scad` to make room for a deeper
  variant. Added `deep_backplate_20mm.scad` (`extra_depth`=20mm) and
  `button_extender_20mm.scad` (auto-scaled rod length) — both render clean
  on `arc-1` but are **not yet printed/tested.**
