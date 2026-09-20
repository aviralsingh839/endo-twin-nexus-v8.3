# ENDO-TWIN V8.5 Android Build Guide

Run from repo root:
```bash
./setup_android.sh
./build_apks.sh patient
./build_apks.sh doctor
```

SDK paths are auto-detected and both `local.properties` files are generated automatically.

Install:
```bash
./build_apks.sh install-patient
./build_apks.sh install-doctor
```
