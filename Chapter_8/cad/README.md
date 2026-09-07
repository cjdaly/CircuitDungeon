# Chapter 8 — CAD (`cd-bp3.6`)

OpenSCAD models for the custom backplate / case work.

| file | what |
|---|---|
| `stock_backplate.scad` | Parametric model of the **stock** Waveshare RP2350-Touch-LCD-1.28 backplate. Baseline for the custom part. Body + hole pattern + notch are **caliper-measured** (2026-09-06, see `../doc/CASE.md`); inner lip, standoff gap, and screw dims still TBD. Verified: printed replica screws on cleanly. |
| `custom_backplate.scad` | Flat stock body + BOOT/RESET Ø3 through-holes. Button positions **print-tested & confirmed** 2026-09-06 (`btn_down` 5.0→6.0). `include`s `stock_backplate.scad`. |
| `deep_backplate.scad` | The bigger-battery part. `include`s `custom_backplate.scad`; pushes the interior floor out by `extra_depth` (6mm now, tunable), wraps it in a `shell`-thick (3mm) box, holds the 4 screws at the stock plane via recessed `well_d` (4.2) counterbores, and runs sealed BOOT/RESET poke-tubes (`btn_tube_up` past the seat plane, `btn_wall` thick). STL: `deep_backplate_6mm.stl`. **Print outer-face-down (cavity up), no supports.** Printed & screw-fitted 2026-09-07. Not yet: battery-connector cutout, power-cut feature, extenders. |

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
- 2026-09-06: `deep_backplate.scad` — first deep pass, `extra_depth`=6mm,
  `shell`=3mm. Poke-tubes then lengthened `btn_tube_up`=2mm toward the PCB.
- 2026-09-07: deep part **printed and screw-fitted — everything lines up.**
  `extra_depth` still expected to move (3–8mm) once the battery + Adafruit
  3922 pigtail are in hand. Still open (`../doc/CASE.md`): standoff gap,
  inner lip, battery-connector cutout, power-cut feature.
