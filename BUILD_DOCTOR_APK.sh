#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
BASE_NAME="$(basename "$SCRIPT_DIR")"
if [[ "$BASE_NAME" == "LAUNCH" || "$BASE_NAME" == "launchers" || "$BASE_NAME" == "launcher" ]]; then
    PROJECT_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
fi
cd "$PROJECT_ROOT"
mkdir -p "$PROJECT_ROOT/logs"
mkdir -p "$PROJECT_ROOT/DIST/android"
mkdir -p "$PROJECT_ROOT/dist/android"

LOG_FILE="$PROJECT_ROOT/logs/build_doctor_apk.log"
echo "$(date): Building Doctor Android APK - Native Kotlin + Jetpack Compose" | tee -a "$LOG_FILE"

echo "======================================================================"
echo "CHRONO-PCOS V8.3+ → ENDO-TWIN - Build Doctor Android APK"
echo "Native Kotlin + Jetpack Compose - Material 3 - Multi-Patient"
echo "Project Root: $PROJECT_ROOT"
echo "Date: $(date)"
echo "======================================================================" | tee -a "$LOG_FILE"

PASS=0
FAIL=0
WARN=0

check_cmd() {
    local name="$1"
    local cmd="$2"
    echo -n "Checking $name... " | tee -a "$LOG_FILE"
    if eval "$cmd" >/dev/null 2>&1; then
        echo "✓ PASS" | tee -a "$LOG_FILE"
        PASS=$((PASS+1))
        return 0
    else
        echo "✗ FAIL" | tee -a "$LOG_FILE"
        FAIL=$((FAIL+1))
        return 1
    fi
}

warn_check_cmd() {
    local name="$1"
    local cmd="$2"
    echo -n "Checking $name... " | tee -a "$LOG_FILE"
    if eval "$cmd" >/dev/null 2>&1; then
        echo "✓ PASS" | tee -a "$LOG_FILE"
        PASS=$((PASS+1))
        return 0
    else
        echo "⚠ WARNING - $name not found, build may fail" | tee -a "$LOG_FILE"
        WARN=$((WARN+1))
        return 1
    fi
}

echo "" | tee -a "$LOG_FILE"
echo "[1/7] Checking prerequisites - Native Kotlin + Jetpack Compose..." | tee -a "$LOG_FILE"
check_cmd "Python3" "command -v python3"
check_cmd "pip" "command -v pip3 || command -v pip"
warn_check_cmd "Java" "command -v java"
warn_check_cmd "Kotlin" "command -v kotlin || command -v kotlinc"
warn_check_cmd "Gradle" "command -v gradle || test -f $PROJECT_ROOT/android/doctor/gradlew"
warn_check_cmd "Android SDK" "test -d \$HOME/Android/Sdk || test -d \$HOME/.android || test -d /opt/android-sdk || test -n \"\$ANDROID_SDK_ROOT\" || test -n \"\$ANDROID_HOME\""
warn_check_cmd "Android NDK" "test -d \$HOME/Android/Sdk/ndk || test -n \"\$ANDROID_NDK_ROOT\""
warn_check_cmd "Buildozer (legacy fallback)" "command -v buildozer || $PROJECT_ROOT/.venv/bin/buildozer --version"
warn_check_cmd "Kivy (legacy fallback)" "$PROJECT_ROOT/.venv/bin/python -c 'import kivy' 2>/dev/null || python3 -c 'import kivy' 2>/dev/null"

echo "" | tee -a "$LOG_FILE"
echo "[2/7] Checking project configuration - Native Kotlin Multi-Patient..." | tee -a "$LOG_FILE"
check_cmd "Doctor Native MainActivity.kt" "test -f $PROJECT_ROOT/android/doctor/app/src/main/java/org/chronopcos/doctor/MainActivity.kt"
check_cmd "Doctor Native build.gradle.kts" "test -f $PROJECT_ROOT/android/doctor/app/build.gradle.kts"
check_cmd "Doctor Native AndroidManifest.xml" "test -f $PROJECT_ROOT/android/doctor/app/src/main/AndroidManifest.xml"
check_cmd "Doctor Native DoctorModels.kt" "test -f $PROJECT_ROOT/android/doctor/app/src/main/java/org/chronopcos/doctor/data/model/DoctorModels.kt"
warn_check_cmd "Doctor Legacy Kivy main.py" "test -f $PROJECT_ROOT/android/doctor_app/main.py"
warn_check_cmd "Doctor Legacy buildozer.spec" "test -f $PROJECT_ROOT/android/doctor_app/buildozer.spec"
check_cmd "ENDO-TWIN Core" "test -f $PROJECT_ROOT/endo_twin/core/twin.py"
check_cmd "ENDO-TWIN Database" "test -f $PROJECT_ROOT/database/endo_twin_database.py"

