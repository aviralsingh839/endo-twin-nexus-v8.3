"""Tests for the continual self-learning layer (``src/core/adaptive_learning.py``).

Everything here runs on SIMULATED wearer streams (:mod:`src.utils.wear_simulator`).
The assertions are about *behaviour that can be checked*: the tier ladder promotes in
order and only on evidence, a persistent shift is absorbed while a transient excursion
is not, poor signal quality rolls the model back, the supervised head refuses to
activate when its labels carry no signal, and per-wearer state round-trips through disk
without cross-contamination.

No test claims clinical validity, and none of them should.
"""
from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import pytest

from src.core.adaptive_learning import (
    HEAD_FEATURES,
    LEARNING_METRICS,
    TIERS,
    AdaptiveConfig,
    AdaptiveWearableModel,
    MetricLearning,
)
from src.utils.wear_simulator import SyntheticWearer, WearEpisode, WearerProfile

# Simulated streams are replayed at one row per minute of wall time.
DAY = 86400.0


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def stream_into(model: AdaptiveWearableModel, wearer: SyntheticWearer, days: float,
                *, record_labels: bool = False) -> list:
    """Replay a simulated wearer into a model. Returns the audit events."""
    events = []
    taken = 0
    for row in wearer.stream(days):
        events.extend(model.observe(row))
        if record_labels:
            labels = wearer.labels()
            while taken < len(labels):
                ts, target, text = labels[taken]
                taken += 1
                model.record_label(text, target=target, at=ts)
    return events


def clone(model: AdaptiveWearableModel, directory: Path, name: str = "clone") -> AdaptiveWearableModel:
    """A second live model on the same learned state (used to avoid test order coupling)."""
    path = Path(directory) / f"{name}.json"
    path.write_text(json.dumps(model.to_dict()), encoding="utf-8")
    return AdaptiveWearableModel(model.patient_id, config=model.cfg, path=path)


# ---------------------------------------------------------------------------
# fixtures - the expensive simulations run once for the whole module
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def ladder_run(tmp_path_factory):
    """Six days of wearing with a clear personal offset from the population prior."""
    directory = tmp_path_factory.mktemp("adaptive-ladder")
    profile = WearerProfile(patient_id="ladder", hr_offset=8.0, rmssd_offset=-10.0,
                            temp_offset=0.4, seed=17)
    model = AdaptiveWearableModel("ladder", path=directory / "ladder.json")
    events = stream_into(model, SyntheticWearer(dataclasses.replace(profile)), 6.0)
    return model, events


@pytest.fixture(scope="module")
def drift_pair(tmp_path_factory):
    """Nine days with a sustained +9 bpm shift starting on day 5.

    One model can reach the adaptive tier, the other is deliberately held at the
    circadian tier by making the top rung unreachable. Same data, same wearer: the only
    difference is the capability the platform has unlocked.
    """
    directory = tmp_path_factory.mktemp("adaptive-drift")
    shift = WearEpisode(start_h=120.0, duration_h=72.0, deltas={"hr_bpm": 9.0, "rmssd_ms": -8.0})
    profile = WearerProfile(patient_id="drift", hr_offset=6.0, rmssd_offset=-6.0, seed=11)

    def run(name: str, cfg: AdaptiveConfig):
        wearer = SyntheticWearer(dataclasses.replace(profile), episodes=[shift])
        model = AdaptiveWearableModel(name, config=cfg, path=directory / f"{name}.json")
        trace = {}
        start = wearer.start_ts
        for row in wearer.stream(9.0):
            model.observe(row)
            wall_h = (row.timestamp_s - start) / 3600.0
            for mark in (120.0, 132.0, 144.0, 192.0):
                if mark not in trace and wall_h >= mark:
                    trace[mark] = model.evaluate("hr_bpm", 85.0)["z"]
        return model, trace

    adaptive, adaptive_trace = run("adaptive", AdaptiveConfig())
    static, static_trace = run("static", AdaptiveConfig(adaptive_min_worn_s=1e9))
    return adaptive, adaptive_trace, static, static_trace


