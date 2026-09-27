"""Complication-related research signals for ENDO-TWIN.

These are NOT calibrated clinical probabilities. The module intentionally
returns "not established" when evidence is insufficient. When enough inputs
exist, the score is a transparent 0-100 RESEARCH SIGNAL for explanation/UI,
not a prediction of an individual's chance of disease.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass
class ComplicationSignal:
    name: str
    signal_percent: float | None
    confidence: float
    status: str
    drivers: list[str]
    limitation: str

    def display_percent(self) -> str:
        return "Not established" if self.signal_percent is None else f"{self.signal_percent:.0f}%"

def _clamp(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, float(v)))

def _clinical(clinical: dict[str, Any], key: str) -> Any:
    if key in clinical:
        return clinical[key]
    profile = clinical.get("profile")
    return getattr(profile, key, None) if profile is not None else None

def _quality(shared: Any) -> float:
    return _clamp(float(getattr(shared, "overall_quality", 0.0)) * 100.0)

def compute_complication_signals(shared: Any, clinical: dict[str, Any] | None = None) -> list[ComplicationSignal]:
    clinical = clinical or {}
    q = _quality(shared)
    hr = getattr(shared, "heart_rate", None)
    hrv = getattr(shared, "hrv_rmssd", None)
    activity = float(getattr(shared, "activity_level", 0.0) or 0.0)
    sleep = float(getattr(shared, "sleep_regularity", 0.0) or 0.0)
    circ = float(getattr(shared, "circadian_disruption", 50.0) or 50.0)
    bmi = _clinical(clinical, "bmi")
    sbp = _clinical(clinical, "systolic_bp")
    glucose = _clinical(clinical, "glucose_mg_dl")
    cycle = _clinical(clinical, "cycle_regularity")
    enough = q >= 40.0

    def make(name, score, drivers, factor=0.75):
        if score is None or not enough:
            return ComplicationSignal(name, None, round(q / 100.0, 2),
                                      "NOT ESTABLISHED",
                                      drivers if enough else ["Insufficient sensor/data quality"],
                                      "Research signal only; no calibrated individual probability is established.")
        return ComplicationSignal(name, _clamp(score),
                                   round(min(0.95, max(0.20, q / 100.0 * factor)), 2),
                                   "RESEARCH SIGNAL", drivers,
                                   "Not a clinical probability; requires validated clinical assessment.")

    metabolic = 15.0
    drivers = []
    if bmi is not None:
        if bmi >= 30: metabolic += 30; drivers.append("BMI input ≥30")
        elif bmi >= 25: metabolic += 15; drivers.append("BMI input ≥25")
    if glucose is not None:
        if glucose >= 126: metabolic += 30; drivers.append("Entered glucose ≥126 mg/dL")
        elif glucose >= 100: metabolic += 15; drivers.append("Entered glucose ≥100 mg/dL")
    if activity < 25: metabolic += 10; drivers.append("Lower activity signal")
    if sleep < 60: metabolic += 8; drivers.append("Lower sleep-regularity signal")
    if not drivers: drivers.append("No strong supported driver in current inputs")

    bp_score = None
    bp_drivers = []
    if sbp is not None:
        bp_score = 15.0
        if sbp >= 140: bp_score += 45; bp_drivers.append("Entered systolic BP ≥140 mmHg")
        elif sbp >= 130: bp_score += 25; bp_drivers.append("Entered systolic BP ≥130 mmHg")
        else: bp_drivers.append("Entered systolic BP below 130 mmHg")
        if bmi is not None and bmi >= 25: bp_score += 10; bp_drivers.append("BMI input ≥25")

    sleep_score = 15.0
    sleep_drivers = []
    if sleep < 50: sleep_score += 30; sleep_drivers.append("Low sleep-regularity signal")
    elif sleep < 70: sleep_score += 15; sleep_drivers.append("Moderately reduced sleep regularity")
    if activity < 25: sleep_score += 10; sleep_drivers.append("Lower activity signal")
    if circ > 60: sleep_score += 15; sleep_drivers.append("Elevated circadian-disruption signal")
    if not sleep_drivers: sleep_drivers.append("No strong supported driver in current inputs")

    ov_score = 20.0
    ov_drivers = []
    if cycle is not None:
        try:
            c = float(cycle)
            if c >= 60:
                ov_score += 25
                ov_drivers.append("Marked cycle irregularity input")
            else:
                ov_score += 10
                ov_drivers.append("Cycle information available")
        except (TypeError, ValueError):
            pass
    if hrv is not None and hr is not None and hrv < 25 and hr > 85:
        ov_score += 8
        ov_drivers.append("Autonomic deviation signal")
    if not ov_drivers: ov_drivers.append("Cycle/clinical evidence not sufficient")

    return [
        make("Insulin-resistance / type-2-diabetes-related domain", metabolic, drivers),
        make("Hypertension-related domain", bp_score, bp_drivers, 0.80),
        make("Sleep-disordered-breathing domain", sleep_score, sleep_drivers, 0.65),
        make("Ovulatory / fertility-related domain", ov_score, ov_drivers, 0.60),
        make("Metabolic-liver (NAFLD/MASLD-related) domain", metabolic * 0.90, drivers + ["Metabolic-domain proxy"], 0.60),
    ]
