# ENDO-TWIN NEXUS V8.7 — Android Build Guide

Run from the repository root:
```bash
./setup_android.sh
./build_apks.sh patient
./build_apks.sh doctor
./build_apks.sh all
```

The applications remain native **Kotlin + Jetpack Compose + Material 3** with Java 17.

## ESP32 BLE

Both Patient and Doctor Android applications use the ESP32 wearable BLE contract:
- scan
- identify `ENDO-TWIN-ESP32`
- filter by the ENDO-TWIN service UUID
- connect and discover services
- subscribe to notifications
- reassemble newline-delimited CP2 frames from fragmented notifications
- validate CP2 CRC
- parse measurements
- show LIVE BLE state
- send `PING` / `WHOAMI`

Android 12+ uses Bluetooth scan/connect permissions. Older Android versions retain the required compatibility permissions.

## Modes

DEMO data is deterministic and visibly labelled. LIVE BLE and LIVE USB are never populated with synthetic sensor values.

## Build output

Debug APKs are copied to `DIST/android/`.