@pytest.fixture(scope="module")
def transient_run(tmp_path_factory):
    """Seven days including one three-hour excursion that must never be absorbed."""
    directory = tmp_path_factory.mktemp("adaptive-transient")
    spike = WearEpisode(start_h=120.0, duration_h=3.0, transient=True,
                        deltas={"hr_bpm": 14.0, "rmssd_ms": -12.0})
    profile = WearerProfile(patient_id="transient", hr_offset=6.0, seed=11)
    model = AdaptiveWearableModel("transient", path=directory / "transient.json")
    events = stream_into(model, SyntheticWearer(dataclasses.replace(profile), episodes=[spike]), 8.0)
    return model, events


def _labelled_episodes(mode: str, days: int = 8) -> list:
    """Label schedules for the supervised head.

    ``informative`` - which hours are abnormal changes every day, so the *only* thing
    that predicts the label is physiology (not clock time).  ``random`` - every episode
    has identical physiology and the labels are noise.
    """
    import random as _random

    hours = (6.0, 8.0, 10.0, 12.0, 14.0, 17.0, 19.0, 21.0)
    rng = _random.Random(99)
    episodes = []
    for day in range(days):
        base = 24.0 * day
        abnormal_hours = set(rng.sample(hours, 4))
        for hour in hours:
            if mode == "informative":
                abnormal = hour in abnormal_hours
                deltas = {"hr_bpm": 11.0, "rmssd_ms": -9.0} if abnormal else {}
                symptom = abnormal
            else:
                deltas = {}
                symptom = rng.random() < 0.5
            # Short episodes: an event the model should keep out of the personal norm.
            episodes.append(WearEpisode(start_h=base + hour, duration_h=0.6, deltas=deltas,
                                        label=f"{mode}-{day}-{hour}", symptom=symptom,
                                        label_delay_h=0.3))
    return episodes


@pytest.fixture(scope="module")
def head_runs(tmp_path_factory):
    directory = tmp_path_factory.mktemp("adaptive-head")
    out = {}
    for mode in ("informative", "random"):
        wearer = SyntheticWearer(WearerProfile(patient_id=f"head-{mode}", seed=5),
                                 wear_start_hour=None, wear_end_hour=None,
                                 episodes=_labelled_episodes(mode))
        model = AdaptiveWearableModel(f"head-{mode}", path=directory / f"{mode}.json")
        stream_into(model, wearer, 8.0, record_labels=True)
        out[mode] = model
    return out


# ---------------------------------------------------------------------------
# the ladder
# ---------------------------------------------------------------------------
def test_tier_ladder_promotes_in_order(ladder_run):
    _, events = ladder_run
    promotions = [e for e in events if e.kind == "promotion"]
    assert [e.to_tier for e in promotions] == ["personalized", "circadian", "adaptive"]
    assert [e.from_tier for e in promotions] == ["population", "personalized", "circadian"]


def test_ladder_does_not_skip_a_rung(ladder_run):
    model, _ = ladder_run
    assert model.status()["tier"] in TIERS
    assert model.status()["upgrades"] == 3


def test_promotion_needs_wearing_time(tmp_path):
    model = AdaptiveWearableModel("fresh", path=tmp_path / "fresh.json")
    wearer = SyntheticWearer(WearerProfile(patient_id="fresh"), wear_start_hour=None,
                             wear_end_hour=None)
    stream_into(model, wearer, 0.02)          # ~29 minutes of wearing
    assert model.tier == "population"
    assert model.worn_seconds < 3600.0


def test_gate_report_says_what_unlocks_next(tmp_path):
    model = AdaptiveWearableModel("gates", path=tmp_path / "gates.json")
    report = model.gate_report()
    assert report["current_tier"] == "population"
    assert report["next_tier"] == "personalized"
    assert report["ready"] is False
    ids = [r["id"] for r in report["requirements"]]
    assert ids == ["worn_seconds", "samples", "metrics", "quality"]
    assert all(r["met"] is False for r in report["requirements"])
    assert "Wear the device" in model.requirement_lines()[0]


def test_requirement_lines_reflect_progress(tmp_path, ladder_run):
    model = AdaptiveWearableModel("progress", path=tmp_path / "progress.json")
    lines = model.requirement_lines()
    assert lines and all(line.startswith("[") for line in lines)
    assert all(".." in line for line in lines)          # nothing met yet
    top, _ = ladder_run
    assert top.gate_report()["next_tier"] is None        # nothing left to unlock
    assert top.requirement_lines() == []


