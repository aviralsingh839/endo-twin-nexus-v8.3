# ENDO-TWIN V8.6 Quick Start

## Start
```bash
./START.sh
```

Choose:
1. Doctor Workstation
2. Patient Workstation
3. ENDO-TWIN Platform

For Doctor or Patient Workstation, the next screen is the **startup-only DEMO MODE / LIVE SENSOR MODE** chooser.

## Live sensor
Choose LIVE SENSOR MODE, select the Arduino serial port, and start the session. The workstation validates packet CRCs and processes PPG/HRV, IMU, GSR and temperature data with visible quality gates.

## Demo
Choose DEMO MODE for the hardware-free exhibition stream. All synthetic values are visibly marked DEMO_DATA.

## Android
```bash
./setup_android.sh
./build_apks.sh all
```
