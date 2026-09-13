
# CircuitDungeon - Chapter 8 - Round and Round

Bring-up and experiments for the [Waveshare RP2350-Touch-LCD-1.28](https://circuitpython.org/board/waveshare_rp2350_touch_lcd_1_28/)
(a 240x240 **round** display). No buttons -- just a touchscreen and a 6-DoF
IMU (accel + gyro) for input. See [`doc/VISION.md`](doc/VISION.md) for the
original pitch.

This chapter is a **demo, not a game** -- it's where techniques for this
board get tried out and de-risked before landing in Chapter 9's actual
game, [`Christmas Critters`](../Chapter_9) (tracked in beads under `cd-zw2`).

## What's here

* **Device bring-up** -- round GC9A01A display, CST816 touch (shares the
  IMU's I2C bus, has a documented sleep/wedge quirk), QMI8658 IMU. Everything
  learned probing the board live is in [`doc/HARDWARE.md`](doc/HARDWARE.md).
* **Diagnostic HUD** (`game/main.py`) -- one combined screen: system info,
  live touch position + last tap/swipe gesture, live accel/gyro with derived
  tilt and shake detection. Deploy instructions in
  [`doc/DEPLOY.md`](doc/DEPLOY.md).
* **Custom backplate / case** (`cad/`) -- a bigger battery bay plus BOOT/RESET
  button access, replacing the stock backplate. Two depths: 6mm (sized for a
  150mAh battery) and 20mm (420mAh, print-confirmed). See
  [`doc/CASE.md`](doc/CASE.md) for the battery/connector plan and
  [`cad/README.md`](cad/README.md) for the OpenSCAD models themselves.
* **Battery monitoring** (`game/battery.py`) -- a first pass at reading
  `board.BAT_ADC` for a rough charge estimate. This board has no fuel-gauge
  IC, so it's a voltage-to-percent guess, not exact -- untested on-device.
* **Per-device config** (`tools/set_device_config.py`, `cd-bp3.7`) -- writes
  a device id (`ws-1`, `ws-monica`, ...) and battery product/mAh into the
  device's `settings.toml`, set once at unboxing and untouched by later
  deploys. Fleet-level record lives in `../rpi-fleet`'s `INVENTORY.md`.
* **Ch9 prototyping** (`game/rooms.py`, `game/edge_gesture.py`,
  `game/room_nav_demo.py`, `game/sprite_scale_demo.py`, `game/stillness.py`,
  `game/ornament_demo.py`) -- standalone experiments de-risking Ch9 design
  elements (room-to-room navigation, mixed sprite scales, ornament idle
  mode) before any real content or art exists. Off-device unit tests live in
  `tests/`. Each on-device demo has a walkthrough in
  [`doc/demos/`](doc/demos/README.md) -- deploy with `tools/deploy.sh --demo
  NAME` (see [`doc/DEPLOY.md`](doc/DEPLOY.md)).

## Layout

```
cad/       OpenSCAD backplate/case models + STLs (rendered on a networked
           Linux box -- see cad/README.md)
doc/       design docs -- desktop only (HARDWARE, CASE, DEPLOY, VISION)
game/      copied to CIRCUITPY, plus a couple of off-device-testable
           prototype modules (rooms.py, edge_gesture.py)
tests/     off-device unit tests -- `python3 tests/test_<name>.py`, no
           hardware or CircuitPython needed
tools/     deploy.sh, set_device_config.py
vendor/    third-party drivers not in the Adafruit bundle (qmi8658c.py)
pics/      reference photos
```

## Beads

Tracked under label `ch8`, two epics:

* `cd-bp3` -- Round touch/IMU diagnostic demo (bring-up, HUD, backplate/case)
* `cd-45v` -- Sprite/room/navigation prototyping for Ch9

`bd show cd-bp3` / `bd show cd-45v` for current status.
