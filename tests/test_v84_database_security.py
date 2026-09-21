from pathlib import Path
import tempfile

from database.database import LocalDatabase


def test_passwords_use_versioned_hashes_for_new_users():
    with tempfile.TemporaryDirectory() as tmp:
        db = LocalDatabase(db_path=Path(tmp) / "auth.db")
        user_id = db.create_user("test-user", "correct-password", "doctor")
        row = db.conn.execute("SELECT password_hash FROM users WHERE user_id=?", (user_id,)).fetchone()
        stored = row["password_hash"]
        assert stored.startswith("pbkdf2_sha256$")
        assert db.authenticate("test-user", "correct-password") is not None
        assert db.authenticate("test-user", "wrong-password") is None


def test_report_label_is_explicit_and_not_forced_to_real():
    with tempfile.TemporaryDirectory() as tmp:
        db = LocalDatabase(db_path=Path(tmp) / "reports.db")
        patient_id = db.create_patient(anonymous_id="DEMO-REPORT")
        report_id = db.create_report(
            patient_id, "research", "demo report", label="DEMO_DATA"
        )
        row = db.conn.execute("SELECT label FROM reports WHERE report_id=?", (report_id,)).fetchone()
        assert row["label"] == "DEMO_DATA"


def test_session_is_patient_scoped():
    with tempfile.TemporaryDirectory() as tmp:
        db = LocalDatabase(db_path=Path(tmp) / "session.db")
        patient_a = db.create_patient(anonymous_id="A")
        patient_b = db.create_patient(anonymous_id="B")
        session = db.create_session(patient_a, "TEST", "DEMO_DATA")
        assert db.get_session(session, patient_id=patient_a) is not None
        assert db.get_session(session, patient_id=patient_b) is None
