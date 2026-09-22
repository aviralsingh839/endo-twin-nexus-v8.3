# ENDO-TWIN NEXUS V8.7 — Current Operating Path

ENDO-TWIN is the personalized physiological modelling platform; CHRONO-PCOS is one disease-specific research extension inside it.

## Active hardware
- **ESP8266 NodeMCU / ESP-12E = low-cost Wi-Fi sensor-pod option**
- **ESP32-S3 = higher-capability Wi-Fi sensor-pod option**
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
ESP8266 sensor pod ── Wi-Fi TCP ── CP2 ──> Android/Desktop
ESP32-S3 sensor pod ── Wi-Fi TCP ── CP2 ──> Android/Desktop
Mega lab      ───── USB Serial ────────────── CP2 ──> Python/Desktop
```

The current Android network path is board-neutral and uses Wi-Fi/TCP. ESP8266 is the low-cost direct sensor-pod option; ESP32-S3 remains the higher-capability option. The desktop USB path remains available for flashing, debugging and live acquisition.

## Android
```bash
./setup_android.sh
./build_apks.sh all
```

Patient and Doctor remain native Kotlin + Compose + Material 3. Live mobile acquisition uses the validated CP2 TCP stream from the sensor pod; DEMO_DATA remains explicitly separated from live data.

> Research prototype — not a medical device, not clinically validated, not a diagnosis.
