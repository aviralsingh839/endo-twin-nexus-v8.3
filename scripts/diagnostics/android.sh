#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"
echo "=== Android Build Diagnostics ==="
echo "Checking real gradlew..."
ls -lh "$PROJECT_ROOT/android/patient/gradle/wrapper/gradle-wrapper.jar" || echo "Patient wrapper jar missing"
ls -lh "$PROJECT_ROOT/android/doctor/gradle/wrapper/gradle-wrapper.jar" || echo "Doctor wrapper jar missing"
ls -lh "$PROJECT_ROOT/android/patient/gradlew" || echo "Patient gradlew missing"
ls -lh "$PROJECT_ROOT/android/doctor/gradlew" || echo "Doctor gradlew missing"
echo "Attempting real builds..."
./START.sh build-gradle
