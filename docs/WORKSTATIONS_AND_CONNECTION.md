# ENDO-TWIN NEXUS V8.7 — Workstations & Connection

## Active hardware paths

**ESP8266 primary wearable**
→ USB Serial or Wi-Fi/TCP
→ CP3
→ Patient / Doctor / Research processing

**Arduino Mega bench/lab**
→ USB Serial
→ CP3
→ Prototype / Research processing

The workstation accepts dynamically discovered serial ports; it does not assume `/dev/ttyUSB0`.

## Modes

- DEMO MODE: deterministic synthetic stream explicitly labelled `DEMO_DATA`
- LIVE SENSOR MODE: actual CP3 packets from ESP8266 or Mega, CRC checked before processing

## Android

Native Kotlin + Jetpack Compose + Material 3 remain the Android architecture. ESP8266 has no BLE, so mobile live acquisition uses Wi-Fi/TCP. The default AP is `ENDO-TWIN-ESP8266` with TCP port 7777.

## Local-first data

Patient data, doctor data, raw sensor data and research outputs remain locally scoped with provenance. Missing evidence produces UNKNOWN / insufficient-evidence states rather than invented values.

## Prototype Lab

Doctor → Prototype Lab is the engineering surface for testing ESP8266 and Mega hardware before using a session in the wider ENDO-TWIN pipeline.
