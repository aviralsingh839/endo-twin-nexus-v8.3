from src.endo_twin.core.schema_models import MeasurementSchema, PatientSchema
from src.endo_twin.integrations.scientific_backend import imaging_backend_status, optional_backend_status


def test_patient_schema_keeps_patient_scope():
    patient = PatientSchema(patient_id="DEMO-001", enabled_disease_models=["chrono_pcos"])
    assert patient.patient_id == "DEMO-001"
    assert "chrono_pcos" in patient.enabled_disease_models


def test_measurement_schema_rejects_invalid_quality():
    try:
        MeasurementSchema(patient_id="DEMO-001", measurement_type="heart_rate", value=72, unit="bpm", quality=1.5, provenance="DEMO_DATA")
    except Exception:
        return
    raise AssertionError("measurement quality outside [0,1] must be rejected")


def test_optional_backends_are_reported_without_being_required():
    statuses = optional_backend_status()
    assert "neurokit2" in statuses
    assert "pyhrv" in statuses
    assert "monai" in statuses
    assert "pydicom" in statuses


def test_imaging_backend_status_has_no_fabricated_model_result():
    status = imaging_backend_status()
    assert set(status) == {"pydicom", "monai"}
    assert all(isinstance(value, bool) for value in status.values())
