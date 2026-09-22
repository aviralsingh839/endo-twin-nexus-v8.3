# ENDO-TWIN NEXUS — Wearable + Mega Hub Construction Manual
## ESP32-S3 DevKitC-1 wearable / BME280 / BH1750 / GSR finger electrodes / MAX30102 / MPU6050

**Document purpose:** This is the single physical-build reference for the current prototype. It covers the wearable enclosure, sensor placement, wiring, cable routing, GSR finger electrodes, assembly measurements, ESP32-S3 firmware, the Arduino Mega hub, testing, and final acceptance.

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
   - GSR/EDA module
   - two finger electrodes
   - external status LED
   - battery/power system

2. **Mega Hub / Lab Box**
   - Arduino Mega 2560
   - expanded bench sensors and test interfaces
   - USB connection to the ENDO-TWIN desktop workstation
   - optional OLED, buttons, buzzer, ECG, FSR, microphone and environmental sensors

The wearable and Mega are independent acquisition devices. They do not need to be physically wired together for normal operation.

---

# 2. WEARABLE POD: RECOMMENDED PHYSICAL SIZE

Use these as **prototype enclosure targets**, not as the exact dimensions of every component.

## Recommended enclosure

| Dimension | Target |
|---|---:|
| External length | 110 mm |
| External width | 70 mm |
| External height | 30 mm |
| Internal usable length | ~100 mm |
| Internal usable width | ~60 mm |
| Internal usable height | ~24 mm |
| Wrist strap width | 20–25 mm |
| Recommended cable exit | 8–12 mm opening |
| Finger-electrode lead length | 300–450 mm each |

A 110 × 70 × 30 mm enclosure leaves room for the development board, sensor breakouts, wiring, strain relief and a small protected battery/power section.

**Do not permanently cut the enclosure from an assumed ESP32-S3 board dimension.** ESP32-S3-DevKitC-1 revisions and header arrangements differ; measure the exact board you own and leave clearance around the USB connector and antenna. Espressif provides the official board dimension drawing and notes that both v1.0 and v1.1 exist. citeturn1search0turn1search1

## Wearable orientation

Use this orientation:

```
                TOP / OUTSIDE OF POD
        ┌─────────────────────────────┐
        │       BH1750 LIGHT          │
        │          ▲                  │
        │     BME280 VENT             │
        │                             │
        │   ESP32-S3 + wiring         │
        │                             │
        │        BATTERY              │
        └─────────────────────────────┘
          ═══════ WRIST STRAP ═══════

                BOTTOM / SKIN SIDE
        ┌─────────────────────────────┐
        │       MAX30102              │
        │     optical window          │
        │          ↓                  │
        └─────────────────────────────┘
```

The MAX30102 should face the skin and be mechanically stable. The BH1750 should face the environment rather than the wrist. The BME280 should be exposed to ambient air through vents and should not be buried next to the ESP32 regulator or battery.

The BME280 provides temperature, humidity and pressure. The BH1750 provides ambient illuminance in lux. citeturn2search16turn2search13

---

# 3. SENSOR PLACEMENT

## 3.1 ESP32-S3

Place the ESP32-S3 near the center of the enclosure.

Requirements:

- USB connector faces a removable side panel.
- Antenna end faces away from large metal objects and the battery where practical.
- Do not cover the antenna with foil or a metal plate.
- Leave at least 5 mm clearance around the board edges where wiring bends.
- Use nylon/PLA/ABS standoffs or a small internal mounting plate.
- Do not allow solder joints to touch the enclosure.

The ESP32-S3-DevKitC-1 is designed to be used with jumper wires or mounted on a breadboard/prototype assembly. citeturn2search18

## 3.2 MAX30102

Recommended location: **underside of the pod**, approximately centered over the wrist/skin contact region.

Mounting:

- sensor window facing skin;
- no sharp solder pins exposed toward skin;
- use a thin black foam/rubber gasket around the optical opening if ambient light causes artifacts;
- do not overtighten the strap;
- keep the module from sliding during motion.

