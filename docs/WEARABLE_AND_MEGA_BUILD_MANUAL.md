# ENDO-TWIN NEXUS — Wearable + Mega Hub Construction Manual
## ESP32-S3 DevKitC-1 wearable / BME280 / BH1750 / DS18B20 skin-contact probe / MAX30102 / MPU6050

**Document purpose:** This is the single physical-build reference for the current prototype. It covers the wearable enclosure, sensor placement, wiring, cable routing, skin-contact temperature probe, assembly measurements, ESP32-S3 firmware, the Arduino Mega hub, testing, and final acceptance.

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
| Skin-temperature probe lead | 150–350 mm |

A 110 × 70 × 30 mm enclosure leaves room for the development board, sensor breakouts, wiring, strain relief and a small protected battery/power section.

**Do not permanently cut the enclosure from an assumed ESP32-S3 board dimension.** ESP32-S3-DevKitC-1 revisions and header arrangements differ; measure the exact board you own and leave clearance around the USB connector and antenna. Espressif provides the official board dimension drawing and notes that both v1.0 and v1.1 exist. 

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

The BME280 provides temperature, humidity and pressure. The BH1750 provides ambient illuminance in lux. 

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

The ESP32-S3-DevKitC-1 is designed to be used with jumper wires or mounted on a breadboard/prototype assembly. 

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

Common BME280 I2C addresses are 0x77 and 0x76 depending on the breakout configuration. 

## 3.5 BH1750

Place the BH1750 on the **top surface** of the pod.

Create a clear optical window:

- approximately 8–12 mm opening;
- no opaque tape over the sensor;
- sensor face flush or slightly recessed;
- keep it away from the status LED.

The BH1750 uses I2C; its common address is 0x23, with 0x5C available using the address pin. 

## 3.6 DS18B20 skin-temperature probe

The temperature channel is now the DS18B20 in **direct skin contact**. It replaced the
GSR module; the GSR hardware is no longer fitted and no firmware reads it.

Recommended placement:

- probe taped or stitched against skin that stays in contact while the pod is worn —
  the inner forearm beside the pod, or the wrist strap surface next to the pod;
- at least 15 mm away from the MAX30102 optical window so it does not press on the PPG
  site or block the finger/wrist surface the PPG needs;
- at least 20 mm away from the ESP32-S3, the regulator and the battery — those parts run
  warm and will bias the reading toward pod temperature instead of skin temperature;
- flat against skin over the full probe body, held by a thin adhesive patch or a
  purpose-made low-profile tape. Do not bury it under thick foam or hot glue;
- cable exits through a strain-relieved opening, with a service loop so pulling the lead
  never pulls on the probe joint;
- use the waterproof/stainless-sheathed probe variant if the pod is worn during
  activity or near moisture.

**Contact is what makes the number meaningful.** A probe hanging in air beside the wrist
reads somewhere between skin and ambient and will drift with room temperature; a probe
pressed flat against skin tracks skin temperature within its own accuracy limits.

Limits to record with every session:

- skin temperature is **not** core temperature and lags it;
- it is affected by ambient temperature, airflow, clothing, perfusion and probe pressure;
- the DS18B20 datasheet accuracy applies to the sensor, not to the skin-contact site;
- one probe is fitted, so `temp1` is always `nan`, and the firmware raises status bit 3
  when the probe is missing or falls off.

---

# 4. SKIN-CONTACT PROBE: SAFETY AND HANDLING

The DS18B20 is a passive sensing element: it is read by the ESP32-S3 and drives no
current into the body. Body-contact rules are simpler than they were for the retired
electrode circuit, but they still apply:

- the probe, its cable and its adhesive patch must not press hard enough to mark or
  irritate skin, and should be removed periodically during long sessions;
- keep the probe and its cable away from the mains and from any mains-powered bench
  equipment; run body-contact sessions from battery power;
- do not use damaged probes or probes with cracked sheaths on skin;
- do not place the probe over broken skin, a rash or a mole for repeated sessions;
- confirm the probe is electrically isolated from the pod's charging path (charge with
  the probe removed, or use an isolated charger);
