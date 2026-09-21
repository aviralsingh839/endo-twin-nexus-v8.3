import base64
import time

from database.database import LocalDatabase
from src.data_models import FeatureVector, SensorSample
from src.ml.self_learning import SelfLearningEngine
from src.utils.demo_stream import DemoSensorStream


def test_demo_stream_polling_contract():
    stream = DemoSensorStream()
    assert stream.has_sample() is False
    stream._tick()
    assert stream.has_sample() is True
    sample = stream.get_sample()
    assert sample is not None
    assert stream.has_sample() is False


def test_wearable_study_lifecycle_and_sync(tmp_path):
    db = LocalDatabase(db_path=tmp_path / "doctor.db")
    patient_id = db.create_patient(anonymous_id="TEST-P1", age_years=21, bmi=22.0)
    study_id = db.start_study(patient_id, duration_hours=48)
    session_id = db.create_session(
        patient_id,
        source="TEST",
        label="REAL",
        study_id=study_id,
    )
    db.register_wearable(patient_id, "W-01", "prototype", "BLE")
    db.set_wearable_state(patient_id, "W-01", "WORN")

    sample = SensorSample(
        timestamp_s=time.time(),
        ms=1,
        ir=1000,
        red=900,
        ax_g=0.0,
        ay_g=0.0,
        az_g=1.0,
        gx_dps=0.0,
        gy_dps=0.0,
        gz_dps=0.0,
        temp_c=32.0,
        gsr_raw=400,
        lux=100.0,
        source="serial",
    )
    fv = FeatureVector(timestamp_s=sample.timestamp_s, hr_bpm=72.0, signal_quality=0.9)
    db.save_sensor_sample(patient_id, session_id, sample, fv, "REAL")
    db.save_raw_wearable_packet(
        patient_id,
        session_id,
        base64.b64encode(b"TEST_PACKET").decode(),
        "BLE",
        None,
        "REAL",
    )

    db.close_sensor_session(patient_id, session_id, "Removed before bathing")
    db.record_wearable_event(
        patient_id,
        session_id,
        "WEARABLE_REMOVED_BATHING",
        {"gap_is_missing_data": True},
    )

    package = db.export_patient_data(patient_id)
    assert package["patient"]["patient_id"] == patient_id
    assert package["sessions"]
    assert package["ppg_data"]
    assert package["feature_vectors"]
    assert package["raw_wearable_packets"]
    assert any(e["event_type"] == "WEARABLE_REMOVED_BATHING" for e in package["wearable_events"])

    other = LocalDatabase(db_path=tmp_path / "doctor_import.db")
    imported = other.import_patient_data(package)
    assert imported == patient_id
    assert len(other.list_sessions(patient_id)) == 1
    assert len(other.list_feature_vectors(patient_id)) == 1


def test_personalization_updates_baselines(tmp_path):
    db = LocalDatabase(db_path=tmp_path / "learning.db")
    patient_id = db.create_patient(anonymous_id="TEST-P2")
    session_id = db.create_session(patient_id, "TEST", "REAL")
    for i in range(5):
        fv = FeatureVector(
            timestamp_s=time.time() + i,
            hr_bpm=70 + i,
            rmssd_ms=45 + i,
            skin_temp_c=32.0 + 0.1 * i,
            activity_level=0.2 + 0.02 * i,
            gsr_tonic=400 + i,
            stress_index=20 + i,
            sleep_probability=0.7,
            circadian_disruption=20,
        )
        db.save_feature_vector(patient_id, session_id, fv)
    result = SelfLearningEngine().personalize(db, patient_id)
    assert result.status == "ADAPTED"
    assert result.features_updated >= 1
    assert db.conn.execute(
        "SELECT COUNT(*) FROM personal_baselines WHERE patient_id=?",
        (patient_id,),
    ).fetchone()[0] >= 1