If your prototype is intended to measure from a finger instead of the wrist, put the MAX30102 in a small finger clip and route its I2C wiring back to the pod.

## 3.3 MPU6050

Place the MPU6050 close to the rigid center of the enclosure.

Recommended:

- X/Y axes aligned with the enclosure;
- board mounted flat;
- no flexible mounting;
- document the orientation in the firmware/test record.

The IMU is for movement/context, so it should move with the pod rather than hang on a loose wire.

## 3.4 BME280

Put the BME280 near a **side or top vent**, not against the ESP32 or battery.

Recommended vent:

- one or more openings of roughly 3–6 mm;
- sensor positioned 5–10 mm behind the opening;
- no direct skin contact;
- no foam pressed over the sensor.

The BME280 measures ambient environmental conditions. If it is enclosed beside a warm MCU or battery, its temperature reading can be biased.

Common BME280 I2C addresses are 0x77 and 0x76 depending on the breakout configuration. citeturn2search16

## 3.5 BH1750

Place the BH1750 on the **top surface** of the pod.

Create a clear optical window:

- approximately 8–12 mm opening;
- no opaque tape over the sensor;
- sensor face flush or slightly recessed;
- keep it away from the status LED.

The BH1750 uses I2C; its common address is 0x23, with 0x5C available using the address pin. citeturn2search9turn2search14

## 3.6 GSR module

Do **not** place the finger electrodes directly on the ESP32 enclosure.

Instead:

- GSR module stays inside the pod;
- its electrode connector exits through a strain-relieved side opening;
- two flexible wires run to the finger electrodes;
- electrodes are held on two adjacent fingers.

Recommended prototype placement:

- electrode A: palmar side of index finger;
- electrode B: palmar side of middle finger;
- electrode centers approximately 20–30 mm apart when the fingers are relaxed;
- use soft adjustable straps or conductive finger pads;
- do not use bare sharp metal;
- avoid excessive pressure.

The exact GSR response depends strongly on the module, electrode material, contact pressure, skin condition and circuit design. Record the raw ADC value and calibrate per user/session rather than treating a raw ADC number as a universal conductance value.

---

# 4. GSR FINGER-ELECTRODE SAFETY

**This is a body-contact circuit.**

For body-contact testing:

- use a battery-powered, isolated prototype;
- do not attach finger electrodes while the wearable is simultaneously connected to a laptop/PC by USB unless the entire setup has been designed and verified for safe isolation;
- never connect body electrodes to mains-powered circuitry;
- never connect the ESP32 GPIO directly to the electrodes;
- the electrodes connect to the GSR module's electrode inputs;
- only the GSR module's analog output goes to ESP32 GPIO4.

If the GSR module exposes its own excitation/electrode circuitry, follow that module's electrical limits and documentation.

---

# 5. ESP32-S3 WIRING

## 5.1 Main pin assignment

| Device | Signal | ESP32-S3 |
|---|---|---|
| MAX30102 | SDA | GPIO8 |
| MAX30102 | SCL | GPIO9 |
| MPU6050 | SDA | GPIO8 |
| MPU6050 | SCL | GPIO9 |
| BME280 | SDA | GPIO8 |
| BME280 | SCL | GPIO9 |
| BH1750 | SDA | GPIO8 |
| BH1750 | SCL | GPIO9 |
| GSR module | AO | GPIO4 / ADC |
| Status LED | control | GPIO2 |
| All sensors | GND | ESP32 GND |
| I2C sensors | VCC | 3.3 V-compatible supply |

GPIO8/GPIO9 are used as the dedicated I2C bus in the current firmware. The ESP32-S3-DevKitC-1 exposes GPIOs for peripheral connections; consult the exact board revision's official pin layout before final enclosure drilling. citeturn0search0turn1search24

## 5.2 I2C topology