- the DQ pull-up resistor (4.7 kΩ) sits on the 3V3 rail, so keep the probe wiring away
  from any point that can be energised at a higher voltage.

The purpose is to log a skin-temperature trend on a research prototype, not to measure
body temperature for any clinical decision.

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
| DS18B20 probe | DQ (data) | GPIO4 (OneWire, 4.7 kΩ pull-up to 3V3) |
| Status LED | control | GPIO2 |
| All sensors | GND | ESP32 GND |
| I2C sensors | VCC | 3.3 V-compatible supply |

GPIO8/GPIO9 are used as the dedicated I2C bus in the current firmware. The ESP32-S3-DevKitC-1 exposes GPIOs for peripheral connections; consult the exact board revision's official pin layout before final enclosure drilling. 

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

## 5.3 DS18B20 skin-temperature probe

Use **three-wire (normal) power**, not parasite power: it is more tolerant of long
probe leads and does not need a strong pull-up during conversion.

```
DS18B20 VDD (red)   ───────── ESP32-S3 3V3
DS18B20 GND (black) ───────── ESP32-S3 GND
DS18B20 DQ  (data)  ───────── ESP32-S3 GPIO4
4.7 kΩ resistor     ───────── between DQ and 3V3   (required)
```

Note the pull-up: without it the probe usually returns `DEVICE_DISCONNECTED_C` and the
firmware sets status bit 3. GPIO4 is the pin the GSR module used to occupy; no other
peripheral uses it.

Probe lead lengths up to a few metres work with normal power and a 4.7 kΩ pull-up; keep
the lead short (150–350 mm) so it can be strain-relieved inside or beside the pod.

---

# 6. WIRING AND CABLE LENGTH

For the first prototype:

| Cable | Recommended length |
|---|---:|
| I2C sensor branch | 80–150 mm |
| BME280 branch | 80–120 mm |
| BH1750 branch | 80–150 mm |
| DS18B20 skin-probe lead | 150–350 mm |
| Status LED | 80–150 mm |
| Battery lead | 100–200 mm |

Keep I2C wires short and grouped. Keep the probe lead separated from noisy digital/power wiring where practical.

Use a common ground.

For the wearable prototype, avoid long loose Dupont jumpers. After bench validation, replace them with secured flexible wire and strain relief.

---

# 7. POWER

For development:

- USB power is acceptable for bench testing without body electrodes.
- For any body-contact session, use a suitable battery-powered isolated supply.
- The ESP32-S3 DevKitC-1 supports USB power as well as 5V/GND or 3V3/GND supply options; do not simultaneously feed conflicting power sources. 

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
│  │ ESP32-S3      │      │ 4.7 kΩ pull-up + JST    │    │
│  │               │      │ probe connector ────────┼───┼──► skin probe
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
- DS18B20 probe lead exit (strain-relieved);
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

### Step 8 — Install the skin-temperature probe

Fit the 4.7 kΩ pull-up between DQ and 3V3 on a small piece of perfboard or inline in the
connector housing, then run three wires to the probe.

Use a JST or similar connector at the pod wall so the probe can be replaced without
opening the enclosure.

Add a service loop and a strain relief so a pulled probe lead cannot load the solder
joint. Keep the probe at least 20 mm from the ESP32, regulator and battery.

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

# 10. SKIN-TEMPERATURE PROBE MOUNTING

Recommended prototype:

```
        WEARABLE POD (wrist / forearm strap)
              │
        strain-relieved exit
              │
      ┌───────┴────────┐
      │  probe body    │  flat against skin, thin tape
      │  150–350 mm    │  ≥ 15 mm from PPG window
      └───────┬────────┘  ≥ 20 mm from ESP32 / battery
              │
        skin contact site
        (inner forearm, or wrist beside the pod)
```

Contact checklist:

- the full probe body lies flat on skin, not on top of the strap seam or a bone ridge;
- the adhesive patch is thin; thick foam insulates the probe from skin and adds lag;
- the probe cannot slide or lift when the wrist moves — test by moving the arm and
  watching the reported temperature for a step back toward ambient;
