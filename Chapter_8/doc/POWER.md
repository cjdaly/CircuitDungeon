# Chapter 8 — Power management research (cd-ork)

This board has no physical power switch (`doc/HARDWARE.md` "Power /
battery") — once a battery's connected, it runs continuously. `cd-ork.1`/
`.2` already ship the cheap fix: blank `board.LCD_BL` (a plain GPIO
backlight pin, independent of the display driver) after an idle timeout,
wake instantly on activity. This doc is `cd-ork.3`'s research into whether
going further — real CPU/peripheral sleep via CircuitPython's `alarm`
module — is worth pursuing on top of that. Desk research only (2026-09-13),
no on-device confirmation yet; see "Open follow-ups" below.

## Findings

**1. Does `alarm` (light/deep sleep) even work on this board?** Unsettled.
A CircuitPython GitHub issue reporting `alarm` missing on RP2350 firmware
was closed "not planned"; separately, a Pimoroni forum thread reports
light/deep sleep working on RP2350 boards via a third-party patch
(`proveskit/circuitpython-pico2-sleep`), not necessarily in mainline
Adafruit CircuitPython. **Whether our exact build (Adafruit CircuitPython
10.2.1, 2026-05-13) has a working `alarm` module is unconfirmed** — a
30-second `help('modules')` / `import alarm` check next time a board's
connected would settle it.

Semantics, where it does exist (well-established CircuitPython behavior):
**light sleep** pauses in place and preserves RAM/running state; **deep
sleep** exits the program entirely and restarts `main.py` from scratch on
wake, no state preserved.

**2. Can it wake specifically on touch?** No. Alarm wake sources are
`TimeAlarm` (timer), `PinAlarm` (a real GPIO edge), and `TouchAlarm`
(native capacitive-touch *pins*, e.g. ESP32-S2 — not an I2C touch
*controller* like our CST816). The CST816 has **no interrupt pin wired out
on this board** (`irq_pin=None` is the only option from `board`'s pin
list, already confirmed in `doc/HARDWARE.md`) — no GPIO signal exists to
wake on. The only usable wake source here is a timer: "wake every N
seconds, poll touch briefly, sleep again if nothing." That's *less*
touch-responsive than the current always-awake, backlight-blanked approach
(touch polled every ~50ms), not more.

**3. Power-draw ballpark.** RP2350 bare-metal-SDK figures: ~22mA active →
~1-3.5mA in SDK sleep/dormant → ~0.65-0.85mA in the newer "powman"
power-down mode (CircuitPython's own overhead is unquantified but likely
sits above these bare-metal numbers). The GC9A01A is an ILI9341-class
controller that generally supports a chip-level sleep command, but **the
`adafruit_gc9a01a` CircuitPython driver doesn't expose it** — using it
would mean raw bus commands, for uncertain gain over backlight-off alone
(the backlight LED is very likely the dominant power draw of the display
subsystem, not the panel logic). CST816/QMI8658C idle-current figures:
**not documented anywhere findable** — genuinely unknown without a
multimeter measurement on this exact board.

**4. Re-init cost/risk on wake.** Deep sleep's full restart-on-wake is
directly analogous to a soft reboot — every wake re-runs
`hardware.init_i2c()`/`init_display()`/etc, the same pattern already
documented as **wedging the shared I2C bus when repeated quickly**
(`doc/HARDWARE.md`). Risk plausibly scales with wake *frequency*: one
infrequent sleep/wake (minutes apart) looks very different from a
timer-poll scheme waking every few seconds, which reproduces the
documented risky pattern almost exactly. This is inference from our own
documented failure mode, not confirmed for deep-sleep specifically — deep
sleep might power-cycle peripherals more thoroughly than a soft reboot
does, which could make it *less* wedge-prone, not more. Untested either
way. Light sleep avoids this (no restart), but per #2 still can't wake on
touch.

## Recommendation

**Backlight-only blanking (`cd-ork.1`/`.2`) is the right stopping point for
now.** This board has no hardware path to wake specifically on touch via
`alarm` — real sleep can't deliver the one thing that would matter most,
only timer-based polling that the current approach already matches or
beats. `alarm` support itself is unconfirmed on this firmware. Deep
sleep's restart-on-wake risks the known I2C wedge for an unsized power
gain (peripheral idle-current figures don't exist to even estimate the
payoff). The backlight is very likely the dominant cuttable draw, and
that's already done.

## Open follow-ups (cheap, do opportunistically)

- Confirm `alarm` module presence next time a board's connected —
  `help('modules')` or `import alarm`, ~30 seconds (`cd-ork.4`).
- Piggyback a rough current-draw measurement (backlight off vs. fully
  idle) on the multimeter session already planned for `cd-bp3.6.1`'s
  battery-ADC calibration — would tell us whether chasing deeper sleep is
  even worth revisiting later.

## Sources

- [proveskit/circuitpython-pico2-sleep](https://github.com/proveskit/circuitpython-pico2-sleep)
- [Adafruit Learn: Deep Sleep with CircuitPython — Alarms and Sleep](https://learn.adafruit.com/deep-sleep-with-circuitpython/alarms-and-sleep)
- [Adafruit Learn: Deep Sleep with CircuitPython — Overview](https://learn.adafruit.com/deep-sleep-with-circuitpython?view=all)
- [adafruit/circuitpython #9521 — RAM-preserving "deep" sleep option](https://github.com/adafruit/circuitpython/issues/9521)
- [Pimoroni forums: RP2350 low power modes](https://forums.pimoroni.com/t/rp2350-low-power-modes/27235)
- [adafruit/circuitpython #9920 — Alarm module not included for rp2350](https://github.com/adafruit/circuitpython/issues/9920)
- [Raspberry Pi forums: Trying to figure out Dormant on RP2350](https://forums.raspberrypi.com/viewtopic.php?t=378870)
- [Raspberry Pi forums: RPI pico 2 sleep mode](https://forums.raspberrypi.com/viewtopic.php?t=378659)
- [Adafruit CircuitPython GC9A01A Library docs](https://docs.circuitpython.org/projects/gc9a01a/en/latest/)
