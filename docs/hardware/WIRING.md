# ENDO-TWIN NEXUS — Current Wiring

Wire format reference: `docs/WIRE_FORMAT_CP3.md`.

The complete physical construction, enclosure dimensions, sensor placement, skin-probe
mounting, and Mega hub assembly are documented in:

**docs/WEARABLE_AND_MEGA_BUILD_MANUAL.md**

## ESP32-S3 primary wearable

| Module | Connection |
|---|---|
| MAX30102 | SDA GPIO8, SCL GPIO9 |
| MPU6050 | SDA GPIO8, SCL GPIO9 |
| BME280 | SDA GPIO8, SCL GPIO9 |
| BH1750 | SDA GPIO8, SCL GPIO9 |
| DS18B20 skin probe | DQ GPIO4, VDD 3V3, GND GND, 4.7 kΩ pull-up DQ→3V3 |
| Status LED | GPIO2 through 220 Ω resistor |
| I2C VCC | 3.3 V-compatible supply |
| Common ground | ESP32-S3 GND |

The four I2C devices share the same bus. The wearable uses Wi-Fi/TCP on port 7777 and
emits the canonical `$CP3` frame over USB serial and TCP.

## Skin-temperature probe

The DS18B20 probe sits in **direct skin contact** — inner forearm beside the pod, or the
wrist strap surface next to the pod. It replaced the GSR module, which is no longer
fitted.

Wire it as three-wire (normal) power, not parasite power:

```
DS18B20 VDD ──── 3V3
DS18B20 GND ──── GND
DS18B20 DQ  ──── GPIO4
4.7 kΩ      ──── between DQ and 3V3   (required)
```

Placement rules that decide whether the number means anything:

- full probe body flat against skin, thin tape or a stitched pocket, not thick foam;
- at least 15 mm from the MAX30102 window so it does not press on the PPG site;
- at least 20 mm from the ESP32-S3, regulator and battery, which run warm;
- strain-relieved lead so arm movement cannot lift the probe;
- check by moving the arm: a probe that lifts steps back toward ambient temperature.

`temp0` is this probe. `temp1` is `nan` (only one probe is fitted). When the probe is
missing or disconnected the firmware sets status bit 3.

Skin temperature is **not** core temperature: it lags core temperature and is affected
by ambient conditions, airflow, clothing, perfusion and probe pressure. Run body-contact
sessions from battery power and keep the probe away from the charging path.

## Arduino Mega 2560 lab controller

| Module | Mega connection |
|---|---|
| I2C | SDA D20, SCL D21 |
| DS18B20 | D2 |
| (previous GSR channel) | A0 — retired, pin left free |
| MAX4466 | A1 |
| AD8232 OUT | A2 |
| FSR | A3 |
| ECG LO+ / LO− | D11 / D12 |
| Buttons | D3/D4/D5 |
| LEDs | D8/D9/D10 |
| Buzzer | D6 |

The Mega also emits `$CP3`; the GSR read and its status bit were removed from both
firmwares.

For the complete enclosure/box assembly, use the unified manual above.
