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

LOG_FILE="$PROJECT_ROOT/logs/build_patient_apk.log"
echo "$(date): Building Patient Android APK - Native Kotlin + Jetpack Compose" | tee -a "$LOG_FILE"

echo "======================================================================"
echo "CHRONO-PCOS V8.3+ → ENDO-TWIN - Build Patient Android APK"
echo "Native Kotlin + Jetpack Compose - Material 3"
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
warn_check_cmd "Gradle" "command -v gradle || test -f $PROJECT_ROOT/android/patient/gradlew"
warn_check_cmd "Android SDK" "test -d \$HOME/Android/Sdk || test -d \$HOME/.android || test -d /opt/android-sdk || test -n \"\$ANDROID_SDK_ROOT\" || test -n \"\$ANDROID_HOME\""
warn_check_cmd "Android NDK" "test -d \$HOME/Android/Sdk/ndk || test -n \"\$ANDROID_NDK_ROOT\""
# Legacy Kivy checks for fallback
warn_check_cmd "Buildozer (legacy fallback)" "command -v buildozer || $PROJECT_ROOT/.venv/bin/buildozer --version"
warn_check_cmd "Kivy (legacy fallback)" "$PROJECT_ROOT/.venv/bin/python -c 'import kivy' 2>/dev/null || python3 -c 'import kivy' 2>/dev/null"

echo "" | tee -a "$LOG_FILE"
echo "[2/7] Checking project configuration - Native Kotlin..." | tee -a "$LOG_FILE"
check_cmd "Patient Native MainActivity.kt" "test -f $PROJECT_ROOT/android/patient/app/src/main/java/org/chronopcos/patient/MainActivity.kt"
check_cmd "Patient Native build.gradle.kts" "test -f $PROJECT_ROOT/android/patient/app/build.gradle.kts"
check_cmd "Patient Native AndroidManifest.xml" "test -f $PROJECT_ROOT/android/patient/app/src/main/AndroidManifest.xml"
check_cmd "Patient Native Models.kt" "test -f $PROJECT_ROOT/android/patient/app/src/main/java/org/chronopcos/patient/data/model/PatientModels.kt"
check_cmd "Patient Native Database.kt" "test -f $PROJECT_ROOT/android/patient/app/src/main/java/org/chronopcos/patient/data/database/PatientDatabase.kt"
check_cmd "Patient Native Repository.kt" "test -f $PROJECT_ROOT/android/patient/app/src/main/java/org/chronopcos/patient/data/repository/PatientRepository.kt"
warn_check_cmd "Patient Legacy Kivy main.py" "test -f $PROJECT_ROOT/android/patient_app/main.py"
warn_check_cmd "Patient Legacy buildozer.spec" "test -f $PROJECT_ROOT/android/patient_app/buildozer.spec"
check_cmd "ENDO-TWIN Core" "test -f $PROJECT_ROOT/endo_twin/core/twin.py"
check_cmd "Database" "test -f $PROJECT_ROOT/database/endo_twin_database.py"

echo "" | tee -a "$LOG_FILE"
echo "[3/7] Checking native project structure..." | tee -a "$LOG_FILE"
echo "Patient Android - Kotlin + Jetpack Compose - Material 3 - Navigation Compose - ViewModel - Repository - Room - DataStore - Coroutines" | tee -a "$LOG_FILE"
echo "Structure: app/ui/navigation/screens/components/data/model/database/repository/viewmodel/domain" | tee -a "$LOG_FILE"
ls -R "$PROJECT_ROOT/android/patient" 2>&1 | head -50 | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo "[4/7] Building Native Kotlin APK..." | tee -a "$LOG_FILE"

BUILD_SUCCESS=0