All four digital sensors share the same two lines:

```
ESP32-S3 GPIO8 SDA ───── MAX30102 SDA
                    ├── MPU6050 SDA
                    ├── BME280 SDA
                    └── BH1750 SDA

ESP32-S3 GPIO9 SCL ───── MAX30102 SCL
                    ├── MPU6050 SCL
                    ├── BME280 SCL
                    └── BH1750 SCL

ESP32-S3 3V3 ──────────── sensor VCC
ESP32-S3 GND ──────────── sensor GND
```

Expected addresses:

- MAX30102: 0x57
- MPU6050: usually 0x68
- BME280: 0x76 or 0x77
- BH1750: 0x23 or 0x5C

There is no address collision between these defaults.

## 5.3 GSR

```
GSR module AO ───────── ESP32-S3 GPIO4
GSR module GND ──────── ESP32-S3 GND
GSR module VCC ──────── compatible supply
GSR electrode 1 ─────── finger electrode A
GSR electrode 2 ─────── finger electrode B
```

Verify the GSR module's analog-output voltage range before connecting AO to GPIO4.

---

# 6. WIRING AND CABLE LENGTH

For the first prototype:

| Cable | Recommended length |
|---|---:|
| I2C sensor branch | 80–150 mm |
| BME280 branch | 80–120 mm |
| BH1750 branch | 80–150 mm |
| GSR electrode lead A | 300–450 mm |
| GSR electrode lead B | 300–450 mm |
| Status LED | 80–150 mm |
| Battery lead | 100–200 mm |

Keep I2C wires short and grouped. Keep GSR electrode wires physically separated from noisy digital/power wiring as much as practical.

Use a common ground.

For the wearable prototype, avoid long loose Dupont jumpers. After bench validation, replace them with secured flexible wire and strain relief.

---

# 7. POWER

For development:

- USB power is acceptable for bench testing without body electrodes.
- For body-contact GSR testing, use a suitable battery-powered isolated supply.
- The ESP32-S3 DevKitC-1 supports USB power as well as 5V/GND or 3V3/GND supply options; do not simultaneously feed conflicting power sources. citeturn0search0

Do not place an unprotected Li-ion cell directly on the wearable's 3.3V rail.

Use an appropriate protected battery and regulator/power-management board for the final prototype.

---

# 8. WEARABLE INTERNAL LAYOUT

Recommended top-to-bottom arrangement:

```
┌─────────────────────────────────────────────────────────┐
│  [BH1750 optical window]      [BME280 vent]            │
│                                                         │
│  ┌───────────────┐      ┌─────────────────────────┐    │
│  │ ESP32-S3      │      │ GSR module              │    │
│  │               │      │ electrode connector ────┼───┼──►
│  └───────────────┘      └─────────────────────────┘    │
│                                                         │
│  ┌───────────┐             ┌──────────────────────┐    │
│  │ MPU6050   │             │ protected battery /  │    │
│  └───────────┘             │ power section       │    │
│                            └──────────────────────┘    │
│                                                         │
│  Side: USB + power switch + strain-relieved cables     │
└─────────────────────────────────────────────────────────┘
                       BOTTOM
              ┌─────────────────────┐
              │      MAX30102       │
              │      ↓ skin         │
              └─────────────────────┘
```

Keep the BME280 and BH1750 away from the ESP32 regulator and battery.

---

# 9. WEARABLE ASSEMBLY ORDER

### Step 1 — Prepare the enclosure

Drill/cut:

- USB opening;
- power switch opening if used;
- BH1750 optical window;
- BME280 ventilation opening;
- GSR cable exit;
- optional status LED opening;
- four small mounting holes or standoffs if using a mounting plate.

### Step 2 — Mount the ESP32-S3

Use nylon screws/standoffs or a removable mounting plate.

Do not glue directly over the ESP32 module or antenna.

### Step 3 — Build the I2C bus

Connect GPIO8 to all SDA pins.

