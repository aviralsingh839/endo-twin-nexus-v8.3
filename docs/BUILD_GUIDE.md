# Build Guide - CHRONO-PCOS V8.3+

## Overview

Build from source, no heavy cloud, no expensive APIs, no proprietary paid, unnecessary frameworks avoided, prefer free/open-source keep Python/PySide6/PyQtGraph/NumPy/Pandas/PySerial do NOT introduce Dash/Plotly/Flask/Electron/browser dashboard unless architectural reason not replacing existing.

For Android select appropriate native/mobile tech communicating with local data/analysis Kivy Buildozer SQLite offline-first.

## Prerequisites

- Python 3.10+
- Git
- Garuda Linux / Arch / Debian / Ubuntu
- 4GB RAM
- 2GB disk

## Setup

```bash
git clone <repo> chrono-pcos-v8.1
cd chrono-pcos-v8.1

# Setup environment
./setup_garuda.sh
# Or
./SETUP.sh
# Or
./LAUNCH/SETUP.sh

# 10 steps:
# 1. Detect project root (handles LAUNCH/ launchers/ subdirs, fixes ID_LIKE unbound variable with ${ID:-} ${ID_LIKE:-} ${NAME:-} guards)
# 2. Check Linux/Garuda
# 3. Check Python 3.10+
# 4. Create .venv
# 5. Install requirements.txt (PySide6 6.11.2 80.1MB+175.1MB, pyqtgraph 0.14.0, numpy, pandas, sklearn, pyserial, kivy)
# 6. Set executable permissions for launchers/LAUNCH/*.sh BUILD_*.sh
# 7. Create logs/ directory
# 8. Create DIST/android/ directory
# 9. Run diagnostics (7 checks)
# 10. Report PASS/WARN/FAIL never fake
```

## Python Build

```bash
# .venv
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Verify
.venv/bin/python -c "import PySide6; print(PySide6.__version__)"
.venv/bin/python -c "import numpy, pandas, sklearn; print('deps OK')"
.venv/bin/python -c "from database.database import LocalDatabase; db=LocalDatabase(); print(db.list_providers())"
.venv/bin/python -c "from src.core.feature_extraction import RealtimeFeatureExtractor; print('core OK')"
```

## Launchers Build

No build needed - shell scripts.

```bash
chmod +x *.sh
chmod +x LAUNCH/*.sh
chmod +x launchers/*.sh
chmod +x BUILD_*.sh
chmod +x LAUNCH/BUILD*.sh
chmod +x launchers/BUILD*.sh

# Test
./LAUNCH/DIAGNOSTICS.sh
./DIAGNOSTICS.sh
./LAUNCH/COMPLETE_LAUNCHER.sh &
python launcher/main.py &
```

## Complete Control Center Build

```bash
# launcher/main.py - Polished Control Center 1450x950 min 1200x800
# AppCard Frame min 320x180 max 400x220 Expanding Fixed WordWrap title 30px 14px bold #0f172a desc 40-60px 11px #64748b status 30px 10px color detail[:50] tooltip full detail button 36px 12px bold #0ea5e9 radius 6px QFrame border 2px color radius 12px hover #0ea5e9 bg #f8fafc header_frame gradient #0f172a #1e293b radius 12px padding 10px title 32px bold white subtitle 18px #cbd5e1 letter-spacing 2px tagline 14px #0ea5e9 3px disclaimer #fbbf24 bg rgba border status overview grid 4 cols cards 200x60 max80 left border 4px category GroupBox border #cbd5e1 bg #f8fafc main_layout margins 20 spacing 16 scroll widgetResizable footer #0f172a wrapping info footer #f8fafc border responsive no clipped text overlapping Fusion style tooltip launcher details launch via SCRIPT_DIR PROJECT_ROOT detection non-blocking Popen

python launcher/main.py
# Or
./COMPLETE_LAUNCHER.sh
./LAUNCH/COMPLETE_LAUNCHER.sh
```

