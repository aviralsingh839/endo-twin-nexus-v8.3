# ENDO-TWIN NEXUS V9.0 — Current Operating Path

ENDO-TWIN is the personalized physiological modelling platform; CHRONO-PCOS is one disease-specific research extension inside it.

## Active hardware
- **ESP8266 NodeMCU / ESP-12E = low-cost Wi-Fi sensor-pod option**
- **Adafruit Feather ESP32-S3 2MB PSRAM = V9 primary wearable (analog PPG + GSR + DS18B20 + optional MPU6050/BME280/BH1750)**
- **Arduino Mega 2560 = bench/lab/expanded test controller**
- **ESP32 = legacy only**
- **Arduino Nano = legacy only**

## Start
```bash
./START.sh
```

Both workstations support DEMO MODE and LIVE SENSOR MODE. Desktop LIVE mode uses dynamically discovered USB serial ports and CRC-checked `$CP/$CP2/$CP3` packets. The V9 ESP32-S3 wearable uses the CP3 analog-PPG transport.

## Live paths
```
ESP8266 legacy pod ── Wi-Fi TCP ── legacy CP2 ──> compatible clients
ESP32-S3 V9 pod   ── USB/Wi-Fi TCP ── CP3 ──> V9 desktop workstations
Mega lab          ───── USB Serial ────────── CP2 ──> compatible clients
```

The V9 desktop path uses the Feather's CP3 protocol. Legacy CP2 devices remain supported for compatibility. The Android network path remains board-neutral for the legacy CP2 transport; V9 desktop is the primary end-to-end live validation path.

## Android
```bash
./setup_android.sh
./build_apks.sh all
```

Patient and Doctor remain native Kotlin + Compose + Material 3. Live mobile acquisition uses the validated CP2 TCP stream from the sensor pod; DEMO_DATA remains explicitly separated from live data.

> Research prototype — not a medical device, not clinically validated, not a diagnosis.
