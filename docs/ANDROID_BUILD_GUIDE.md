# Android Build Guide - CHRONO-PCOS V8.3+

## Overview

Android applications must be ACTUALLY PACKAGED AS APKs, not simply run Python source on Linux.

We need:

- Patient Android APK: `DIST/android/CHRONO_PCOS_Patient.apk`
- Doctor Android APK: `DIST/android/CHRONO_PCOS_Doctor.apk`

Source preserved in:

- `android/patient_app/main.py` Kivy TabbedPanel Dashboard/Profile/Measurements/Symptoms/Cycle/Results/Find Care
- `android/doctor_app/main.py` Kivy patient list/search/profiles/recent measurements/trends/screening results/ultrasound/reports/notes/follow-up
- `android/patient_app/buildozer.spec` and `android/doctor_app/buildozer.spec`

Build scripts:

- `BUILD_PATIENT_APK.sh` - checks prerequisites, builds APK, logs to logs/build_patient_apk.log, output DIST/android/
- `BUILD_DOCTOR_APK.sh` - checks prerequisites, builds APK, logs to logs/build_doctor_apk.log
- `BUILD_ALL_APKS.sh` - builds both, check-only mode for environments without Android toolchain

Desktop launcher provides [BUILD PATIENT APK] [BUILD DOCTOR APK] [OPEN APK OUTPUT] via Complete Launcher.

## Prerequisites

### On Garuda Linux / Arch

```bash
# System packages
sudo pacman -Syu
sudo pacman -S python python-pip jdk-openjdk android-tools android-sdk android-ndk base-devel libffi openssl libx11 libgl

# Python dependencies
python -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
.venv/bin/pip install kivy buildozer cython

# Android SDK/NDK
# Install Android Studio or SDK via pacman or from https://developer.android.com/studio
# Set environment variables:
export ANDROID_SDK_ROOT=$HOME/Android/Sdk
export ANDROID_NDK_ROOT=$HOME/Android/Sdk/ndk/25.1.8937393
export PATH=$PATH:$ANDROID_SDK_ROOT/cmdline-tools/latest/bin:$ANDROID_SDK_ROOT/platform-tools

# Accept licenses
yes | sdkmanager --licenses

# Buildozer dependencies
sudo pacman -S autoconf automake libtool pkg-config
```

### Check Prerequisites

```bash
./BUILD_PATIENT_APK.sh --check-only
./BUILD_DOCTOR_APK.sh --check-only
./BUILD_ALL_APKS.sh
./LAUNCH/DIAGNOSTICS.sh
```

Each checks:

- Python3
- pip
- Buildozer (`command -v buildozer` or `.venv/bin/buildozer`)
- Kivy (`python -c 'import kivy'`)
- Java (`java -version`)
- Android SDK (`$HOME/Android/Sdk` or `$ANDROID_SDK_ROOT`)
- Android NDK (`$HOME/Android/Sdk/ndk` or `$ANDROID_NDK_ROOT`)

Outputs PASS/WARN/FAIL never fake.

If missing, explains exactly what is missing, provides setup/build script, preserves Android source, never claims APK exists when not.

## Building APKs

### Patient Android

```bash
./BUILD_PATIENT_APK.sh
# Or
./LAUNCH/PATIENT_ANDROID.sh  # Will show APK not built message and launch PC demo if no APK
# Or direct
cd android/patient_app
buildozer android debug
# Or with venv
../../.venv/bin/buildozer android debug
```

First build takes 10-30 minutes (downloads SDK/NDK, builds dependencies).

APK appears in:

- `android/patient_app/bin/*.apk`
- Copied to `DIST/android/CHRONO_PCOS_Patient.apk`

Logs: `logs/build_patient_apk.log`

Install on device:

```bash
adb install DIST/android/CHRONO_PCOS_Patient.apk
```

### Doctor Android

```bash
./BUILD_DOCTOR_APK.sh
cd android/doctor_app
buildozer android debug
adb install DIST/android/CHRONO_PCOS_Doctor.apk
```

### All APKs

```bash
./BUILD_ALL_APKS.sh
```

## Buildozer Configuration

`android/patient_app/buildozer.spec`:

```ini
[app]
title = CHRONO-PCOS Patient V8.3+
package.name = chronopcospatient
package.domain = org.chronopcos.patient
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,db
version = 8.3
requirements = python3,kivy,sqlite3
orientation = portrait
fullscreen = 0
android.permissions = INTERNET,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.api = 33
android.minapi = 21
android.ndk = 25b
android.sdk = 33
```

`android/doctor_app/buildozer.spec` similar with `chronopcosdoctor`.

Adapt after inspecting actual repository - currently simple, may need to add dependencies like `numpy`, `pandas` if used in Android (but Android apps use local SQLite, not heavy dependencies, offline-first).

## Android Application Quality - Proper Mobile UI

### Patient App

