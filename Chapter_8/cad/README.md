# Chapter 8 — CAD (`cd-bp3.6`)

OpenSCAD models for the custom backplate / case work.

| file | what |
|---|---|
| `stock_backplate.scad` | Parametric model of the **stock** Waveshare RP2350-Touch-LCD-1.28 backplate. Baseline for the custom part. **All dims are photo estimates** — see the header and `../doc/CASE.md`. |

## Rendering — done on `arc-1` (the fleet Pi assigned to this repo)

`arc-1.local` has `openscad` **2021.01** (Debian trixie) + `xvfb` (installed
2026-09-05; OpenSCAD needs an X server for PNG export, none for STL).

Login details are **not in this (public) repo** — see `arc1.local.env`
(gitignored, next to this file) or `../../../rpi-fleet/INVENTORY.md` (a
private, non-pushed repo). The fleet is LAN-only behind a home router.

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

The fleet uses password SSH (creds in `arc1.local.env` / `../../../rpi-fleet`).
From this Mac there's no `sshpass`; wrap it with `expect`, or just type the
password when prompted.

## Status

- 2026-09-05: toolchain validated end-to-end (author on macOS → render on
  arc-1). `stock_backplate.scad` is a **rough first pass from photos only** —
  every dimension is a guess pending calipers (`../doc/CASE.md` checklist).
