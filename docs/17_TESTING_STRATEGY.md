# 17 - Testing Strategy - V8.3+

## Proper Testing
- Database: create_user, authenticate, create_patient, get_patient, list_patients, search_patients, log_symptom, log_cycle, create_session, list_providers, search_providers, get_nearby_providers, list_supplies, create_report, add_doctor_note, get_doctor_notes, grant_access, check_access, export_patient_data, import_patient_data, backup_database
- Sensor: serial packet parser $CP2 CRC XOR, filtering, baseline removal, artifact detection, missing handling, reconnection, graceful handling unavailable/disconnected/noisy/missing/invalid/serial failure/partial
- Signal Processing: filtering, baseline, artifact, quality control, feature extraction HR HRV GSR motion temp quality
- Artifact: motion artifact detection MPU6050 correlation PPG, PPG artifact amplitude HR outlier, GSR sudden jumps
- Missing: short gaps interpolation quality penalty, long gaps mark missing not fabricate
- Reconnection: SerialManager retry fallback
- Permissions: PATIENT own data only, DOCTOR authorized only, ADMIN provider directory, patient cannot access other patient, doctor only authorized
- Report: generation with disclaimer Research / risk-screening output — not a medical diagnosis, model transparency name/version/input/data quality/confidence/features/limitations
- Import/Export: export_patient_data package, import_package, backup_database, encrypted package, audit logged, permission checks
- Android UI: Patient App Kivy dashboard/profile/measurements/symptoms/cycle/results/reports/sharing/find care, Doctor Android patient list/search/profiles/recent measurements/trends/screening results/ultrasound/reports/notes/follow-up, console demo if Kivy not available
- PC UI: Doctor PC PySide6 dashboard/patient management/physiological data/advanced analysis/ultrasound/longitudinal/notes/reports, preserves src/ui/main_window.py
- AI/Ultrasound: ModelTrainer, ModelEvaluator, PCOSModule SleepModule CardiometabolicModule AutonomicModule, MultimodalFusion, ShapExplainer, ultrasound loading/preprocessing/quality checks/segmentation/inference/visualization/confidence/training/evaluation/storage no invented accuracy

## Failure Conditions
- Unplug: sensor unplugged during measurement, graceful handling, notify user, save partial with quality penalty
- Corrupt: corrupt packet $CP2 CRC fail, discard, log artifact, quality penalty
- No Internet: offline-first core works without internet patient records/sensor collection/signal processing/AI inference/ultrasound/reports/historical/local DB, internet optional provider directory/map/updates/controlled sync, no crash
- Empty DB: no patients, no providers, handle empty list, show No authorized patients yet demo data
- Invalid: invalid input age negative BMI zero, validation discard invalid, error message not crash
- Damaged Image: ultrasound damaged image, quality check fails, result insufficient, not fabricate
- Interrupted: measurement interrupted, save partial session, quality overall reduced
- Duplicate: duplicate patient anonymous_id, handle unique constraint, error message
- Unauthorized: patient trying access other patient data, doctor not authorized, PermissionError, audit logged failure

## Test Files
- tests/test_feature_extraction.py: RealtimeFeatureExtractor initializes, 27 tests pass (existing V8.3)
- tests/test_database.py: LocalDatabase 18 tables, auth, patient CRUD, providers, supplies, export/import (new V8.3+)
- tests/test_care_discovery.py: CareDiscoveryEngine find_nearby search details directions_url OSM list_by_type, SupplyDiscoveryEngine list/search/categories (new)
- tests/test_chrono_metabolic.py: ChronoMetabolicFingerprint build_from_features components categories quality provenance (new)
- tests/test_security.py: AuthManager hash verify, RoleManager check_permission can_access_patient, EncryptionManager encrypt decrypt, AuditLogger (new)

## Running Tests
- pytest tests/ -k not hardware -q (existing)
- python -m database.database (new manual)
- python -m provider_network.care_discovery (new manual)
- python -m core.chrono_metabolic (new manual)
- python -m desktop.doctor_app.main_enhanced (new manual)
- python android/patient_app/main.py (new manual console demo)
- python android/doctor_app/main.py (new manual console demo)
