# Chapter 9 — CAD

The gift ornament's case parts (`cd-342.33`). Chapter 8's CAD
([`../../Chapter_8/cad`](../../Chapter_8/cad)) stays as it is; these files
build on it.

| file | what |
|---|---|
| `ornament_backplate.scad` | The gift backplate. Starts from Chapter 8's `deep_backplate_20mm.scad` (same 20 mm cavity, screw wells and BOOT/RESET poke-tubes, so `../../Chapter_8/cad/button_extender_20mm.stl` still fits) and `include`s Chapter 8's `custom_backplate.scad` for the caliper-verified outline, screw pattern and notch. Adds: two Ø3 **hanging holes** through the top (notch) wall, 3 mm back from the notch centre and 4 mm either side (iterated in Bambu Studio from Ø2 at 8 and 8; moved 1 mm up toward the notch 2026-11-12); a **rounded back** (curves in 3.5 mm toward the back face, 45° overhang at the bed, no supports); and **open screw wells**, slotted on their outside edge from the back face to 10 mm above the screw head (8 mm until 2026-11-15); **corner bulges** (2026-11-15) -- that last 10 mm of each well is a closed sleeve (1.2 mm wall) bulging 1.25 mm out past the wall up to the seat plane, with a ~63° cone below it and each slot's top a round arch instead of a flat bridge, so it prints smoothly (the wells sit so near the edge that the plain wall left a hairline gap there); and a **shorter, wider screw seat** (2026-11-12: Ø5.2 well, 1 mm wider for the driver, down to 1 mm short of the inner face, then a 1 mm countersink taper 4.5 → 2.5, instead of Ch8's 2 mm taper 4.0 → 2.0, so the screws reach the board). STL: `ornament_backplate.stl`; previews: `ornament_backplate_views.png`. Renders clean (one solid) on `arc-1`, last 2026-11-15; the corner bulges are **not yet printed**, and `backplate_ornament.3mf` (Bambu) is re-sliced from this STL. Print back face down. |

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