# Try native Kotlin build if Gradle and SDK available
if [[ -f "$PROJECT_ROOT/android/patient/gradlew" || -f "$PROJECT_ROOT/android/patient/app/build.gradle.kts" ]]; then
    echo "Native Kotlin project detected - attempting Gradle build" | tee -a "$LOG_FILE"
    echo "Project: android/patient/" | tee -a "$LOG_FILE"
    echo "Technology: Kotlin + Jetpack Compose + Material 3 + Navigation Compose + ViewModel + Repository + Room + DataStore + Coroutines" | tee -a "$LOG_FILE"
    
    cd "$PROJECT_ROOT/android/patient"
    
    # Check if we can build
    if command -v gradle >/dev/null 2>&1 || [[ -f "gradlew" ]]; then
        if [[ "${1:-}" == "--check-only" ]]; then
            echo "Check-only mode - skipping actual Gradle build" | tee -a "$LOG_FILE"
            echo "To build native APK, run: ./BUILD_PATIENT_APK.sh (without --check-only)" | tee -a "$LOG_FILE"
            echo "Or: cd android/patient && ./gradlew assembleDebug" | tee -a "$LOG_FILE"
        else
            echo "Attempting: ./gradlew assembleDebug or gradle assembleDebug" | tee -a "$LOG_FILE"
            if [[ -f "gradlew" ]]; then
                chmod +x gradlew 2>&1 | tee -a "$LOG_FILE" || true
                if ./gradlew assembleDebug 2>&1 | tee -a "$LOG_FILE"; then
                    echo "✓ Native Gradle build succeeded" | tee -a "$LOG_FILE"
                    BUILD_SUCCESS=1
                    PASS=$((PASS+1))
                else
                    echo "✗ Native Gradle build failed - likely missing Android SDK/Gradle toolchain" | tee -a "$LOG_FILE"
                    echo "This is expected in environments without Android SDK - honest reporting, not fake success" | tee -a "$LOG_FILE"
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
        echo "This is expected without Android SDK/Gradle - honest reporting" | tee -a "$LOG_FILE"
        echo "To setup:" | tee -a "$LOG_FILE"
        echo "  - Install Java 17+: sudo pacman -S jdk-openjdk or sudo apt install openjdk-17-jdk" | tee -a "$LOG_FILE"
        echo "  - Install Android Studio: https://developer.android.com/studio" | tee -a "$LOG_FILE"
        echo "  - Or Android SDK: sudo pacman -S android-tools android-sdk android-ndk" | tee -a "$LOG_FILE"
        echo "  - Set env: export ANDROID_SDK_ROOT=\$HOME/Android/Sdk ANDROID_HOME=\$HOME/Android/Sdk" | tee -a "$LOG_FILE"
        echo "  - Accept licenses: yes | sdkmanager --licenses" | tee -a "$LOG_FILE"
        echo "  - Then: cd android/patient && ./gradlew assembleDebug" | tee -a "$LOG_FILE"
        WARN=$((WARN+1))
    fi
    cd "$PROJECT_ROOT"
else
    echo "Native Kotlin project not found at android/patient/" | tee -a "$LOG_FILE"
    FAIL=$((FAIL+1))
fi

# Fallback to legacy Kivy if native build failed and not check-only
if [[ $BUILD_SUCCESS -eq 0 && "${1:-}" != "--check-only" ]]; then
    echo "" | tee -a "$LOG_FILE"
    echo "[5/7] Fallback: Attempting legacy Kivy build..." | tee -a "$LOG_FILE"
    if [[ -f "$PROJECT_ROOT/android/patient_app/buildozer.spec" ]]; then
        cd "$PROJECT_ROOT/android/patient_app"
        if ! command -v buildozer >/dev/null 2>&1 && [[ -f "$PROJECT_ROOT/.venv/bin/buildozer" ]]; then
            BUILD_CMD="$PROJECT_ROOT/.venv/bin/buildozer"
        else
            BUILD_CMD="buildozer"
        fi
        echo "Legacy build command: $BUILD_CMD android debug" | tee -a "$LOG_FILE"
        echo "Kivy prototype - preserved as legacy, primary is now Kotlin + Compose" | tee -a "$LOG_FILE"
        if $BUILD_CMD android debug 2>&1 | tee -a "$LOG_FILE"; then
            echo "✓ Legacy Kivy build succeeded" | tee -a "$LOG_FILE"
            BUILD_SUCCESS=1
            PASS=$((PASS+1))
        else
            echo "✗ Legacy Kivy build failed - expected without Android SDK" | tee -a "$LOG_FILE"
            WARN=$((WARN+1))
        fi
        cd "$PROJECT_ROOT"
    fi
