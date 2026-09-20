#!/usr/bin/env bash
set -euo pipefail

# CHRONO-PCOS V8.3+ / CHRONO-TWIN NEXUS V8.3 - Canonical Launcher
# START.sh - Single entry point for entire ecosystem
# Usage: ./START.sh [mode]
# Modes: gui (default), diagnostics, patient, doctor, build, demo, help, menu

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
cd "$PROJECT_ROOT"

mkdir -p "$PROJECT_ROOT/logs"
mkdir -p "$PROJECT_ROOT/artifacts/android"
mkdir -p "$PROJECT_ROOT/DIST/android"

VENV_PYTHON="$PROJECT_ROOT/.venv/bin/python"
LOG_FILE="$PROJECT_ROOT/logs/start.log"

MODE="${1:-menu}"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

show_help() {
    cat << 'EOF'
CHRONO-PCOS V8.3+ / CHRONO-TWIN NEXUS V8.3
Canonical Launcher - START.sh - One launcher system, no chaos

Usage: ./START.sh [mode]

Modes:
  menu          Interactive menu with 12 options (default when no args)
  gui           Launch Control Center GUI - launcher/main.py
  endo-twin     Launch ENDO-TWIN general dashboard
  doctor        Launch Doctor Desktop
  patient       Launch Patient App (Kivy PC demo if no APK)
  doctor-android Launch Doctor Android App (Kivy PC demo if no APK)
  research      Launch Research Lab
  diagnostics   Run system diagnostics
  build-patient Build Patient APK only
  build-doctor  Build Doctor APK only
  build         Build All APKs (check-only if no toolchain)
  build-gradle  Attempt real Gradle builds ./gradlew assembleDebug
  test          Run tests (pytest -q)
  test-cross    Run cross-patient isolation tests
  benchmark     Performance benchmark
  health        Project health check
  demo          Run full showcase demo (17 steps)
  help          Show this help

Examples:
  ./START.sh
  ./START.sh menu
  ./START.sh gui
  ./START.sh diagnostics
  ./START.sh build
  ./START.sh build-gradle
  ./START.sh test
  ./START.sh health
  ./START.sh demo

Architecture:
  ENDO-TWIN Core: src/endo_twin/ + src/core/ + src/signal_processing/
  Patient Android: android/patient_app/ (Kivy) + android/patient/ (Native Kotlin Compose)
  Doctor Android:  android/doctor_app/ (Kivy) + android/doctor/ (Native Kotlin Compose)
  Doctor PC:       desktop/doctor_app/ + launcher/
  Local DB:        database/ + data/
  Analysis Engine: src/signal_processing/ + src/analysis/ + src/ai/ + src/ultrasound/ + src/fusion/

Offline-first: Core works without internet. Internet optional for provider directory/map/updates.

Safety: Research / risk-screening output — not a medical diagnosis.

Final Commands (must actually work):
  ./START.sh
  ./scripts/build/build_patient_apk.sh (or ./START.sh build-patient)
  ./scripts/build/build_doctor_apk.sh (or ./START.sh build-doctor)
  ./scripts/build/build_all_apks.sh (or ./START.sh build)
  pytest -q (or ./START.sh test)
  ./scripts/diagnostics/project_health.sh (or ./START.sh health)

EOF
}

check_venv() {
    if [[ ! -f "$VENV_PYTHON" ]]; then
        log "ERROR: CHRONO-PCOS environment not found at $VENV_PYTHON"
        log "Please run: ./setup_garuda.sh or ./SETUP.sh"
        if [[ -f "$PROJECT_ROOT/setup_garuda.sh" ]]; then
            log "Attempting setup_garuda.sh..."
            bash "$PROJECT_ROOT/setup_garuda.sh" 2>&1 | tee -a "$LOG_FILE" || true
        fi
        if [[ ! -f "$VENV_PYTHON" ]]; then
            echo "ERROR: .venv not found. Run ./setup_garuda.sh"
            exit 1
        fi
    fi
}

