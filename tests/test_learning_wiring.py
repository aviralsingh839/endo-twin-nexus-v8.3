"""Wiring tests for the continual self-learning layer.

Three things are checked here, all headless:

1. the live feature path (``RealtimeFeatureExtractor``) really does feed every computed
   row into the learner, and prefers the learner's personal z-score over the frozen
   one-hour snapshot once the learner has a personal norm;
2. the data contract between the engine and the learning panel (``src/ui/learning_panel.py``).
   The panel is PySide6 code and cannot be imported in this environment (no libGL), so
   the contract is checked at the source level: every ``status.get("<key>")`` the panel
   reads must exist in ``AdaptiveWearableModel.status()``. If someone renames a status
   field, this test fails instead of the panel silently rendering nothing;
3. a wearer's learned state survives a restart of the app.

Everything is simulated. Nothing here is clinical evidence.
"""
from __future__ import annotations

import re
import time
from pathlib import Path

import pytest

from src.config import DEFAULT_PROFILE
from src.core.adaptive_learning import TIERS, AdaptiveWearableModel
from src.core.feature_extraction import RealtimeFeatureExtractor
from src.core.personal_baseline import PersonalBaselineEngine
from src.data_models import SensorSample

ROOT = Path(__file__).resolve().parents[1]
PANEL_SOURCE = ROOT / "src" / "ui" / "learning_panel.py"
DAY = 86400.0


def _sample(i: int) -> SensorSample:
    return SensorSample(
        timestamp_s=time.time(), ms=i, ir=1000 + i, red=1200 + i,
        ax_g=0.01, ay_g=0.0, az_g=1.0, gx_dps=0.0, gy_dps=0.0, gz_dps=0.0,
        temp_c=32.5, gsr_raw=450, lux=120.0,
    )


def _fresh_extractor(tmp_path: Path, learner: AdaptiveWearableModel) -> RealtimeFeatureExtractor:
    return RealtimeFeatureExtractor(
        profile=DEFAULT_PROFILE,
        baseline_engine=PersonalBaselineEngine(path=tmp_path / "baseline.json",
                                              history_path=tmp_path / "history.json"),
        learner=learner,
    )


def _row(ts: float, hr: float = 74.0, quality: float = 0.9) -> dict:
    return {
        "timestamp_s": ts,
        "hr_bpm": hr,
        "resting_hr_bpm": hr - 8.0,
        "rmssd_ms": 42.0,
        "skin_temp_c": 32.5,
        "gsr_tonic": 450.0,
        "activity_level": 0.12,
        "signal_quality": quality,
    }


def _seed_personal_norm(model: AdaptiveWearableModel, metric: str = "hr_bpm") -> None:
    """Give the learner a settled personal norm for one metric."""
    for minute in range(0, 60 * 24, 1):
        model.observe(_row(1_700_000_000.0 + minute * 60.0))
    assert model.metrics[metric].norm_ready, "the seeded stream should establish a norm"


# ---------------------------------------------------------------------------
# live path
# ---------------------------------------------------------------------------
def test_extractor_observes_every_computed_row(tmp_path):
    learner = AdaptiveWearableModel("wiring", path=tmp_path / "model.json")
    extractor = _fresh_extractor(tmp_path, learner)

    for i in range(5):
        extractor.add_sample(_sample(i))
        extractor.compute()

    assert learner.status()["observations"] == 5
    assert extractor.learning_events == []
    assert learner.status()["tier"] in TIERS


def test_extractor_prefers_the_learned_norm_once_it_exists(tmp_path):
    learner = AdaptiveWearableModel("wiring", path=tmp_path / "model.json")
    _seed_personal_norm(learner)
    extractor = _fresh_extractor(tmp_path, learner)

    ts = 1_700_000_000.0 + DAY  # one minute past the seeded window
    expected = learner.z("hr_bpm", 88.0, at_ts=ts)
    assert expected is not None

    from_learner = extractor._z("hr_bpm", 88.0, ts)
    from_snapshot = extractor.baseline_engine.zscore("hr_bpm", 88.0)

    assert from_learner == pytest.approx(expected)
    assert from_learner != from_snapshot or from_snapshot is None


def test_extractor_falls_back_to_the_frozen_snapshot(tmp_path):
    learner = AdaptiveWearableModel("wiring", path=tmp_path / "model.json")
    extractor = _fresh_extractor(tmp_path, learner)

    # No learner norm yet, and no captured baseline either: the old path must be reached.
    assert learner.z("hr_bpm", 88.0, at_ts=1_700_000_000.0) is None
    assert extractor._z("hr_bpm", 88.0, 1_700_000_000.0) == extractor.baseline_engine.zscore("hr_bpm", 88.0)