def test_worn_time_ignores_gaps(tmp_path):
    model = AdaptiveWearableModel("gap", path=tmp_path / "gap.json")
    row = {"timestamp_s": 1_000_000.0, "hr_bpm": 70.0, "rmssd_ms": 40.0,
           "skin_temp_c": 32.5, "activity_level": 0.1,
           "signal_quality": 0.9}
    model.observe(row)
    model.observe(dict(row, timestamp_s=1_000_000.0 + 10 * 3600))   # device off for 10 h
    assert model.worn_seconds == 0.0


def test_out_of_range_values_are_refused_not_learned(tmp_path):
    model = AdaptiveWearableModel("bounds", path=tmp_path / "bounds.json")
    wearer = SyntheticWearer(WearerProfile(patient_id="bounds"), wear_start_hour=None,
                             wear_end_hour=None)
    rows = list(wearer.stream(0.05))
    for offset, row in enumerate(rows):
        row.hr_bpm = 9000.0
        model.observe(row, now=1000.0 + offset)
    assert model.metrics["hr_bpm"].n == 0
    assert model.metrics["hr_bpm"].rejected == len(rows)
    assert model.status()["metrics"]["hr_bpm"]["rejected_hint"].endswith("not learned from")


def test_personal_norm_beats_the_population_prior(ladder_run):
    model, _ = ladder_run
    learnt = model.metrics["hr_bpm"].median
    assert learnt is not None
    true_level = 70.0 + 8.0               # population base + this wearer's offset
    population = 72.0
    assert abs(learnt - true_level) < abs(population - true_level)
    assert abs(learnt - true_level) < 4.0


def test_personal_norm_needs_a_representative_window(tmp_path):
    """The norm must not be set from a couple of morning hours."""
    cfg = AdaptiveConfig()
    learner = MetricLearning("hr_bpm", cfg, __import__("random").Random(0))
    cfg = AdaptiveConfig(norm_init_samples=100, norm_init_span_s=6 * 3600.0,
                         norm_init_min_quality=0.5)
    learner = MetricLearning("hr_bpm", cfg, __import__("random").Random(0))
    for i in range(150):                                  # enough samples, ~2.5 h span
        learner.add(70.0, ts=1000.0 + i * 60.0, quality=1.0, dt=60.0)
    assert learner.n is 150
    assert learner.norm_ready is False
    for i in range(150, 700):                             # now the window spans a day
        learner.add(76.0, ts=1000.0 + i * 60.0, quality=1.0, dt=60.0)
    assert learner.norm_ready is True
    assert learner.scale > 1.0                            # starts wide on purpose


def test_z_scores_are_available_only_after_personalization(tmp_path):
    model = AdaptiveWearableModel("early", path=tmp_path / "early.json")
    assert model.z("hr_bpm", 90.0) is None
    evaluation = model.evaluate("hr_bpm", 90.0)
    assert evaluation["basis"] == "population"
    assert evaluation["provenance"] == "POPULATION_PRIOR"
    assert evaluation["z"] is None
    assert "population reference" in evaluation["note"]


# ---------------------------------------------------------------------------
# drift: absorb what persists, never absorb an event
# ---------------------------------------------------------------------------
def test_persistent_shift_is_absorbed_when_adaptive(drift_pair):
    model, trace, _, _ = drift_pair
    assert model.tier == "adaptive"
    assert abs(trace[120.0]) > 3.0            # the deviation is real at the start
    assert abs(trace[144.0]) < abs(trace[120.0])   # and is being absorbed
    assert abs(trace[192.0]) < 1.5            # settled into the new normal
    drift_events = [e for e in model.events if e.kind == "drift"]
    assert drift_events, "a confirmed shift must leave an audit event"
    assert any(e.metric == "hr_bpm" and e.evidence["shift"] > 0 for e in drift_events)


def test_static_tier_cannot_absorb_and_keeps_alarming(drift_pair):
    _, _, static, trace = drift_pair
    assert static.tier == "circadian"          # never earned the adaptive rung
    assert not [e for e in static.events if e.kind == "drift"]
    assert abs(trace[192.0]) > 3.0             # still alarming three days later


