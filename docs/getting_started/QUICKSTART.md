# QUICKSTART - ENDO-TWIN / CHRONO-PCOS V8.3+

Date: 2026-09-19
Version: 8.3+
Status: IMPLEMENTED
Purpose: Quick start guide for new users

## One Launcher System

No need to hunt through dozens of scripts - one canonical entry:

```bash
./START.sh
```

Interactive menu with 12 options:
1. ENDO-TWIN - General physiological modelling platform
2. Doctor Desktop - Multipatient workstation
3. Patient Demo - Patient Android PC demo
4. Research Lab - Signal processing, training, evaluation
5. Diagnostics - System diagnostics
6. Build Patient APK - Kivy + Native Gradle
7. Build Doctor APK - Kivy + Native Gradle
8. Build All APKs - Both
9. Run Tests - pytest + acceptance + isolation
10. Performance Benchmark - Real measurements
11. Project Health - Dependencies, DB, models, launchers, Android Gradle
12. Exit

## Quick Commands

```bash
# Clone and setup (original repo)
git clone https://github.com/aviralsingh839/chrono-pcos-v8.1.git
cd chrono-pcos-v8.1

# Setup environment (Garuda Linux / Arch)
./setup_garuda.sh
# Or
./SETUP.sh

# Check health
./scripts/diagnostics/project_health.sh
# Or
./START.sh health

# Run ENDO-TWIN general dashboard
./START.sh endo-twin
# Or
./START.sh gui

# Run Doctor Desktop
./START.sh doctor

# Run Patient Demo
./START.sh patient

# Build APKs (real Gradle wrapper, not placeholder)
./START.sh build-gradle
# Real command:
# cd android/patient && ./gradlew assembleDebug
# APK: android/patient/app/build/outputs/apk/debug/app-debug.apk → artifacts/android/endo-twin-patient-debug.apk
# Same for doctor

# Run tests
pytest -q
# Or
./START.sh test

# Cross-patient isolation
./START.sh test-cross

# Performance benchmark
./START.sh benchmark
# See docs/performance/PERFORMANCE_REPORT.md

# Project health
./scripts/diagnostics/project_health.sh
```

## Prerequisites

- Python 3.11+
- .venv with PySide6, NumPy, Pandas, scikit-learn, joblib, Kivy, Buildozer
- JDK 17+ for Android Gradle builds
- Android SDK 34 for Android builds
- No cloud required - offline-first local-first

See `docs/getting_started/INSTALLATION.md` for detailed installation.

## Architecture

ENDO-TWIN is platform, CHRONO-PCOS is first disease-specific model.

```
ENDO-TWIN Core: src/endo_twin/ + src/core/ + src/signal_processing/
Patient Android: android/patient_app/ (Kivy) + android/patient/ (Native Kotlin)
Doctor Android: android/doctor_app/ (Kivy) + android/doctor/ (Native Kotlin)
Doctor PC: desktop/doctor_app/ + launcher/
Local DB: database/ + data/
```

## Safety

Research / risk-screening output — not a medical diagnosis. Requires clinical evaluation.

## Demo Data

DEMO-001, DEMO-002, DEMO-003 with intentionally different data HR 72/78/68, clearly labeled DEMO_DATA, separate from private records, no cross-contamination PASS 7 FAIL 0.
