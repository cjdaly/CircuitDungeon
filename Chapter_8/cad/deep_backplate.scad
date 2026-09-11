// deep_backplate.scad — Chapter 8 / cd-bp3.6
// The custom backplate with a DEEPER interior for a bigger battery.
//
// Builds on custom_backplate.scad (-> stock_backplate.scad): same
// caliper-verified outline, mounting-hole rectangle, rim notch, and
// print-tested BOOT/RESET positions.
//
// WHAT THIS ADDS over the flat custom plate
//   - the interior (PCB-facing) floor is pushed OUT by `extra_depth`
//     (6 mm now; a knob to tune later — 3..8 mm expected) to make room
//     for a thicker battery + an Adafruit 3922-style pigtail once it
//     arrives and gets soldered on
//   - a `shell`-thick wall + floor around that new cavity
//   - 4 recessed screw wells: the screw drops down a `well_d` counterbore
//     to the ORIGINAL countersink + hole at the ORIGINAL plane, so the
//     same screws still reach the same PCB standoffs — nothing about the
//     screw path itself changes, only the material around it moved out
//   - BOOT/RESET poke-tubes: sealed `btn_hole_d` channels from the outer
//     face up to the seat plane, so a tool reaches the buttons without
//     passing through the battery compartment
//
// NOT MODELED YET (later passes, see ../doc/CASE.md)
//   - battery-connector / wire cutout + a no-disassembly power-cut feature
//   - printed button extenders (these are just open poke-tubes for now)
//   - exact standoff gap, any inner locating lip, outer-edge chamfer
//
// COORDINATE FRAME  (same as stock_backplate.scad)
//   +Z points INTO the device (toward the PCB). The seat plane region is
//   Z = 0 .. plate_th and is IDENTICAL to the stock plate there, so it
//   still indexes into the housing. Going outward (-Z):
//     Z = plate_th - extra_depth          -> cavity floor (top surface)
//     Z = plate_th - extra_depth - shell  -> device outer back face
//   PRINT OUTER FACE DOWN (cavity opens upward) — no supports needed.

as_include_custom = true;   // suppress custom_backplate's own render
                            // (custom_backplate.scad sets as_include for stock)
include <custom_backplate.scad>

/* ============================ PARAMETERS ================================= */

extra_depth = 6.0;   // extra interior depth vs. the flat stock plate. TUNABLE.
shell       = 3.0;   // new wall + floor thickness. TUNABLE.

well_d      = 4.2;   // screw-well counterbore dia (driver + head clearance;
                     //   open toward 4.5 if a #0 driver binds)
well_boss_d = 8.0;   // solid boss dia around each screw well

btn_wall    = 1.5;   // poke-tube wall thickness (-> OD = btn_hole_d + 2*btn_wall)
btn_tube_up = 2.0;   // extra poke-tube length ABOVE the seat plane, toward the
                     //   PCB — reaches past a nearby cable connector to the
                     //   button. Watch for a PCB/connector clash on the print.

// BOOT/RESET bore: a short round lip at the back surface, then a WIDER,
// D-shaped bore the rest of the way up.
btn_bore_lip    = 1.0;   // round Ø btn_hole_d kept at the outer (back) face
btn_bore_wide_d = 4.5;   // round part of the wider D bore past the lip
btn_bore_flat   = 1.0;   // how far the D's flat is cut in from the round edge

btn_boss_d  = btn_bore_wide_d + 2 * btn_wall;   // sized to the wide bore

deep_ribs   = false; // stock inner-face ribs are dropped on the deep part

/* ============================== derived ================================= */

floor_top  = plate_th - extra_depth;        // Z, cavity floor top surface
outer_face = floor_top - shell;             // Z, device outer back face
box_h      = plate_th - outer_face;         // total wall height (Z span)
btn_bore_flat_at = btn_bore_wide_d / 2 - btn_bore_flat;  // flat offset from axis

module cavity_2d() offset(r = -shell) outline_2d();

// D profile: a circle with one side flattened to a chord `flat_at` from the
// axis (flat faces -Y). Shared with button_extender.scad so bore and rod mate.
module d2d(dia, flat_at) {
    intersection() {
        circle(d = dia);
        translate([-dia, -flat_at]) square([2 * dia, 2 * dia]);
    }
}

