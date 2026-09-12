# SPDX-License-Identifier: MIT
"""Battery voltage/percentage estimate from board.BAT_ADC.

This board has no fuel-gauge IC (see doc/HARDWARE.md "Power / battery") --
only a charge/discharge chip (ETA6098) and a bare ADC pin. `board.BAT_ADC`
is in `dir(board)` alongside A0-A3, but nothing in the Adafruit bundle reads
it, and no CircuitPython library gives this hardware a battery-percentage
API. What follows is do-it-yourself: raw ADC counts -> volts at the pin,
then (assuming BAT_ADC taps the battery through a resistor divider, the
usual reason a board exposes a separate ADC pin instead of routing VBAT
straight to an input) volts-at-the-pin -> actual battery voltage via
_DIVIDER_RATIO, then voltage -> percent via a rough LiPo discharge curve.

STATUS: UNTESTED -- written from the pin's existence in dir(board), not a
live read. _DIVIDER_RATIO is a placeholder; see calibrate() below and the
cd-bp3.6 bead to try this on-device before trusting any number it returns.
"""
import analogio
import board

# PLACEHOLDER, not verified on this board -- assumes a straight 2:1 divider
# (a common choice: halves a ~4.2V max charge down under the 3.3V ADC
# ceiling). Calibrate with a multimeter: read raw_voltage() while metering
# the battery directly, then set this to metered_voltage / raw_voltage().
_DIVIDER_RATIO = 2.0  # TODO(cd-bp3.6): calibrate against a multimeter reading

# Rough 3.7V LiPo discharge curve (volts -> percent): flat in the middle,
# steep at both ends. Generic, not specific to either battery on hand
# (Adafruit 4236 or 1317) -- good enough for a HUD icon, not a fuel gauge.
# Sorted highest-voltage first.
_CURVE = (
    (4.20, 100),
    (4.00, 90),
    (3.85, 75),
    (3.70, 50),
    (3.55, 25),
    (3.40, 10),
    (3.30, 5),
    (3.00, 0),
)


class BatteryMonitor:
    """Poll-friendly wrapper: .read() -> {"voltage": V, "percent": 0-100}."""

    def __init__(self, divider_ratio=_DIVIDER_RATIO):
        self._adc = analogio.AnalogIn(board.BAT_ADC)
        self._divider_ratio = divider_ratio

    def raw_voltage(self):
        """Volts at the ADC pin itself, before the divider correction."""
        return self._adc.value / 65535 * self._adc.reference_voltage

    def read(self):
        voltage = self.raw_voltage() * self._divider_ratio
        return {"voltage": voltage, "percent": _voltage_to_percent(voltage)}


def _voltage_to_percent(voltage):
    if voltage >= _CURVE[0][0]:
        return 100
    if voltage <= _CURVE[-1][0]:
        return 0
    for (v_hi, p_hi), (v_lo, p_lo) in zip(_CURVE, _CURVE[1:]):
        if v_lo <= voltage <= v_hi:
            frac = (voltage - v_lo) / (v_hi - v_lo)
            return round(p_lo + frac * (p_hi - p_lo))
    return 0  # unreachable given the bounds checks above
