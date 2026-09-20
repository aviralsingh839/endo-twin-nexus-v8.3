# 16 - Security & Privacy - V8.3+

## Principles
- Local-first, no cloud upload of private health data default
- Minimal collection, no unnecessary personal info
- Role separation
- Encrypted storage prototype
- Controlled export
- Audit logging
- Patient cannot access other patient, doctor only authorized patients

## Auth
- AuthManager: hash_password password salt -> salt hashed SHA256 PBKDF2 100000 iterations, verify_password
- Users table: user_id, username UNIQUE, password_hash, role patient/doctor/admin, created_at, last_login, is_active
- create_user username password role -> user_id, authenticate username password -> dict or None, audit logged
- Prototype hashing, production would use bcrypt

## Encryption
- EncryptionManager: key_path DATA_DIR/.chrono_key, Fernet if cryptography available else prototype base64 PROTOTYPE_ENCRYPTED label NOT secure
- encrypt data str -> token, decrypt token -> data
- Encrypted storage prototype, labeled

## Role System
- PATIENT: own_data, measurements, results, manage, share - own data only, cannot access other patient
- DOCTOR: authorized_patients, review, analysis, notes, reports - only authorized patients via patient_doctor_access
- ADMIN: provider_directory, system_config, demo_data, verification - prototype manage provider directory system config demo data verification
- RoleManager: ROLES dict permissions description, check_permission role permission -> bool, can_access_patient requester_role requester_id patient_id access_list -> bool patient only own doctor only authorized admin all

## Access Control
- patient_doctor_access table: access_id, patient_id FK, doctor_id FK users, granted_at, granted_by, is_active
- grant_access patient_id doctor_id granted_by -> access_id audit logged
- check_access patient_id doctor_id -> bool
- list_patients doctor_id filter authorized only
- Patient cannot access other patient, doctor only authorized patients

## Audit Logging
- AuditLogger log_path DATA_DIR/audit.log parent mkdir
- audit_records table: audit_id, user_id FK, patient_id FK, action, details_json, timestamp, ip_address
- _log_audit user_id patient_id action details -> audit_id
- log user_id action resource details success -> entry timestamp user_id action resource details success append JSON per line file
- Actions: create_user, login, create_patient, add_doctor_note, grant_access, import_patient_data, export

## Data Portability
- DataPortabilityManager: db, encryption_mgr
- export_patient_package patient_id requester_id requester_role include_sensitive -> package export_version 8.3+ exported_at exported_by role patient_id data disclaimer research data export not medical diagnosis controlled sharing local-first encryption encrypted/prototype_obfuscation audit logged, permission check patient only own doctor authorized, encrypt sensitive if needed
- import_package package importer_id importer_role -> new_id validate patient_id data, decrypt if encrypted, import, audit
- backup_database backup_path -> Path SQLite backup conn.backup

## Minimal Collection
- Anonymous_id PXXXXX not real name required
- Age, BMI USER-ENTERED minimal
- No unnecessary personal info
- Symptoms, cycles USER-ENTERED
- Sensor data labeled REAL/SIMULATED/DEMO

## No Cloud Upload
- Default without cloud
- Local SQLite
- Do NOT upload private health to public website
- Provider directory separate from private records
- Optional internet: provider directory/map/updates/controlled sync only, not private health
