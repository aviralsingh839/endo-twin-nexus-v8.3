"""Personalization and self-learning orchestration for ENDO-TWIN.

Automatic adaptation means learning an individual's baseline and drift from
valid patient data. Disease-model weight updates are a separate, explicitly
gated research operation and are never silently promoted into production.
"""
from __future__ import annotations

import json
import math
import statistics
from dataclasses import dataclass
from typing import Any, Iterable


CORE_FIELDS = (
    "hr_bpm",
    "rmssd_ms",
    "skin_temp_c",
    "activity_level",
    "gsr_tonic",
    "stress_index",
    "sleep_probability",
    "circadian_disruption",
)


@dataclass
class PersonalizationResult:
    patient_id: str
    observations: int
    features_updated: int
    status: str
    notes: list[str]


class SelfLearningEngine:
    """Builds an adaptive personal layer without rewriting disease models."""

    def __init__(self, algorithm_version: str = "personal-twin-0.1.0"):
        self.algorithm_version = algorithm_version

    @staticmethod
    def _finite(values: Iterable[Any]) -> list[float]:
        out = []
        for value in values:
            try:
                x = float(value)
                if math.isfinite(x):
                    out.append(x)
            except (TypeError, ValueError):
                continue
        return out

    def personalize(self, db, patient_id: str, limit: int = 5000) -> PersonalizationResult:
        rows = db.list_feature_vectors(patient_id, limit=limit)
        if not rows:
            return PersonalizationResult(patient_id, 0, 0, "INSUFFICIENT_DATA", ["No stored feature vectors."])

        parsed = []
        for row in rows:
            try:
                parsed.append(json.loads(row["data_json"]))
            except (TypeError, ValueError, json.JSONDecodeError):
                continue

        updated = 0
        for field in CORE_FIELDS:
            values = self._finite(item.get(field) for item in parsed)
            if len(values) < 3:
                continue
            median = statistics.median(values)
            mean = statistics.fmean(values)
            std = statistics.pstdev(values) if len(values) > 1 else 0.0
            deviations = [abs(v - median) for v in values]
            mad = statistics.median(deviations)
            confidence = min(1.0, len(values) / 100.0)
            db.save_personal_baseline(
                patient_id,
                field,
                {
                    "median": median,
                    "mean": mean,
                    "std": std,
                    "mad": mad,
                    "sample_count": len(values),
                    "days_covered": self._days_covered(parsed),
                    "confidence": confidence,
                },
                self.algorithm_version,
            )
            updated += 1

        status = "ADAPTED" if updated else "INSUFFICIENT_DATA"
        db.record_learning_run(
            patient_id,
            model_name="ENDO-TWIN Personal Twin",
            base_model_version=None,
            mode="PERSONALIZATION",
            status=status,
            input_sessions=sorted({str(r.get("session_id")) for r in rows if r.get("session_id")}),
            metrics={"observations": len(parsed), "features_updated": updated},
            limitations=(
                "Automatic adaptation updates the individual's baseline layer. "
                "It does not retrain or clinically validate a disease classifier."
            ),
        )
        return PersonalizationResult(
            patient_id,
            len(parsed),
            updated,
            status,
            [
                "Personal baseline updated from stored valid observations.",
                "Disease-model weights are unchanged.",
                "Two-day data can personalize the research twin but cannot establish clinical validity.",
            ],
        )

    @staticmethod
    def _days_covered(parsed: list[dict]) -> float:
        timestamps = []
        for item in parsed:
            try:
                ts = float(item.get("timestamp_s"))
                if math.isfinite(ts):
                    timestamps.append(ts)
            except (TypeError, ValueError):
                continue
        if len(timestamps) < 2:
            return 0.0
        return max(0.0, (max(timestamps) - min(timestamps)) / 86400.0)

    def candidate_training_gate(self, db, target: str = "pcos_reference") -> dict:
        labels = db.list_research_labels(target)
        patient_ids = {row["patient_id"] for row in labels}
        non_demo = [
            row for row in labels
            if str(row.get("label_value", "")).strip()
            and str(row.get("source", "")).upper() not in {"DEMO", "DEMO_DATA", "SYNTHETIC"}
        ]
        return {
            "status": "READY_FOR_CANDIDATE_TRAINING" if len({r["patient_id"] for r in non_demo}) >= 5 else "INSUFFICIENT_COHORT",
            "target": target,
            "label_rows": len(non_demo),
            "distinct_participants": len({r["patient_id"] for r in non_demo}),
            "engineering_gate": 5,
            "note": "Engineering gate only; not a clinical validation threshold. Candidate models require participant-level split, leakage checks and independent validation before use.",
        }
