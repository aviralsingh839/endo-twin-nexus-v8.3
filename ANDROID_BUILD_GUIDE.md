# Android Build Guide

The repository currently preserves native Kotlin + Jetpack Compose patient and doctor applications.

Prerequisites used by CI: JDK 17, Android SDK 34, Gradle wrapper.

From repository root:

    ./BUILD_PATIENT_APK.sh
    ./BUILD_DOCTOR_APK.sh
    ./BUILD_ALL_APKS.sh

The current CI workflow builds both debug APKs. Local environments must provide the required Java/Android toolchain.

Flutter/Riverpod/Dio/Drift/Melos remain a future shared-mobile architecture rather than replacing the working native apps in this milestone.
