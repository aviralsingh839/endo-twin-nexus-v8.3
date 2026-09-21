# ENDO-TWIN Complete Build Guide

## 1. Clone

    git clone https://github.com/aviralsingh839/endo-twin-nexus-v8.3.git
    cd endo-twin-nexus-v8.3

## 2. Python environment

    python3 --version
    python3 -m venv .venv
    . .venv/bin/activate
    python -m pip install --upgrade pip
    pip install -r requirements.txt

## 3. Core checks

    python -m compileall -q src disease_models database apps tests
    pytest -q
    python apps/main/main_app.py

## 4. Canonical launcher

    ./START.sh help
    ./START.sh endo-twin
    ./START.sh doctor
    ./START.sh doctor-test
    ./START.sh test
    ./START.sh health

## 5. Doctor Test Workstation

    ./START.sh doctor-test

Create a test patient, create a DEMO_DATA session, and execute explicit infrastructure/sensor-state checks. A missing sensor becomes an explicit failure; no physiological value is synthesized.

## 6. Native Android builds

Requirements: JDK 17 and Android SDK 34.

    ./BUILD_PATIENT_APK.sh
    ./BUILD_DOCTOR_APK.sh
    ./BUILD_ALL_APKS.sh

Direct Gradle:

    cd android/patient && ./gradlew clean assembleDebug
    cd ../doctor && ./gradlew clean assembleDebug

## 7. Hardware

Read HARDWARE_BUILD_GUIDE.md, WIRING_GUIDE.md, WEARABLE_MEASUREMENT_SPEC.md, SENSOR_CALIBRATION_GUIDE.md and SENSOR_TESTING_GUIDE.md before connecting a sensor.

Record the exact breakout/module variants before freezing pin assignments. Never guess a pinout from a chip name.

## 8. Evidence rule

Only report a command as PASS after actually executing it. CI configuration is present for Python tests and both Android debug builds. The current development environment may not have a usable Android SDK/JDK or installed research packages.

## 9. Safety

Research prototype only. Not a medical device and not clinically validated. Do not use model output as diagnosis.