Dashboard:
- patient overview
- today's status
- physiological measurements (HR 72 bpm MEASURED quality 0.91, HRV RMSSD 48 ms DERIVED quality 0.85, Skin Temp 32.5°C MEASURED quality 0.88, Activity 35% MEASURED, Sleep Regularity 75% MODEL-INFERRED)
- trends (longitudinal changes)
- personal baseline (mean median std MAD rolling confidence min obs circadian context)
- alerts/flags
- education
- reports (professional with disclaimer Research / risk-screening output — not a medical diagnosis)
- privacy (local-first, no cloud upload default)
- synchronization/export (controlled export/import/backup/restore/encrypted package deliberate sharing not automatic)

Use clear language, never present model inference as diagnosis, understandable language Data quality Good not raw technical unless advanced, touch-friendly, large readable fonts, simple navigation tabs, multilingual-ready, offline-first.

### Doctor App

Dashboard:
- patient list (only authorized patients)
- patient profile (basic info anonymous_id age BMI USER-ENTERED)
- longitudinal trends (HR trend, HRV trend, activity trend, temp trend, baseline deviation)
- physiological signals (raw/filtered PPG HR HRV GSR motion temp quality artifacts visualization time-series)
- ultrasound analysis (image quality features provenance CLINICALLY-ENTERED vs IMAGE-DERIVED, no invented accuracy, quality gate UNKNOWN by design)
- model output (PCOSModule v8.3.0 pcos_associated_risk low confidence 0.75 data quality 0.85 clinical validation NOT ESTABLISHED, SleepModule, Cardiometabolic, Autonomic, model name/version/input/data quality/confidence/features/limitations never hide uncertainty)
- evidence/provenance (MEASURED CLINICALLY ENTERED IMAGE-DERIVED MODEL-INFERRED UNKNOWN clearly labeled)
- uncertainty (confidence model output not clinical certainty, quality scores 0-1)
- reports (professional research/clinical-review style not diagnosis)
- clinical notes (doctor notes follow-up)
- review workflow

Touch-friendly, mobile UI not desktop squeezed onto phone.

## Current Environment Limitation

In current build environment (Debian container, not Garuda, no Android SDK/NDK, no libGL), APKs cannot be built - honest reporting, not fake success:

- Detects missing prerequisites: Android SDK/NDK not found
- Explains exactly what is missing: Android SDK/NDK, Java, Buildozer dependencies
- Provides setup/build script: BUILD_PATIENT_APK.sh, BUILD_DOCTOR_APK.sh, BUILD_ALL_APKS.sh, setup_garuda.sh
- Preserves Android source: android/patient_app/main.py and android/doctor_app/main.py work PC demo
- Never claims APK exists when not: DIAGNOSTICS.sh shows WARN APK not built, PC demo available, BUILD scripts show ⚠ No APK found in android/patient_app/bin/, DIST/android/ empty, honest reporting

## Output Directory

Predictable directory:

```
DIST/
  android/
    CHRONO_PCOS_Patient.apk (if built)
    CHRONO_PCOS_Doctor.apk (if built)
    .gitkeep (placeholder if not built)
```

Desktop launcher provides [BUILD PATIENT APK] [BUILD DOCTOR APK] [OPEN APK OUTPUT] via Complete Launcher cards that launch build scripts.

## Troubleshooting

- `libGL.so.1: cannot open shared object file`: Install libgl via `sudo pacman -S libgl` or `sudo apt install libgl1` (Debian), on Garuda libgl is available
- `No module named 'PySide6'` or `kivy`: Run `./setup_garuda.sh` or `./SETUP.sh` to create .venv and install requirements
- `Android SDK not found`: Install Android Studio or SDK, set ANDROID_SDK_ROOT, run `sdkmanager --licenses`
- `Buildozer fails`: Check logs/build_*.log, ensure Java 17+, check buildozer.spec requirements, ensure network for downloads
- `APK not built`: Expected in environments without Android toolchain - PC demo available via PATIENT_APP.sh, DOCTOR_ANDROID.sh, honest reporting not fake

## Why Android?

Patient accessibility, doctor mobile review, offline-first, local SQLite, touch-friendly, low complexity, clear explanations, large readable, accessibility-friendly, multilingual-ready, privacy-focused, local-first.

APK via Buildozer appropriate for Class 11 research innovation project.

## No Fake Completion

Never fake an APK, never claim APK exists when not, never hide build failures, never hide missing dependencies. If something cannot be completed in current environment identify why, implement everything possible, create required setup/build mechanism, clearly report remaining limitation.

Current: Build infrastructure complete, source preserved, PC demo works, APK build scripts work check-only mode, actual APK building requires Android SDK/NDK - honest reporting.

## Final Deliverable

- Fully polished Android source (Kivy)
- Working PC demo via launchers
- Build scripts BUILD_PATIENT_APK.sh, BUILD_DOCTOR_APK.sh, BUILD_ALL_APKS.sh with prerequisite checks, logs, error reporting, output DIST/android/
- Documentation docs/ANDROID_BUILD_GUIDE.md
- No fake APKs
