# ENDO-TWIN NEXUS V8.7 — Hardware Architecture

## Active architecture

| Controller | Role | Active? |
|---|---|---|
| **ESP32** | **Primary wearable** | YES |
| **Arduino Mega 2560** | Bench / lab / expanded test controller | YES |
| Arduino Nano | Historical wearable implementation | NO — legacy only |
| ESP8266 | Historical network bridge | NO — legacy only |

The platform remains **ENDO-TWIN NEXUS**. CHRONO-PCOS is a disease-specific research extension inside the platform.

## Primary wearable — ESP32

Canonical firmware:
`hardware/esp32/endo_twin_wearable/endo_twin_wearable.ino`

Core sensors:
- MAX30102 PPG: SDA GPIO21, SCL GPIO22
- MPU6050: SDA GPIO21, SCL GPIO22
- DS18B20: DATA GPIO18 with 4.7 kΩ pull-up to 3.3 V
- GSR/EDA: ADC GPIO34
- Status LED: GPIO2

Transport:
- USB serial at 115200 baud
- BLE device name `ENDO-TWIN-ESP32`
- BLE service `7f300001-6c12-4f70-9e6b-8e9f7b8b1001`
- BLE notify `7f300002-6c12-4f70-9e6b-8e9f7b8b1001`
- BLE command `7f300003-6c12-4f70-9e6b-8e9f7b8b1001`

## Bench/lab controller — Mega 2560

Canonical firmware:
`hardware/arduino/endo_twin_mega_lab/endo_twin_mega_lab.ino`

The Mega may host the expanded lab set:
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

Mega I2C is D20/SDA and D21/SCL. It is USB-connected to the PC and is not the primary wearable wireless controller.

## Data path

```
ESP32 wearable ── USB Serial / BLE ──┐
                                     ├─ CP2 ── Python/Desktop/Android
Mega lab controller ── USB Serial ──┘          │
                                               ├─ quality + features
                                               ├─ local-first storage
                                               └─ ENDO-TWIN / disease modules
```

Both active controllers emit the same canonical enhanced `$CP2` packet.

## Legacy boundary

Historical Nano and ESP8266 implementations are preserved under `hardware/legacy/` for reference only. No current build, launcher, Android path, desktop live path, or test requires them.

## Safety

This is an educational/research prototype, not a medical device. Sensor voltage compatibility, battery isolation, wiring integrity, placement, calibration and independent reference validation remain necessary. Never use unsafe power sources on body-worn hardware.