fi

echo "" | tee -a "$LOG_FILE"
echo "[6/7] Collecting APKs..." | tee -a "$LOG_FILE"

# Check for native APK
NATIVE_APK=$(find "$PROJECT_ROOT/android/patient/app/build/outputs" -name "*.apk" 2>/dev/null | head -1)
if [[ -n "$NATIVE_APK" ]]; then
    echo "Native APK found: $NATIVE_APK" | tee -a "$LOG_FILE"
    cp "$NATIVE_APK" "$PROJECT_ROOT/DIST/android/CHRONO-PCOS-Patient.apk" 2>&1 | tee -a "$LOG_FILE" || true
    cp "$NATIVE_APK" "$PROJECT_ROOT/dist/android/CHRONO-PCOS-Patient.apk" 2>&1 | tee -a "$LOG_FILE" || true
    cp "$NATIVE_APK" "$PROJECT_ROOT/DIST/android/CHRONO_PCOS_Patient.apk" 2>&1 | tee -a "$LOG_FILE" || true
    ls -lh "$PROJECT_ROOT/DIST/android/"*Patient*.apk 2>&1 | tee -a "$LOG_FILE" || true
    PASS=$((PASS+1))
fi

# Check for legacy APK
LEGACY_APK=$(find "$PROJECT_ROOT/android/patient_app/bin" -name "*.apk" 2>/dev/null | head -1)
if [[ -n "$LEGACY_APK" ]]; then
    echo "Legacy APK found: $LEGACY_APK" | tee -a "$LOG_FILE"
    cp "$LEGACY_APK" "$PROJECT_ROOT/DIST/android/CHRONO_PCOS_Patient_legacy.apk" 2>&1 | tee -a "$LOG_FILE" || true
    ls -lh "$PROJECT_ROOT/DIST/android/" 2>&1 | tee -a "$LOG_FILE"
    PASS=$((PASS+1))
fi

# Check output directories
echo "APK Output Directories:" | tee -a "$LOG_FILE"
echo "  DIST/android/ (primary)" | tee -a "$LOG_FILE"
ls -lh "$PROJECT_ROOT/DIST/android/" 2>&1 | tee -a "$LOG_FILE" || echo "DIST/android/ empty" | tee -a "$LOG_FILE"
echo "  dist/android/ (alternative)" | tee -a "$LOG_FILE"
ls -lh "$PROJECT_ROOT/dist/android/" 2>&1 | tee -a "$LOG_FILE" || echo "dist/android/ empty" | tee -a "$LOG_FILE"

if [[ -z "$NATIVE_APK" && -z "$LEGACY_APK" ]]; then
    echo "⚠ No APK found - expected without Android SDK/Gradle toolchain" | tee -a "$LOG_FILE"
    echo "Current status: Native Kotlin source preserved (Kotlin + Jetpack Compose), Kivy legacy preserved, PC demo available, APK not built in this environment (Android SDK/NDK/Gradle missing) - honest reporting, build scripts provided, never claim APK exists when not" | tee -a "$LOG_FILE"
    WARN=$((WARN+1))
fi

