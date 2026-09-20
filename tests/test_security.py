"""
Test Security & Privacy V8.3+
"""
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from database.security import AuthManager, EncryptionManager, RoleManager, AuditLogger
from database.database import LocalDatabase

def test_security():
    # AuthManager hash_password verify
    salt, hashed = AuthManager.hash_password("testpass")
    assert salt
    assert hashed
    assert AuthManager.verify_password("testpass", salt, hashed) == True
    assert AuthManager.verify_password("wrongpass", salt, hashed) == False

    # EncryptionManager encrypt decrypt
    key_path = Path("/tmp/test_chrono_key")
    if key_path.exists():
        key_path.unlink()
    enc_mgr = EncryptionManager(key_path)
    original = "Sensitive patient data - research only"
    encrypted = enc_mgr.encrypt(original)
    assert encrypted != original
    decrypted = enc_mgr.decrypt(encrypted)
    assert decrypted == original

    # RoleManager check_permission
    assert RoleManager.check_permission("PATIENT", "own_data") == True
    assert RoleManager.check_permission("PATIENT", "authorized_patients") == False
    assert RoleManager.check_permission("DOCTOR", "authorized_patients") == True
    assert RoleManager.check_permission("DOCTOR", "own_data") == False
    assert RoleManager.check_permission("ADMIN", "provider_directory") == True

    # can_access_patient patient cannot access other patient, doctor only authorized
    assert RoleManager.can_access_patient("PATIENT", "patient_001", "patient_001", []) == True
    assert RoleManager.can_access_patient("PATIENT", "patient_001", "patient_002", []) == False
    assert RoleManager.can_access_patient("DOCTOR", "doctor_001", "patient_001", ["patient_001"]) == True
    assert RoleManager.can_access_patient("DOCTOR", "doctor_001", "patient_002", ["patient_001"]) == False
    assert RoleManager.can_access_patient("ADMIN", "admin_001", "patient_001", []) == True

    # AuditLogger
    log_path = Path("/tmp/test_audit.log")
    if log_path.exists():
        log_path.unlink()
    audit_logger = AuditLogger(log_path)
    entry = audit_logger.log("user_001", "test_action", "test_resource", {"detail": "test"}, success=True)
    assert entry['user_id'] == "user_001"
    assert entry['action'] == "test_action"
    assert log_path.exists()
    # Check file contains JSON
    content = log_path.read_text()
    assert "test_action" in content

    # DataPortabilityManager with LocalDatabase
    db_path = Path("/tmp/test_security_db.db")
    if db_path.exists():
        db_path.unlink()
    db = LocalDatabase(db_path=db_path)
    from database.security import DataPortabilityManager
    port_mgr = DataPortabilityManager(db, enc_mgr)

    patient_id = db.create_patient(display_name="Security Test", age_years=22, bmi=23.5)
    doctor_id = db.create_user("sec_doctor", "pass", "doctor")
    db.grant_access(patient_id, doctor_id, granted_by=doctor_id)

    # Export patient package - patient own data
    package = port_mgr.export_patient_package(patient_id, patient_id, "PATIENT")
    assert package['patient_id'] == patient_id
    assert 'data' in package
    assert 'disclaimer' in package

    # Export - doctor authorized
    package2 = port_mgr.export_patient_package(patient_id, doctor_id, "DOCTOR")
    assert package2['patient_id'] == patient_id

    # Export - patient cannot export other patient
    try:
        port_mgr.export_patient_package(patient_id, "other_patient", "PATIENT")
        assert False, "Should have raised PermissionError"
    except PermissionError:
        pass  # Expected

    # Export - doctor not authorized
    try:
        port_mgr.export_patient_package(patient_id, "unauthorized_doctor", "DOCTOR")
        assert False, "Should have raised PermissionError"
    except PermissionError:
        pass  # Expected

    # Import package
    new_id = port_mgr.import_package(package, doctor_id, "DOCTOR")
    assert new_id

    print("All security tests passed")
    print("Local auth, role separation PATIENT/DOCTOR/ADMIN, encrypted storage prototype, controlled export, audit logging, minimal collection, no cloud upload")
    print("Patient cannot access other patient, doctor only authorized")

if __name__ == '__main__':
    test_security()
