// stock_backplate.scad — Chapter 8 / cd-bp3.6
// Parametric model of the STOCK Waveshare RP2350-Touch-LCD-1.28 backplate.
//
// PURPOSE
//   1. Baseline reference geometry the custom (bigger-battery) backplate will
//      be derived from.
//   2. A printable clone to compare against the real part before modifying it.
//
// ACCURACY
//   2026-09-06: rebuilt from Chris's caliper readings (see ../doc/CASE.md
//   "Caliper readings"). Values tagged MEAS are measured; EST are still
//   guesses. The outline is now a flatted disc (circle sliced top + bottom),
//   not a plain circle.
//
//   Known simplifications in this clone (expect these to show in the print):
//     - side profile modeled as a single circular arc (d = width_lr); the
//       straight edges then come out ~20 mm vs. 19.15 mm measured
//     - notch is a plain rectangular tab; closeups hint at a step/slot
//     - NO inner locating lip (unverified on the real part)
//     - holes are a straight cone with no cylindrical throat
//     - wall 2.0 vs. 2.15 measured
//
// COORDINATE FRAME / PRINT ORIENTATION
//   Origin at the plate center. X = left-right (width). Y = top-bottom, with
//   the notch on +Y ("top", opposite the USB-C edge). The flat OUTER (convex,
//   label) face sits on Z=0 — model is outer-face-DOWN, ready to print flat.
//   Material fills Z = 0..plate_th; the inner (concave) face is at Z=plate_th.
//   Screw cones open wide on the Z=0 (outer) face.

$fn = 200;

/* ============================ PARAMETERS ================================= */

// ---- plate body (MEAS 2026-09-06) ----
width_lr   = 46.5;   // MEAS overall left-right width (widest point of the sides)
flat_tb    = 42.0;   // MEAS top-flat -> bottom-flat, excludes notch (meas 42.4)
plate_th   = 2.0;    // MEAS wall thickness (meas 2.15; set to 2.15 for a truer clone)
edge_len_ref = 19.15; // MEAS straight-edge length — REFERENCE ONLY (see echo below)

// ---- rim notch: centered on the top (+Y) edge ----
notch_on   = true;
notch_w    = 4.5;    // MEAS width along the edge (meas 4.8)
notch_out  = 1.0;    // MEAS protrusion beyond the top flat

// ---- mounting holes: TRUE rectangle, confirmed symmetric (MEAS) ----
hole_dx    = 25.0;   // MEAS c-c of the top pair (== bottom pair), left-right
hole_dy    = 33.0;   // MEAS c-c of the left pair (== right pair), top-bottom
hole_d_out = 4.0;    // MEAS cone dia at the OUTER face
hole_d_in  = 2.0;    // MEAS cone dia at the INNER face

// ---- inner-face ribs: shallow grooves running along Y (MEAS pitch) ----
ribs_on    = true;
rib_pitch  = 2.1;    // MEAS (9 gaps measured over 18.9 mm)
rib_depth  = 0.3;    // EST — not measured
rib_w      = 0.6;    // EST — not measured

/* ============================ derived / helpers ========================== */

eps = 0.02;

module hole_positions() {
    for (sx = [-1, 1], sy = [-1, 1])
        translate([sx * hole_dx / 2, sy * hole_dy / 2, 0]) children();
}

// plate outline as a 2D shape: circle of dia width_lr, sliced flat top+bottom
module outline_2d() {
    intersection() {
        circle(d = width_lr);
        square([width_lr + 2, flat_tb], center = true);
    }
}

/* ================================ part =================================== */

module stock_backplate() {
    difference() {
        union() {
            // main flatted disc
            linear_extrude(height = plate_th) outline_2d();

            // top-edge notch (plain rectangular tab, overlapping into the body)
            if (notch_on)
                translate([-notch_w / 2, flat_tb / 2 - 1, 0])
                    cube([notch_w, notch_out + 1, plate_th]);
        }

        // screw cones — wide on the Z=0 outer face, narrow at the inner face
        hole_positions()
            translate([0, 0, -eps])
                cylinder(d1 = hole_d_out, d2 = hole_d_in, h = plate_th + 2 * eps);

        // inner-face ribs (grooves cut into the Z=plate_th face)
        if (ribs_on) {
            n = floor((width_lr - 4) / rib_pitch / 2);
            for (i = [-n : n])
                translate([i * rib_pitch - rib_w / 2, -flat_tb / 2 - 1,
                           plate_th - rib_depth])
                    cube([rib_w, flat_tb + 2, rib_depth + eps]);
        }
    }
}

stock_backplate();

/* ============================ sanity echoes ============================= */

// straight-edge length implied by the circle-arc side profile
implied_edge = 2 * sqrt(pow(width_lr / 2, 2) - pow(flat_tb / 2, 2));

echo(str("plate: ", width_lr, " (L-R) x ", flat_tb, " (T-B, +", notch_out,
         " notch) x ", plate_th, " thick  [mm]"));
echo(str("implied straight-edge length: ", implied_edge,
         " mm   (measured ", edge_len_ref, " mm)"));
echo(str("hole rectangle: ", hole_dx, " x ", hole_dy, " mm  (diagonal ",
         sqrt(hole_dx * hole_dx + hole_dy * hole_dy), " mm)"));
echo(str("hole center -> top/bottom flat: ", (flat_tb - hole_dy) / 2, " mm"));
