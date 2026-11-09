# Chapter 9 — CAD

The gift ornament's case parts (`cd-342.33`). Chapter 8's CAD
([`../../Chapter_8/cad`](../../Chapter_8/cad)) stays as it is; these files
build on it.

| file | what |
|---|---|
| `ornament_backplate.scad` | The gift backplate. Starts from Chapter 8's `deep_backplate_20mm.scad` (same 20 mm cavity, screw wells and BOOT/RESET poke-tubes, so `../../Chapter_8/cad/button_extender_20mm.stl` still fits) and `include`s Chapter 8's `custom_backplate.scad` for the caliper-verified outline, screw pattern and notch. Adds: two Ø3 **hanging holes** through the top (notch) wall, 4 mm back from the notch centre and 4 mm either side (iterated in Bambu Studio from Ø2 at 8 and 8); a **rounded back** (curves in 3.5 mm toward the back face, 45° overhang at the bed, no supports); and **open screw wells**, slotted on their outside edge from the back face to 8 mm above the screw head. STL: `ornament_backplate.stl`; previews: `ornament_backplate_views.png`. Renders clean (one solid) on `arc-1` 2026-11-08, **not yet printed.** Print back face down. |

## Rendering

As Chapter 8's [CAD README](../../Chapter_8/cad/README.md) (OpenSCAD 2021.01
on `arc-1`), but keep the two chapters' folders side by side so the
`include <../../Chapter_8/cad/...>` resolves:

```bash
source Chapter_8/cad/arc1.local.env   # sets ARC1_USER / ARC1_HOST
ssh "$ARC1_USER@$ARC1_HOST" 'mkdir -p ~/cad/ch9/Chapter_8/cad ~/cad/ch9/Chapter_9/cad'
scp Chapter_8/cad/{stock,custom}_backplate.scad "$ARC1_USER@$ARC1_HOST:~/cad/ch9/Chapter_8/cad/"
scp Chapter_9/cad/ornament_backplate.scad "$ARC1_USER@$ARC1_HOST:~/cad/ch9/Chapter_9/cad/"
ssh "$ARC1_USER@$ARC1_HOST" 'cd ~/cad/ch9/Chapter_9/cad && openscad -o ornament_backplate.stl ornament_backplate.scad'
```

About a minute and a half on the Pi 5.
