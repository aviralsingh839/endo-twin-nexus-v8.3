# ENDO-TWIN NEXUS — ESP32-S3 Wearable + Mega Hub

The active topology is:

```
ESP32-S3 wearable ── Wi-Fi/TCP 7777 ── Android/Desktop
Mega 2560 lab hub ── USB Serial ─────── Desktop
```

The two controllers are independent CP3 producers.

## Wearable

- ESP32-S3-DevKitC-1
- MAX30102
- MPU6050
- BME280
- BH1750
- DS18B20 skin-temperature probe
- TCP port 7777

## Mega

- Arduino Mega 2560
- expanded lab sensors and controls
- USB Serial 115200

For the full physical construction and box measurements, use:

`docs/WEARABLE_AND_MEGA_BUILD_MANUAL.md`

The previous ESP8266 wearable is no longer an active build target.