// wider D bore past the lip
module btn_bore_wide_2d() d2d(btn_bore_wide_d, btn_bore_flat_at);

/* ================================ part ================================== */

module deep_backplate() {
    difference() {
        union() {
            // everything that must stay within the verified outline
            // footprint: the box + the internal bosses (bosses that reach
            // the rim get clipped flush to the edge, which is fine).
            intersection() {
                translate([0, 0, outer_face - 1])
                    linear_extrude(height = box_h + 2) outline_2d();

                union() {
                    // hollow box: full outline, cavity removed
                    difference() {
                        translate([0, 0, outer_face])
                            linear_extrude(height = box_h) outline_2d();
                        translate([0, 0, floor_top])
                            linear_extrude(height = plate_th - floor_top + 1)
                                cavity_2d();
                    }
                    // screw-well bosses: cavity floor -> seat plane
                    hole_positions()
                        translate([0, 0, floor_top])
                            cylinder(d = well_boss_d, h = plate_th - floor_top);
                }
            }

            // rim notch — seat-plane region only, unchanged from stock,
            // added AFTER the outline clip since it protrudes past the edge
            if (notch_on)
                translate([-notch_w / 2, flat_tb / 2 - 1, 0])
                    cube([notch_w, notch_out + 1, plate_th]);

            // BOOT/RESET poke-tube bosses — cavity floor up past the seat
            // plane by btn_tube_up. Outside the outline clip (they sit well
            // inboard) so btn_tube_up can exceed the box height.
            if (buttons_on)
                button_positions()
                    translate([0, 0, floor_top])
                        cylinder(d = btn_boss_d,
                                 h = plate_th - floor_top + btn_tube_up);
        }

        // ---- screw path: ORIGINAL countersink cone (Z 0..plate_th) ----
        hole_positions()
            translate([0, 0, -eps])
                cylinder(d1 = hole_d_out, d2 = hole_d_in,
                         h = plate_th + 2 * eps);

        // ---- screw-well counterbore: outer face up to the cone ----
        hole_positions()
            translate([0, 0, outer_face - eps])
                cylinder(d = well_d, h = -outer_face + eps);

        // ---- BOOT/RESET bores: round lip at the back face, then wider D ----
        if (buttons_on)
            button_positions() {
                // round Ø btn_hole_d lip at the outer (back) surface
                translate([0, 0, outer_face - eps])
                    cylinder(d = btn_hole_d, h = btn_bore_lip + eps);
                // wider D bore the rest of the way to the tube top
                translate([0, 0, outer_face + btn_bore_lip])
                    linear_extrude(box_h + btn_tube_up - btn_bore_lip + eps)
                        btn_bore_wide_2d();
            }
    }
}

// button_extender.scad sets as_include_deep=true to reuse the params + d2d()
if (is_undef(as_include_deep) || !as_include_deep) deep_backplate();

/* ============================ sanity echoes ============================= */

echo(str("DEEP: extra_depth ", extra_depth, " mm   shell ", shell, " mm"));
echo(str("cavity floor top  Z = ", floor_top,
         "   outer back face  Z = ", outer_face));
echo(str("overall thickness: ", box_h, " mm  (stock plate was ", plate_th, ")"));
echo(str("interior gained over the flat plate: ", extra_depth, " mm"));
echo(str("screw well: dia ", well_d, " x ", -outer_face,
         " mm deep down to the countersink"));
echo(str("battery-area rough clearance between the 4 wells: ",
         hole_dx - well_boss_d, " x ", hole_dy - well_boss_d,
         " mm  x ", extra_depth, " mm deep"));
echo(str("poke-tube: OD ", btn_boss_d, ", top at Z = ", plate_th + btn_tube_up));
echo(str("  bore: round ", btn_hole_d, " for the first ", btn_bore_lip,
         " mm, then D ", btn_bore_wide_d, " (flat ", btn_bore_flat_at,
         " off axis) -> boss wall ", (btn_boss_d - btn_bore_wide_d) / 2,
         " round / ", btn_boss_d / 2 - btn_bore_flat_at, " flat side"));
