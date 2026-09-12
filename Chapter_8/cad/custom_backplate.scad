// custom_backplate.scad — Chapter 8 / cd-bp3.6
// The CUSTOM backplate: derived from the verified stock model, adding
//   1. BOOT / RESET access
//   2. (later) a deeper cavity for a bigger battery, with the 4 mounting
//      points held back at the stock screw plane as recessed wells
//   3. (later) a way to cut battery power without disassembly
//
// STATUS — 2026-09-06
//   BOOT/RESET through-holes on the flat stock body. Positions print-tested
//   and confirmed good (btn_down 5.0 -> 6.0 after the first check). This
//   file stays the flat "buttons only" variant; the deeper cavity lives in
//   deep_backplate_6mm.scad / deep_backplate_20mm.scad, which include this one.
//
// Reuses every parameter + module from stock_backplate.scad. Set
// as_include_custom=true before `include <custom_backplate.scad>` to reuse
// its button params/module without drawing this (flat) part.

as_include = true;
include <stock_backplate.scad>

/* ===================== BOOT / RESET access holes ======================== */
// Positions measured 2026-09-06 relative to the two TOP mounting holes
// (BOOT under the left top hole, RESET under the right top hole):
//   - 5.0 mm "down"   = toward the bottom / -Y
//   - 1.5 mm "in"     = toward the plate center / X=0
// Kept relative to hole_dx/hole_dy so they track if the hole pattern moves.

buttons_on = true;
btn_hole_d = 3.0;    // MEAS-choice straight through-hole diameter
btn_down   = 6.0;    // MEAS center offset from the neighbour top screw hole, -Y
                     //   (was 5.0 in pass 1; +1.0 per Chris's 2026-09-06 print-check)
btn_in     = 1.5;    // MEAS center offset from the neighbour top screw hole, toward X=0

module button_positions() {
    for (sx = [-1, 1])
        translate([sx * (hole_dx / 2 - btn_in), hole_dy / 2 - btn_down, 0])
            children();
}

/* ================================ part ================================== */

module custom_backplate() {
    difference() {
        stock_backplate();

        if (buttons_on)
            button_positions()
                translate([0, 0, -eps])
                    cylinder(d = btn_hole_d, h = plate_th + 2 * eps);
    }
}

if (is_undef(as_include_custom) || !as_include_custom) custom_backplate();

/* ============================ sanity echoes ============================= */

btn_x = hole_dx / 2 - btn_in;
btn_y = hole_dy / 2 - btn_down;
echo(str("button centers: (+/-", btn_x, ", ", btn_y, ")  dia ", btn_hole_d));
echo(str("button center -> its top screw hole: ",
         sqrt(btn_in * btn_in + btn_down * btn_down), " mm  (screw cone r ",
         hole_d_out / 2, " + button r ", btn_hole_d / 2, " = ",
         hole_d_out / 2 + btn_hole_d / 2, " needed)"));
echo(str("button center -> top flat: ", flat_tb / 2 - btn_y, " mm"));
