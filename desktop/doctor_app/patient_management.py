"""Doctor PC patient/workspace data services for ENDO-TWIN V8.3+.

These services are deliberately database-backed.  They never invent patient
measurements, model confidence, or longitudinal values when a record is absent.
"""

from __future__ import annotations

import json
import statistics
import time
from pathlib import Path
from typing import Any, Dict, Optional

from database.database import LocalDatabase
from core.chrono_metabolic import ChronoMetabolicFingerprint


class DoctorDashboard:
    def __init__(self, db: LocalDatabase):
        self.db = db

    def get_overview(self, doctor_id: Optional[str] = None) -> Dict[str, Any]:
        patients = self.db.list_patients(doctor_id=doctor_id)
        cur = self.db.conn.cursor()

        if doctor_id:
            cur.execute(
                """SELECT s.*, p.anonymous_id
                   FROM sensor_sessions s
                   JOIN patients p ON p.patient_id=s.patient_id
                   JOIN patient_doctor_access a ON a.patient_id=p.patient_id
                   WHERE a.doctor_id=? AND a.is_active=1
                   ORDER BY s.start_at DESC LIMIT 10""",
                (doctor_id,),
            )
        else:
            cur.execute(
                """SELECT s.*, p.anonymous_id
                   FROM sensor_sessions s
                   JOIN patients p ON p.patient_id=s.patient_id
                   ORDER BY s.start_at DESC LIMIT 10"""
            )
        recent = [dict(r) for r in cur.fetchall()]

        quality = {"good": 0, "moderate": 0, "poor": 0, "unknown": 0}
        for row in recent:
            q = row.get("data_quality")
            if q is None:
                quality["unknown"] += 1
            elif q >= 0.8:
                quality["good"] += 1
            elif q >= 0.5:
                quality["moderate"] += 1
            else:
                quality["poor"] += 1

        pending = [
            r for r in recent
            if r.get("end_at") is None or r.get("data_quality") is None
        ]

        return {
            "total_patients": len(patients),
            "recent_assessments": recent,
            "data_quality_summary": quality,
            "pending_reviews": pending,
            "longitudinal_summary": (
                "No longitudinal data yet" if not patients
                else f"{len(patients)} authorized patients tracked"
            ),
            "provenance": "DATABASE",
            "label": "REAL_DB_QUERY",
        }


