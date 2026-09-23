# Installation Guide - CHRONO-PCOS V8.3+

## Overview

Local-first, offline-first, privacy-focused, Garuda Linux ready, Class 11 research innovation project.

Sense • Model • Predict • Personalize • Connect

Research / risk-screening output — not a medical diagnosis

## Quick Start - Garuda Linux

### Double-click Method (Recommended for Garuda/Dolphin)

1. Open file manager Dolphin
2. Navigate to CHRONO-PCOS V8.3+ project folder
3. Double-click `LAUNCH/COMPLETE_LAUNCHER.sh` or `COMPLETE_LAUNCHER.sh` in root
4. If Dolphin asks "What do you want to do with this file?" → Choose **Run**
5. If not executable: Right-click .sh → Properties → Permissions → Is executable checked

Dolphin Settings: Configure Dolphin → General → Executable files → Run

### Terminal Method

```bash
# Clone or extract project
cd chrono-pcos-v8.1

# Setup environment (Garuda/Linux generic)
./setup_garuda.sh
# Or
./SETUP.sh
# Or
./LAUNCH/SETUP.sh

# This does:
# - Detects project root (handles the LAUNCH/ subdirectory)
# - Checks Linux/Garuda (handles ID_LIKE unbound variable fixed)
# - Checks Python 3.10+
# - Creates .venv
# - Installs requirements.txt (PySide6, pyqtgraph, numpy, pandas, sklearn, etc)
# - Sets executable permissions for LAUNCH/*.sh
# - Creates logs/ directory
# - Runs diagnostics

# Launch Complete Control Center
./COMPLETE_LAUNCHER.sh
# Or
./LAUNCH/COMPLETE_LAUNCHER.sh
# Or
python launcher/main.py

# Or individual launchers
./LAUNCH/DOCTOR_PC.sh
./LAUNCH/PATIENT_APP.sh
./LAUNCH/FULL_SHOWCASE.sh
./LAUNCH/WEBSITE.sh
./LAUNCH/DIAGNOSTICS.sh
```

## Prerequisites

- Python 3.10+
- Garuda Linux / Arch Linux / Debian / Ubuntu
- 4GB RAM minimum
- 2GB disk space

## System Packages

### Garuda / Arch

```bash
sudo pacman -Syu
sudo pacman -S python python-pip python-venv base-devel libffi openssl libx11 libgl qt6-base
```

### Debian / Ubuntu

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv build-essential libffi-dev libssl-dev libgl1 libxcb-cursor0
```

## Python Environment

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

requirements.txt includes:

- PySide6 6.11.2 (80.1MB + 175.1MB)
- pyqtgraph 0.14.0
- numpy
- pandas
- scikit-learn
- pyserial
- kivy (for Android apps PC demo)

## Verification

```bash
./LAUNCH/DIAGNOSTICS.sh
# Or
./DIAGNOSTICS.sh
# Or
python -m launchers.diagnostics
```

Checks:

- Python PASS
- .venv PASS
- PySide6 PASS v6.11.2
- Core Deps PASS numpy pandas sklearn
- Database PASS 4 providers 18 tables
- Scientific Core PASS Feature extraction OK
- AI/ML PASS PCOS, Sleep, Cardio, Autonomic
- Ultrasound PASS Pipeline ready
- Doctor PC PASS Workstation ready
- Patient App PASS Kivy app ready
- Android APKs WARN Not built - use BUILD scripts (expected without SDK)
- Website PASS Static site ready
- Care Discovery PASS FIND CARE ready
- Chrono-Metabolic PASS Fingerprint engine

Actual checks never fake PASS.

## Android Prerequisites (Optional)

For APK building:

```bash
# Install Java
sudo pacman -S jdk-openjdk
# Or Debian
sudo apt install openjdk-17-jdk

# Install Android SDK/NDK
# Via Android Studio https://developer.android.com/studio
# Or via pacman
sudo pacman -S android-tools android-sdk android-ndk