## Doctor PC Build

```bash
# desktop/doctor_app/main_enhanced.py - Polished Clinical/Research Workstation 1450x950
# Preserves src/ui/main_window.py, adds new architecture
# Dashboard, Patients, Signals, Longitudinal, Ultrasound, AI/ML, Reports, Data Provenance, Model Explanation, Database, Diagnostics
# Clearly separates OBSERVED, ASSOCIATED, MODEL-INFERRED, UNKNOWN, never mixes them

python desktop/doctor_app/main_enhanced.py
# Or
./LAUNCH/DOCTOR_PC.sh
./DOCTOR_PC.sh
```

## Patient App Build (PC Demo)

```bash
# android/patient_app/main.py - Kivy TabbedPanel Dashboard/Profile/Measurements/Symptoms/Cycle/Results/Find Care
# PC demo via Kivy, APK via Buildozer

python android/patient_app/main.py
# Or
./LAUNCH/PATIENT_APP.sh
./PATIENT_APP.sh
```

## Doctor Android Build (PC Demo)

```bash
python android/doctor_app/main.py
./LAUNCH/DOCTOR_ANDROID.sh
```

## Android APK Build

See docs/ANDROID_BUILD_GUIDE.md for details.

```bash
# Prerequisites check
./BUILD_PATIENT_APK.sh --check-only
./BUILD_DOCTOR_APK.sh --check-only
./BUILD_ALL_APKS.sh
./LAUNCH/BUILD_PATIENT_APK.sh --check-only
./LAUNCH/BUILD_DOCTOR_APK.sh --check-only
./LAUNCH/BUILD_ALL_APKS.sh

# Checks:
# - Python3 PASS/WARN/FAIL
# - pip
# - Buildozer (command -v buildozer or .venv/bin/buildozer)
# - Kivy (python -c 'import kivy')
# - Java (java -version)
# - Android SDK ($HOME/Android/Sdk or $ANDROID_SDK_ROOT)
# - Android NDK ($HOME/Android/Sdk/ndk or $ANDROID_NDK_ROOT)
# Outputs PASS/WARN/FAIL never fake
# If missing, explains exactly what is missing, provides setup/build script, preserves Android source, never claims APK exists when not

# Build APK (requires SDK/NDK, 10-30 min first time)
./BUILD_PATIENT_APK.sh
./BUILD_DOCTOR_APK.sh
./BUILD_ALL_APKS.sh

# Or direct
cd android/patient_app
buildozer android debug
# Or with venv
../../.venv/bin/buildozer android debug

# Output
# android/patient_app/bin/*.apk
# Copied to DIST/android/CHRONO_PCOS_Patient.apk
# Logs: logs/build_patient_apk.log

# Install on device
adb install DIST/android/CHRONO_PCOS_Patient.apk
```

Current environment (Debian container, no SDK/NDK, no libGL) APKs cannot be built - honest reporting, not fake success:

- Detects missing prerequisites: Android SDK/NDK not found
- Explains exactly what is missing
- Provides setup/build script
- Preserves Android source
- Never claims APK exists when not
- DIAGNOSTICS.sh shows WARN APK not built, PC demo available

## Website Build

No build needed - static site.

```bash
# website/index.html 40K+ extensive scientific site
# website/style.css polished modern CSS variables primary #0f172a accent #0ea5e9 shadows sm/md/lg header sticky gradient nav flex wrap hero gradient 135deg radial overlay architecture-preview backdrop blur section 4rem alt #f8fafc grid gap 1.5rem card hover -2px shadow-md flow-step border-left 4px accent timeline dot 44px active dot accent provider-card demo #fffbeb yellow left warning-box gradient #fef2f2 #fee2e2 left red footer gradient responsive 1024 768 no excessive animations
# website/script.js minimal JS smooth scroll pushState highlightNav scrollY active link background rgba(14,165,233,0.2) IntersectionObserver fade-in opacity 0→1 translateY 10→0 0.4s console logs integrity

./LAUNCH/WEBSITE.sh
./WEBSITE.sh
# Or
python -m http.server 8000 --directory website
# Then open http://localhost:8000
# Or
xdg-open website/index.html
```