class PatientManager:
    def __init__(self, db: LocalDatabase):
        self.db = db

    def create_patient(
        self, anonymous_id: str, age: Optional[float] = None,
        bmi: Optional[float] = None, **kwargs: Any
    ) -> str:
        return self.db.create_patient(
            anonymous_id=anonymous_id,
            age_years=age,
            bmi=bmi,
            **kwargs,
        )

    def search(self, query: str, doctor_id: Optional[str] = None):
        results = self.db.search_patients(query)
        if doctor_id:
            authorized = {
                p["patient_id"]
                for p in self.db.list_patients(doctor_id=doctor_id)
            }
            results = [r for r in results if r["patient_id"] in authorized]
        return results

    def open_patient(
        self, patient_id: str, doctor_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        if doctor_id and not self.db.check_access(patient_id, doctor_id):
            return None
        return self.db.get_patient(patient_id)

    def archive_patient(
        self, patient_id: str, doctor_id: Optional[str] = None
    ) -> Dict[str, Any]:
        if doctor_id and not self.db.check_access(patient_id, doctor_id):
            return {
                "archived": False,
                "patient_id": patient_id,
                "error": "UNAUTHORIZED",
            }
        cur = self.db.conn.cursor()
        cur.execute(
            "UPDATE patients SET is_archived=1, updated_at=? WHERE patient_id=?",
            (time.time(), patient_id),
        )
        self.db.conn.commit()
        return {
            "archived": cur.rowcount > 0,
            "patient_id": patient_id,
            "provenance": "DATABASE",
        }

    def get_history(
        self, patient_id: str, doctor_id: Optional[str] = None
    ) -> Dict[str, Any]:
        if doctor_id and not self.db.check_access(patient_id, doctor_id):
            return {"patient": None, "error": "UNAUTHORIZED"}

        cur = self.db.conn.cursor()
        result: Dict[str, Any] = {"patient": self.db.get_patient(patient_id)}

        for key, table in (
            ("sessions", "sensor_sessions"),
            ("symptoms", "symptoms"),
            ("cycles", "cycles"),
            ("reports", "reports"),
        ):
            cur.execute(
                f"SELECT * FROM {table} WHERE patient_id=? ORDER BY 1 DESC",
                (patient_id,),
            )
            result[key] = [dict(r) for r in cur.fetchall()]

        result["notes"] = self.db.get_doctor_notes(patient_id)
        result["provenance"] = "DATABASE"
        return result


class PhysiologicalDataViewer:
    """Read actual time-series tables for one sensor session."""

    def __init__(self, db: LocalDatabase):
        self.db = db

    def get_session_data(self, session_id: str) -> Dict[str, Any]:
        cur = self.db.conn.cursor()
        cur.execute("SELECT * FROM sensor_sessions WHERE session_id=?", (session_id,))
        session = cur.fetchone()
        if not session:
            return {
                "session_id": session_id,
                "found": False,
                "error": "SESSION_NOT_FOUND",
                "provenance": "DATABASE",
            }

        def rows(table: str):
            cur.execute(
                f"SELECT * FROM {table} WHERE session_id=? ORDER BY timestamp_s",
                (session_id,),
            )
            return [dict(r) for r in cur.fetchall()]

        ppg = rows("ppg_data")
        hrv = rows("hrv_data")
        gsr = rows("gsr_data")
        motion = rows("motion_data")
        temp = rows("temperature_data")
        quality = rows("sensor_quality")

        hr_values = [r["hr_bpm"] for r in hrv if r.get("hr_bpm") is not None]
        rmssd = [r["rmssd_ms"] for r in hrv if r.get("rmssd_ms") is not None]
        sdnn = [r["sdnn_ms"] for r in hrv if r.get("sdnn_ms") is not None]
        activity = [r["activity_level"] for r in motion if r.get("activity_level") is not None]
        skin_temp = [r["skin_temp_c"] for r in temp if r.get("skin_temp_c") is not None]

        q_values = [r["quality"] for r in quality if r.get("quality") is not None]
        overall_q = (
            statistics.fmean(q_values) if q_values else session["data_quality"]
        )

        artifact_rows = [r for r in quality if r.get("artifact")]
        return {
            "session_id": session_id,
            "found": True,
            "session": dict(session),
            "ppg": {
                "raw": [r for r in ppg],
                "quality": self._mean(r.get("quality") for r in ppg),
            },
            "hr": {
                "values": hr_values,
                "mean": self._mean(hr_values),
            },
            "hrv": {
                "rmssd": self._mean(rmssd),
                "sdnn": self._mean(sdnn),
                "values": hrv,
            },
            "gsr": {"values": gsr},
            "motion": {
                "values": motion,
                "activity": self._mean(activity),
            },
            "temperature": {
                "values": temp,
                "mean": self._mean(skin_temp),
            },
            "quality": {
                "overall": overall_q,
                "sensor_quality_rows": quality,
            },
            "artifacts": {
                "detected": len(artifact_rows),
                "rows": artifact_rows,
            },
            "provenance": "DATABASE",
        }

    @staticmethod
    def _mean(values):
        values = [v for v in values if v is not None]
        return statistics.fmean(values) if values else None


class AdvancedAnalysisViewer:
    """Run research analysis on actual stored session features when available."""

    def __init__(self, db: LocalDatabase):
        self.db = db
        self.fingerprint_engine = ChronoMetabolicFingerprint()

    def analyze(self, patient_id: str, session_id: Optional[str] = None):
        cur = self.db.conn.cursor()

        if session_id is None:
            cur.execute(
                """SELECT session_id FROM sensor_sessions
                   WHERE patient_id=? ORDER BY start_at DESC LIMIT 1""",
                (patient_id,),
            )
            row = cur.fetchone()
            session_id = row["session_id"] if row else None

        if not session_id:
            return self._empty_analysis(patient_id)

        viewer = PhysiologicalDataViewer(self.db)
        session_data = viewer.get_session_data(session_id)
        if not session_data.get("found"):
            return self._empty_analysis(patient_id, session_id, "SESSION_NOT_FOUND")

        features = {
            "hrv_rmssd": session_data["hrv"].get("rmssd"),
            "activity_level": session_data["motion"].get("activity"),
            "skin_temperature": session_data["temperature"].get("mean"),
        }
        quality = {
            "ppg": session_data["ppg"].get("quality"),
            "motion": self._safe_quality(session_data, "motion"),
            "temperature": self._safe_quality(session_data, "temperature"),
        }
        fingerprint = self.fingerprint_engine.build_from_features(features, quality)

        ai_outputs = []
        # The stored database values are observations/features. Do not fabricate
        # a clinical-model result from them when the clinical 37-feature inputs
        # are absent.
        ai_outputs.append({
            "module": "CHRONO-PCOS clinical model",
            "output": "NOT_RUN",
            "reason": (
                "The real trained clinical model requires its 37 clinical "
                "features; wearable session values alone are not a valid substitute."
            ),
            "provenance": "UNKNOWN",
        })

        return {
            "patient_id": patient_id,
            "session_id": session_id,
            "circadian": {
                "status": "AVAILABLE_ONLY_WHEN_ENGINE_COMPUTES_IT",
                "provenance": "DERIVED_OR_MODEL_INFERRED",
            },
            "autonomic": {
                "status": "AVAILABLE_ONLY_WHEN_ENGINE_COMPUTES_IT",
                "provenance": "DERIVED_OR_MODEL_INFERRED",
            },
            "metabolic": {
                "status": "RESEARCH_ONLY",
                "provenance": "MODEL_INFERRED",
            },
            "fingerprint": fingerprint,
            "multimodal": {
                "fusion_output": "RESEARCH_SIGNAL",
                "confidence": None,
                "quality": self._mean_quality(quality),
                "provenance": "DERIVED_FEATURE",
                "note": "No synthetic confidence is emitted.",
            },
            "ai_outputs": ai_outputs,
            "session_data": session_data,
            "disclaimer": "Research / risk-screening output — not a medical diagnosis",
            "provenance": "DATABASE",
            "label": "REAL_DB_ANALYSIS",
        }

    @staticmethod
    def _safe_quality(session_data, channel):
        rows = session_data.get("quality", {}).get("sensor_quality_rows", [])
        vals = [r["quality"] for r in rows if r.get("channel") == channel and r.get("quality") is not None]
        return statistics.fmean(vals) if vals else None

    @staticmethod
    def _mean_quality(quality):
        vals = [v for v in quality.values() if v is not None]
        return statistics.fmean(vals) if vals else None

    @staticmethod
    def _empty_analysis(patient_id, session_id=None, reason="NO_SESSION"):
        return {
            "patient_id": patient_id,
            "session_id": session_id,
            "fingerprint": {"components": [], "status": reason},
            "circadian": {"status": "UNKNOWN"},
            "autonomic": {"status": "UNKNOWN"},
            "metabolic": {"status": "UNKNOWN"},
            "multimodal": {"fusion_output": "UNKNOWN", "confidence": None},
            "ai_outputs": [{"module": "CHRONO-PCOS clinical model", "output": "NOT_RUN", "reason": reason}],
            "provenance": "UNKNOWN",
            "label": "INSUFFICIENT_DATA",
        }


class UltrasoundViewer:
    def __init__(self, db: LocalDatabase):
        self.db = db

    def load_image(self, path):
        path = Path(path)
        return {
            "path": str(path),
            "loaded": path.exists(),
            "shape": None,
            "quality_check": "PENDING" if path.exists() else "IMAGE_NOT_FOUND",
        }

    def quality_check(self, image):
        return {
            "quality_score": None,
            "checks": ["blur", "exposure", "anatomy visibility"],
            "result": "UNKNOWN_UNLESS_COMPUTED",
            "provenance": "IMAGE-DERIVED",
        }

    def inference(self, image):
        return {
            "result": "INSUFFICIENT_TRAINED_ULTRASOUND_MODEL",
            "confidence": None,
            "disclaimer": (
                "Ultrasound analysis is research-only; no validated clinical "
                "ultrasound classifier is connected to this workstation."
            ),
            "provenance": "UNKNOWN",
        }


class LongitudinalViewer:
    def __init__(self, db: Optional[LocalDatabase] = None):
        self.db = db

    def compare(self, patient_id, session_ids):
        if not self.db:
            return {
                "patient_id": patient_id,
                "sessions": session_ids,
                "trends": "DATABASE_NOT_CONNECTED",
                "baseline_deviation": "UNKNOWN",
            }

        viewer = PhysiologicalDataViewer(self.db)
        series = [
            (sid, viewer.get_session_data(sid))
            for sid in session_ids
        ]
        hr = [d["hr"].get("mean") for _, d in series if d.get("found")]
        rmssd = [d["hrv"].get("rmssd") for _, d in series if d.get("found")]
        activity = [d["motion"].get("activity") for _, d in series if d.get("found")]

        return {
            "patient_id": patient_id,
            "sessions": session_ids,
            "trends": {
                "hr": hr,
                "hrv_rmssd": rmssd,
                "activity": activity,
            },
            "baseline_deviation": "Computed from supplied sessions only; no baseline is fabricated.",
            "provenance": "DATABASE",
        }


class ReportGenerator:
    def __init__(self, db=None):
        self.db = db

    def generate(self, patient_id, analysis, include_disclaimer=True):
        model_rows = []
        if self.db:
            cur = self.db.conn.cursor()
            cur.execute(
                """SELECT * FROM model_results
                   WHERE patient_id=? ORDER BY created_at DESC LIMIT 20""",
                (patient_id,),
            )
            model_rows = [dict(r) for r in cur.fetchall()]

        return {
            "patient_id": patient_id,
            "analysis": analysis,
            "generated_at": time.time(),
            "provenance": "DATABASE",
            "label": "REAL_DB_REPORT",
            "disclaimer": (
                "Research / risk-screening output — not a medical diagnosis."
                if include_disclaimer else ""
            ),
            "model_results": model_rows,
            "model_transparency": {
                "models_used": [r["module_name"] for r in model_rows] or ["No stored model result"],
                "input_data": (
                    "Database-backed patient/session data only; no synthetic values are inserted."
                ),
                "data_quality": analysis.get("multimodal", {}).get("quality"),
                "confidence": (
                    "Stored model confidence only"
                    if model_rows else "Not available"
                ),
                "features": "Stored measured/derived clinical and wearable features",
                "limitations": (
                    "Clinical validation NOT ESTABLISHED; the wearable pipeline "
                    "is not a diagnostic substitute."
                ),
            },
        }
