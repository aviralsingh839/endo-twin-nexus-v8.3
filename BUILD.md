# ENDO-TWIN NEXUS V8.7 — Build & Run

## Canonical launcher
```bash
./START.sh
```

## Active firmware
ESP32 primary wearable:
`hardware/esp32/endo_twin_wearable/endo_twin_wearable.ino`

Arduino Mega bench/lab:
`hardware/arduino/endo_twin_mega_lab/endo_twin_mega_lab.ino`

Build:
```bash
./scripts/build/build_firmware.sh
```

## Workstations
```bash
./START.sh doctor
./START.sh patient-pc
```

Choose LIVE SENSOR MODE and select the discovered serial port. The same CP2 packet format is used by ESP32 and Mega; the desktop parser remains the single canonical parser.

## Android
```bash
./setup_android.sh
./build_apks.sh patient
./build_apks.sh doctor
./build_apks.sh all
```

## Safety
Use battery/isolation appropriate for body-worn experiments, verify sensor logic voltage, and keep all research outputs clearly separate from clinical diagnosis.
