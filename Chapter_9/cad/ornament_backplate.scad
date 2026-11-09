// ornament_backplate.scad — Chapter 9 / cd-342.33, cd-bp3.6.2
// The gift ornament's backplate. Started as a copy of
// ../../Chapter_8/cad/deep_backplate_20mm.scad (left as-is there), and
// still reuses Chapter 8's caliper-verified outline, screw pattern, notch
// and BOOT/RESET positions by including custom_backplate.scad from there.
// Same 20 mm deep cavity, screw wells and poke-tubes, so Chapter 8's
// button_extender_20mm.stl still fits.
//
// WHAT THIS CHANGES (Chris, 2026-11-08, after test-fitting the 350 mAh
// battery in a printed deep_backplate_20mm: fits, ~33 mm deep overall)
//   1. HANGING HOLES: two Ø3 holes through the top wall (the notch side),
//      4 mm back from the notch's centre and 4 mm either side of it, for a
//      ribbon or string loop.
//   2. ROUNDED BACK: the side walls curve in toward the back face, like a
//      bauble. The back face is on the print bed, so the curve is an
//      overhang; it starts at `round_max_deg` from vertical at the bed and
//      eases to vertical, so it prints without supports.
//   3. OPEN SCREW WELLS: each 21 mm deep screw well is slotted open on its
//      outside edge, from the back face down to `well_keep` above the screw
//      head, to make the screws easier to get at. The bottom `well_keep` mm
//      stays a closed tube to guide the screw onto its standoff.
//
// COORDINATE FRAME  (as Chapter 8's stock/deep backplates)
//   Origin at the plate centre. +Y = top (the notch, hanging-on-the-tree
//   up). +Z points INTO the device: Z = 0 .. plate_th is the seat plane
//   region that indexes into the housing, the screw heads sit flush at
//   Z = 0, and the back face is at Z = outer_face (negative).
//   PRINT BACK FACE DOWN (cavity opens upward), no supports.

as_include_custom = true;   // suppress custom_backplate's own render
include <../../Chapter_8/cad/custom_backplate.scad>

/* ============================ PARAMETERS ================================= */

// ---- carried over from deep_backplate_20mm.scad, unchanged ----
extra_depth = 20.0;  // extra interior depth vs. the flat stock plate
shell       = 3.0;   // wall + floor thickness
well_d      = 4.2;   // screw-well counterbore dia
well_boss_d = 8.0;   // solid boss dia around each screw well
btn_wall    = 1.5;
btn_tube_up = 2.0;
btn_bore_lip    = 1.0;
btn_bore_wide_d = 4.5;
btn_bore_flat   = 1.0;
btn_boss_d  = btn_bore_wide_d + 2 * btn_wall;

// ---- 1. hanging holes ----
hang_on     = true;
hang_d      = 3.0;   // hole dia (was 2)
hang_back   = 4.0;   // from the notch's centre toward the back face (8 -> 5 -> 3 -> 4, Chris 2026-11-08)
hang_across = 4.0;   // each side of the centre line (8 -> 5 -> 3 -> 4)

// ---- 2. rounded back ----
round_on      = true;
round_r       = 12.0; // radius of the curve. Bigger = taller, gentler curve
round_max_deg = 45;   // overhang at the bed, degrees from vertical (<= ~50)
round_steps   = 12;   // slices the curve is built from

// ---- 3. open screw wells ----
well_slot_on = true;
well_keep    = 8.0;   // closed tube left above the screw head (Z = 0)
well_slot_w  = well_d; // slot width; = well_d opens the well's outer half

/* ============================== derived ================================= */

floor_top  = plate_th - extra_depth;        // cavity floor top surface
outer_face = floor_top - shell;             // back face (on the print bed)
box_h      = plate_th - outer_face;
btn_bore_flat_at = btn_bore_wide_d / 2 - btn_bore_flat;
hang_z     = plate_th / 2 - hang_back;      // the notch spans Z 0..plate_th

round_h  = round_on ? round_r * sin(round_max_deg) : 0;        // curve height
round_in = round_on ? round_r * (1 - cos(round_max_deg)) : 0;  // inset at the bed

// How far the outline is pulled in at height dz above the back face: a
// circular arc, vertical at the top of the curve, round_max_deg at the bed.
function inset_at(dz) =
    (!round_on || dz >= round_h) ? 0
    : round_r - sqrt(round_r * round_r - (round_h - dz) * (round_h - dz));

