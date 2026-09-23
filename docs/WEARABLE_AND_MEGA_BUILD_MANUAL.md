# ENDO-TWIN NEXUS — Wearable + Mega Hub Construction Manual
## ESP32-S3 DevKitC-1 wearable / BME280 / BH1750 / DS18B20 skin-contact probe / MAX30102 / MPU6050

**Document purpose:** This is the single physical-build reference for the current prototype. It covers the wearable enclosure, sensor placement, wiring, cable routing, skin-contact temperature probe, assembly measurements, ESP32-S3 firmware, the Arduino Mega hub, testing, and final acceptance.

**Step-by-step physical build:** `CARDBOARD_POD_BUILD.md` (cardboard, no battery, no screws,
with figures and a PPG contact test). This manual keeps the reference material: sensor
placement logic, wiring, firmware, bench hub, tests and acceptance.

**Wear site:** the pod is worn on the **wrist** or the **shoulder** (upper arm / deltoid). Placement changes what several channels mean, so the site is set for the session (`ENDO_TWIN_WEAR_SITE=wrist|shoulder`, default wrist) and shown beside the numbers. Mounting notes for both sites, and a per-measurement table, live in `docs/WEAR_SITES.md`.

**Prototype status:** educational/research hardware. It is not a medical device and the measurements are not diagnostic.

---

# 1. CURRENT HARDWARE ARCHITECTURE

The active hardware is split into two units:

1. **Wearable Pod**
   - ESP32-S3-DevKitC-1
   - MAX30102 PPG
   - MPU6050 IMU
   - BME280 environmental sensor
   - BH1750 ambient-light sensor
   - DS18B20 skin-temperature probe (skin contact, GPIO4)
   - external status LED
   - **USB power and data (no battery in v1)**

2. **Mega Hub / Lab Box**
   - Arduino Mega 2560
   - expanded bench sensors and test interfaces
   - USB connection to the ENDO-TWIN desktop workstation
   - optional OLED, buttons, buzzer, ECG, FSR, microphone and environmental sensors

The wearable and Mega are independent acquisition devices. They do not need to be physically wired together for normal operation.

---

# 2. WEARABLE POD — REFERENCE DIGEST

Physical build, cutting, folding and the PPG contact test live in **`CARDBOARD_POD_BUILD.md`**.
This is the short version of what matters when you change anything.

## Enclosure target

| Dimension | Target |
|---|---:|
| External | 60 x 40 x 18 mm (a matchbox) |
| Material | thin corrugated cardboard, 1.5-2 mm |
| Strap | 20-25 mm elastic through two slots |
| Probe lead | 150-350 mm, notch + internal slack |
| Power | thin USB-C cable, no battery |

The pod must be flat: only the PPG window and the temperature probe press on skin, and
nothing on the far side of the limb is rigid.

## Sensor placement

| Sensor | Position | Why |
|---|---|---|
| MAX30102 | flush in the skin face, Ø 12 mm window with a foam gasket | optical contact; the gasket seals ambient light |
| DS18B20 probe | 20-30 mm from the pod along the same limb, taped in the middle | skin contact without pressing on the PPG site |
| MPU6050 | rigidly on the board stack, pads keeping the pod level | motion must be the limb's, not the box's |
| BH1750 | lid window, facing out | must not sit behind a sleeve or against skin |
| BME280 | lid vents, away from the ESP32 | under clothing it measures microclimate, not the room |

Wrist: inner (volar) side over the artery, clear of the wrist bone. Upper arm: inner arm
1-2 cm above the elbow crease, over the brachial artery, found by touch first. Strap
tension: gasket compressed, skin not blanched. Full detail and the contact test are in
the build guide; site-specific measurement meanings are in `WEAR_SITES.md`.

## Wiring

| Device | Signal | ESP32-S3 |
|---|---|---|
| MAX30102 / MPU6050 / BME280 / BH1750 | SDA | GPIO8 |
| MAX30102 / MPU6050 / BME280 / BH1750 | SCL | GPIO9 |
| DS18B20 probe | DQ | GPIO4, 4.7 kΩ pull-up to 3V3 |
| Status LED | control | GPIO2 |