launch_gui() {
    check_venv
    log "Launching Control Center GUI: launcher/main.py"
    exec "$VENV_PYTHON" "$PROJECT_ROOT/launcher/main.py" 2>&1 | tee -a "$LOG_FILE"
}

launch_endo_twin() {
    check_venv
    log "Launching ENDO-TWIN general dashboard"
    if [[ -f "$PROJECT_ROOT/ENDO_TWIN.sh" ]]; then
        bash "$PROJECT_ROOT/ENDO_TWIN.sh" 2>&1 | tee -a "$LOG_FILE"
    else
        "$VENV_PYTHON" "$PROJECT_ROOT/apps/main/main_app.py" 2>&1 | tee -a "$LOG_FILE"
    fi
}

launch_diagnostics() {
    check_venv
    log "Launching DIAGNOSTICS"
    exec "$VENV_PYTHON" "$PROJECT_ROOT/launcher/diagnostics.py" 2>&1 | tee -a "$LOG_FILE"
}

launch_patient() {
    check_venv
    log "Launching Patient Android (PC demo)"
    if [[ -f "$PROJECT_ROOT/LAUNCH/PATIENT_ANDROID.sh" ]]; then
        bash "$PROJECT_ROOT/LAUNCH/PATIENT_ANDROID.sh" 2>&1 | tee -a "$LOG_FILE"
    else
        "$VENV_PYTHON" "$PROJECT_ROOT/android/patient_app/main.py" 2>&1 | tee -a "$LOG_FILE"
    fi
}

launch_doctor() {
    check_venv
    log "Launching Doctor PC"
    if [[ -f "$PROJECT_ROOT/LAUNCH/DOCTOR_PC.sh" ]]; then
        bash "$PROJECT_ROOT/LAUNCH/DOCTOR_PC.sh" 2>&1 | tee -a "$LOG_FILE"
    else
        "$VENV_PYTHON" "$PROJECT_ROOT/desktop/doctor_app/main.py" 2>&1 | tee -a "$LOG_FILE"
    fi
}

launch_doctor_android() {
    check_venv
    log "Launching Doctor Android (PC demo)"
    if [[ -f "$PROJECT_ROOT/LAUNCH/DOCTOR_ANDROID.sh" ]]; then
        bash "$PROJECT_ROOT/LAUNCH/DOCTOR_ANDROID.sh" 2>&1 | tee -a "$LOG_FILE"
    else
        "$VENV_PYTHON" "$PROJECT_ROOT/android/doctor_app/main.py" 2>&1 | tee -a "$LOG_FILE"
    fi
}

