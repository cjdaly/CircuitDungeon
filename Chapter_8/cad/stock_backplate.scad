// stock_backplate.scad — Chapter 8 / cd-bp3.6
// Parametric model of the STOCK Waveshare RP2350-Touch-LCD-1.28 backplate.
//
// PURPOSE
//   1. Baseline reference geometry the custom (bigger-battery) backplate will
//      be derived from.
//   2. Toolchain smoke test: authored on macOS, rendered to STL with OpenSCAD
//      on arc-1.
//
// ACCURACY — READ THIS
//   EVERY dimension below is an EYEBALL ESTIMATE off the 2026-09-04 photos in
//   ../pics (PCB ruler in frame, ~7 px/mm). NOTHING here is caliper-verified.
//   See ../doc/CASE.md "Measurement checklist". Grep this file for "EST" to
//   find every guessed value — expect all of them to move once real numbers
//   land.
//
// COORDINATE FRAME / PRINT ORIENTATION
//   Origin at the plate center. The flat OUTER (convex, label) face sits on
//   the Z=0 plane — i.e. the model is oriented outer-face-DOWN, ready to print
//   flat on the bed. Material fills Z=0..plate_th. The inner locating lip and
//   the mounting bosses grow in +Z (into the case). Screw countersinks open
//   downward on the Z=0 face.
//
// The stock backplate design constraint (Chris, 2026-09-04): the 4 mounting
// points reach FIXED-height standoffs on the PCB, so in the custom part they
// must stay recessed bosses at THIS depth while the shell bulges out around
// them. This file models the stock (flat) baseline only.

$fn = 160;

/* ================= ESTIMATED PARAMETERS (replace with caliper data) ======= */

// ---- plate body ----
plate_od        = 40.5;   // EST overall outer diameter (backplate rim)
plate_th        = 2.0;    // EST flat wall thickness, outer face -> inner face
// Photos show the outer face is essentially FLAT (no dome). If a real crown
// turns up, add a shallow spherical cap on the -Z side here.

// ---- inner locating lip (nests inside the case shell) ----
// UNVERIFIED that this exists / its size — inner face is hard to read in the
// photos. Set lip_on=false if the stock plate is just flat.
lip_on          = true;
lip_h           = 0.8;    // EST height above the inner face
lip_th          = 1.0;    // EST radial wall thickness
lip_gap         = 0.6;    // EST inset of lip outer dia from plate_od

// ---- mounting holes: 4, rectangular pattern, symmetric about center ----
// Long axis (dy) ~ USB-C <-> LCD-FPC ; short axis (dx) ~ BOOT <-> BAT.
hole_dx         = 22.0;   // EST center-to-center, short axis
hole_dy         = 28.0;   // EST center-to-center, long axis
screw_clear_d   = 2.3;    // EST screw-shank through clearance (heads look ~M2)
csink_top_d     = 4.2;    // EST countersink major dia at the outer face
csink_depth     = 1.5;    // EST countersink depth (flat / countersunk head)

// ---- inner bosses around each hole (raised rings on the concave face) ----
boss_on         = true;
boss_d          = 5.0;    // EST outer dia
boss_h          = 1.5;    // EST height above the inner face (lands on PCB standoff)

// ---- rim notch ----
// A small stepped feature is visible at one point on the rim in the screw-hole
// closeups. Purpose unknown (strap lug? tool-pry slot? molding parting mark?).
// Modeled as a plain rectangular bite so it's at least represented.
notch_on        = true;
notch_w         = 4.0;    // EST width along the rim
notch_depth     = 1.5;    // EST radial bite depth
notch_angle     = 90;     // EST angular position (deg; 90 = +Y)

/* ============================ derived / helpers ========================== */

eps = 0.01;

module hole_positions() {
    for (sx = [-1, 1], sy = [-1, 1])
        translate([sx * hole_dx / 2, sy * hole_dy / 2, 0]) children();
}

module ring(od, wall, h) {
    difference() {
        cylinder(d = od, h = h);
        translate([0, 0, -eps]) cylinder(d = od - 2 * wall, h = h + 2 * eps);
    }
}

/* ================================ part =================================== */

module stock_backplate() {
    difference() {
        union() {
            // main disc
            cylinder(d = plate_od, h = plate_th);

            // inner locating lip
            if (lip_on)
                translate([0, 0, plate_th - eps])
                    ring(plate_od - 2 * lip_gap, lip_th, lip_h + eps);

            // inner bosses
            if (boss_on)
                hole_positions()
                    translate([0, 0, plate_th - eps])
                        cylinder(d = boss_d, h = boss_h + eps);
        }

        // screw through-holes (all the way through disc + boss)
        hole_positions()
            translate([0, 0, -eps])
                cylinder(d = screw_clear_d, h = plate_th + boss_h + 4 * eps);

        // countersinks, opening on the Z=0 (outer) face
        hole_positions()
            translate([0, 0, -eps])
                cylinder(d1 = csink_top_d, d2 = screw_clear_d,
                         h = csink_depth + eps);

        // rim notch
        if (notch_on)
            rotate([0, 0, notch_angle])
                translate([plate_od / 2 - notch_depth, -notch_w / 2, -eps])
                    cube([notch_depth + 2, notch_w, plate_th + 2 * eps]);
    }
}

stock_backplate();

/* ============================ sanity echoes ============================= */

echo(str("plate: OD ", plate_od, " mm  x thickness ", plate_th, " mm"));
echo(str("hole rectangle: ", hole_dx, " x ", hole_dy, " mm  (diagonal ",
         sqrt(hole_dx * hole_dx + hole_dy * hole_dy), " mm)"));
echo(str("inner face -> top of boss: ", plate_th + boss_h, " mm above outer face"));
echo(str("edge margin at nearest hole (short axis): ",
         (plate_od - hole_dx) / 2 - boss_d / 2, " mm to boss edge"));
