# ENDO-TWIN NEXUS V8.7 — Workstations & Connection

## Active hardware paths

**ESP32 primary wearable**
→ USB Serial or BLE
→ CP2
→ Patient / Doctor / Research processing

**Arduino Mega bench/lab**
→ USB Serial
→ CP2
→ Prototype / Research processing

The workstation accepts dynamically discovered serial ports; it does not assume `/dev/ttyUSB0`.

## Modes

- DEMO MODE: deterministic synthetic stream explicitly labelled `DEMO_DATA`
- LIVE SENSOR MODE: actual CP2 packets from ESP32 or Mega, CRC checked before processing

The mode is selected at startup to prevent accidental mixing of synthetic and measured records.

## Android

Native Kotlin + Jetpack Compose + Material 3 remain the Android architecture. ESP32 BLE is the active wearable transport. The app must keep DEMO, LIVE USB and LIVE BLE states distinct and must not replace live sensor data with demo values.

## Local-first data

Patient data, doctor data, raw sensor data and research outputs remain locally scoped with provenance. Missing evidence produces UNKNOWN / insufficient-evidence states rather than invented values.

## Prototype Lab

Doctor → Prototype Lab is the engineering surface for testing ESP32 and Mega hardware before using a session in the wider ENDO-TWIN pipeline.