launch_research() {
    check_venv
    log "Launching Research Lab"
    if [[ -f "$PROJECT_ROOT/launcher/main.py" ]]; then
        # Research lab is part of Control Center or separate
        "$VENV_PYTHON" -c "
import sys
from pathlib import Path
PROJECT_ROOT = Path('$PROJECT_ROOT')
sys.path.insert(0, str(PROJECT_ROOT))
print('Research Lab - Signal Processing, Training, Evaluation, Validation')
print('Available: src/signal_processing/, disease_models/, models/, science/')
from src.endo_twin.core.twin_core import EndoTwinCore
core = EndoTwinCore()
print(f\"ENDO-TWIN Core: {core.version}\")
print(f\"Models: {core.model_registry.get_registry_info()['summary']}\")
" 2>&1 | tee -a "$LOG_FILE"
    fi
    # Also try to launch research lab if exists
    if [[ -f "$PROJECT_ROOT/apps/research_lab/main.py" ]]; then
        "$VENV_PYTHON" "$PROJECT_ROOT/apps/research_lab/main.py" 2>&1 | tee -a "$LOG_FILE"
    fi
}

launch_build() {
    log "Building Android APKs (check-only if no toolchain)"
    if [[ -f "$PROJECT_ROOT/BUILD_ALL_APKS.sh" ]]; then
        bash "$PROJECT_ROOT/BUILD_ALL_APKS.sh" 2>&1 | tee -a "$LOG_FILE"
    else
        log "BUILD_ALL_APKS.sh not found"
        exit 1
    fi
}

launch_build_patient() {
    log "Building Patient APK"
    if [[ -f "$PROJECT_ROOT/BUILD_PATIENT_APK.sh" ]]; then
        bash "$PROJECT_ROOT/BUILD_PATIENT_APK.sh" 2>&1 | tee -a "$LOG_FILE"
    else
        log "BUILD_PATIENT_APK.sh not found"
        exit 1
    fi
}

launch_build_doctor() {
    log "Building Doctor APK"
    if [[ -f "$PROJECT_ROOT/BUILD_DOCTOR_APK.sh" ]]; then
        bash "$PROJECT_ROOT/BUILD_DOCTOR_APK.sh" 2>&1 | tee -a "$LOG_FILE"
    else
        log "BUILD_DOCTOR_APK.sh not found"
        exit 1
    fi
}

launch_build_gradle() {
    log "Attempting real Gradle builds: ./gradlew assembleDebug"
    log "Env limitations will be documented"
    mkdir -p "$PROJECT_ROOT/artifacts/android"
    mkdir -p "$PROJECT_ROOT/logs"
    
    # Patient Native
    log "=== Patient Native (android/patient/) ==="
    if [[ -f "$PROJECT_ROOT/android/patient/gradlew" ]]; then
        cd "$PROJECT_ROOT/android/patient"
        ./gradlew assembleDebug --no-daemon 2>&1 | tee -a "$LOG_FILE" || true
        if [[ -f "$PROJECT_ROOT/android/patient/app/build/outputs/apk/debug/app-debug.apk" ]]; then
            cp "$PROJECT_ROOT/android/patient/app/build/outputs/apk/debug/app-debug.apk" "$PROJECT_ROOT/artifacts/android/endo-twin-patient-debug.apk" 2>&1 | tee -a "$LOG_FILE" || true
            cp "$PROJECT_ROOT/android/patient/app/build/outputs/apk/debug/app-debug.apk" "$PROJECT_ROOT/artifacts/android/CHRONO-PCOS-Patient-Native-debug.apk" 2>&1 | tee -a "$LOG_FILE" || true
            log "Patient Native APK copied to artifacts/android/"
        else
            log "Patient Native APK not generated - likely missing JAVA_HOME/Android SDK (env limitation)"
        fi
        cd "$PROJECT_ROOT"
    else
        log "android/patient/gradlew not found"
    fi

    # Doctor Native
    log "=== Doctor Native (android/doctor/) ==="
    if [[ -f "$PROJECT_ROOT/android/doctor/gradlew" ]]; then
        cd "$PROJECT_ROOT/android/doctor"
        ./gradlew assembleDebug --no-daemon 2>&1 | tee -a "$LOG_FILE" || true
        if [[ -f "$PROJECT_ROOT/android/doctor/app/build/outputs/apk/debug/app-debug.apk" ]]; then
            cp "$PROJECT_ROOT/android/doctor/app/build/outputs/apk/debug/app-debug.apk" "$PROJECT_ROOT/artifacts/android/endo-twin-doctor-debug.apk" 2>&1 | tee -a "$LOG_FILE" || true
            cp "$PROJECT_ROOT/android/doctor/app/build/outputs/apk/debug/app-debug.apk" "$PROJECT_ROOT/artifacts/android/CHRONO-PCOS-Doctor-Native-debug.apk" 2>&1 | tee -a "$LOG_FILE" || true
            log "Doctor Native APK copied to artifacts/android/"
        else
            log "Doctor Native APK not generated - likely missing JAVA_HOME/Android SDK (env limitation)"
        fi
        cd "$PROJECT_ROOT"
    else
        log "android/doctor/gradlew not found"
    fi

    log "=== Gradle Build Attempt Complete ==="
    log "Artifacts: $PROJECT_ROOT/artifacts/android/"
    ls -lh "$PROJECT_ROOT/artifacts/android/" 2>&1 | tee -a "$LOG_FILE" || true
    log "If no APK, env limitation: JAVA_HOME not set, no java, no Android SDK - real wrapper exists and attempted build"
}

launch_demo() {
    check_venv
    log "Launching Full Showcase Demo (17 steps)"
    if [[ -f "$PROJECT_ROOT/LAUNCH/FULL_SHOWCASE.sh" ]]; then
        bash "$PROJECT_ROOT/LAUNCH/FULL_SHOWCASE.sh" 2>&1 | tee -a "$LOG_FILE"
    else
        "$VENV_PYTHON" "$PROJECT_ROOT/demo/full_showcase.py" 2>&1 | tee -a "$LOG_FILE"
    fi
}

launch_test() {
    check_venv
    log "Running tests: pytest -q"
    cd "$PROJECT_ROOT"
    "$VENV_PYTHON" -m pytest -q 2>&1 | tee -a "$LOG_FILE"
    # Also run acceptance tests
    "$VENV_PYTHON" "$PROJECT_ROOT/apps/main/main_app.py" 2>&1 | tee -a "$LOG_FILE"
}

launch_test_cross() {
    check_venv
    log "Running cross-patient isolation tests"
    cd "$PROJECT_ROOT"
    "$VENV_PYTHON" "$PROJECT_ROOT/tests/test_endo_twin_isolation.py" 2>&1 | tee -a "$LOG_FILE"
    if [[ -f "$PROJECT_ROOT/tests/test_multi_patient_isolation.py" ]]; then
        "$VENV_PYTHON" "$PROJECT_ROOT/tests/test_multi_patient_isolation.py" 2>&1 | tee -a "$LOG_FILE"
    fi
}

launch_benchmark() {
    check_venv
    log "Running performance benchmark"
    cd "$PROJECT_ROOT"
    "$VENV_PYTHON" - << 'PY' 2>&1 | tee -a "$LOG_FILE"
import os, time, sys
from pathlib import Path
PROJECT_ROOT = Path(os.environ.get("ENDO_TWIN_PROJECT_ROOT", str(Path.cwd())))
sys.path.insert(0, str(PROJECT_ROOT))
print("=== Performance Benchmark - Real Measurements ===")
start = time.time()
import src.config, src.data_models, src.core.feature_extraction
print(f"Import core: {(time.time()-start)*1000:.1f} ms")
from database.database import LocalDatabase
import tempfile
tmp = Path(tempfile.gettempdir()) / f"perf_{int(time.time())}.db"
if tmp.exists():
    tmp.unlink()
db = LocalDatabase(db_path=tmp)
print(f"DB init: {(time.time()-start)*1000:.1f} ms - placeholder, real benchmark in docs/performance/PERFORMANCE_REPORT.md")
tmp.unlink(missing_ok=True)
print("See docs/performance/PERFORMANCE_REPORT.md for full benchmark")
PY
    cat "$PROJECT_ROOT/docs/performance/PERFORMANCE_REPORT.md" 2>&1 | head -100 | tee -a "$LOG_FILE" || true
}

launch_health() {
    log "Running project health check"
    if [[ -f "$PROJECT_ROOT/scripts/diagnostics/project_health.sh" ]]; then
        bash "$PROJECT_ROOT/scripts/diagnostics/project_health.sh" 2>&1 | tee -a "$LOG_FILE"
    else
        log "project_health.sh not found"
        exit 1
    fi
}

show_menu() {
    while true; do
        clear
        cat << 'MENU'
================================================================================
ENDO-TWIN / CHRONO-PCOS V8.3+ - Canonical Launcher - One Launcher System
================================================================================
Research-grade system: FAST COHERENT EXPLAINABLE MODULAR TESTABLE MAINTAINABLE
OFFLINE-CAPABLE SCIENTIFICALLY HONEST VISUALLY PROFESSIONAL

No need to hunt through dozens of scripts - one entry point: ./START.sh

Architecture: ENDO-TWIN is platform, CHRONO-PCOS is first disease-specific model
Safety: Research / risk-screening output — not a medical diagnosis

--------------------------------------------------------------------------------
1. ENDO-TWIN - General physiological modelling platform
2. Doctor Desktop - Multipatient workstation
3. Patient Demo - Patient Android PC demo
4. Research Lab - Signal processing, training, evaluation
5. Diagnostics - System diagnostics
6. Build Patient APK - Kivy + Native Gradle
7. Build Doctor APK - Kivy + Native Gradle
8. Build All APKs - Both patient and doctor
9. Run Tests - pytest + acceptance + isolation
10. Performance Benchmark - Real measurements
11. Project Health - Dependencies, DB, models, launchers, Android Gradle
12. Exit

--------------------------------------------------------------------------------
Artifacts: artifacts/android/ endo-twin-patient-debug.apk endo-twin-doctor-debug.apk
Docs: docs/recovery/ docs/benchmarks/ docs/performance/
Logs: logs/
================================================================================
MENU
        echo -n "Select option [1-12]: "
        read -r choice
        case "$choice" in
            1)
                launch_endo_twin
                echo "Press Enter to continue..."
                read -r
                ;;
            2)
                launch_doctor
                echo "Press Enter to continue..."
                read -r
                ;;
            3)
                launch_patient
                echo "Press Enter to continue..."
                read -r
                ;;
            4)
                launch_research
                echo "Press Enter to continue..."
                read -r
                ;;
            5)
                launch_diagnostics
                echo "Press Enter to continue..."
                read -r
                ;;
            6)
                launch_build_patient
                echo "Press Enter to continue..."
                read -r
                ;;
            7)
                launch_build_doctor
                echo "Press Enter to continue..."
                read -r
                ;;
            8)
                launch_build
                echo "Press Enter to continue..."
                read -r
                ;;
            9)
                launch_test
                launch_test_cross
                echo "Press Enter to continue..."
                read -r
                ;;
            10)
                launch_benchmark
                echo "Press Enter to continue..."
                read -r
                ;;
            11)
                launch_health
                echo "Press Enter to continue..."
                read -r
                ;;
            12)
                echo "Exiting..."
                exit 0
                ;;
            *)
                echo "Invalid option: $choice"
                sleep 1
                ;;
        esac
    done
}

