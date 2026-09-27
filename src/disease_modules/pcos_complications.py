"""PCOS / PMOS complication-context engine.

This is a research-surveillance view, not a diagnostic engine. Wearable signals
are used only as longitudinal context. Clinical conditions that require
laboratory, clinical, or validated questionnaire assessment remain explicitly
marked as needing clinical data.
"""
from __future__ import annotations

from typing import Any


class PCOSComplicationContextEngine:
    VERSION = "9.0-research-context"

    def _item(self, domain: str, status: str, finding: str, data_needed: str,
              source: str = "CLINICAL DATA") -> dict[str, str]:
        return {
            "domain": domain,
            "status": status,
            "finding": finding,
            "data_needed": data_needed,
            "source": source,
        }

    def evaluate(self, clinical: dict[str, Any] | None, feature: Any | None,
                 history: list[Any] | None = None) -> list[dict[str, str]]:
        c = clinical or {}
        f = feature
        out: list[dict[str, str]] = []

        glucose = c.get("glucose_mg_dl")
        bmi = c.get("bmi")
        if glucose is not None:
            out.append(self._item(
                "Glycemic / metabolic", "MEASURED CONTEXT",
                f"Entered glucose: {float(glucose):.1f} mg/dL.",
                "Clinician-directed glycemic assessment such as fasting glucose, HbA1c and/or OGTT.",
                "USER / CLINICAL",
            ))
        else:
            out.append(self._item(
                "Glycemic / metabolic", "CLINICAL DATA NEEDED",
                "No glucose value is available in the workstation context.",
                "Clinician-directed glycemic assessment.",
            ))
        if bmi is not None:
            out.append(self._item(
                "Weight / metabolic context", "MEASURED CONTEXT",
                f"Entered BMI: {float(bmi):.1f}.",
                "Clinical interpretation should consider age, growth, body composition and overall context.",
                "USER / CLINICAL",
            ))
        else:
            out.append(self._item(
                "Weight / metabolic context", "CLINICAL DATA NEEDED",
                "BMI has not been entered.",
                "Height and weight with age-appropriate clinical interpretation.",
            ))

        sys_bp = c.get("systolic_bp")
        dia_bp = c.get("diastolic_bp")
        if sys_bp is not None or dia_bp is not None:
            out.append(self._item(
                "Cardiovascular / blood pressure", "MEASURED CONTEXT",
                f"Entered BP: {sys_bp if sys_bp is not None else '—'}/{dia_bp if dia_bp is not None else '—'} mmHg.",
                "Repeat standardized BP assessment and clinician interpretation.",
                "USER / CLINICAL",
            ))
        else:
            out.append(self._item(
                "Cardiovascular / blood pressure", "CLINICAL DATA NEEDED",
                "No blood-pressure measurement is available.",
                "Standardized BP assessment.",
            ))

        out.append(self._item(
            "Lipids", "CLINICAL DATA NEEDED",
            "Wearable signals do not measure lipid concentrations.",
            "Lipid profile when clinically indicated.",
        ))

        cycle = c.get("cycle_irregular")
        days = c.get("days_since_last_period")
        if cycle is not None or days is not None:
            parts = []
            if cycle is not None:
                parts.append("irregular" if cycle else "reported regular")
            if days is not None:
                parts.append(f"{int(days)} days since last reported period")
            out.append(self._item(
                "Endometrial / cycle context", "PATIENT-REPORTED CONTEXT",
                "; ".join(parts) + ".",
                "Longitudinal cycle history and clinician assessment; persistent prolonged amenorrhea requires appropriate evaluation.",
                "PATIENT-REPORTED",
            ))
        else:
            out.append(self._item(
                "Endometrial / cycle context", "CLINICAL DATA NEEDED",
                "Cycle history is incomplete.",
                "Longitudinal menstrual history and clinician assessment.",
            ))

        stress = getattr(f, "stress_index", None) if f is not None else None
        sleep = getattr(f, "sleep_probability", None) if f is not None else None
        activity = getattr(f, "activity_level", None) if f is not None else None
        if stress is not None or sleep is not None or activity is not None:
            vals = []
            if stress is not None:
                vals.append(f"stress-context {float(stress):.0f}/100")
            if sleep is not None:
                vals.append(f"sleep-state estimate {float(sleep):.0f}%")
            if activity is not None:
                vals.append(f"activity {float(activity):.0f}/100")
            out.append(self._item(
                "Sleep / autonomic context", "RESEARCH PHYSIOLOGY",
                ", ".join(vals) + ". These are contextual signals, not complication diagnoses.",
                "Validated sleep assessment and clinical review when symptoms suggest sleep-disordered breathing or other sleep conditions.",
                "WEARABLE + RESEARCH",
            ))
        else:
            out.append(self._item(
                "Sleep / autonomic context", "DATA INSUFFICIENT",
                "No reliable wearable feature window is available.",
                "Clean wearable recording plus clinical review when indicated.",
                "WEARABLE",
            ))

        out.append(self._item(
            "Androgenic / dermatologic", "CLINICAL DATA NEEDED",
            "The wearable cannot directly measure androgen concentrations or diagnose hyperandrogenic complications.",
            "Clinical symptom assessment and, when indicated, biochemical androgen evaluation.",
        ))

        out.append(self._item(
            "Psychological wellbeing", "CLINICAL DATA NEEDED",
            "The workstation may display stress-context physiology, but it does not screen or diagnose psychological conditions.",
            "Validated, age-appropriate screening and clinical assessment when indicated.",
        ))

        return out
