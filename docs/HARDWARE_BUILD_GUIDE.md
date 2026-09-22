# ENDO-TWIN NEXUS V8.7 — Hardware Build Guide

## Active controller architecture

**ESP32 = primary wearable.**  
**Arduino Mega 2560 = bench/lab/expanded controller.**  
**Arduino Nano = not required; legacy only.**  
**ESP8266 = not part of the active communication path; legacy only.**

### Active firmware

- ESP32: `hardware/esp32/endo_twin_wearable/endo_twin_wearable.ino`
- Mega: `hardware/arduino/endo_twin_mega_lab/endo_twin_mega_lab.ino`

Legacy snapshots are stored under `hardware/legacy/`.

## End-to-end architecture

```
ESP32 ── USB / BLE ──> CP2 ──> Android/Desktop ──> processing ──> local-first data
Mega  ── USB ────────> CP2 ──> Python/Desktop ──> processing ──> local-first data
```

No mandatory cloud service, Nano or ESP8266 bridge exists in this current path.

## Bench/lab expansion

The Mega supports the larger sensor set for experiments: ECG, microphone, FSR, environmental sensing and OLED in addition to the core wearable sensors.

## Prototype procedure

Use Doctor → Prototype Lab after selecting LIVE SENSOR MODE. Confirm:
- ESP32 or Mega serial device
- packet count/rate
- CP2 CRC pass/fail
- PPG / IMU / temperature / GSR status
- raw packet stream
- signal quality
- exportable test log

## Communication

USB serial uses 115200 baud. BLE is provided by the ESP32 wearable with the documented ENDO-TWIN service and characteristic UUIDs. CP2 remains the only active sensor packet protocol.

## Safety

This remains a research/educational prototype. Do not interpret the output as diagnosis or treatment guidance. For body-worn testing, use appropriate battery/isolation arrangements and verify sensor logic levels before powering or attaching hardware.
