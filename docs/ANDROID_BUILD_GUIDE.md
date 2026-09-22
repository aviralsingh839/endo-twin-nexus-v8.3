# ENDO-TWIN V8.6 Android Build Guide

Run from the repository root:
```bash
./setup_android.sh
./build_apks.sh patient
./build_apks.sh doctor
```

The setup helper auto-detects common Android SDK locations and writes the two required `local.properties` files.

Install to an attached Android device:
```bash
./build_apks.sh install-patient
./build_apks.sh install-doctor
```

The Android apps are native Kotlin + Compose. Their current mobile bridge transport is the controlled DEMO_DATA path; the desktop workstations are the canonical live USB sensor-processing surfaces.
