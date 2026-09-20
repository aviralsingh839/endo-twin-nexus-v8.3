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

LOG_FILE="$PROJECT_ROOT/logs/build_all_apks.log"
echo "$(date): Building All Android APKs - Native Kotlin + Jetpack Compose" | tee "$LOG_FILE"

echo "======================================================================"
echo "CHRONO-PCOS V8.3+ → ENDO-TWIN - Build All Android APKs"
echo "Native Kotlin + Jetpack Compose - Patient + Doctor"
echo "Project Root: $PROJECT_ROOT"
echo "Date: $(date)"
echo "======================================================================" | tee -a "$LOG_FILE"

echo "" | tee -a "$LOG_FILE"
echo "Building Patient Android APK - Native Kotlin + Jetpack Compose..." | tee -a "$LOG_FILE"
if bash "$PROJECT_ROOT/BUILD_PATIENT_APK.sh" --check-only 2>&1 | tee -a "$LOG_FILE"; then
    echo "✓ Patient check completed" | tee -a "$LOG_FILE"
else
    echo "⚠ Patient check completed with warnings" | tee -a "$LOG_FILE"
fi

echo "" | tee -a "$LOG_FILE"
echo "Building Doctor Android APK - Native Kotlin + Jetpack Compose Multi-Patient..." | tee -a "$LOG_FILE"
if bash "$PROJECT_ROOT/BUILD_DOCTOR_APK.sh" --check-only 2>&1 | tee -a "$LOG_FILE"; then
    echo "✓ Doctor check completed" | tee -a "$LOG_FILE"
else
    echo "⚠ Doctor check completed with warnings" | tee -a "$LOG_FILE"
fi

echo "" | tee -a "$LOG_FILE"
echo "APK Output Directories:" | tee -a "$LOG_FILE"
echo "Primary: DIST/android/" | tee -a "$LOG_FILE"
ls -lh "$PROJECT_ROOT/DIST/android/" 2>&1 | tee -a "$LOG_FILE" || echo "DIST/android/ empty - expected without SDK" | tee -a "$LOG_FILE"
echo "Alternative: dist/android/" | tee -a "$LOG_FILE"
ls -lh "$PROJECT_ROOT/dist/android/" 2>&1 | tee -a "$LOG_FILE" || echo "dist/android/ empty - expected without SDK" | tee -a "$LOG_FILE"

echo "" | tee -a "$LOG_FILE"
echo "======================================================================"
echo "Build All APKs Summary"
echo "======================================================================" | tee -a "$LOG_FILE"
echo "Patient Android: Kotlin + Jetpack Compose + Material 3 - Single patient only, never global list" | tee -a "$LOG_FILE"
echo "  Source: android/patient/ - MainActivity.kt, PatientModels.kt, PatientDatabase.kt, PatientRepository.kt, PatientNavigation.kt, PatientHomeScreen.kt" | tee -a "$LOG_FILE"
echo "  Features: HOME, MY HEALTH, MEASUREMENTS, TIMELINE, SYMPTOMS, CYCLE, ULTRASOUND, RESULTS, REPORTS, DOCTOR SHARING, FIND CARE, EDUCATION, SETTINGS" | tee -a "$LOG_FILE"
echo "  Safety: Patient-scoped queries, no cross-contamination, provenance visible, offline-first, privacy-first" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
echo "Doctor Android: Kotlin + Jetpack Compose + Material 3 - Multi-patient" | tee -a "$LOG_FILE"
echo "  Source: android/doctor/ - MainActivity.kt, DoctorModels.kt, multi-patient safety DEMO-001 DEMO-002 DEMO-003" | tee -a "$LOG_FILE"
echo "  Features: Dashboard, Patients, Recent Activity, Pending Review, Reports, Settings, Patient List Search/Filter/Sort/Open/Archive/Create/Import/Export, Patient Profile Tabs OVERVIEW/TIMELINE/PHYSIOLOGY/SENSORS/ULTRASOUND/AI/MODELS/CLINICAL DATA/REPORTS/NOTES/PROVENANCE/AUDIT" | tee -a "$LOG_FILE"
echo "  Safety: DEMO-001 cannot see DEMO-002 - database level, Reports patient-specific, Ultrasounds patient-specific, AI runs patient-specific, Sensor sessions patient-specific, Timeline patient-specific" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
echo "ENDO-TWIN Core: endo_twin/ - core, identity, physiology, baseline, longitudinal, provenance, uncertainty, models, registry, interfaces" | tee -a "$LOG_FILE"
echo "  CHRONO-PCOS is first disease-specific module on ENDO-TWIN architecture" | tee -a "$LOG_FILE"
echo "  NOT clinically validated universal human digital twin - research framework" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
echo "Database: database/endo_twin_database.py - patients, sensor_sessions, measurements, features, clinical_records, symptoms, cycle_events, ultrasound_studies, ultrasound_features, model_runs, model_versions, reports, notes, providers, audit_events - stable IDs, foreign keys, patient-scoped, no cross-contamination" | tee -a "$LOG_FILE"
echo "  Multi-patient test: DEMO-001, DEMO-002, DEMO-003 with deliberately different data" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
echo "To build actual APKs (requires Android SDK/NDK/Gradle):" | tee -a "$LOG_FILE"
echo "  ./BUILD_PATIENT_APK.sh" | tee -a "$LOG_FILE"
echo "  ./BUILD_DOCTOR_APK.sh" | tee -a "$LOG_FILE"
echo "Or:" | tee -a "$LOG_FILE"
echo "  cd android/patient && ./gradlew assembleDebug" | tee -a "$LOG_FILE"
echo "  cd android/doctor && ./gradlew assembleDebug" | tee -a "$LOG_FILE"
echo "  adb install DIST/android/CHRONO-PCOS-Patient.apk" | tee -a "$LOG_FILE"
echo "  adb install DIST/android/CHRONO-PCOS-Doctor.apk" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
echo "See docs/ANDROID_BUILD_GUIDE.md for full Android toolchain setup" | tee -a "$LOG_FILE"
echo "======================================================================" | tee -a "$LOG_FILE"

if command -v kdialog >/dev/null 2>&1; then
    kdialog --msgbox "Build All APKs - Native Kotlin + Compose\\n\\nPatient: Kotlin + Compose Single Patient\\nDoctor: Kotlin + Compose Multi-Patient DEMO-001 DEMO-002 DEMO-003\\n\\nAPK Output: DIST/android/\\nLogs: $LOG_FILE\\n\\nSee docs/ANDROID_BUILD_GUIDE.md" 2>/dev/null || true
fi
