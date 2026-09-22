# ENDO-TWIN NEXUS V8.7 — Hardware Build Guide

## Active controller architecture

**ESP8266 NodeMCU / ESP-12E = primary Wi-Fi wearable.**  
**Arduino Mega 2560 = bench/lab/expanded controller.**  
**ESP32 = legacy only.**  
**Arduino Nano = legacy only.**

### Active firmware

- ESP8266: `hardware/esp8266/endo_twin_wearable/endo_twin_wearable.ino`
- Mega: `hardware/arduino/endo_twin_mega_lab/endo_twin_mega_lab.ino`

## End-to-end architecture

```
ESP8266 ── USB / Wi-Fi TCP ──> CP2 ──> Android/Desktop ──> processing ──> local-first data
Mega     ── USB ──────────────> CP2 ──> Python/Desktop ──> processing ──> local-first data
```

No Nano or ESP32 is required by the current path. The old ESP8266 bridge is historical; the active ESP8266 firmware now reads the wearable sensors directly.

## Prototype procedure

Use Doctor → Prototype Lab after selecting LIVE SENSOR MODE. Confirm:
- ESP8266 or Mega serial device
- packet count/rate
- CP2 CRC pass/fail
- PPG / IMU / temperature / GSR status
- raw packet stream
- signal quality
- exportable test log

## Communication

USB serial uses 115200 baud. ESP8266 mobile connectivity uses TCP port 7777. CP2 remains the active sensor packet protocol.

## Safety

Research/educational prototype only. Verify logic levels and use suitable battery/isolation arrangements for body-worn testing.
