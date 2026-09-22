# ENDO-TWIN NEXUS V8.7 — ESP32 + Mega Active Connection

This page supersedes the old ESP8266 bridge topology.

## Active topology

### Wearable
ESP32 → USB Serial → PC

or

ESP32 → BLE → Android / Desktop BLE-capable client

### Bench/lab
Arduino Mega 2560 → USB Serial → PC

The Mega does not sit between the ESP32 and the PC. The active controllers are independent CP2 producers.

## ESP32 BLE

- Device name: `ENDO-TWIN-ESP32`
- Service: `7f300001-6c12-4f70-9e6b-8e9f7b8b1001`
- Notify: `7f300002-6c12-4f70-9e6b-8e9f7b8b1001`
- Command: `7f300003-6c12-4f70-9e6b-8e9f7b8b1001`

Old ESP8266 Wi-Fi bridge details are historical only and are preserved in `hardware/legacy/esp8266/` and the project legacy history.