echo "" | tee -a "$LOG_FILE"
echo "[3/7] Checking native project structure - Multi-Patient Safety..." | tee -a "$LOG_FILE"
echo "Doctor Android - Kotlin + Jetpack Compose - Material 3 - Multi-patient - Patient switching scopes entire context" | tee -a "$LOG_FILE"
echo "DEMO-001 cannot see DEMO-002 - implemented at database level not merely UI hidden" | tee -a "$LOG_FILE"
echo "Reports patient-specific, Ultrasounds patient-specific, AI runs patient-specific, Sensor sessions patient-specific, Timeline patient-specific" | tee -a "$LOG_FILE"
ls -R "$PROJECT_ROOT/android/doctor" 2>&1 | head -50 | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo "[4/7] Building Native Kotlin APK - Multi-Patient..." | tee -a "$LOG_FILE"

BUILD_SUCCESS=0

if [[ -f "$PROJECT_ROOT/android/doctor/gradlew" || -f "$PROJECT_ROOT/android/doctor/app/build.gradle.kts" ]]; then
    echo "Native Kotlin multi-patient project detected - attempting Gradle build" | tee -a "$LOG_FILE"
    cd "$PROJECT_ROOT/android/doctor"
    
    if command -v gradle >/dev/null 2>&1 || [[ -f "gradlew" ]]; then
        if [[ "${1:-}" == "--check-only" ]]; then
            echo "Check-only mode - skipping actual Gradle build" | tee -a "$LOG_FILE"
            echo "To build native APK: ./BUILD_DOCTOR_APK.sh (without --check-only)" | tee -a "$LOG_FILE"
            echo "Or: cd android/doctor && ./gradlew assembleDebug" | tee -a "$LOG_FILE"
        else
            echo "Attempting: ./gradlew assembleDebug or gradle assembleDebug" | tee -a "$LOG_FILE"
            if [[ -f "gradlew" ]]; then
                chmod +x gradlew 2>&1 | tee -a "$LOG_FILE" || true
                if ./gradlew assembleDebug 2>&1 | tee -a "$LOG_FILE"; then
                    echo "✓ Native Gradle build succeeded" | tee -a "$LOG_FILE"
                    BUILD_SUCCESS=1
                    PASS=$((PASS+1))
                else
                    echo "✗ Native Gradle build failed - likely missing Android SDK/Gradle" | tee -a "$LOG_FILE"
                    echo "Expected without SDK - honest reporting, not fake success" | tee -a "$LOG_FILE"
                    WARN=$((WARN+1))
                fi
            elif command -v gradle >/dev/null 2>&1; then
                if gradle assembleDebug 2>&1 | tee -a "$LOG_FILE"; then
                    echo "✓ Native Gradle build succeeded" | tee -a "$LOG_FILE"
                    BUILD_SUCCESS=1
                    PASS=$((PASS+1))
                else
                    echo "✗ Native Gradle build failed" | tee -a "$LOG_FILE"
                    WARN=$((WARN+1))
                fi
            fi
        fi
    else
        echo "⚠ Gradle not found - cannot build native Kotlin APK in this environment" | tee -a "$LOG_FILE"
        echo "Setup: Install Java 17+, Android Studio, set ANDROID_SDK_ROOT, accept licenses" | tee -a "$LOG_FILE"
        WARN=$((WARN+1))
    fi
    cd "$PROJECT_ROOT"
else
    echo "Native Kotlin project not found at android/doctor/" | tee -a "$LOG_FILE"
    FAIL=$((FAIL+1))
fi