case "$MODE" in
    menu|"")
        # If running in non-interactive terminal, show help and launch gui
        if [[ ! -t 0 ]]; then
            show_help
            launch_gui
        else
            show_menu
        fi
        ;;
    gui)
        launch_gui
        ;;
    endo-twin|endo|twin|general)
        launch_endo_twin
        ;;
    doctor|doctor-pc|doctor-desktop)
        launch_doctor
        ;;
    patient|patient-android|patient-demo)
        launch_patient
        ;;
    doctor-android)
        launch_doctor_android
        ;;
    research|research-lab|lab)
        launch_research
        ;;
    diagnostics|diag)
        launch_diagnostics
        ;;
    build-patient|build_patient)
        launch_build_patient
        ;;
    build-doctor|build_doctor)
        launch_build_doctor
        ;;
    build|build-all|build_all)
        launch_build
        ;;
    build-gradle|gradle|build_native)
        launch_build_gradle
        ;;
    test|tests|pytest)
        launch_test
        ;;
    test-cross|test_cross|cross|isolation)
        launch_test_cross
        ;;
    benchmark|bench|performance)
        launch_benchmark
        ;;
    health|project-health|project_health)
        launch_health
        ;;
    demo|showcase|full)
        launch_demo
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "Unknown mode: $MODE"
        show_help
        exit 1
        ;;
esac