# Set env
export ANDROID_SDK_ROOT=$HOME/Android/Sdk
export ANDROID_NDK_ROOT=$HOME/Android/Sdk/ndk/25.1.8937393
export PATH=$PATH:$ANDROID_SDK_ROOT/cmdline-tools/latest/bin:$ANDROID_SDK_ROOT/platform-tools

# Accept licenses
yes | sdkmanager --licenses

# Install buildozer + kivy
.venv/bin/pip install kivy buildozer cython

# Check
./BUILD_PATIENT_APK.sh --check-only
./BUILD_DOCTOR_APK.sh --check-only
```

See docs/ANDROID_BUILD_GUIDE.md for details.

## Directory Structure

```
chrono-pcos-v8.1/
  COMPLETE_LAUNCHER.sh - Root launcher, auto-detects project root
  SETUP.sh - Wrapper for setup_garuda.sh
  setup_garuda.sh - 10-step setup
  BUILD_PATIENT_APK.sh - Build Patient APK workflow
  BUILD_DOCTOR_APK.sh - Build Doctor APK workflow
  BUILD_ALL_APKS.sh - Build both
  LAUNCH/ - Individual launchers (20 scripts) + SETUP + BUILD

  launcher/main.py - Complete Control Center GUI 1450x950 polished
  desktop/doctor_app/main_enhanced.py - Doctor PC polished workstation
  android/patient_app/main.py - Patient Android Kivy
  android/doctor_app/main.py - Doctor Android Kivy
  core/ - Scientific core, signal processing, chrono-metabolic, analysis
  database/ - LocalDatabase 18 tables
  provider_network/ - Care discovery FIND CARE
  website/ - Public scientific website index.html 40K+ style.css script.js
  DIST/android/ - APK output CHRONO_PCOS_Patient.apk Doctor.apk
  logs/ - Build logs, diagnostics logs
  docs/ - 25+ docs
  demo/ - Full showcase 16 steps
  tests/ - Tests
  requirements.txt
```

## Launch Methods

1. Complete Control Center (recommended): `COMPLETE_LAUNCHER.sh` → polished GUI with categories PATIENT/DOCTOR/SCIENCE/CARE/DATA/PUBLIC/SYSTEM/ANDROID APK BUILD, AppCard min 320x180 max 400x220 WordWrap, status overview 4 cols, footer wrapping

2. Individual launchers: `LAUNCH/DOCTOR_PC.sh`, `LAUNCH/PATIENT_APP.sh`, etc - each auto-detects project root, uses .venv/bin/python, logs to logs/

3. Direct Python: `python launcher/main.py`, `python desktop/doctor_app/main_enhanced.py`, `python android/patient_app/main.py` (Kivy PC demo)

4. Website: `LAUNCH/WEBSITE.sh` opens `website/index.html` via xdg-open or python http.server

5. Android APK: `BUILD_PATIENT_APK.sh` builds APK to DIST/android/

## Troubleshooting

- `libGL.so.1: cannot open shared object file`: `sudo pacman -S libgl` or `sudo apt install libgl1`
- `ID_LIKE: unbound variable`: Fixed in setup_garuda.sh with `${ID:-} ${ID_LIKE:-} ${NAME:-}` guards
- `ModuleNotFoundError: No module named 'PySide6'`: Run `./setup_garuda.sh`
- `Permission denied`: `chmod +x LAUNCH/*.sh *.sh`
- `Dolphin asks Run/Display/Cancel`: Choose Run, or set Dolphin Settings → General → Executable files → Run
- `APK not built`: Expected without Android SDK/NDK, use PC demo via PATIENT_ANDROID.sh, BUILD scripts show honest reporting

See docs/TROUBLESHOOTING.md

## Safety

Research prototype not medical diagnosis, local-first offline privacy-focused, no cloud upload private health, no prescription sales, no treatment decisions, encourage professional consultation.

## Next Steps

- Read docs/GARUDA_LAUNCH_GUIDE.md for launch details
- Read docs/PROJECT_STATUS.md for the demo walkthrough and current status
- Read docs/ARCHITECTURE.md for system architecture
- Read docs/ANDROID_BUILD_GUIDE.md for APK building
- Run `./LAUNCH/FULL_SHOWCASE.sh` for science-fair demonstration
