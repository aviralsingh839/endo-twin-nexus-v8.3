"""Patient-scoped local adaptive Personal Twin."""
from __future__ import annotations

from dataclasses import dataclass
import math
import time
from types import SimpleNamespace
from typing import Any

from src.personal_twin.profile_store import (
    append_event,
    ensure_person,
    get_learning,
    load_state,
    replace_learning,
    upsert_state,
)

METRICS = (
    "hr_bpm", "rmssd_ms", "skin_temp_c", "room_temp_c", "gsr_tonic",
    "activity_level", "stress_index", "sleep_probability",
)


@dataclass
class MetricState:
    count: float = 0.0
    mean: float = 0.0
    m2: float = 0.0
    last: float | None = None

    @property
    def variance(self) -> float:
        return self.m2 / max(self.count, 1.0)

    @property
    def std(self) -> float:
        return max(math.sqrt(max(self.variance, 0.0)), 1e-3)


class PersonalAdaptiveModel:
    """Quality-gated personalization; deliberately not a disease classifier."""

    def __init__(self, participant_id: str | None = None, alpha: float = 0.05):
        state = load_state()
        self.participant_id = str(participant_id or state.get("active_participant_id") or "LOCAL")
        self.alpha = float(alpha)
        ensure_person(self.participant_id, make_active=False)
        self.state = load_state()
        learning = self.state["people"][self.participant_id]["learning"]
        learning.setdefault("metrics", {})
        learning.setdefault("hourly_profiles", {})
        learning.setdefault("samples", 0)
        learning.setdefault("quality_weighted_samples", 0.0)
        self._restore()

    def _restore(self) -> None:
        learning = self.state["people"][self.participant_id]["learning"]
        raw = learning.get("metrics", {})
        self.metrics = {}
        for name in METRICS:
            item = raw.get(name, {})
            self.metrics[name] = MetricState(
                count=float(item.get("count", 0.0)),
                mean=float(item.get("mean", 0.0)),
                m2=float(item.get("m2", 0.0)),
                last=item.get("last"),
            )

    @property
    def learning(self) -> dict[str, Any]:
        return self.state["people"][self.participant_id]["learning"]

    def _persist(self) -> None:
        learning = self.learning
        learning["metrics"] = {
            name: {"count": s.count, "mean": s.mean, "m2": s.m2, "last": s.last}
            for name, s in self.metrics.items()
        }
        learning["updated_at"] = time.time()
        learning["quality_sum"] = float(learning.get("quality_sum", 0.0))
        learning["first_observation_ts"] = learning.get("first_observation_ts")
        learning["last_observation_ts"] = learning.get("last_observation_ts")
        learning["version"] = "adaptive-personal-twin-v1"
        replace_learning(self.participant_id, learning)
        self.state = load_state()

    def set_participant(self, participant_id: str) -> None:
        self.participant_id = str(participant_id)
        ensure_person(self.participant_id, make_active=False)
        self.state = load_state()
        self._restore()

    def observe(self, feature: Any, quality: float | None = None) -> None:
        q = float(max(0.0, min(1.0, quality if quality is not None else getattr(feature, "signal_quality", 0.0))))
        if q < 0.25:
            return
        if self.participant_id not in self.state.get("people", {}):
            ensure_person(self.participant_id, make_active=False)
            self.state = load_state()
            self._restore()

        ts = float(getattr(feature, "timestamp_s", time.time()))
        if learning.get("first_observation_ts") is None:
            learning["first_observation_ts"] = ts
        learning["last_observation_ts"] = ts
        hour_key = str(int(time.localtime(ts).tm_hour))
        learning = self.learning
        hp = learning.setdefault("hourly_profiles", {})
        hour_state = hp.setdefault(hour_key, {"samples": 0, "metrics": {}})

        for name in METRICS:
            value = getattr(feature, name, None)
            try:
                value = float(value)
            except (TypeError, ValueError):
                continue
            if not math.isfinite(value):
                continue
            s = self.metrics[name]
            weight = max(q, 0.25)
            prev_mean = s.mean
            s.count += weight
            if s.count <= weight:
                s.mean = value
                s.m2 = 0.0
            else:
                delta = value - prev_mean
                s.mean += (weight / s.count) * delta
                s.m2 += weight * delta * (value - s.mean)
            s.last = value

            hm = hour_state["metrics"].setdefault(name, {"mean": value, "count": 0.0})
            hcount = float(hm.get("count", 0.0))
            hmean = float(hm.get("mean", value))
            hnew = hcount + weight
            hm["mean"] = hmean + (weight / hnew) * (value - hmean)
            hm["count"] = hnew

        learning["samples"] = int(learning.get("samples", 0)) + 1
        learning["quality_weighted_samples"] = float(learning.get("quality_weighted_samples", 0.0)) + q
        learning["quality_sum"] = float(learning.get("quality_sum", 0.0)) + q
        # Persist every observation so Doctor, Patient, Unified and ENDO-TWIN
        # processes see the same patient-scoped learning state without waiting
        # for another polling cycle.
        self._persist()

        append_event({
            "kind": "feature_observation",
            "participant_id": self.participant_id,
            "quality": q,
            "metrics": {k: getattr(feature, k, None) for k in METRICS},
        })

    def reset_learning(self) -> None:
        """Reset only this participant's adaptive learning state."""
        learning = _empty_learning()
        self.state = load_state()
        if self.participant_id not in self.state.get("people", {}):
            ensure_person(self.participant_id, make_active=False)
            self.state = load_state()
        self.state["people"][self.participant_id]["learning"] = learning
        replace_learning(self.participant_id, learning)
        self._restore()
        append_event({"kind": "learning_reset", "participant_id": self.participant_id})

    @property
    def baseline_ready(self) -> bool:
        return int(self.learning.get("samples", 0)) >= 60

    def quality_average(self) -> float:
        return float(self.learning.get("quality_sum", 0.0)) / max(int(self.learning.get("samples", 0)), 1)

    def flush(self) -> None:
        self._persist()

    def baseline(self, name: str) -> dict[str, float] | None:
        s = self.metrics.get(name)
        if s is None or s.count < 3:
            return None
        return {"mean": float(s.mean), "std": float(s.std), "samples": float(s.count)}

    def deviation(self, name: str, value: float | None) -> float | None:
        if value is None:
            return None
        b = self.baseline(name)
        return None if not b else float((float(value) - b["mean"]) / max(b["std"], 1e-3))

    def snapshot(self) -> dict[str, Any]:
        learning = self.learning
        return {
            "participant_id": self.participant_id,
            "version": learning.get("version", "adaptive-personal-twin-v1"),
            "samples": int(learning.get("samples", 0)),
            "quality_weighted_samples": round(float(learning.get("quality_weighted_samples", 0.0)), 2),
            "quality_average": round(float(learning.get("quality_sum", 0.0)) / max(int(learning.get("samples", 0)), 1), 3),
            "baseline_ready": int(learning.get("samples", 0)) >= 60,
            "first_observation_ts": learning.get("first_observation_ts"),
            "last_observation_ts": learning.get("last_observation_ts"),
            "metrics": {
                name: {
                    "mean": round(s.mean, 4),
                    "std": round(s.std, 4),
                    "samples": round(s.count, 2),
                    "last": s.last,
                }
                for name, s in self.metrics.items() if s.count > 0
            },
            "hourly_profiles": learning.get("hourly_profiles", {}),
        }

    def sync_from_disk(self) -> None:
        self.state = load_state()
        if self.participant_id not in self.state.get("people", {}):
            ensure_person(self.participant_id, make_active=False)
            self.state = load_state()
        self._restore()