- the cable cannot tug the probe when the arm moves.

Record with every session:

- probe site and side (left/right forearm, wrist);
- how it was fixed (patch, tape, strap pocket) and for how long;
- ambient/room temperature at the start (BME280 `roomT`);
- whether the probe was replaced or repositioned mid-session;
- the `status` bit 3 state, so a probe that fell off is visible in the recording.

This makes later comparisons reproducible, and makes it obvious when a temperature
change is a contact problem rather than a physiological one.

---

# 11. CURRENT ESP32-S3 FIRMWARE

Source:

`hardware/esp32s3/endo_twin_wearable/endo_twin_wearable.ino`

The firmware:

- reads MAX30102 IR/red;
- reads MPU6050 acceleration/gyro;
- reads the DS18B20 skin probe once per second (non-blocking conversion);
- reads BME280 temperature/humidity/pressure;
- reads BH1750 lux;
- emits canonical CP3 at approximately 20 Hz;
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
arduino-cli lib install "OneWire"
arduino-cli lib install "DallasTemperature"
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

Wire format reference: `docs/WIRE_FORMAT_CP3.md`.

# 13. CP3 PACKET

The active packet is **CP3** — CP2 with the retired `gsr` field removed:

```
$CP3,ms,ir,red,ax,ay,az,gx,gy,gz,temp0,temp1,micRaw,micRms,micPitch,ecg,fsr,lux,roomT,hum,press,buttons,status,crc
```

CP2 is still accepted by the host parser so recordings made before the change keep
loading, and the Android clients accept both. Current firmware only ever emits CP3.

Wearable meanings:

| Field | Wearable source |
|---|---|
| ir | MAX30102 |
| red | MAX30102 |
| ax/ay/az | MPU6050 |
| gx/gy/gz | MPU6050 |
| temp0 | DS18B20 skin-contact probe (°C, NAN until the first conversion) |
| temp1 | `nan` - only one probe is fitted |
| micRaw / micRms / micPitch | `-1` - not installed |
| ecg | -1 |
| fsr | -1 |
| lux | BH1750 |
| roomT | BME280 |
| hum | BME280 |
| press | BME280 |
| buttons | 0 |
| status | firmware quality/status bits |
| crc | XOR CRC |

The Android TCP parser accepts both formats: 24 fields for CP3, 25 for legacy CP2.

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

## Test 7 — DS18B20 skin probe

Start the pod and watch `temp0` in the stream.

Verify:

- `temp0` is a plausible skin-range number (roughly 28–36 °C depending on site and room);
- it is not `nan` and not `85` (85 °C is the DS18B20 power-on value - it means the
  firmware read the scratchpad before a conversion finished);
- pinch the probe between two fingers for ~30 s: the reading should climb toward
  ~33–35 °C, then fall back toward ambient when released;
- unplug the probe: `temp0` becomes `nan` and status bit 3 (value 8) sets;
- `roomT` from the BME280 and `temp0` must not track each other exactly — if they do,
  the probe is reading pod/ambient air rather than skin.

Do not interpret `temp0` as core body temperature.

## Test 8 — CP3

Verify:

```
$CP3,...,<CRC>
$CP3,...,<CRC>
$CP3,...,<CRC>
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

- [ ] enclosure approximately 110 × 70 × 30 mm
- [ ] ESP32-S3 firmly mounted
- [ ] USB accessible
- [ ] antenna area unobstructed
- [ ] MAX30102 faces skin
- [ ] MPU6050 rigidly mounted
- [ ] BME280 has ambient-air vent
- [ ] BH1750 has clear optical window
- [ ] skin-temperature probe connector strain relieved
- [ ] probe sites labelled in the session log
- [ ] all grounds common
- [ ] no exposed sharp conductive parts
- [ ] battery protected and secured
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
4. Keep BME280 thermally isolated from the ESP32 and battery.
5. Keep BH1750 optically exposed.
6. Keep the probe lead strain relieved and the pull-up resistor fitted.
7. Treat skin temperature as a contact-dependent research channel: it is not core
   temperature, and a loose probe reads the room, not the wearer.
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