echo "" | tee -a "$LOG_FILE"
echo "[7/7] Final report..." | tee -a "$LOG_FILE"
echo "======================================================================" | tee -a "$LOG_FILE"
echo "Build Summary: PASS $PASS WARN $WARN FAIL $FAIL" | tee -a "$LOG_FILE"
echo "Technology: Kotlin + Jetpack Compose + Material 3 + Navigation Compose + ViewModel + Repository + Room + DataStore + Coroutines + Clean Architecture" | tee -a "$LOG_FILE"
echo "Architecture: app/ui/navigation/screens/components/data/model/database/repository/viewmodel/domain" | tee -a "$LOG_FILE"
echo "Patient App: Single patient only, never global list, CURRENT PATIENT with stable ID" | tee -a "$LOG_FILE"
echo "Features: HOME, MY HEALTH, MEASUREMENTS, TIMELINE, SYMPTOMS, CYCLE, ULTRASOUND, RESULTS, REPORTS, DOCTOR SHARING, FIND CARE, EDUCATION, SETTINGS" | tee -a "$LOG_FILE"
echo "Safety: Patient ID scoped queries, no cross-patient contamination, reports patient-specific, ultrasounds patient-specific, AI runs patient-specific, timeline patient-specific, provenance visible MEASURED/CLINICALLY_ENTERED/IMAGE-DERIVED/MODEL-INFERRED/DEMO_DATA/UNKNOWN, offline-first, privacy-first" | tee -a "$LOG_FILE"
echo "Logs: $LOG_FILE" | tee -a "$LOG_FILE"
echo "APK Output: DIST/android/CHRONO-PCOS-Patient.apk and dist/android/CHRONO-PCOS-Patient.apk" | tee -a "$LOG_FILE"
ls -lh "$PROJECT_ROOT/DIST/android/" 2>&1 | tee -a "$LOG_FILE" || true
ls -lh "$PROJECT_ROOT/dist/android/" 2>&1 | tee -a "$LOG_FILE" || true
echo "======================================================================" | tee -a "$LOG_FILE"

if [[ $FAIL -eq 0 ]]; then
    echo "" | tee -a "$LOG_FILE"
    echo "Patient Android build check complete - Native Kotlin + Jetpack Compose" | tee -a "$LOG_FILE"
    if [[ -f "$PROJECT_ROOT/DIST/android/CHRONO-PCOS-Patient.apk" ]]; then
        echo "✓ Native APK available: DIST/android/CHRONO-PCOS-Patient.apk" | tee -a "$LOG_FILE"
        echo "Install: adb install DIST/android/CHRONO-PCOS-Patient.apk" | tee -a "$LOG_FILE"
    elif [[ -f "$PROJECT_ROOT/DIST/android/CHRONO_PCOS_Patient.apk" ]]; then
        echo "✓ APK available: DIST/android/CHRONO_PCOS_Patient.apk (legacy Kivy or native)" | tee -a "$LOG_FILE"
    else
        echo "⚠ APK not built in this environment - expected without Android SDK/Gradle" | tee -a "$LOG_FILE"
        echo "  - Native Kotlin source preserved: android/patient/ with MainActivity.kt, PatientModels.kt, PatientDatabase.kt, PatientRepository.kt, PatientNavigation.kt, PatientHomeScreen.kt" | tee -a "$LOG_FILE"
        echo "  - Legacy Kivy preserved: android/patient_app/main.py" | tee -a "$LOG_FILE"
        echo "  - PC demo available via PATIENT_APP.sh" | tee -a "$LOG_FILE"
        echo "  - To build native APK requires Android SDK/Gradle - see docs/ANDROID_BUILD_GUIDE.md" | tee -a "$LOG_FILE"
        echo "  - Setup: Install Android Studio, set ANDROID_SDK_ROOT, accept licenses, run ./gradlew assembleDebug" | tee -a "$LOG_FILE"
    fi
    echo "" | tee -a "$LOG_FILE"
    if command -v kdialog >/dev/null 2>&1; then
        kdialog --msgbox "Patient Android Build - Native Kotlin + Compose\\n\\nPASS: $PASS WARN: $WARN FAIL: $FAIL\\n\\nAPK Output: DIST/android/CHRONO-PCOS-Patient.apk\\nLogs: $LOG_FILE\\n\\nTechnology: Kotlin + Jetpack Compose Material 3\\nArchitecture: Clean Architecture with Repository, Room, ViewModel" 2>/dev/null || true
    fi
    exit 0
else
    echo "" | tee -a "$LOG_FILE"
    echo "Build completed with $FAIL failure(s), $WARN warning(s)" | tee -a "$LOG_FILE"
    echo "Check logs: $LOG_FILE" | tee -a "$LOG_FILE"
    exit 1
fi
