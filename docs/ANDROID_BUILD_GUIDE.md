# ENDO-TWIN NEXUS V8.7 — Android Build Guide

Run from the repository root:
```bash
./setup_android.sh
./build_apks.sh patient
./build_apks.sh doctor
./build_apks.sh all
```

The applications remain native **Kotlin + Jetpack Compose + Material 3** with Java 17.

## ESP32-S3 TCP

Both Patient and Doctor Android applications use the ESP32-S3 Wi-Fi/TCP path:
- join the `ENDO-TWIN-ESP32-S3` access point or the configured network
- default host `192.168.4.1`
- TCP port `7777`
- connect to the ESP32-S3 TCP stream
- reassemble newline-delimited CP2 frames
- validate CP2 CRC
- parse measurements
- show LIVE TCP state
- send `PING` / `WHOAMI`

The ESP32-S3 does not provide BLE.

## Modes

DEMO data is deterministic and visibly labelled. LIVE TCP and LIVE USB are never populated with synthetic sensor values.

## Build output

Debug APKs are copied to `DIST/android/`.
