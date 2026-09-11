// button_extender.scad — Chapter 8 / cd-bp3.6
// Printed BOOT/RESET push-rods for deep_backplate.scad's poke-tubes.
//
// Matches the two-diameter bore in the deep part:
//   - the case bore is round Ø btn_hole_d for the first btn_bore_lip mm at
//     the back face, then a WIDER D the rest of the way up
//   - so the rod is a narrow D TIP (fits the round lip, pokes ~tip_out mm
//     out the back to press on) then a WIDER D BODY (slides in the wide
//     bore). The tip->body shoulder can't pass back through the round lip,
//     so the rod is captured — drop it in from the cavity side.
//
//        press ──►  ▐ tip ▌████ body ████  ──► toward the switch
//                   (Ø<lip)     (Ø<wide bore, keyed by the flat)
//
// Each printed variant is a [over, tip_out] pair:
//   over     mm the body runs PAST the top of the poke-tube toward the
//            switch — this is what sets the actual reach/actuation point.
//   tip_out  mm the tip pokes past the back surface — just the external
//            press nub, does NOT change the reach (the tip/body seam is
//            pinned to the case's round-lip/wide-bore step).
// Printed left -> right in list order; test-fit to pick one.
//
// D shaft => prints flat-side-down, no supports, no bed knife-edge.

as_include_deep = true;   // deep_backplate.scad sets the custom/stock guards
include <deep_backplate.scad>

/* ============================ PARAMETERS ================================= */

// 2026-09-10: the over=1/tip_out=1.0 rod (previous shortest) was very close
// but a little too long. Two variations on it:
//   A: body 0.5 mm shorter                              -> over 0.5
//   B: body 1.0 mm shorter, tip (press nub) 0.5 mm longer -> over 0, tip_out 1.5
variants = [
    [0.5, 1.0],
    [0.0, 1.5],
];
layout_dx  = 8;           // spacing between rods on the bed

ext_clear  = 0.30;        // sliding clearance rod <-> bore (per side)

/* ============================== derived ================================= */

tube_top     = plate_th + btn_tube_up;               // Z, poke-tube inner end
tip_d        = btn_hole_d - 2 * ext_clear;           // fits the round lip
body_d       = btn_bore_wide_d - 2 * ext_clear;      // fits the wide D bore
body_flat_at = btn_bore_flat_at - ext_clear;         // flat inboard of the bore's
seam_z       = outer_face + btn_bore_lip;            // tip -> body shoulder (fixed)

/* ================================ parts ================================= */

// one rod, built "standing" on deep_backplate's Z axis (tip end -Z)
module extender_rod(over, tip_out) {
    tip_z0   = outer_face - tip_out;   // tip outer end
    body_top = tube_top + over;
    union() {
        // narrow D tip: pokes out the back, through the round lip
        translate([0, 0, tip_z0])
            linear_extrude(seam_z - tip_z0) d2d(tip_d, body_flat_at);
        // wider D body: slides the wide bore, runs `over` mm past the tube
        translate([0, 0, seam_z])
            linear_extrude(body_top - seam_z) d2d(body_d, body_flat_at);
    }
}

// rotated flat-side-down and lifted so the flat sits on Z=0
module extender_rod_printable(over, tip_out) {
    translate([0, 0, body_flat_at])
        rotate([90, 0, 0])
            extender_rod(over, tip_out);
}

for (i = [0 : len(variants) - 1])
    translate([i * layout_dx, 0, 0])
        extender_rod_printable(variants[i][0], variants[i][1]);

/* ============================ sanity echoes ============================= */

echo(str("tip: D ", tip_d, " (in round lip ", btn_hole_d, ")"));
echo(str("body: D ", body_d, " (in wide bore ", btn_bore_wide_d,
         "), shoulder catches the lip -> captured"));
for (v = variants)
    echo(str("  variant over=+", v[0], " tip_out=", v[1],
             ": body top (contact point) at Z = ", tube_top + v[0],
             "  (", tube_top + v[0] - outer_face,
             " mm below the back surface);  tip pokes ", v[1], " mm out"));
