"""Tests for the longitudinal core: change detector, gradual baseline,
digital-twin timeline and manual-input storage."""
import time

from src.config import APP_VERSION, APP_VERSION_LABEL
from src.data_models import FeatureVector
from src.models.change_detector import ChangeDetector
from src.models.personalization import BaselineManager
from src.models.timeline import build_timeline, timeline_text
from src.utils.history_store import HistoryStore


def _fv(ts: float, hr: float, q: float = 0.9, rmssd: float = 40.0,
        temp: float = 32.5, gsr: float = 450.0, activity: float = 10.0) -> FeatureVector:
    return FeatureVector(
        timestamp_s=ts, hr_bpm=hr, rmssd_ms=rmssd, skin_temp_c=temp,
        gsr_tonic=gsr, activity_level=activity, motion_index=0.05,
        signal_quality=q,
    )


# ------------------------------------------------------------- versioning
def test_versioning():
    assert APP_VERSION.startswith("8.")
    assert "not clinically validated" in APP_VERSION_LABEL.lower()


# ------------------------------------------------------- change detector
def test_change_detector_normal():
    det = ChangeDetector()
    feats = [_fv(100 + i * 60, 72.0) for i in range(40)]
    rep = det.evaluate(feats)
    assert rep.overall_kind == "normal"
    assert rep.per_metric["hr_bpm"].kind == "normal"


def test_change_detector_single_deviation():
    det = ChangeDetector()
    feats = [_fv(100 + i * 60, 72.0) for i in range(39)]
    feats.append(_fv(100 + 39 * 60, 125.0))
    rep = det.evaluate(feats)
    assert rep.per_metric["hr_bpm"].kind == "single"
    assert rep.overall_kind == "deviation"


def test_change_detector_persistent():
    det = ChangeDetector()
    feats = [_fv(100 + i * 60, 72.0) for i in range(5)]
    feats += [_fv(100 + (5 + i) * 60, 108.0) for i in range(30)]
    rep = det.evaluate(feats)
    assert rep.per_metric["hr_bpm"].kind == "persistent"
    assert rep.per_metric["hr_bpm"].persistence_points >= 3
    assert rep.contributors


def test_change_detector_progressive():
    det = ChangeDetector()
    feats = [_fv(100 + i * 60, 72.0 + 0.95 * i) for i in range(40)]  # ramp 72 -> 110
    rep = det.evaluate(feats)
    assert rep.per_metric["hr_bpm"].kind == "progressive"
    assert rep.per_metric["hr_bpm"].slope_per_day > 0


def test_change_detector_recovery():
    det = ChangeDetector()
    feats = [_fv(100 + i * 60, 72.0) for i in range(10)]
    feats += [_fv(100 + (10 + i) * 60, 108.0) for i in range(15)]
    feats += [_fv(100 + (25 + i) * 60, 72.0) for i in range(15)]
    rep = det.evaluate(feats)
    assert rep.per_metric["hr_bpm"].kind == "recovery"


def test_change_detector_never_alerts_on_noisy_single_reading():
    det = ChangeDetector()
    feats = [_fv(100 + i * 60, 72.0) for i in range(30)]
    feats += [_fv(100 + (30 + i) * 60, 125.0, q=0.15) for i in range(4)]
    rep = det.evaluate(feats)
    assert rep.overall_kind == "insufficient_quality"
    assert rep.per_metric["hr_bpm"].kind == "insufficient"


# ------------------------------------------------- gradual baseline update
def test_baseline_gradual_updates(tmp_path):
    mgr = BaselineManager(path=tmp_path / "b.json", history_path=tmp_path / "h.json")
    feats = [_fv(100 + i * 10, 70.0) for i in range(80)]
    mgr.capture_from_features(feats, min_samples=60)
    assert mgr.has_baseline
    med0 = mgr.baseline.stats["hr_bpm"].median

    # A run of outliers must NOT redefine the baseline.
    for i in range(60):
        mgr.update_observation(_fv(2000 + i * 10, 145.0))
    assert abs(mgr.baseline.stats["hr_bpm"].median - med0) < 1.0

    # Gradual drift follows slowly (far less than the raw +10 shift).
    for i in range(60):
        mgr.update_observation(_fv(3000 + i * 10, 80.0))
    moved = mgr.baseline.stats["hr_bpm"].median - med0
    assert 0.0 < moved < 6.0

    # Robust z-score works after updates.
    z = mgr.robust_zscore("hr_bpm", 90.0)
    assert z is not None and z > 0


# ------------------------------------------------------ timeline + store
def test_timeline_and_manual_tables(tmp_path):
    db = HistoryStore(tmp_path / "t.db")
    db.start_session(source="demo")
    db.log_calibration(duration_s=300, quality=0.9, stats_json="{}")
    db.log_anomaly(None, time.time(), type("A", (), {
        "signal": "hr_bpm", "value": 120.0, "expected_low": 60.0, "expected_high": 85.0,
        "severity": 70.0, "description": "HR outside personal range"}))
    db.log_bp(118, 76)
    db.log_glucose(92, context="fasting")
    db.log_weight(64.5)
    db.log_symptom("bloating", 4)
    db.log_cycle_entry(cycle_day=12, cycle_length=30)
    db.log_ultrasound(cyst_size_mm=28, morphology="simple")
    db.log_event(None, "ecg_checkpoint", "completed")

    events = build_timeline(db)
    kinds = {e.kind for e in events}
    assert {"session", "baseline", "anomaly", "bp", "glucose", "weight",
            "symptom", "cycle", "ultrasound", "ecg_checkpoint"} <= kinds
    assert timeline_text(events)

    # Round-trips.
    assert db.bp_readings()[0]["systolic"] == 118
    assert db.glucose_readings()[0]["context"] == "fasting"
    assert db.symptoms()[0]["severity"] == 4
    assert db.ultrasound_history()[0]["cyst_size_mm"] == 28
    counts = db.row_counts()
    assert counts["bp_readings"] == 1 and counts["ultrasound_observations"] == 1
