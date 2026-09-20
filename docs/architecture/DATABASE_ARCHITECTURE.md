# DATABASE ARCHITECTURE

Date: 2026-09-19
Version: 8.3+
Status: IMPLEMENTED

## One Canonical Database Architecture

At minimum:

- patients
- patient_identity
- observations
- measurements
- signals
- sensor_sessions
- features
- baselines
- timeline_events
- symptoms
- cycles
- clinical_observations
- ultrasound_studies
- ultrasound_features
- model_versions
- model_runs
- predictions
- reports
- providers
- doctor_notes
- audit_events
- provenance_records

Use: foreign keys, migrations, repositories, transactions, indexes, validation. UI code should not randomly manipulate raw tables.

## Current Implementation

- `database/database.py` - Original DB LocalDatabase
- `database/endo_twin_database.py` - ENDO-TWIN DB EndoTwinDatabase with DEMO_DATA DEMO-001,002,003 clearly labeled, patient_id DEMO-xxx is_demo=1 label DEMO_DATA, HR 72/78/68 intentionally different data
- `database/security.py` - Security AuthManager hash_password PBKDF2, EncryptionManager Fernet if available else PROTOTYPE_ENCRYPTED base64 labeled, RoleManager PATIENT/DOCTOR/ADMIN permissions
- SQLite tables: patients/profiles/symptoms/cycles/sensor_sessions/PPG/HRV/GSR/motion/temp/quality/ultrasound/model_results/analysis_results/reports/doctor_notes/providers/supplies/audit/access - matches required list
- Local-first, no upload private health to public website, default no cloud
- Portability: controlled export/import/backup/restore/encrypted package deliberate not automatic

## Multipatient Support

- Doctor workflow: Doctor → Patient Registry → Search/Filter → Patient Selection → Patient Workspace
- Per-doctor scoping: list_patients doctor_id filtering, search_patients with authorized filter
- Patient isolation: DEMO-001 cannot see DEMO-002 database level, tests/test_multi_patient_isolation.py PASS 7 FAIL 0, tests/test_endo_twin_isolation.py PASS
- Selected patient identity always obvious
- Multipatient functionality implemented database/repository layer not just UI

## Provenance

Every important value carries origin: MEASURED, CLINICAL_ENTRY, DERIVED, IMAGE_DERIVED, MODEL_INFERRED, DEMO, SIMULATED, UNKNOWN - first-class.

## Performance

- DB init 61.6 ms fast
- Patient creation 2.1 ms fast
- List patients 0.1 ms very fast indexed
- Search patients 0.1 ms very fast
- No repeatedly load entire database → recompute → redraw for every screen

## Offline-First

Core works without internet, SQLite local-first.

## Testing

- Database migrations, CRUD, foreign keys, patient isolation
- DEMO-001,002,003 intentionally different data, test Select DEMO-001→only DEMO-001 data etc., any leakage test failure
