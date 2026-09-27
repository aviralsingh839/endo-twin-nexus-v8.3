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
- Analog Pulse Sensor / PPG on GPIO4 (single channel)
- MPU6050 IMU (optional)
- BME280 temperature/humidity/pressure (optional)
- BH1750 ambient light (optional)
- GSR/EDA with external finger electrodes on GPIO34

Transport:
- USB serial 115200
- Wi-Fi SoftAP `ENDO-TWIN-S3`
- password `endotwins3`
- TCP port 7777

The active V9 firmware uses USB serial at 115200 and a Wi-Fi SoftAP/TCP transport at port 7777. The current wire protocol is CP3. A single analog PPG channel is used for pulse/HR/HRV research features; SpO2 is not computed from the analog channel.

## Mega hub

Firmware:
`hardware/arduino/endo_twin_mega_lab/endo_twin_mega_lab.ino`

The Mega remains the separate bench/lab controller for expanded experiments.

## Unified build guide

Physical assembly, dimensions, wiring, sensor placement, GSR safety, wearable enclosure and Mega box assembly:

`docs/WEARABLE_AND_MEGA_BUILD_MANUAL.md`

## Safety

Research/educational prototype only. Verify sensor voltage compatibility, battery isolation, body-contact safety, wiring, placement and calibration before testing on a person.
