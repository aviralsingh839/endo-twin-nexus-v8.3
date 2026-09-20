# ENDO-TWIN V8.6 Build Guide

## One entry point
```bash
./START.sh
```

Doctor Workstation:
```bash
./START.sh doctor
```

Patient Workstation:
```bash
./START.sh patient-pc
```

Each workstation asks for **DEMO MODE** or **LIVE SENSOR MODE** before opening.

## Android
```bash
./setup_android.sh
./build_apks.sh all
```

Install:
```bash
./build_apks.sh install-patient
./build_apks.sh install-doctor
```

## Live sensor
For LIVE SENSOR MODE, connect the Arduino by USB and choose its serial port. The workstation requires CRC-checked $CP/$CP2 packets and then runs the existing signal-processing pipeline.

## Mobile bridge
Doctor Workstation uses port 7777. Patient Workstation uses 7778. The current Android transport path is deliberately DEMO_DATA and is documented separately.
