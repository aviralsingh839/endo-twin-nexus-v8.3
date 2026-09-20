# INSTALLATION - ENDO-TWIN V8.3+

Date: 2026-09-19
Version: 8.3+
Status: IMPLEMENTED

## System Requirements

- OS: Garuda Linux / Arch (recommended), or any Linux, macOS, Windows with Python
- Python: 3.11+
- RAM: 4GB minimum, 8GB recommended (ordinary hardware)
- Storage: 2GB for code + models (17M + 5.1M) + .venv
- No GPU required, no cloud required, offline-first

## Quick Install

```bash
git clone https://github.com/aviralsingh839/chrono-pcos-v8.1.git
cd chrono-pcos-v8.1
./setup_garuda.sh
```

`setup_garuda.sh` does:
- System packages check (python, pip, jdk-openjdk, android-tools, android-sdk, base-devel, libffi, openssl, libx11, libgl)
- Python venv creation .venv
- pip upgrade
- pip install -r requirements.txt
- pip install kivy buildozer cython
- Android SDK/NDK check
- Logs to logs/setup.log

## Manual Install

```bash
# System packages (Garuda/Arch)
sudo pacman -Syu
sudo pacman -S python python-pip jdk-openjdk android-tools android-sdk android-ndk base-devel libffi openssl libx11 libgl

# Python venv
python -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
.venv/bin/pip install kivy buildozer cython
.venv/bin/pip install PySide6 PyQtGraph numpy pandas scikit-learn joblib

# Android SDK/NDK
# Install Android Studio or SDK via pacman or https://developer.android.com/studio
export ANDROID_SDK_ROOT=$HOME/Android/Sdk
export ANDROID_NDK_ROOT=$HOME/Android/Sdk/ndk/25.1.8937393
export PATH=$PATH:$ANDROID_SDK_ROOT/cmdline-tools/latest/bin:$ANDROID_SDK_ROOT/platform-tools

# Accept licenses
yes | sdkmanager --licenses

# Buildozer deps
sudo pacman -S autoconf automake libtool pkg-config
```

## Check Installation

```bash
./START.sh health
# Or
./scripts/diagnostics/project_health.sh
# Or
./BUILD_ALL_APKS.sh --check-only
./LAUNCH/DIAGNOSTICS.sh
```

Checks: Python3, pip, Buildozer, Kivy, Java, Android SDK, Android NDK, .venv, database, models, launchers, Android Gradle wrapper real not placeholder.

Outputs PASS/WARN/FAIL never fake.

## Android SDK

For real Gradle builds `./gradlew assembleDebug` (not placeholder):

- JDK 17+ required - `java -version`
- Android SDK 34 compileSdk, minSdk 24 targetSdk 34
- Real wrapper: android/patient/gradle/wrapper/gradle-wrapper.jar 61K + gradlew 8.4K script (not placeholder echo exit 1)
- Build: `cd android/patient && ./gradlew assembleDebug` → `app/build/outputs/apk/debug/app-debug.apk` → `artifacts/android/endo-twin-patient-debug.apk`
- Same for doctor
- If no SDK, build fails with env limitation documented: JAVA_HOME not set, no java, no Android SDK - real wrapper exists and attempted build

## Kivy Android

For Kivy APKs via Buildozer:

```bash
./BUILD_PATIENT_APK.sh
# Or
cd android/patient_app
buildozer android debug
# APK: android/patient_app/bin/*.apk → DIST/android/CHRONO_PCOS_Patient.apk
# Logs: logs/build_patient_apk.log
```

First build takes 10-30 minutes (downloads SDK/NDK, builds dependencies).

## Offline-First

Core works without internet: records/sensor/signal/AI/ultrasound/reports/DB

Internet optional: provider directory/map/updates/controlled sync

No cloud required, local-first SQLite, no upload private health to public website.

## Troubleshooting

See `docs/TROUBLESHOOTING.md` and `logs/` for logs.

Common:
- .venv not found → run ./setup_garuda.sh
- Java not found → install jdk-openjdk, set JAVA_HOME
- Android SDK not found → install Android Studio, set ANDROID_SDK_ROOT, accept licenses
- Gradle wrapper placeholder → fixed real wrapper 61K jar + 8.4K script, if still placeholder run git pull
- PySide6 not available → console mode only, install pip install PySide6
