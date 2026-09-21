from pathlib import Path
import tempfile

from database.database import LocalDatabase
from desktop.doctor_app.test_workstation import DoctorTestWorkstation


def test_doctor_test_workstation_creates_patient_and_session():
    with tempfile.TemporaryDirectory() as tmp:
        db = LocalDatabase(db_path=Path(tmp) / "test.db")
        service = DoctorTestWorkstation(db)
        result = service.run("TEST-001")
        assert result["data_status"] == "DEMO_DATA"
        assert db.get_patient(result["patient_id"]) is not None
        assert db.get_session(result["session_id"], result["patient_id"]) is not None


def test_doctor_test_workstation_does_not_create_physiology_from_missing_samples():
    with tempfile.TemporaryDirectory() as tmp:
        db = LocalDatabase(db_path=Path(tmp) / "test.db")
        service = DoctorTestWorkstation(db)
        result = service.run("TEST-002")
        sensor_checks = [c for c in result["checks"] if c["component"] == "MAX30102"]
        assert sensor_checks[0]["code"] == "FLATLINE"
        assert sensor_checks[0]["status"] == "FAIL"
