# MIGRATION PLAN - ENDO-TWIN from V8.1

Date: 2026-09-19
Version: 8.3+ → ENDO-TWIN
Status: IMPLEMENTED

## Original V8.1

- chrono_pcos_project V8/ with src/, models/, data/, docs/, arduino/, tests/
- 208 files, many duplicates with src/ (97 files) byte-identical groups
- Android placeholder gradlew 226/336 bytes echo exit 1
- Hard-coded DEMO-001,002,003 in UI
- Hard-coded confidence 0.75 in many example paths
- Database 22 tables but sparse demo DB

## Migration to ENDO-TWIN

General Core (src/endo_twin/):
- patient management → src/endo_twin/core/patient.py PatientIdentity
- sensors → src/endo_twin/physiology/ general
- signal acquisition → src/serial_io/ preserved
- signal processing → src/signal_processing/ + src/endo_twin/signals/ general
- feature extraction → src/core/feature_extraction.py + src/endo_twin/features/ general
- baseline → src/core/personal_baseline.py + src/endo_twin/baseline/ general
- longitudinal → src/core/longitudinal_engine.py + src/endo_twin/longitudinal/ general
- database → database/ general + disease-specific references disease_model_id
- reports → reports/ general + disease_models/chrono_pcos/reports/ specific
- provenance → endo_twin/provenance/ + src/endo_twin/provenance/ general MEASURED/CLINICALLY_ENTERED/IMAGE-DERIVED/MODEL-INFERRED/DEMO_DATA/UNKNOWN first-class
- model registry → src/endo_twin/models/model_registry.py general + disease
- uncertainty → src/endo_twin/uncertainty/ general
- visualization → src/ui/ general

PCOS-Specific (disease_models/chrono_pcos/):
- PCOS features, risk logic, model, ultrasound, chrono-metabolic, reports

Preserved: Original scientific work PPG filtering artifact handling HR HRV motion temp sensor communication streaming feature extraction personal baseline longitudinal sleep/circadian chrono-metabolic multimodal fusion ultrasound PCOS modelling reports model artifacts datasets database hardware

Fixed: Real Gradle wrappers 61K jar + 8.4K script, hard-coded inference labeled EXAMPLE_DATA, core no direct PCOS import dynamic importlib plugin loading

One canonical location per purpose.

## Folder Mapping

- src/ → platform/endo_twin/ target (current src/endo_twin/ already close)
- disease_models/chrono_pcos/ → disease_models/chrono_pcos/ already matches
- apps/main/ → apps/endo_twin_desktop/
- desktop/doctor_app/ → apps/doctor_desktop/
- android/patient_app/ + android/patient/ → apps/patient_android/
- android/doctor_app/ + android/doctor/ → apps/doctor_android/
- chrono_pcos_project V8/ → archive/legacy_versions/ (preserve)
- LAUNCH/ launchers/ launcher/ → archive/legacy_launchers/ (preserve) + START.sh canonical
- models/ → models/registry/production/experimental/metadata
- database/ → database/schema/migrations/repositories/seed
- hardware/arduino/ → hardware/arduino/sensors/wiring
- data/ → data/demo/synthetic/public
- scripts/run/build/diagnostics/ → scripts/run/build/test/diagnostics/setup
- tests/ → tests/unit/integration/database/cross_patient/architecture/apps/end_to_end/
- docs/ → docs/recovery/benchmarks/architecture/science/ai_ml/applications/performance/hardware/testing/archive/
- artifacts/android/ → artifacts/android/ endo-twin-patient-debug.apk endo-twin-doctor-debug.apk

## Tests

- TEST1 general dashboard no PCOS knowledge PASS
- TEST2 3 models CHRONO-PCOS True PASS disease-specific module
- TEST3 main without disease model dashboard works general sections PASS true general architecture
- TEST4 extensibility dummy future models Future Cardio/Sleep total 3 PASS can add without rewriting core
- TEST5 preserves original functionality signal pcos_associated_risk level low PASS migration preserved
- TEST6 isolation PASS 7 FAIL 0 no cross-contamination

All 6 PASS after migration.
