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

    def train_candidate(self, db, target: str = "pcos_reference", artifact_path: str | None = None, min_participants: int = 5) -> dict:
        """Train a research candidate model from explicitly labelled participants.

        This is never auto-promoted. Each participant is aggregated before the
        split, preventing repeated samples from the same participant leaking
        across train/validation folds.
        """
        gate = self.candidate_training_gate(db, target)
        if gate["distinct_participants"] < min_participants:
            return {**gate, "status": "INSUFFICIENT_COHORT"}

        try:
            import joblib
            import numpy as np
            from sklearn.linear_model import LogisticRegression
            from sklearn.metrics import accuracy_score, f1_score
            from sklearn.model_selection import StratifiedKFold, cross_val_predict
            from sklearn.pipeline import Pipeline
            from sklearn.preprocessing import StandardScaler
        except ImportError as exc:
            return {
                **gate,
                "status": "DEPENDENCY_UNAVAILABLE",
                "reason": str(exc),
            }

        labels = {}
        for row in db.list_research_labels(target):
            labels.setdefault(row["patient_id"], row["label_value"])

        X = []
        y = []
        participants = []
        for patient_id, label in labels.items():
            rows = db.list_feature_vectors(patient_id, limit=5000)
            parsed = []
            for row in rows:
                try:
                    data = json.loads(row["data_json"])
                    parsed.append(data)
                except (TypeError, ValueError, json.JSONDecodeError):
                    continue
            vector = []
            valid = True
            for field in CORE_FIELDS:
                vals = self._finite(item.get(field) for item in parsed)
                if not vals:
                    valid = False
                    break
                vector.append(statistics.fmean(vals))
            if valid:
                X.append(vector)
                y.append(str(label))
                participants.append(patient_id)

        if len(set(y)) < 2 or len(X) < min_participants:
            return {
                **gate,
                "status": "INSUFFICIENT_TRAINING_DATA",
                "usable_participants": len(X),
                "classes": sorted(set(y)),
            }

        class_counts = {label: y.count(label) for label in set(y)}
        n_splits = min(5, min(class_counts.values()))
        if n_splits < 2:
            return {
                **gate,
                "status": "INSUFFICIENT_CLASS_BALANCE",
                "usable_participants": len(X),
                "classes": class_counts,
            }

        model = Pipeline([
            ("scale", StandardScaler()),
            ("classifier", LogisticRegression(max_iter=2000, random_state=7)),
        ])
        cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=7)
        predictions = cross_val_predict(model, np.asarray(X, dtype=float), y, cv=cv)
        metrics = {
            "accuracy": float(accuracy_score(y, predictions)),
            "f1_weighted": float(f1_score(y, predictions, average="weighted")),
            "participants": len(X),
            "classes": sorted(set(y)),
            "feature_count": len(CORE_FIELDS),
        }

        model.fit(np.asarray(X, dtype=float), y)
        path = artifact_path or str(db.db_path.parent / f"{target}_candidate.joblib")
        joblib.dump({
            "model": model,
            "target": target,
            "feature_names": list(CORE_FIELDS),
            "participants": participants,
            "metrics": metrics,
            "status": "RESEARCH_CANDIDATE",
            "clinical_validation": "NOT ESTABLISHED",
        }, path)

        run_id = db.record_learning_run(
            None,
            model_name=f"{target} research candidate",
            base_model_version=None,
            mode="CANDIDATE_TRAINING",
            status="COMPLETED_CANDIDATE",
            input_sessions=[],
            metrics=metrics,
            limitations=(
                "Research candidate only. Metrics are engineering evaluation on the "
                "labelled cohort and are not clinical validation. Review leakage, "
                "confounding, external validity and independent validation before use."
            ),
        )
        return {
            **gate,
            "status": "CANDIDATE_TRAINED",
            "artifact_path": path,
            "learning_run_id": run_id,
            "metrics": metrics,
            "note": "Candidate model was trained offline and is not automatically promoted into inference.",
        }

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