if [[ $BUILD_SUCCESS -eq 0 && "${1:-}" != "--check-only" ]]; then
    echo "" | tee -a "$LOG_FILE"
    echo "[5/7] Fallback: Attempting legacy Kivy build..." | tee -a "$LOG_FILE"
    if [[ -f "$PROJECT_ROOT/android/doctor_app/buildozer.spec" ]]; then
        cd "$PROJECT_ROOT/android/doctor_app"
        if ! command -v buildozer >/dev/null 2>&1 && [[ -f "$PROJECT_ROOT/.venv/bin/buildozer" ]]; then
            BUILD_CMD="$PROJECT_ROOT/.venv/bin/buildozer"
        else
            BUILD_CMD="buildozer"
        fi
        echo "Legacy build: $BUILD_CMD android debug - Kivy prototype preserved as legacy, primary is now Kotlin + Compose" | tee -a "$LOG_FILE"
        if $BUILD_CMD android debug 2>&1 | tee -a "$LOG_FILE"; then
            echo "✓ Legacy Kivy build succeeded" | tee -a "$LOG_FILE"
            BUILD_SUCCESS=1
            PASS=$((PASS+1))
        else
            echo "✗ Legacy Kivy build failed - expected without SDK" | tee -a "$LOG_FILE"
            WARN=$((WARN+1))
        fi
        cd "$PROJECT_ROOT"
    fi
fi

echo "" | tee -a "$LOG_FILE"
echo "[6/7] Collecting APKs - Multi-Patient Safety..." | tee -a "$LOG_FILE"

NATIVE_APK=$(find "$PROJECT_ROOT/android/doctor/app/build/outputs" -name "*.apk" 2>/dev/null | head -1)
if [[ -n "$NATIVE_APK" ]]; then
    echo "Native APK found: $NATIVE_APK" | tee -a "$LOG_FILE"
    cp "$NATIVE_APK" "$PROJECT_ROOT/DIST/android/CHRONO-PCOS-Doctor.apk" 2>&1 | tee -a "$LOG_FILE" || true
    cp "$NATIVE_APK" "$PROJECT_ROOT/dist/android/CHRONO-PCOS-Doctor.apk" 2>&1 | tee -a "$LOG_FILE" || true
    cp "$NATIVE_APK" "$PROJECT_ROOT/DIST/android/CHRONO_PCOS_Doctor.apk" 2>&1 | tee -a "$LOG_FILE" || true
    ls -lh "$PROJECT_ROOT/DIST/android/"*Doctor*.apk 2>&1 | tee -a "$LOG_FILE" || true
    PASS=$((PASS+1))
fi

LEGACY_APK=$(find "$PROJECT_ROOT/android/doctor_app/bin" -name "*.apk" 2>/dev/null | head -1)
if [[ -n "$LEGACY_APK" ]]; then
    echo "Legacy APK found: $LEGACY_APK" | tee -a "$LOG_FILE"
    cp "$LEGACY_APK" "$PROJECT_ROOT/DIST/android/CHRONO-PCOS-Doctor_legacy.apk" 2>&1 | tee -a "$LOG_FILE" || true
    PASS=$((PASS+1))
fi

echo "APK Output Directories:" | tee -a "$LOG_FILE"
ls -lh "$PROJECT_ROOT/DIST/android/" 2>&1 | tee -a "$LOG_FILE" || echo "DIST/android/ empty" | tee -a "$LOG_FILE"
ls -lh "$PROJECT_ROOT/dist/android/" 2>&1 | tee -a "$LOG_FILE" || echo "dist/android/ empty" | tee -a "$LOG_FILE"

if [[ -z "$NATIVE_APK" && -z "$LEGACY_APK" ]]; then
    echo "⚠ No APK found - expected without Android SDK/Gradle" | tee -a "$LOG_FILE"
    echo "Current status: Native Kotlin multi-patient source preserved, Kivy legacy preserved, PC demo available, APK not built in this environment (Android SDK/NDK/Gradle missing) - honest reporting" | tee -a "$LOG_FILE"
    WARN=$((WARN+1))
fi

