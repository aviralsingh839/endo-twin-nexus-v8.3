# 13 - Data Portability - V8.3+

## Overview
Controlled export/import/backup/restore/encrypted package, deliberate sharing not automatic, default without cloud, local-first.

## Export
- export_patient_data patient_id -> dict with patient profiles symptoms cycles sessions reports exported_at label EXPORTED_PACKAGE note research data export not medical record local-first
- Controlled: patient can export own data only, doctor only authorized patients, permission check
- Format: JSON dict, includes disclaimer research / risk-screening not diagnosis
- Audit logged

## Import
- import_patient_data data -> new patient_id
- Validates package has patient_id and data
- Creates new patient with imported data
- Audit logged
- If encrypted, decrypt via EncryptionManager

## Backup
- backup_database backup_path -> Path
- SQLite backup via conn.backup
- File path, parent mkdir
- No cloud upload default

## Encrypted Package
- EncryptionManager: Fernet if cryptography available, else prototype base64 with PROTOTYPE_ENCRYPTED label NOT secure
- Key path: DATA_DIR/.chrono_key
- encrypt data str -> token str, decrypt token -> data
- Prototype fallback NOT secure labeled clearly

## Deliberate Sharing
- Patient-to-doctor deliberate controlled
- Not automatic upload
- Doctor sharing tab in patient app: controlled sharing/export of selected info local-first
- Grant access: grant_access patient_id doctor_id granted_by -> access_id audit logged
- Check access: check_access patient_id doctor_id -> bool
- Patient cannot access other patient, doctor only authorized patients

## Audit
- AuditLogger log_path DATA_DIR/audit.log
- log user_id action resource details success -> entry dict timestamp user_id action resource details success
- Append JSON per line

## Why?
Privacy, local-first, no unnecessary cloud upload, patient control, research prototype.

## Testing
Report generation/import/export/android UI/PC UI/AI/ultrasound plus failure conditions unplug/corrupt/no internet/empty DB/invalid/damaged image/interrupted/duplicate/unauthorized
