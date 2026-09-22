# ENDO-TWIN NEXUS V8.7 — Current Operating Path

ENDO-TWIN is the personalized physiological modelling platform; CHRONO-PCOS is one disease-specific research extension inside it.

## Active hardware
- **ESP32-S3 NodeMCU / ESP-12E = primary Wi-Fi wearable**
- **Arduino Mega 2560 = bench/lab/expanded test controller**
- **ESP32 = legacy only**
- **Arduino Nano = legacy only**

## Start
```bash
./START.sh
```

Both workstations support DEMO MODE and LIVE SENSOR MODE. Desktop LIVE mode uses dynamically discovered USB serial ports and CRC-checked `$CP/$CP2` packets.

## Live paths
```
ESP32-S3 wearable ── USB Serial / Wi-Fi TCP ── CP2 ──> Android/Desktop
Mega lab      ───── USB Serial ────────────── CP2 ──> Python/Desktop
```

The ESP32-S3 has no BLE; Android connects over Wi-Fi/TCP. The desktop USB path remains available for flashing, debugging and live acquisition.

## Android
```bash
./setup_android.sh
./build_apks.sh all
```

Patient and Doctor remain native Kotlin + Compose + Material 3. Live mobile acquisition uses the ESP32-S3 TCP stream; DEMO_DATA remains explicitly separated from live data.

> Research prototype — not a medical device, not clinically validated, not a diagnosis.
