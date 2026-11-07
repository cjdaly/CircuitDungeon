#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Read a board's battery drain log over USB serial and report it -- cd-342.29.

    python3 Chapter_9/tools/drain_report.py /dev/cu.usbmodemXXXX [--ratio 3] [--csv out.csv]
    python3 Chapter_9/tools/drain_report.py /dev/cu.usbmodemXXXX --clear

Needs pyserial. Stops whatever the board is running (Ctrl-C) to reach the REPL;
reset the board afterwards. The log (game/drain_log.py) lives in nvm, so it
survived the battery dying; it only records when settings.toml has
POWER_LOG = "<minutes>".

Each boot starts a new run. For each run: how long it lasted, the voltage
curve, and a rough average current from the percent drop and BATTERY_MAH.
Voltage = raw / 65535 * 3.3 * ratio; the BAT_ADC divider is unconfirmed
(cd-bp3.6.1), x3 is the working guess. Readings above ~4.35 V mean USB power
was present (charging or full), so those runs say nothing about drain.
"""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "game"))
from drain_log import KIND_BOOT, records  # noqa: E402

# Rough 3.7 V LiPo curve, as Chapter_8/game/battery.py.
_CURVE = ((4.20, 100), (4.00, 90), (3.85, 75), (3.70, 50), (3.55, 25),
          (3.40, 10), (3.30, 5), (3.00, 0))
_USB_VOLTS = 4.35


def percent(volts):
    if volts >= _CURVE[0][0]:
        return 100.0
    for (v_hi, p_hi), (v_lo, p_lo) in zip(_CURVE, _CURVE[1:]):
        if v_lo <= volts <= v_hi:
            return p_lo + (volts - v_lo) / (v_hi - v_lo) * (p_hi - p_lo)
    return 0.0


def _repl(port, code, wait=4.0):
    import serial

    s = serial.Serial(port, 115200, timeout=0.2)
    s.write(b"\x03")
    time.sleep(0.3)
    s.write(b"\x03")
    time.sleep(0.5)
    s.write(b"\r\n")
    time.sleep(0.5)
    s.read(100000)
    s.write(code.encode() + b"\r\n")
    out = b""
    end = time.time() + wait
    while time.time() < end:
        out += s.read(65536)
    return out.decode(errors="replace")


def fetch(port):
    """(nvm bytes, BATTERY_MAH or None, DEVICE_ID or None) from the board."""
    out = _repl(port, "import microcontroller,binascii,os;print('NVM:'+binascii.hexlify("
                      "microcontroller.nvm[:]).decode()+':'+str(os.getenv('BATTERY_MAH'))"
                      "+':'+str(os.getenv('DEVICE_ID')))")
    for line in out.splitlines():
        if line.startswith("NVM:"):
            _, hexdata, mah, device = line.strip().split(":")
            return bytes.fromhex(hexdata), (None if mah == "None" else float(mah)), device
    sys.exit("no NVM line in the board's reply:\n" + out[-500:])


def runs(recs):
    """Split records into runs, one per boot."""
    out = []
    for rec in recs:
        if rec[0] == KIND_BOOT or not out:
            out.append([])
        out[-1].append(rec)
    return out


def report(data, ratio, mah, device, csv_path=None):
    recs = records(data)
    print("{}: {} records, {} runs (ratio x{}, {} mAh)".format(
        device, len(recs), len(runs(recs)), ratio, mah or "?"))
    rows = []
    for n, run in enumerate(runs(recs), 1):
        volts = [r[5] / 65535 * 3.3 * ratio for r in run]
        hours = run[-1][4] / 60
        print("\nrun {}: {:.1f} h logged, {:.2f} V -> {:.2f} V".format(
            n, hours, volts[0], volts[-1]))
        # Drain only counts from the first reading after USB power went away.
        on_usb = [i for i, v in enumerate(volts) if v > _USB_VOLTS]
        start = on_usb[-1] + 1 if on_usb else 0
        if start >= len(run) - 1:
            print("   (on USB power, or not long enough off it, to measure drain)")
        else:
            batt_hours = (run[-1][4] - run[start][4]) / 60
            drop = percent(volts[start]) - percent(volts[-1])
            print("   on battery from minute {}: {:.1f} h, {:.2f} V -> {:.2f} V, ~{:.0f}% used".format(
                run[start][4], batt_hours, volts[start], volts[-1], drop))
            if mah and batt_hours > 0:
                print("   -> roughly {:.1f} mA average (rough: voltage-curve percent)".format(
                    mah * drop / 100 / batt_hours))
        print("    min    volts   ~%   lit%  deep%")
        for rec, v in zip(run, volts):
            kind, lit, deep, seq, minutes, raw = rec
            print("   {:5d}   {:.3f}  {:3.0f}   {:3d}   {:3d}{}".format(
                minutes, v, percent(v), lit, deep, "  boot" if kind == KIND_BOOT else ""))
            rows.append((n, minutes, raw, round(v, 3), lit, deep))
    if csv_path:
        with open(csv_path, "w") as f:
            f.write("run,minutes,raw,volts,lit_pct,deep_pct\n")
            for row in rows:
                f.write(",".join(str(x) for x in row) + "\n")
        print("\nwrote", csv_path)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("port")
    ap.add_argument("--ratio", type=float, default=3.0, help="BAT_ADC divider ratio")
    ap.add_argument("--mah", type=float, help="battery capacity (default: BATTERY_MAH)")
    ap.add_argument("--csv", help="also write the records to this CSV file")
    ap.add_argument("--clear", action="store_true", help="erase the log (after showing it)")
    args = ap.parse_args()

    data, mah, device = fetch(args.port)
    report(data, args.ratio, args.mah or mah, device, args.csv)
    if args.clear:
        out = _repl(args.port, "import microcontroller;microcontroller.nvm[0:len("
                               "microcontroller.nvm)]=b'\\xff'*len(microcontroller.nvm);"
                               "print('CLEARED')")
        print("\nlog cleared" if "CLEARED" in out else "\nclear FAILED:\n" + out[-300:])
    print("\nThe board is at the REPL now: reset it to run the game again.")


if __name__ == "__main__":
    main()
