# ENDO-TWIN V8.4 Build Guide

## Fast path

### Patient APK

    cd android/patient
    ./gradlew assembleDebug

Output:

    android/patient/app/build/outputs/apk/debug/app-debug.apk

### Doctor APK

    cd android/doctor
    ./gradlew assembleDebug

Output:

    android/doctor/app/build/outputs/apk/debug/app-debug.apk

## One-command project checks

    ./START.sh health
    ./START.sh test

## Build all native Android apps

    ./START.sh build-gradle

The launcher only reports an APK when a real APK file was produced.

## Toolchain

The native apps use Gradle + Android Gradle Plugin + Kotlin + Jetpack Compose + Room.

The repository includes a Gradle wrapper for both apps, so a globally installed Gradle executable is not required.

For local Android development use a JDK 17 environment and an Android SDK containing API 34/build tools 34.0.0.

## CI artifacts

Every push/PR runs the Python quality gate and builds both debug APKs in GitHub Actions. Successful runs publish:

- endo-twin-patient-debug
- endo-twin-doctor-debug

as workflow artifacts.

## Scientific non-negotiables

A build is not considered complete merely because it compiles. The system must preserve provenance, uncertainty, patient scope, demo separation, and the research-only status of disease-model output.
