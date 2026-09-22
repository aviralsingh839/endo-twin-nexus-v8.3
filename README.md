# ENDO-TWIN NEXUS V8.7 — Current Operating Path

ENDO-TWIN is the personalized physiological modelling platform; CHRONO-PCOS is one disease-specific research extension inside it.

## Active hardware
- **ESP32 = primary wearable**
- **Arduino Mega 2560 = bench/lab/expanded test controller**
- **Arduino Nano = legacy only; not required by the current build or runtime**
- **ESP8266 = legacy only; not an active communication bridge**

## Start
```bash
./START.sh
```

## Workstations
```bash
./START.sh doctor
./START.sh patient-pc
```

Both workstations can use **DEMO MODE** or **LIVE SENSOR MODE**. LIVE mode accepts dynamically selected USB serial ports and canonical CRC-checked `$CP/$CP2` packets.

## Live paths
```
ESP32 wearable ── USB Serial / BLE ── CP2 ──> Android/Desktop
Mega lab      ── USB Serial ──────── CP2 ──> Python/Desktop
```

The existing signal-processing, quality-gating, local-first storage and provenance architecture is preserved.

## Android
```bash
./setup_android.sh
./build_apks.sh all
```

Patient and Doctor remain native Kotlin + Compose + Material 3. The ESP32 BLE transport is the active wearable mobile path; DEMO_DATA remains explicitly separated from live data.

> Research prototype — not a medical device, not clinically validated, not a diagnosis.
