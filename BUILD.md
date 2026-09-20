# ENDO-TWIN V8.6 — Build & Run

## Canonical launcher
```bash
./START.sh
```

## Workstations
```bash
./START.sh doctor
./START.sh patient-pc
```

At startup, choose **DEMO MODE** or **LIVE SENSOR MODE**. The choice is fixed for the session.

## Android
```bash
./setup_android.sh
./build_apks.sh all
```

Outputs are copied to `DIST/android/`.

## Live USB sensor
Connect the Arduino and choose LIVE SENSOR MODE. The workstation reads the existing CRC-protected `$CP/$CP2` protocol and processes the received stream. The firmware's internal sensor sampling rate is not confused with the approximately 20 Hz PC packet rate.

## Mobile bridge
Doctor Workstation: port **7777**.
Patient Workstation: port **7778**.

The current phone transport path remains DEMO_DATA and is not a replacement for clinically validated acquisition or secure production health infrastructure.