module d2d(dia, flat_at) {
    intersection() {
        circle(d = dia);
        translate([-dia, -flat_at]) square([2 * dia, 2 * dia]);
    }
}
module btn_bore_wide_2d() d2d(btn_bore_wide_d, btn_bore_flat_at);

module slice(z, inset) {
    translate([0, 0, z]) linear_extrude(height = 0.01)
        offset(r = -inset) outline_2d();
}

// The outline swept from z0 to z1, pulled in by `extra` everywhere plus the
// rounded-back curve. The outline is convex, so hulling neighbouring slices
// gives a smooth wall.
module rounded_prism(z0, z1, extra) {
    curve_top = outer_face + round_h;
    if (round_on && z0 < curve_top) {
        top = min(z1, curve_top);
        for (i = [0 : round_steps - 1]) {
            za = z0 + (top - z0) * i / round_steps;
            zb = z0 + (top - z0) * (i + 1) / round_steps;
            hull() {
                slice(za, extra + inset_at(za - outer_face));
                slice(zb - 0.01, extra + inset_at(zb - outer_face));
            }
        }
    }
    straight = max(z0, outer_face + round_h);
    if (z1 > straight)
        translate([0, 0, straight]) linear_extrude(height = z1 - straight)
            offset(r = -extra) outline_2d();
}

/* ================================ part ================================== */

module ornament_backplate() {
    difference() {
        union() {
            // the shell: the rounded outline, less the cavity, except where
            // the screw-well bosses run from the floor up to the seat plane
            difference() {
                rounded_prism(outer_face, plate_th, 0);
                difference() {
                    rounded_prism(floor_top, plate_th + 1, shell);
                    hole_positions()
                        translate([0, 0, floor_top - 1])
                            cylinder(d = well_boss_d, h = plate_th - floor_top + 2);
                }
            }

            // rim notch, seat-plane region only, unchanged from stock
            if (notch_on)
                translate([-notch_w / 2, flat_tb / 2 - 1, 0])
                    cube([notch_w, notch_out + 1, plate_th]);

            // BOOT/RESET poke-tube bosses
            if (buttons_on)
                button_positions()
                    translate([0, 0, floor_top])
                        cylinder(d = btn_boss_d,
                                 h = plate_th - floor_top + btn_tube_up);
        }

        // screw path: the stock countersink cone at the seat plane...
        hole_positions()
            translate([0, 0, -eps])
                cylinder(d1 = hole_d_out, d2 = hole_d_in, h = plate_th + 2 * eps);
        // ...and the well from the back face down to it
        hole_positions()
            translate([0, 0, outer_face - eps])
                cylinder(d = well_d, h = -outer_face + eps);

        // 3. each well slotted open on its outside edge (pointing away from
        // the centre), back face to well_keep above the screw head
        if (well_slot_on)
            for (sx = [-1, 1], sy = [-1, 1])
                translate([sx * hole_dx / 2, sy * hole_dy / 2, outer_face - 1])
                    rotate([0, 0, atan2(sy * hole_dy, sx * hole_dx)])
                        translate([0, -well_slot_w / 2, 0])
                            cube([width_lr, well_slot_w, -well_keep - outer_face + 1]);

        // BOOT/RESET bores: round lip at the back face, then the wider D
        if (buttons_on)
            button_positions() {
                translate([0, 0, outer_face - eps])
                    cylinder(d = btn_hole_d, h = btn_bore_lip + eps);
                translate([0, 0, outer_face + btn_bore_lip])
                    linear_extrude(box_h + btn_tube_up - btn_bore_lip + eps)
                        btn_bore_wide_2d();
            }

        // 1. hanging holes through the top wall, along Y
        if (hang_on)
            for (sx = [-1, 1])
                translate([sx * hang_across, flat_tb / 2 - shell - 1, hang_z])
                    rotate([-90, 0, 0])
                        cylinder(d = hang_d, h = shell + notch_out + 2, $fn = 48);
    }
}

ornament_backplate();

/* ============================ sanity echoes ============================= */

echo(str("ORNAMENT: depth ", box_h, " mm (back face Z = ", outer_face,
         ", cavity floor Z = ", floor_top, ")"));
echo(str("rounded back: ", round_in, " mm in at the bed, curve ", round_h,
         " mm tall, ", round_max_deg, " deg max overhang"));
echo(str("hanging holes: dia ", hang_d, " at X = +/-", hang_across, ", Z = ", hang_z,
         " (", hang_back, " mm back from the notch centre)"));
echo(str("screw-well slots: back face to Z = ", -well_keep, " (", -well_keep - outer_face,
         " mm open, ", well_keep, " mm closed above the screw head)"));