Connect GPIO9 to all SCL pins.

Connect 3.3V and GND.

Do not run separate random I2C buses unless the firmware is changed.

### Step 4 — Mount MAX30102

Place it on the bottom face.

Check that the optical window can make stable skin contact.

### Step 5 — Mount MPU6050

Fix it rigidly.

Mark the board's X/Y direction on the enclosure so orientation is documented.

### Step 6 — Mount BME280

Put it next to the ventilation opening.

Do not cover it with hot glue, foam or conformal coating.

### Step 7 — Mount BH1750

Place it under the top optical window.

The sensor must see ambient light.

### Step 8 — Install GSR

Secure the GSR board inside.

Add a strain-relieved connector for the two electrode leads.

### Step 9 — Add status LED

GPIO2 → 220 Ω resistor → LED anode.

LED cathode → GND.

### Step 10 — Secure all wiring

Use:

- heat-shrink;
- cable ties;
- adhesive cable anchors;
- JST connectors where possible.

No wire should be able to pull directly on a sensor solder joint.

---

# 10. FINGER ELECTRODE STRAP

Recommended prototype:

```
INDEX FINGER             MIDDLE FINGER
     │                         │
 [electrode A]             [electrode B]
     │                         │
     └──── 300–450 mm ────────┘
              │
          GSR MODULE
              │
          WEARABLE POD
```

Use two soft conductive-contact surfaces.

The electrode should make repeatable contact but should not cut into the finger or cause discomfort.

Record:

- finger locations;
- electrode material;
- electrode spacing;
- contact pressure/strap tightness;
- session duration;
- skin preparation;
- raw GSR values.

This makes later comparisons reproducible.

---

# 11. CURRENT ESP32-S3 FIRMWARE

Source:

`hardware/esp32s3/endo_twin_wearable/endo_twin_wearable.ino`

The firmware:

- reads MAX30102 IR/red;
- reads MPU6050 acceleration/gyro;
- reads GSR ADC;
- reads BME280 temperature/humidity/pressure;
- reads BH1750 lux;
- emits canonical CP2 at approximately 20 Hz;
- validates data through an XOR CRC;
- provides USB serial;
- starts Wi-Fi SoftAP;
- provides TCP port 7777;
- supports PING;
- supports WHOAMI;
- supports LED commands.

Network:

- SSID: `ENDO-TWIN-S3`
- password: `endotwins3`
- default AP address: normally `192.168.4.1`
- TCP port: `7777`

---

# 12. BUILD AND FLASH

Install the ESP32 Arduino core:

```bash
arduino-cli core update-index
arduino-cli core install esp32:esp32
```

Install required libraries:

```bash
arduino-cli lib install "SparkFun MAX3010x Pulse and Proximity Sensor Library"
arduino-cli lib install "Adafruit MPU6050"
arduino-cli lib install "Adafruit Unified Sensor"
arduino-cli lib install "BH1750"
arduino-cli lib install "Adafruit BME280 Library"
```

Compile:

```bash
arduino-cli compile \
  --fqbn esp32:esp32:esp32s3 \
  hardware/esp32s3/endo_twin_wearable
```

Find the USB port:

```bash
arduino-cli board list
```

Upload, replacing `/dev/ttyACM0` with the actual port:

```bash
arduino-cli upload \
  -p /dev/ttyACM0 \
  --fqbn esp32:esp32:esp32s3 \
  hardware/esp32s3/endo_twin_wearable
```

Monitor:

```bash
arduino-cli monitor -p /dev/ttyACM0 -c baudrate=115200
```

Expected startup information includes the ESP32-S3 AP address and TCP server status.

---

# 13. CP2 PACKET

The active packet remains:

```
$CP2,ms,ir,red,ax,ay,az,gx,gy,gz,temp0,temp1,gsr,micRaw,micRms,micPitch,ecg,fsr,lux,roomT,hum,press,buttons,status,crc
```

Wearable meanings:

