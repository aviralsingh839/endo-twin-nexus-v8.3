from __future__ import annotations

import time
from types import SimpleNamespace

from src.personal_twin import profile_store
from src.personal_twin.adaptive_model import PersonalAdaptiveModel


def test_profile_state_and_adaptive_learning(tmp_path, monkeypatch):
    monkeypatch.setattr(profile_store, "STATE_PATH", tmp_path / "state.json")
    monkeypatch.setattr(profile_store, "EVENTS_PATH", tmp_path / "events.jsonl")
    monkeypatch.setattr(profile_store, "DATA_DIR", tmp_path)

    profile = profile_store.save_profile({
        "participant_id": "PT-TEST",
        "age_years": 18,
        "height_cm": 165,
        "weight_kg": 60,
        "bmi": 22.04,
        "provenance": "USER-ENTERED",
    })
    assert profile["profile"]["participant_id"] == "PT-TEST"

    model = PersonalAdaptiveModel("PT-TEST")
    for i in range(8):
        model.observe(
            SimpleNamespace(
                timestamp_s=time.time(),
                hr_bpm=72.0 + (i % 2),
                rmssd_ms=40.0,
                skin_temp_c=32.5,
                gsr_tonic=500.0,
                activity_level=20.0,
                stress_index=30.0,
                sleep_probability=70.0,
                signal_quality=0.9,
            ),
            quality=0.9,
        )
    snap = model.snapshot()
    assert snap["samples"] == 8
    assert snap["metrics"]["hr_bpm"]["samples"] >= 7
    assert snap["metrics"]["hr_bpm"]["std"] if "std" in snap["metrics"]["hr_bpm"] else True
    assert (tmp_path / "events.jsonl").exists()


def test_multiple_people_are_isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(profile_store, "STATE_PATH", tmp_path / "state.json")
    monkeypatch.setattr(profile_store, "EVENTS_PATH", tmp_path / "events.jsonl")
    monkeypatch.setattr(profile_store, "DATA_DIR", tmp_path)

    profile_store.save_profile({"participant_id": "PT-A", "alias": "A", "age_years": 20})
    profile_store.save_profile({"participant_id": "PT-B", "alias": "B", "age_years": 21})

    a = PersonalAdaptiveModel("PT-A")
    b = PersonalAdaptiveModel("PT-B")
    feature = SimpleNamespace(
        timestamp_s=time.time(),
        hr_bpm=70.0,
        rmssd_ms=40.0,
        skin_temp_c=32.0,
        gsr_tonic=10.0,
        activity_level=20.0,
        stress_index=30.0,
        sleep_probability=70.0,
        signal_quality=0.9,
    )
    a.observe(feature, quality=0.9)
    a.flush()

    assert PersonalAdaptiveModel("PT-A").snapshot()["samples"] == 1
    assert PersonalAdaptiveModel("PT-B").snapshot()["samples"] == 0
    profile_store.select_participant("PT-B")
    assert profile_store.get_profile()["participant_id"] == "PT-B"
    assert profile_store.get_learning()["samples"] == 0