## Database Build

```bash
# database/database.py LocalDatabase 18 tables local-first
# Tables: users patients profiles symptoms cycles sensor_sessions ppg_data hrv_data gsr_data motion_data temperature_data sensor_quality ultrasound_records model_results analysis_results reports doctor_notes providers supplies audit_records patient_doctor_access
# Methods: create_user authenticate create_patient get_patient list_patients search log_symptom log_cycle create_session list_providers search_providers get_nearby_providers list_supplies create_report add_doctor_note grant_access check_access export import backup
# Demo: 4 providers clearly marked demo 5 supplies

python -c "from database.database import LocalDatabase; db=LocalDatabase(); print('providers', len(db.list_providers()), 'supplies', len(db.list_supplies()))"
./LAUNCH/DATABASE.sh
```

## Scientific Core Build

```bash
# core/ scientific core, signal processing, chrono-metabolic, analysis
# src/core/feature_extraction.py RealtimeFeatureExtractor
# src/disease_modules/ pcos sleep cardiometabolic autonomic

python -c "from src.core.feature_extraction import RealtimeFeatureExtractor; print('core OK')"
./LAUNCH/SCIENTIFIC_CORE.sh
./LAUNCH/SIGNAL_PROCESSING.sh
./LAUNCH/CHRONO_METABOLIC.sh
./LAUNCH/AI_ML.sh
./LAUNCH/ULTRASOUND.sh
```

## Full Showcase Build

```bash
# demo/full_showcase.py 16 steps polished GUI 1450x950 NEXT/SKIP/EXIT non-blocking console fallback

python demo/full_showcase.py
./LAUNCH/FULL_SHOWCASE.sh
./FULL_SHOWCASE.sh
```

## Care Discovery Build

```bash
# provider_network/care_discovery.py CareDiscoveryEngine FIND CARE

python -c "from provider_network.care_discovery import CareDiscoveryEngine; e=CareDiscoveryEngine(); print(e.search_providers())"
./LAUNCH/CARE_FINDER.sh
```

## Testing Build

```bash
# tests/ tests for DB/sensor/signal/artifact/missing/reconnection/permissions/report/import/export/Android UI/PC UI/AI/ultrasound plus failures unplug/corrupt/no internet/empty DB/invalid/damaged image/interrupted/duplicate/unauthorized

pytest tests/ -v
# Or
python -m pytest tests/ -v
./LAUNCH/DIAGNOSTICS.sh
```

## Performance

Ordinary hardware avoid heavy cloud/expensive APIs/proprietary/unnecessary frameworks keep Python/PySide6/PyQtGraph/NumPy/Pandas/PySerial no Dash/Plotly/Flask/Electron unless reason Android appropriate native/mobile offline SQLite.

## No Fake Features

Real or prototype labeled, never fake APK, never claim APK exists when not, never hide build failures, never hide missing dependencies, if something cannot be completed identify why, implement everything possible, create required setup/build mechanism, clearly report remaining limitation.

Current: Build infrastructure complete, source preserved, PC demo works, APK build scripts work check-only mode, actual APK building requires Android SDK/NDK - honest reporting.

## Final Deliverable

- Fully polished Python source (PySide6, Kivy, SQLite, NumPy, Pandas)
- Working PC demo via launchers
- Build scripts BUILD_PATIENT_APK.sh BUILD_DOCTOR_APK.sh BUILD_ALL_APKS.sh with prerequisite checks logs error reporting output DIST/android/
- Documentation docs/ANDROID_BUILD_GUIDE.md docs/BUILD_GUIDE.md docs/INSTALLATION.md docs/GARUDA_LAUNCH_GUIDE.md docs/SHOWCASE_GUIDE.md
- No fake APKs