def test_transient_excursion_is_never_absorbed(transient_run):
    model, events = transient_run
    assert not [e for e in events if e.kind == "drift"]
    assert abs(model.metrics["hr_bpm"].absorbed_total) < 1.5
    # the norm stays where the wearer's normal is, not where the spike was
    assert abs(model.metrics["hr_bpm"].median - 76.0) < 3.5


def test_drift_evidence_is_recorded(drift_pair):
    model, _, _, _ = drift_pair
    for event in (e for e in model.events if e.kind == "drift"):
        assert event.evidence["persistence_h"] >= 6.0
        assert "shift" in event.evidence
        assert event.detail
        assert event.to_dict()["iso"]


def test_absorption_is_rate_limited(drift_pair):
    """A confirmed shift becomes the new normal over hours, not in one jump."""
    model, _, _, _ = drift_pair
    assert model.cfg.max_adapt_sigma_per_hour > 0
    assert model.cfg.settle_sigma < model.cfg.drift_window_sigma
    assert model.cfg.max_absorb_sigma > 0


# ---------------------------------------------------------------------------
# rollback
# ---------------------------------------------------------------------------
def test_sustained_poor_quality_rolls_the_model_back(ladder_run, tmp_path):
    model = clone(ladder_run[0], tmp_path, "rollback")
    assert model.tier == "adaptive"
    wearer = SyntheticWearer(WearerProfile(patient_id="rollback"), wear_start_hour=None,
                             wear_end_hour=None)
    start = model.last_ts or wearer.start_ts
    events = []
    for offset, row in enumerate(wearer.stream(0.12)):
        row.timestamp_s = start + 60.0 * (offset + 1)
        row.signal_quality = 0.05
        events.extend(model.observe(row, quality=0.05))
    rollbacks = [e for e in events if e.kind == "rollback"]
    assert rollbacks, "sustained bad signal must not leave the model claiming a tier"
    assert rollbacks[0].from_tier == "adaptive"
    assert rollbacks[0].to_tier == "circadian"
    assert "quality" in rollbacks[0].detail
    assert model.tier != "adaptive"          # the claim was withdrawn
    # every demotion is chained and audited
    for earlier, later in zip(rollbacks, rollbacks[1:]):
        assert later.from_tier == earlier.to_tier
        assert later.to_tier in TIERS


def test_rollback_and_recovery_keep_an_audit_trail(ladder_run):
    _, events = ladder_run
    assert [e.to_dict() for e in events] == [e.to_dict() for e in events]   # stable
    assert all(e.kind in {"promotion", "rollback", "drift", "capability"} for e in events)


# ---------------------------------------------------------------------------
# supervised head
# ---------------------------------------------------------------------------
def test_head_stays_collecting_without_labels(ladder_run):
    model, _ = ladder_run
    head = model.status()["head"]
    assert head["status"] == "collecting"
    assert head["n_train"] == 0
    assert "no wearer-labelled events" in head["reason"]


def test_informative_labels_activate_the_head(head_runs):
    head = head_runs["informative"].status()["head"]
    assert head["status"] == "active"
    assert head["prospective_logloss"] < head["baseline_logloss"]
    assert head["prospective_wins"] >= 0.65 * head["n_prospective"]
    assert "not clinical validation" in head["reason"]


def test_labels_without_signal_are_withheld(head_runs):
    """The head must refuse to claim personalization it cannot demonstrate."""
    head = head_runs["random"].status()["head"]
    assert head["status"] == "withheld"
    assert head["prospective_logloss"] >= head["baseline_logloss"]
    assert "no claim is made" in head["reason"]


def test_head_features_are_declared(head_runs):
    model = head_runs["informative"]
    assert len(HEAD_FEATURES) == 6
    assert not any("gsr" in f for f in HEAD_FEATURES)
    assert set(model.status()["head_features"]) == set(HEAD_FEATURES)


def test_label_without_nearby_features_is_refused(tmp_path):
    model = AdaptiveWearableModel("nolabels", path=tmp_path / "nolabels.json")
    assert model.record_label("pain", target=True, at=12345.0) is False
    assert model.status()["head"]["n_train"] == 0