Addresses: MAX30102 0x57, MPU6050 0x68, BME280 0x76/0x77, BH1750 0x23/0x5C. Three-wire
(normal) power for the probe, not parasite power. Pin-level tables: `hardware/WIRING.md`.

## Power

v1 has **no battery**: one thin USB-C cable carries power and data, so nothing is
charged on the body and nothing needs to be swapped mid-session. If a battery is added
later, use a protected cell with a proper regulator, keep it out of the 20 mm near the
probe (heat bias), and keep body-contact sessions on an isolated, battery-only supply.

## Firmware and frame

- Source: `hardware/esp32s3/endo_twin_wearable/endo_twin_wearable.ino`
- Reads MAX30102 IR/red, MPU6050, the DS18B20 skin probe (non-blocking, once per second),
  BME280 and BH1750; 20 Hz `$CP3` frames with XOR CRC; USB serial; Wi-Fi SoftAP
  `ENDO-TWIN-S3` / `endotwins3`, TCP 7777; PING / WHOAMI / LED commands.
- Channels the board does not carry (microphone, ECG, FSR) are sent as `-1`, never as 0.
- Frame and status bits: `WIRE_FORMAT_CP3.md`.

Build and flash:

```bash
bash scripts/build/build_firmware.sh          # installs cores + libraries, then compiles
arduino-cli board list                        # find the port
arduino-cli upload -p /dev/ttyACM0 --fqbn esp32:esp32:esp32s3 hardware/esp32s3/endo_twin_wearable
```

## Test order

1. Board alone: powers on, serial works, no reset loop.
2. I2C scan: all four addresses present.
3. MAX30102: IR responds to covering the window; no permanent saturation.
4. MPU6050: axes respond to rotation.
5. BME280 / BH1750: plausible values, not blocked by the enclosure.
6. DS18B20: skin-range value, responds to fingers, `nan` + status bit 3 when unplugged,
   never a steady 85 °C.
7. `$CP3` frames at ~20 packets/second with a valid CRC.
8. Wi-Fi: phone joins the AP, TCP client connects, PING answers.
9. PPG contact test on the intended wear site (`CARDBOARD_POD_BUILD.md`, section 6).

# 15. MEGA HUB / LAB BOX

The Mega is a separate larger enclosure for bench testing.

## Recommended prototype box

| Dimension | Target |
|---|---:|
| Length | 180 mm |
| Width | 120 mm |
| Height | 55 mm |
| Front-panel usable width | ~165 mm |
| Rear cable area | 15–20 mm |

These are recommended fabrication dimensions, not a claim about a commercial box.

## Mega box front panel

Recommended layout:

```
┌─────────────────────────────────────────────────────────┐
│ ENDO-TWIN MEGA HUB                                     │
│                                                         │
│ [OLED 128x64]        [GREEN] [YELLOW] [RED]            │
│                                                         │
│ [MODE] [BASELINE] [POST]      [BUZZER]                │
│                                                         │
│ USB ───────────────────────────────────────────────►    │
└─────────────────────────────────────────────────────────┘
```

## Mega internal layout

```
┌─────────────────────────────────────────────────────────┐
│ USB opening                                             │
│                                                         │
│ ┌─────────────────┐    ┌─────────────────────────────┐ │
│ │ Arduino Mega    │    │ Sensor interface area       │ │
│ │ 2560            │    │ MAX30102 / BME280 / BH1750 │ │
│ └─────────────────┘    └─────────────────────────────┘ │
│                                                         │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ optional ECG / FSR / microphone connectors         │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│ cable strain relief + external sensor ports            │
└─────────────────────────────────────────────────────────┘
```

Do not put the Mega hub inside the wearable. It is deliberately a bench/lab controller.

---

# 16. MEGA HUB PIN MAP

Current Mega firmware uses:

| Function | Mega |
|---|---|
| I2C SDA | D20 |
| I2C SCL | D21 |
| DS18B20 | D2 |
| (GSR, A0) | retired - pin free, no firmware reads it |
| MAX4466 | A1 |
| AD8232 ECG OUT | A2 |
| FSR | A3 |
| ECG LO+ | D11 |
| ECG LO- | D12 |
| Mode button | D3 |
| Baseline button | D4 |
| Post button | D5 |
| Buzzer | D6 |
| Green LED | D8 |
| Yellow LED | D9 |
| Red LED | D10 |

