from pathlib import Path

from database.database import LocalDatabase


def test_local_patient_can_be_created_and_retrieved(tmp_path: Path):
    db = LocalDatabase(tmp_path / "test.db")
    patient_id = db.create_patient(
        display_name="Bench Test",
        anonymous_id="PROTO-001",
        age_years=24,
        bmi=22.5,
    )
    patient = db.get_patient(patient_id)
    assert patient is not None
    assert patient["anonymous_id"] == "PROTO-001"
    assert patient["display_name"] == "Bench Test"
    assert patient["age_years"] == 24
    assert patient["bmi"] == 22.5
    db.close()


def test_created_patient_starts_without_disease_model(tmp_path: Path):
    db = LocalDatabase(tmp_path / "test.db")
    patient_id = db.create_patient(display_name="No Model", anonymous_id="PROTO-002")
    patient = db.get_patient(patient_id)
    assert patient is not None
    assert db.list_patients()
    db.close()