| Field | Wearable source |
|---|---|
| ir | MAX30102 |
| red | MAX30102 |
| ax/ay/az | MPU6050 |
| gx/gy/gz | MPU6050 |
| temp0/temp1 | NAN / unused on wearable |
| gsr | GSR module ADC |
| micRaw | - not installed |
| micRms | 0 |
| micPitch | 0 |
| ecg | -1 |
| fsr | -1 |
| lux | BH1750 |
| roomT | BME280 |
| hum | BME280 |
| press | BME280 |
| buttons | 0 |
| status | firmware quality/status bits |
| crc | XOR CRC |

The Android TCP parser continues to consume the same 25-field CP2 frame.

---

# 14. SENSOR TEST ORDER

Never assemble everything permanently before testing.

## Test 1 — ESP32-S3 alone

Verify:

- powers on;
- USB serial works;
- board does not reset continuously.

## Test 2 — I2C scan

Verify:

- MAX30102;
- MPU6050;
- BME280;
- BH1750.

Expected addresses are listed above.

## Test 3 — MAX30102

Verify:

- IR changes when the optical sensor is covered;
- red changes with contact;
- no permanent saturation.

## Test 4 — MPU6050

Verify:

- X/Y/Z change when the pod is rotated;
- gyro changes when rotated.

## Test 5 — BME280

Verify:

- room temperature is plausible;
- humidity changes when the sensor is exposed;
- pressure is nonzero.

## Test 6 — BH1750

Verify:

- lux rises under brighter light;
- sensor is not blocked by enclosure material.

## Test 7 — GSR

First test with no finger contact.

Then connect the electrodes and test with a relaxed finger position.

Record the raw values. Do not assume that a particular raw number means a particular physiological state.

## Test 8 — CP2

Verify:

```
$CP2,...,<CRC>
$CP2,...,<CRC>
$CP2,...,<CRC>
```

at approximately 20 packets/second.

## Test 9 — Wi-Fi

Connect the phone to:

```
ENDO-TWIN-S3
```

Password:

```
endotwins3
```

Then connect the app to:

```
192.168.4.1:7777
```

---

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
│ │ optional ECG / GSR / FSR / microphone connectors   │ │
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
| GSR | A0 |
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
- GSR
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
                │ PPG / IMU / GSR    │
                │ BME280 / BH1750     │
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

- [ ] enclosure approximately 110 × 70 × 30 mm
- [ ] ESP32-S3 firmly mounted
- [ ] USB accessible
- [ ] antenna area unobstructed
- [ ] MAX30102 faces skin
- [ ] MPU6050 rigidly mounted
- [ ] BME280 has ambient-air vent
- [ ] BH1750 has clear optical window
- [ ] GSR connector strain relieved
- [ ] finger electrodes labelled A/B
- [ ] all grounds common
- [ ] no exposed sharp conductive parts
- [ ] battery protected and secured
- [ ] no loose wires

### Firmware

- [ ] ESP32-S3 firmware compiles
- [ ] board uploads successfully
- [ ] I2C sensors detected
- [ ] GSR ADC changes
- [ ] CP2 CRC validates
- [ ] ~20 Hz packet stream
- [ ] Wi-Fi AP starts
- [ ] TCP 7777 accepts a client
- [ ] PING works
- [ ] WHOAMI reports ENDO-TWIN-ESP32S3

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
3. Do not use GPIO33–37 on variants where Espressif reserves them for internal flash/PSRAM. citeturn0search3
4. Keep BME280 thermally isolated from the ESP32 and battery.
5. Keep BH1750 optically exposed.
6. Keep GSR electrode wires strain relieved.
7. Treat GSR as a raw research channel requiring calibration.
8. Never treat wearable data alone as a medical diagnosis.
9. Test every sensor separately before sealing the enclosure.
10. Record the exact board revision, sensor breakout version, wiring, electrode placement and firmware commit for every experimental session.

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