All optional modules should be clearly labelled on the rear/front panel.

---

# 17. MEGA HUB ASSEMBLY

1. Mount Mega on four standoffs.
2. Leave USB access unobstructed.
3. Install OLED in the front panel.
4. Install three status LEDs.
5. Install buttons with labels.
6. Route I2C as a short trunk.
7. Route analog sensor wires away from high-current/power wires.
8. Add labelled sensor connectors.
9. Add cable strain relief.
10. Close the box only after the acceptance test passes.

Recommended connector labels:

- PPG
- IMU
- TEMP
- ECG
- FSR
- MIC
- BME280
- BH1750
- USB
- POWER

---

# 18. WEARABLE ↔ MEGA RELATIONSHIP

The normal topology is:

```
                ┌─────────────────────┐
                │ ESP32-S3 WEARABLE  │
                │ PPG / IMU / TEMP   │
                │ BME280 / BH1750    │
                └──────────┬──────────┘
                           │ Wi-Fi/TCP
                           ▼
                  Android / Desktop

                ┌─────────────────────┐
                │ ARDUINO MEGA HUB    │
                │ expanded bench I/O  │
                └──────────┬──────────┘
                           │ USB Serial
                           ▼
                         Desktop
```

The two controllers can be tested independently.

---

# 19. FINAL PHYSICAL ACCEPTANCE CHECKLIST

### Wearable

- [ ] enclosure approximately 60 × 40 × 18 mm (cardboard, per the build guide)
- [ ] ESP32-S3 firmly mounted
- [ ] USB accessible
- [ ] antenna area unobstructed
- [ ] MAX30102 faces skin
- [ ] MPU6050 rigidly mounted
- [ ] BME280 has ambient-air vent
- [ ] BH1750 has clear optical window
- [ ] probe cable notch strain relieved, slack loop inside the pod
- [ ] probe sites labelled in the session log
- [ ] all grounds common
- [ ] no exposed sharp conductive parts
- [ ] USB cable anchored at two points, pod cannot be tugged
- [ ] no loose wires

### Firmware

- [ ] ESP32-S3 firmware compiles
- [ ] board uploads successfully
- [ ] I2C sensors detected
- [ ] skin temperature responds to contact and drops when released
- [ ] CP3 CRC validates
- [ ] ~20 Hz packet stream
- [ ] Wi-Fi AP starts
- [ ] TCP 7777 accepts a client
- [ ] PING works
- [ ] WHOAMI reports ENDO-TWIN-ESP32S3-CP3

### Mega

- [ ] Mega uploads
- [ ] USB serial works
- [ ] OLED works if installed
- [ ] buttons work
- [ ] LEDs work
- [ ] buzzer works
- [ ] optional sensors individually tested
- [ ] all external connectors labelled

---

# 20. IMPORTANT DESIGN RULES

1. Do not mix the old ESP8266 pin map with this ESP32-S3 design.
2. Do not use GPIO numbers from an ordinary ESP32 DevKit for the ESP32-S3.
3. Do not use GPIO33–37 on variants where Espressif reserves them for internal flash/PSRAM. 

4. Keep BME280 thermally isolated from the ESP32 (and from any future battery).
5. Keep BH1750 optically exposed.
6. Keep the probe lead strain relieved and the pull-up resistor fitted.
7. Treat skin temperature as a contact-dependent research channel: it is not core
   temperature, and a loose probe reads the room, not the wearer.
7b. Keep one wear site per session and record it. Wrist and shoulder numbers are not
    comparable, and a site change means a new baseline (docs/WEAR_SITES.md).
8. Never treat wearable data alone as a medical diagnosis.
9. Test every sensor separately before sealing the enclosure.
10. Record the exact board revision, sensor breakout version, wiring, probe site and firmware commit for every experimental session.

---

# 21. CURRENT SOURCE FILES

Wearable:

`hardware/esp32s3/endo_twin_wearable/endo_twin_wearable.ino`

Mega:

`hardware/arduino/endo_twin_mega_lab/endo_twin_mega_lab.ino`

Build helper:

`scripts/build/build_firmware.sh`

CI:

`.github/workflows/arduino_firmware.yml`

This document should be treated as the primary physical-build reference for the current prototype.