def test_labels_are_wearer_scoped(head_runs):
    """One wearer's labels must never train another wearer's head."""
    import numpy as np

    informative = head_runs["informative"]
    random_labels = head_runs["random"]
    a = informative.status()["head"]
    b = random_labels.status()["head"]
    assert a["n_train"] == b["n_train"] > 0          # same schedule, same label count
    assert informative.path != random_labels.path
    assert not np.allclose(informative.head.w, random_labels.head.w)
    assert a["status"] != b["status"]


# ---------------------------------------------------------------------------
# persistence, isolation, honesty
# ---------------------------------------------------------------------------
def test_state_round_trips_through_disk(ladder_run, tmp_path):
    model, _ = ladder_run
    path = tmp_path / "resume.json"
    model.save()
    resumed = AdaptiveWearableModel(model.patient_id, path=Path(str(model.path)))
    assert resumed.tier == model.tier
    assert resumed.model_version == model.model_version
    assert resumed.worn_seconds == pytest.approx(model.worn_seconds, rel=1e-9)
    assert resumed.metrics["hr_bpm"].median == pytest.approx(model.metrics["hr_bpm"].median)
    assert resumed.metrics["hr_bpm"].circadian_enabled is True
    # a fresh model at an unused path starts at the bottom of the ladder
    fresh = AdaptiveWearableModel(model.patient_id, path=tmp_path / "unused.json")
    assert fresh.tier == "population"
    assert path is not None


def test_wearers_do_not_share_state(tmp_path):
    quiet = AdaptiveWearableModel("wearer-a", path=tmp_path / "a.json")
    active = AdaptiveWearableModel("wearer-b", path=tmp_path / "b.json")
    for wearer, model in ((SyntheticWearer(WearerProfile(patient_id="a", hr_offset=-6.0),
                                           wear_start_hour=None, wear_end_hour=None), quiet),
                          (SyntheticWearer(WearerProfile(patient_id="b", hr_offset=12.0),
                                           wear_start_hour=None, wear_end_hour=None), active)):
        stream_into(model, wearer, 1.6)
    assert quiet.patient_id != active.patient_id
    assert quiet.path != active.path
    assert quiet.metrics["hr_bpm"].median != active.metrics["hr_bpm"].median
    assert not json.loads(active.path.read_text(encoding="utf-8"))["metrics"]["hr_bpm"]["n"] \
        == quiet.metrics["hr_bpm"].n


def test_status_is_json_serialisable_and_labeled(ladder_run):
    model, _ = ladder_run
    status = model.status()
    json.dumps(status)                                    # must not raise
    assert status["schema"] == "endo_twin.adaptive_wearable/1"
    assert "not a diagnosis" in status["disclaimer"].lower()
    assert status["confidence_note"].startswith("engineering confidence")
    assert 0.0 <= status["confidence"] <= 1.0
    assert status["tier_headline"]
    assert set(status["metrics"]) == set(LEARNING_METRICS)


def test_status_exposes_wearing_time_and_norms(ladder_run):
    model, _ = ladder_run
    status = model.status()
    assert status["worn_hours"] > 72.0
    assert status["days_covered"] >= 3
    hr = status["metrics"]["hr_bpm"]
    assert hr["median"] is not None and hr["scale"] > 0
    assert hr["hours_covered"]


def test_observe_accepts_objects_and_mappings(tmp_path):
    model = AdaptiveWearableModel("mixed", path=tmp_path / "mixed.json")
    wearer = SyntheticWearer(WearerProfile(patient_id="mixed"), wear_start_hour=None,
                             wear_end_hour=None)
    for row in wearer.stream(0.05):
        model.observe(row)                                  # dataclass
    for row in wearer.stream(0.05):
        model.observe({                                     # mapping
            "timestamp_s": row.timestamp_s, "hr_bpm": row.hr_bpm, "rmssd_ms": row.rmssd_ms,
            "skin_temp_c": row.skin_temp_c,
            "activity_level": row.activity_level, "signal_quality": row.signal_quality,
        })
    assert model.observations > 0
    assert model.metrics["hr_bpm"].n > 0


def test_scaled_config_only_moves_thresholds():
    base = AdaptiveConfig()
    fast = base.scaled(10.0)
    assert fast.personal_min_worn_s < base.personal_min_worn_s
    assert fast.max_adapt_sigma_per_hour == base.max_adapt_sigma_per_hour
    assert fast.freeze_z == base.freeze_z
    with pytest.raises(ValueError):
        base.scaled(0)
