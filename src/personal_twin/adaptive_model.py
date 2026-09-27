"""Local adaptive personal-twin model.

This is a personalization engine, not a disease classifier. It learns the user's
own recurring physiological range using quality-weighted exponential updates,
robust running variance and hour-of-day context. It can improve individualized
comparison over time without silently retraining the CHRONO-PCOS disease model.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
import time
from typing import Any

import numpy as np

from src.personal_twin.profile_store import load_state, upsert_state, append_event


METRICS = ("hr_bpm", "rmssd_ms", "skin_temp_c", "gsr_tonic", "activity_level", "stress_index", "sleep_probability")


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
    def __init__(self, participant_id: str | None = None, alpha: float = 0.05):
        self.participant_id = participant_id or "LOCAL"
        self.alpha = float(alpha)
        self.state = load_state()
        learning = self.state.setdefault("learning", {})
        learning.setdefault("metrics", {})
        learning.setdefault("hourly_profiles", {})
        learning.setdefault("samples", 0)
        learning.setdefault("quality_weighted_samples", 0.0)
        self._restore()

    def _restore(self) -> None:
        raw = self.state["learning"].get("metrics", {})
        self.metrics: dict[str, MetricState] = {}
        for name in METRICS:
            item = raw.get(name, {})
            self.metrics[name] = MetricState(
                count=float(item.get("count", 0.0)),
                mean=float(item.get("mean", 0.0)),
                m2=float(item.get("m2", 0.0)),
                last=item.get("last"),
            )

    def _persist(self) -> None:
        self.state["learning"]["metrics"] = {
            name: {
                "count": s.count,
                "mean": s.mean,
                "m2": s.m2,
                "last": s.last,
            }
            for name, s in self.metrics.items()
        }
        self.state["learning"]["updated_at"] = time.time()
        self.state["learning"]["version"] = "adaptive-personal-twin-v1"
        upsert_state(self.state)

    def observe(self, feature: Any, quality: float | None = None) -> None:
        q = float(max(0.0, min(1.0, quality if quality is not None else getattr(feature, "signal_quality", 0.0))))
        if q < 0.25:
            return
        ts = float(getattr(feature, "timestamp_s", time.time()))
        hour = int(time.localtime(ts).tm_hour)
        hour_key = str(hour)
        hp = self.state["learning"].setdefault("hourly_profiles", {})
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

        hour_state["samples"] = float(hour_state.get("samples", 0.0)) + q
        self.state["learning"]["samples"] = int(self.state["learning"].get("samples", 0)) + 1
        self.state["learning"]["quality_weighted_samples"] = float(
            self.state["learning"].get("quality_weighted_samples", 0.0)
        ) + q

        # Persist frequently enough that another workstation can open the state
        # while this process is running.
        if self.state["learning"]["samples"] % 10 == 0:
            self._persist()
        append_event({
            "kind": "feature_observation",
            "participant_id": self.participant_id,
            "quality": q,
            "metrics": {
                k: getattr(feature, k, None) for k in METRICS
            },
        })

    def baseline(self, name: str) -> dict[str, float] | None:
        s = self.metrics.get(name)
        if s is None or s.count < 3:
            return None
        return {"mean": float(s.mean), "std": float(s.std), "samples": float(s.count)}

    def deviation(self, name: str, value: float | None) -> float | None:
        if value is None:
            return None
        b = self.baseline(name)
        if not b:
            return None
        return float((float(value) - b["mean"]) / max(b["std"], 1e-3))

    def snapshot(self) -> dict[str, Any]:
        return {
            "version": self.state["learning"].get("version", "adaptive-personal-twin-v1"),
            "samples": int(self.state["learning"].get("samples", 0)),
            "quality_weighted_samples": round(float(self.state["learning"].get("quality_weighted_samples", 0.0)), 2),
            "metrics": {
                name: {
                    "mean": round(s.mean, 4),
                    "std": round(s.std, 4),
                    "samples": round(s.count, 2),
                    "last": s.last,
                }
                for name, s in self.metrics.items() if s.count > 0
            },
        }

    def sync_from_disk(self) -> None:
        self.state = load_state()
        self._restore()