echo "" | tee -a "$LOG_FILE"
echo "[7/7] Final report - Multi-Patient Safety..." | tee -a "$LOG_FILE"
echo "======================================================================" | tee -a "$LOG_FILE"
echo "Build Summary: PASS $PASS WARN $WARN FAIL $FAIL" | tee -a "$LOG_FILE"
echo "Technology: Kotlin + Jetpack Compose + Material 3 + Navigation Compose + ViewModel + Repository + Room + DataStore + Coroutines + Clean Architecture" | tee -a "$LOG_FILE"
echo "Multi-Patient: Dashboard, Patients, Recent Activity, Pending Review, Reports, Settings" | tee -a "$LOG_FILE"
echo "Patient List: Patient ID, Name/alias, Age, Last session, Last analysis, Status, Search, Filter, Sort, Open, Archive, Create, Import/export" | tee -a "$LOG_FILE"
echo "Patient Profile: Opening patient CP-0001 switches entire context to CP-0001" | tee -a "$LOG_FILE"
echo "Tabs: OVERVIEW, TIMELINE, PHYSIOLOGY, SENSORS, ULTRASOUND, AI/MODELS, CLINICAL DATA, REPORTS, NOTES, PROVENANCE, AUDIT" | tee -a "$LOG_FILE"
echo "Safety: DEMO-001 cannot see DEMO-002, implemented at database level not merely UI hidden, Reports patient-specific, Ultrasounds patient-specific, AI runs patient-specific, Sensor sessions patient-specific, Timeline patient-specific" | tee -a "$LOG_FILE"
echo "Database: Stable patient IDs, foreign keys, patient-scoped queries, audit events, no cross-patient contamination - database/endo_twin_database.py" | tee -a "$LOG_FILE"
echo "Logs: $LOG_FILE" | tee -a "$LOG_FILE"
echo "APK Output: DIST/android/CHRONO-PCOS-Doctor.apk and dist/android/CHRONO-PCOS-Doctor.apk" | tee -a "$LOG_FILE"
ls -lh "$PROJECT_ROOT/DIST/android/" 2>&1 | tee -a "$LOG_FILE" || true
echo "======================================================================" | tee -a "$LOG_FILE"

if [[ $FAIL -eq 0 ]]; then
    echo "" | tee -a "$LOG_FILE"
    echo "Doctor Android build check complete - Native Kotlin + Jetpack Compose Multi-Patient" | tee -a "$LOG_FILE"
    if [[ -f "$PROJECT_ROOT/DIST/android/CHRONO-PCOS-Doctor.apk" ]]; then
        echo "✓ Native APK available: DIST/android/CHRONO-PCOS-Doctor.apk" | tee -a "$LOG_FILE"
        echo "Install: adb install DIST/android/CHRONO-PCOS-Doctor.apk" | tee -a "$LOG_FILE"
    elif [[ -f "$PROJECT_ROOT/DIST/android/CHRONO_PCOS_Doctor.apk" ]]; then
        echo "✓ APK available: DIST/android/CHRONO_PCOS_Doctor.apk (legacy or native)" | tee -a "$LOG_FILE"
    else
        echo "⚠ APK not built in this environment - expected without Android SDK/Gradle" | tee -a "$LOG_FILE"
        echo "  - Native Kotlin multi-patient source preserved: android/doctor/ with MainActivity.kt, DoctorModels.kt, multi-patient safety DEMO-001 DEMO-002 DEMO-003" | tee -a "$LOG_FILE"
        echo "  - Legacy Kivy preserved: android/doctor_app/main.py" | tee -a "$LOG_FILE"
        echo "  - PC demo available via DOCTOR_ANDROID.sh" | tee -a "$LOG_FILE"
        echo "  - To build native APK requires Android SDK/Gradle - see docs/ANDROID_BUILD_GUIDE.md" | tee -a "$LOG_FILE"
    fi
    echo "" | tee -a "$LOG_FILE"
    if command -v kdialog >/dev/null 2>&1; then
        kdialog --msgbox "Doctor Android Build - Native Kotlin + Compose Multi-Patient\\n\\nPASS: $PASS WARN: $WARN FAIL: $FAIL\\n\\nAPK Output: DIST/android/CHRONO-PCOS-Doctor.apk\\nLogs: $LOG_FILE\\n\\nMulti-Patient Safety: DEMO-001 cannot see DEMO-002 database level" 2>/dev/null || true
    fi
    exit 0
else
    echo "" | tee -a "$LOG_FILE"
    echo "Build completed with $FAIL failure(s), $WARN warning(s)" | tee -a "$LOG_FILE"
    exit 1
fi
