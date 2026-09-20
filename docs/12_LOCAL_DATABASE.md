# 12 - Local Database - V8.3+

## Overview
Local-first, prefer SQLite, no cloud upload of private health data default.

## Location
DATA_DIR/chrono_twin_nexus_v8_3_plus.db, fallback /tmp for testing

## Tables (18)

### Users
- user_id PK, username UNIQUE, password_hash, role patient/doctor/admin, created_at, last_login, is_active
- Auth: create_user, authenticate SHA256 prototype, audit logged

### Patients
- patient_id PK, user_id FK, anonymous_id UNIQUE PXXXXX, display_name, age_years, bmi, created_at, updated_at, is_archived
- Methods: create_patient, get_patient, list_patients doctor_id filter authorized only, search_patients, archive

### Profiles
- profile_id PK, patient_id FK, data_json, label USER-ENTERED default, created_at, updated_at

### Symptoms
- symptom_id PK, patient_id FK, symptom_type, severity, notes, logged_at, label USER-ENTERED

### Cycles
- cycle_id PK, patient_id FK, start_date, end_date, cycle_length_days, irregularity, symptoms_json, notes, logged_at, label USER-ENTERED

### Sensor Sessions
- session_id PK, patient_id FK, source, start_at, end_at, sample_count, data_quality, notes, label REAL/SIMULATED/DEMO, created_at

### PPG Data
- id PK, session_id FK, timestamp_s, ir, red, hr_bpm, spo2_pct, pulse_amplitude, quality, label

### HRV Data
- id PK, session_id FK, timestamp_s, hr_bpm, resting_hr_bpm, rmssd_ms, sdnn_ms, pnn50_pct, quality, label

### GSR Data
- id PK, session_id FK, timestamp_s, gsr_raw, gsr_tonic, gsr_phasic_per_min, quality, label

### Motion Data
- id PK, session_id FK, timestamp_s, ax_g, ay_g, az_g, gx_dps, gy_dps, gz_dps, motion_index, activity_level, quality, label

### Temperature Data
- id PK, session_id FK, timestamp_s, skin_temp_c, room_temp_c, temp_slope_c_per_min, quality, label

### Sensor Quality
- id PK, session_id FK, timestamp_s, channel, value, quality, source, artifact, artifact_type, reason, label

### Ultrasound Records
- record_id PK, patient_id FK, image_path, cyst_size_mm, volume_cc, morphology, quality, source, confidence, notes, created_at, label REAL/SYNTHETIC/DEMO

### Model Results
- result_id PK, patient_id FK, session_id, module_name, module_version, signal, level, confidence, data_quality, clinical_validation NOT ESTABLISHED, drivers_json, explanation, provenance_json, limitations, extra_json, created_at, label

### Analysis Results
- analysis_id PK, patient_id FK, session_id, fingerprint_json, circadian_json, autonomic_json, metabolic_json, longitudinal_json, created_at, label

### Reports
- report_id PK, patient_id FK, session_id, report_type, content_text, file_path, created_at, created_by, label REAL

### Doctor Notes
- note_id PK, patient_id FK, doctor_id FK users, note_text, created_at, updated_at, is_private

### Providers (Care Discovery - Separate from Private Records)
- provider_id PK, name, type doctor/clinic/lab/supply, specialty, address, latitude, longitude, distance_km, opening_hours, services_json, contact_info, verification_status verified/pending/unverified/demo, is_demo, created_at, updated_at
- Seeded 4 demo providers all demo status clearly marked never falsely label real doctor/clinic verified

### Supplies
- supply_id PK, name, category sensor/accessory/menstrual/monitoring, description, provider_id FK, price, availability, image_path, created_at
- Seeded 5 supplies: MAX30102 450, MPU6050 250, DS18B20 150, Wrist Band 200, Menstrual Care Kit 300

### Audit Records
- audit_id PK, user_id FK, patient_id FK, action, details_json, timestamp, ip_address

### Patient-Doctor Access
- access_id PK, patient_id FK, doctor_id FK users, granted_at, granted_by, is_active
- grant_access, check_access, doctor only authorized, patient cannot access other patient

## Methods
create_user, authenticate, create_patient, get_patient, list_patients, search_patients, log_symptom, log_cycle, create_session, list_providers, search_providers, get_nearby_providers, list_supplies, create_report, add_doctor_note, get_doctor_notes, grant_access, check_access, export_patient_data, import_patient_data, backup_database

## Export/Import
export_patient_data -> dict patient profiles symptoms cycles sessions reports exported_at label EXPORTED_PACKAGE note research data export not medical record local-first
import_patient_data -> new patient_id audit logged
backup_database -> Path SQLite backup conn.backup
DataPortabilityManager controlled export/import/backup/restore/encrypted package deliberate sharing not automatic

## Why Local-First?
Privacy, offline, no cloud upload default, patient-to-doctor deliberate controlled, Class 11 research.
