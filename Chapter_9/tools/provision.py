#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Program one Ch9 unit with the golden setup, then check it -- cd-342.32.

    python3 Chapter_9/tools/provision.py --id ws-10 --battery-product gift-350 \\
        --battery-mah 350 --player Test10

Needs pyserial. Plug in ONE unit to program (other CircuitPython boards on USB
are fine; they're told apart by which drive and serial port are new):

- A new board (factory firmware): hold BOOT while plugging in USB, so the
  RP2350 drive shows up. One time only.
- A board already running CircuitPython: just plug it in and pass --port;
  this script puts it into the bootloader itself.

Steps: flash the firmware in tools/golden.json, wait for its CIRCUITPY drive,
install exactly the golden libraries, write settings.toml, deploy game/ (which
also removes a new drive's code.py, which would otherwise run instead of
main.py), clear the nvm drain log, take a hardware fingerprint, reset, and
wait for "Ch9 ready". The fingerprint (chip IDs on the I2C bus, flash size,
the RP2350's unique ID, firmware) is saved to Chapter_9/units/<id>.json so
the units can be compared.
"""
import argparse
import glob
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
CH9 = os.path.dirname(HERE)
REPO = os.path.dirname(CH9)
DOWNLOADS = os.path.join(REPO, "downloads", "golden")  # gitignored
UNITS = os.path.join(CH9, "units")

_FINGERPRINT = r'''
import board, binascii, json, microcontroller, os, sys, time, hardware
from adafruit_bus_device.i2c_device import I2CDevice
fp = {"firmware": sys.implementation.version, "build": sys.implementation._build,
      "machine": sys.implementation._machine, "board_id": board.board_id,
      "uid": binascii.hexlify(microcontroller.cpu.uid).decode()}
st = os.statvfs("/")
fp["fs_kb"] = st[0] * st[2] // 1024
hardware.reset_touch()
fp["sda_clocks"] = hardware.clock_out_bus()
i2c = hardware.init_i2c()
while not i2c.try_lock():
    pass
fp["i2c"] = [hex(a) for a in i2c.scan()]
i2c.unlock()
def regs(addr, reg, n):
    for _ in range(5):
        try:
            b = bytearray(n)
            d = I2CDevice(i2c, addr, probe=False)
            with d:
                d.write_then_readinto(bytes((reg,)), b)
            return [hex(x) for x in b]
        except (OSError, ValueError, RuntimeError) as e:
            err = repr(e)
            time.sleep(0.02)
    return err
fp["imu_who_rev"] = regs(0x6B, 0x00, 2)
hardware.reset_touch()
fp["touch_chip_id"] = regs(0x15, 0xA7, 1)
fp["touch_fw"] = regs(0x15, 0xA9, 1)
i2c.deinit()
for i in range(len(microcontroller.nvm) // 512):
    microcontroller.nvm[i * 512:(i + 1) * 512] = b"\xff" * 512
fp["nvm_cleared"] = len(microcontroller.nvm)
print("FP:" + json.dumps(fp))
'''


def step(msg):
    print("\n== " + msg, flush=True)


def fetch(url, dest):
    if not os.path.exists(dest):
        print("downloading", url)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        urllib.request.urlretrieve(url, dest + ".part")
        os.rename(dest + ".part", dest)
    return dest


def volumes():
    return set(glob.glob("/Volumes/CIRCUITPY*"))


def ports():
    return set(glob.glob("/dev/cu.usbmodem*"))


def wait_for(what, check, timeout=60):
    end = time.time() + timeout
    while time.time() < end:
        found = check()
        if found:
            return found
        time.sleep(1)
    sys.exit("timed out waiting for " + what)


def serial_open(port):
    import serial

    return serial.Serial(port, 115200, timeout=0.2)


def to_repl(port):
    s = serial_open(port)
    s.write(b"\x03")
    time.sleep(0.3)
    s.write(b"\x03")
    time.sleep(0.5)
    s.write(b"\r\n")
    time.sleep(0.8)
    s.read(100000)
    return s


def run_paste(port, code, wait):
    """Run `code` at the REPL in paste mode; return everything printed."""
    s = to_repl(port)
    s.write(b"\x05")
    time.sleep(0.3)
    for line in code.strip("\n").split("\n"):
        s.write(line.encode() + b"\r")
        time.sleep(0.02)
    s.write(b"\x04")
    out = b""
    end = time.time() + wait
    while time.time() < end:
        out += s.read(65536)
        if b"FP:" in out and out.rstrip().endswith(b">>>"):
            break
    s.close()
    return out.decode(errors="replace")


def reset(port):
    s = to_repl(port)
    s.write(b"import microcontroller; microcontroller.reset()\r\n")
    time.sleep(0.5)
    try:
        s.close()
    except OSError:
        pass


def write_settings(volume, values):
    """Set these keys in settings.toml, keeping any other lines."""
    path = os.path.join(volume, "settings.toml")
    lines = open(path).read().splitlines() if os.path.exists(path) else []
    kept = [ln for ln in lines if ln.split("=")[0].strip() not in values]
    kept += ['{} = "{}"'.format(k, v) for k, v in values.items()]
    with open(path, "w") as f:
        f.write("\n".join(kept) + "\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--id", required=True, help="DEVICE_ID, e.g. ws-10")
    ap.add_argument("--battery-product", required=True)
    ap.add_argument("--battery-mah", required=True)
    ap.add_argument("--player", required=True, help="PLAYER, the recipient's name")
    ap.add_argument("--port", help="serial port, if the board already runs CircuitPython")
    args = ap.parse_args()
    golden = json.load(open(os.path.join(HERE, "golden.json")))

    step("downloads")
    fw = golden["firmware"]
    uf2 = fetch(fw["url"], os.path.join(DOWNLOADS, os.path.basename(fw["url"])))
    zip_path = fetch(golden["bundle"]["url"],
                     os.path.join(DOWNLOADS, os.path.basename(golden["bundle"]["url"])))
    bundle_dir = zip_path[:-4]
    if not os.path.isdir(bundle_dir):
        zipfile.ZipFile(zip_path).extractall(os.path.dirname(zip_path))
    lib_src = os.path.join(bundle_dir, "lib")

    step("flash CircuitPython " + fw["version"])
    vols_before, ports_before = volumes(), ports()
    if args.port:
        ports_before.discard(args.port)
        s = to_repl(args.port)
        s.write(b"import microcontroller; microcontroller.on_next_reset("
                b"microcontroller.RunMode.UF2); microcontroller.reset()\r\n")
        time.sleep(0.5)
        try:
            s.close()
        except OSError:
            pass
        for v in list(vols_before):  # its drive goes away and comes back
            if not os.path.exists(v):
                vols_before.discard(v)
    boot = wait_for("the RP2350 bootloader drive", lambda: os.path.isdir("/Volumes/RP2350"), 30)
    vols_before = volumes()
    shutil.copy(uf2, "/Volumes/RP2350/")
    volume = wait_for("a new CIRCUITPY drive",
                      lambda: next(iter(volumes() - vols_before), None), 90)
    wait_for("boot_out.txt", lambda: os.path.exists(os.path.join(volume, "boot_out.txt")))
    time.sleep(2)
    banner = open(os.path.join(volume, "boot_out.txt")).readline().strip()
    print(volume, "->", banner)
    if fw["version"] not in banner:
        sys.exit("wrong firmware on the board: " + banner)

    step("libraries")
    lib = os.path.join(volume, "lib")
    shutil.rmtree(lib, ignore_errors=True)
    os.makedirs(lib)
    for name in golden["bundle"]["libs"]:
        src = os.path.join(lib_src, name)
        (shutil.copytree if os.path.isdir(src) else shutil.copy)(src, os.path.join(lib, name))
    for rel in golden["vendored_libs"]:
        shutil.copy(os.path.join(REPO, rel), lib)
    print(sorted(os.listdir(lib)))

    step("settings.toml")
    values = {"DEVICE_ID": args.id, "BATTERY_PRODUCT": args.battery_product,
              "BATTERY_MAH": args.battery_mah, "PLAYER": args.player}
    values.update(golden["settings"])
    write_settings(volume, values)
    print(open(os.path.join(volume, "settings.toml")).read().strip())

    step("deploy game/")
    for stray in ("code.py", "code.txt", "main.txt"):  # these run instead of main.py
        if os.path.exists(os.path.join(volume, stray)):
            os.remove(os.path.join(volume, stray))
            print("removed", stray)
    subprocess.run([os.path.join(HERE, "deploy.sh"), "--no-eject", volume], check=True,
                   stdout=subprocess.DEVNULL)
    subprocess.run(["sync"], check=True)
    diff = subprocess.run(
        ["diff", "-rq", "--exclude", "lib", "--exclude", "sd", "--exclude", "boot_out.txt",
         "--exclude", "settings.toml", "--exclude", ".*", "--exclude", "__pycache__",
         os.path.join(CH9, "game"), volume], capture_output=True, text=True)
    if diff.returncode:
        sys.exit("game files differ from the repo:\n" + diff.stdout)
    print("game files identical to the repo")
    subprocess.run(["diskutil", "eject", volume], check=True, stdout=subprocess.DEVNULL)

    step("fingerprint + clear the drain log")
    port = wait_for("its serial port", lambda: next(iter(ports() - ports_before), None), 30)
    print("port", port)
    reset(port)  # run the freshly written code once, with autoreload now off
    time.sleep(6)
    out = run_paste(port, _FINGERPRINT, 25)
    line = next((ln for ln in out.splitlines() if ln.startswith("FP:")), None)
    if line is None:
        sys.exit("no fingerprint:\n" + out[-1500:])
    fp = json.loads(line[3:])
    fp.update({"device_id": args.id, "battery": args.battery_product,
               "battery_mah": args.battery_mah, "provisioned": time.strftime("%Y-%m-%d %H:%M"),
               "golden": {"firmware": fw["version"], "bundle": golden["bundle"]["date"]}})
    os.makedirs(UNITS, exist_ok=True)
    with open(os.path.join(UNITS, args.id + ".json"), "w") as f:
        json.dump(fp, f, indent=2, sort_keys=True)
        f.write("\n")
    print(json.dumps(fp, indent=2, sort_keys=True))

    step("start the game")
    reset(port)
    time.sleep(2)
    s = wait_for("the port after reset", lambda: os.path.exists(port) and serial_open(port), 30)
    out = b""
    end = time.time() + 25
    while time.time() < end and b"Ch9 ready" not in out:
        out += s.read(4096)
    text = out.decode(errors="replace")
    print("\n".join(ln for ln in text.splitlines() if "ticks=" not in ln and ln.strip())[-800:])
    if "Ch9 ready" not in text:
        sys.exit("FAILED: no 'Ch9 ready' within 25 s")
    print("\n{} is provisioned: {} on CircuitPython {}".format(args.id, args.player, fw["version"]))


if __name__ == "__main__":
    main()
