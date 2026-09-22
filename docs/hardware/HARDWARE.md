# ENDO-TWIN NEXUS V8.7 — Hardware Architecture

## Active architecture

| Controller | Role | Active? |
|---|---|---|
| **ESP8266 NodeMCU / ESP-12E** | **Primary Wi-Fi wearable** | YES |
| **Arduino Mega 2560** | Bench / lab / expanded test controller | YES |
| ESP32 | Historical wearable implementation | NO — legacy only |
| Arduino Nano | Historical wearable implementation | NO — legacy only |

ENDO-TWIN remains the parent platform; CHRONO-PCOS is a disease-specific research extension.

## Primary wearable — ESP8266

Canonical firmware:
`hardware/esp8266/endo_twin_wearable/endo_twin_wearable.ino`

Core sensors:
- MAX30102 PPG: SDA D1 (GPIO5), SCL D2 (GPIO4)
- MPU6050: SDA D1 (GPIO5), SCL D2 (GPIO4)
- DS18B20: DATA D6 (GPIO12), 4.7 kΩ pull-up to 3.3 V
- GSR/EDA: A0
- Status LED: D4 (GPIO2)

Transport:
- USB serial at 115200 baud
- Wi-Fi SoftAP: `ENDO-TWIN-ESP8266`
- Default SoftAP password: `endotwin8266`
- TCP server: port `7777`
- USB and TCP both carry newline-terminated canonical CP2 packets
- ESP8266 has no BLE; Android uses Wi-Fi/TCP

The default wiring assumes a NodeMCU 1.0 / ESP-12E style board. NodeMCU labels D1/D2/D4/D6 map to GPIO5/4/2/12.

## Bench/lab controller — Mega 2560

Canonical firmware:
`hardware/arduino/endo_twin_mega_lab/endo_twin_mega_lab.ino`

The Mega may host:
- MAX30102 / MPU6050
- DS18B20
- GSR
- optional MAX4466 microphone
- optional AD8232 ECG
- optional FSR
- optional BH1750
- optional BME280
- optional SSD1306 OLED
- buttons, LEDs, buzzer

Mega I2C is D20/SDA and D21/SCL.

## Data path

```
ESP8266 wearable ── USB Serial / Wi-Fi TCP ──┐
                                             ├─ CP2 ── Desktop/Android
Mega lab controller ── USB Serial ───────────┘          │
                                                        ├─ quality + features
                                                        ├─ local-first storage
                                                        └─ ENDO-TWIN / disease modules
```

Both active controllers emit the same enhanced `$CP2` packet.

## Legacy boundary

Historical ESP32, Nano and old ESP8266 bridge snapshots remain under `hardware/legacy/`. They are not required by the active build or runtime.

## Safety

Research/educational prototype only. Verify sensor voltage compatibility, battery isolation, wiring, placement and calibration before body-worn testing. Never connect unsafe mains-powered circuitry to body-worn hardware.