def test_learner_accepts_the_mapping_rows_the_patient_app_sends(tmp_path):
    learner = AdaptiveWearableModel("wiring", path=tmp_path / "model.json")

    learner.observe(_row(1_700_000_000.0))
    learner.observe({"hr_bpm": None, "signal_quality": 0.4}, now=1_700_000_060.0)

    assert learner.status()["observations"] == 2


# ---------------------------------------------------------------------------
# panel <-> engine contract
# ---------------------------------------------------------------------------
def _panel_status_keys() -> set[str]:
    source = PANEL_SOURCE.read_text(encoding="utf-8")
    keys = set(re.findall(r'status\.get\(\s*"([a-z_]+)"', source))
    keys |= set(re.findall(r"status\['([a-z_]+)'\]", source))
    assert keys, "the panel contract test found no status keys - did the panel move?"
    return keys


def test_panel_only_reads_status_fields_the_engine_provides(tmp_path):
    learner = AdaptiveWearableModel("contract", path=tmp_path / "model.json")
    status = learner.status()

    missing = sorted(key for key in _panel_status_keys() if key not in status)
    assert not missing, f"learning panel reads fields the engine does not publish: {missing}"


def test_panel_requirement_rows_carry_label_progress_and_met(tmp_path):
    learner = AdaptiveWearableModel("contract", path=tmp_path / "model.json")
    requirements = learner.status()["requirements"]

    assert requirements, "a fresh model should still list what it is waiting for"
    for row in requirements:
        assert {"label", "current", "target", "met"} <= set(row)
        assert isinstance(row["met"], bool)


def test_panel_colours_must_be_supplied_by_the_host(tmp_path):
    """The panel must not carry its own hex values - the host palette is audited."""
    source = PANEL_SOURCE.read_text(encoding="utf-8")
    hexes = re.findall(r"#[0-9A-Fa-f]{6}", source)
    assert hexes == [], f"learning panel introduces unaudited colours: {hexes}"
    assert "REQUIRED_COLOURS" in source


def test_host_palettes_reuse_audited_theme_colours():
    """Whatever the two hosts hand the panel must already live in an audited theme file."""
    theme = (ROOT / "src" / "ui" / "theme.py").read_text(encoding="utf-8")
    workstations = (ROOT / "desktop" / "workstation_theme.py").read_text(encoding="utf-8")

    window = (ROOT / "src" / "ui" / "main_window.py").read_text(encoding="utf-8")
    window_palette = re.search(r"LearningStatusPanel\(palette=\{(.*?)\}\)", window, re.S)
    assert window_palette, "main_window should pass an explicit palette to the panel"
    body = window_palette.group(1)
    assert not re.findall(r"#[0-9A-Fa-f]{6}", body), "main_window should pass theme names, not hexes"
    for name in sorted(set(re.findall(r":\s*([A-Z][A-Z_0-9]{2,})\b", body))):
        assert re.search(rf"^{name}\s*=", theme, re.M), f"{name} is not a token in src/ui/theme.py"

    patient = (ROOT / "desktop" / "patient_app" / "main.py").read_text(encoding="utf-8")
    patient_palette = re.search(r"palette=\{(.*?)\},\s*\n\s*allow_labels", patient, re.S)
    assert patient_palette, "patient app should pass an explicit palette to the panel"
    hexes = re.findall(r"#[0-9A-Fa-f]{6}", patient_palette.group(1))
    assert len(hexes) == 6, f"expected six palette colours, found {hexes}"
    for hexcode in hexes:
        assert hexcode.lower() in workstations.lower(), \
            f"patient palette colour {hexcode} is not used by the audited workstation theme"


# ---------------------------------------------------------------------------
# persistence
# ---------------------------------------------------------------------------
def test_learned_state_survives_a_restart(tmp_path):
    path = tmp_path / "model.json"
    first = AdaptiveWearableModel("restart", path=path)
    for minute in range(0, 60 * 30):
        first.observe(_row(1_700_000_000.0 + minute * 60.0))
    first.save()

    before = first.status()
    assert before["observations"] > 0
    assert before["tier"] != "population", "half a day of good signal should personalise"

    resumed = AdaptiveWearableModel("restart", path=path)
    after = resumed.status()

    assert after["tier"] == before["tier"]
    assert after["observations"] == before["observations"]
    assert after["model_version"] == before["model_version"]
    assert after["worn_hours"] == pytest.approx(before["worn_hours"], abs=0.01)
