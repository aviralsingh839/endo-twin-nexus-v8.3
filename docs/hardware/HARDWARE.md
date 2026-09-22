# ENDO-TWIN NEXUS — Hardware Architecture

## Active architecture

| Controller | Role | Active |
|---|---|---|
| **ESP32-S3-DevKitC-1** | **Primary wireless wearable** | YES |
| **Arduino Mega 2560** | Bench / lab / expanded controller | YES |
| ESP8266 | Superseded wearable implementation | Legacy |
| ESP32 original wearable | Historical implementation | Legacy |
| Arduino Nano | Historical implementation | Legacy |

## ESP32-S3 wearable

Firmware:
`hardware/esp32s3/endo_twin_wearable/endo_twin_wearable.ino`

Sensors:
- MAX30102 PPG
- MPU6050 IMU
- BME280 temperature/humidity/pressure
- BH1750 ambient light
- GSR/EDA with external finger electrodes

Transport:
- USB serial 115200
- Wi-Fi SoftAP `ENDO-TWIN-S3`
- password `endotwins3`
- TCP port 7777

The ESP32-S3 has Wi-Fi and BLE capability; the current Android transport remains Wi-Fi/TCP so the existing CP2/TCP architecture can be retained. citeturn2search18

## Mega hub

Firmware:
`hardware/arduino/endo_twin_mega_lab/endo_twin_mega_lab.ino`

The Mega remains the separate bench/lab controller for expanded experiments.

## Unified build guide

Physical assembly, dimensions, wiring, sensor placement, GSR safety, wearable enclosure and Mega box assembly:

`docs/WEARABLE_AND_MEGA_BUILD_MANUAL.md`

## Safety

Research/educational prototype only. Verify sensor voltage compatibility, battery isolation, body-contact safety, wiring, placement and calibration before testing on a person.
