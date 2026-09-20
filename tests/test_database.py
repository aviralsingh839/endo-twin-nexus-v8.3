"""
Test LocalDatabase V8.3+
"""
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from database.database import LocalDatabase

def test_database():
    db_path = Path("/tmp/test_chrono_db_unit.db")
    if db_path.exists():
        db_path.unlink()
    db = LocalDatabase(db_path=db_path)

    # Users
    user_id = db.create_user("test_patient", "password123", "patient")
    assert user_id
    auth = db.authenticate("test_patient", "password123")
    assert auth
    assert auth['role'] == 'patient'

    # Patients
    patient_id = db.create_patient(user_id=user_id, display_name="Test Patient", age_years=22, bmi=23.5)
    assert patient_id
    patient = db.get_patient(patient_id)
    assert patient
    assert patient['age_years'] == 22

    patients = db.list_patients()
    assert len(patients) >= 1

    search = db.search_patients(patient['anonymous_id'][:3])
    assert len(search) >= 1

    # Symptoms
    sym_id = db.log_symptom(patient_id, "irregular_cycle", 3, "Test notes USER-ENTERED")
    assert sym_id

    # Cycles
    import time
    cycle_id = db.log_cycle(patient_id, time.time(), 28, "regular", "Test USER-ENTERED")
    assert cycle_id

    # Sessions
    session_id = db.create_session(patient_id, "REAL", "REAL", "Test session")
    assert session_id

    # Providers
    providers = db.list_providers()
    assert len(providers) == 4  # seeded demo
    assert providers[0]['verification_status'] == 'demo'
    assert providers[0]['is_demo'] == 1

    nearby = db.get_nearby_providers(28.6692, 77.4538, 10)
    assert len(nearby) == 4

    search_prov = db.search_providers("Gynecology")
    assert len(search_prov) >= 1

    # Supplies
    supplies = db.list_supplies()
    assert len(supplies) == 5

    # Reports
    report_id = db.create_report(patient_id, "screening", "Test report content Research / risk-screening output — not a medical diagnosis", "test_doctor")
    assert report_id

    # Doctor notes
    doctor_id = db.create_user("test_doctor", "docpass", "doctor")
    note_id = db.add_doctor_note(patient_id, doctor_id, "Test note - follow-up in 2 weeks")
    assert note_id
    notes = db.get_doctor_notes(patient_id)
    assert len(notes) == 1

    # Access control
    access_id = db.grant_access(patient_id, doctor_id, granted_by=doctor_id)
    assert access_id
    assert db.check_access(patient_id, doctor_id) == True
    assert db.check_access(patient_id, "nonexistent") == False

    # Export/Import
    exported = db.export_patient_data(patient_id)
    assert 'patient' in exported
    assert 'profiles' in exported
    assert exported['label'] == 'EXPORTED_PACKAGE'

    imported_id = db.import_patient_data(exported)
    assert imported_id

    # Backup
    backup_path = Path("/tmp/backup_test.db")
    if backup_path.exists():
        backup_path.unlink()
    backup = db.backup_database(backup_path)
    assert backup.exists()

    # Audit
    # _log_audit called internally, check audit_records
    import sqlite3
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM audit_records")
    count = cur.fetchone()[0]
    assert count > 0

    print("All database tests passed")
    print(f"Providers: {len(providers)} demo, Supplies: {len(supplies)}, Patients: {len(patients)}")
    print("Research / risk-screening output — not a medical diagnosis")

if __name__ == '__main__':
    test_database()
