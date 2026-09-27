"""Complication prediction for ENDO-TWIN NEXUS (research use only).

A transparent, auditable risk layer that sits on top of whatever the database
actually holds for a participant. Every complication is scored from named
factors with explicit weights; a factor that has no data contributes nothing and
is reported back to the user as *missing input* instead of being guessed.

If too little of a complication's evidence base is available the item is
returned with ``status = "insufficient"`` and no number at all — the platform
never prints a probability it cannot support.

Not a diagnosis. Not validated for clinical use.
"""
from __future__ import annotations

import time
from typing import Any, Callable, Dict, List, Optional

MODEL_NAME = "endotwin_complication_rules"
MODEL_VERSION = "1.1.0"


# --------------------------------------------------------------------------- #
#  helpers
# --------------------------------------------------------------------------- #
def _num(v) -> Optional[float]:
    try:
        if v is None or v == "":
            return None
        f = float(v)
        return None if f != f else f
    except (TypeError, ValueError):
        return None


def _ramp(v: Optional[float], lo: float, hi: float) -> Optional[float]:
    """0 at/below lo, 1 at/above hi (or reversed when lo > hi)."""
    if v is None:
        return None
    if lo == hi:
        return 0.0
    x = (v - lo) / (hi - lo)
    return max(0.0, min(1.0, x))


def _slope(series: List[float]) -> Optional[float]:
    xs = [v for v in (series or []) if isinstance(v, (int, float))]
    if len(xs) < 6:
        return None
    n = len(xs)
    mx = (n - 1) / 2.0
    my = sum(xs) / n
    num = sum((i - mx) * (v - my) for i, v in enumerate(xs))
    den = sum((i - mx) ** 2 for i in range(n)) or 1.0
    return num / den


def _sym(record: Dict[str, Any], *names: str) -> Optional[float]:
    """Max severity (0-5) for any matching logged symptom; None if never logged."""
    got = None
    for s in record.get("symptoms") or []:
        label = str(s.get("name") or "").lower()
        if any(n in label for n in names):
            sev = _num(s.get("severity")) or 0
            got = sev if got is None else max(got, sev)
    return got


def _lab(record: Dict[str, Any], *keys: str) -> Optional[float]:
    for l in record.get("labs") or []:
        k = str(l.get("k") or l.get("name") or "").lower()
        if any(key in k for key in keys):
            v = l.get("value")
            if v is None:
                v = str(l.get("v") or "").split(" ")[0].replace("%", "")
            return _num(v)
    return None


def _bp(record: Dict[str, Any]):
    bp = (record.get("vitals") or {}).get("bp") or record.get("bp")
    if not bp or "/" not in str(bp):
        return None, None
    try:
        s, d = str(bp).split("/")[:2]
        return _num(s), _num(d)
    except Exception:
        return None, None


class Factor:
    """One weighted piece of evidence."""

    def __init__(self, key: str, label: str, weight: float, value: Optional[float],
                 score: Optional[float], detail: str, unit: str = "", need: str = ""):
        self.key, self.label, self.weight = key, label, weight
        self.value, self.score, self.detail, self.unit = value, score, detail, unit
        self.need = need or label

    @property
    def available(self) -> bool:
        return self.score is not None

    def as_dict(self) -> Dict[str, Any]:
        return {"k": self.label, "key": self.key, "v": None if self.score is None else round(self.score * 100),
                "value": self.value, "unit": self.unit, "weight": self.weight,
                "detail": self.detail, "available": self.available}


# --------------------------------------------------------------------------- #
#  feature extraction from the stored record
# --------------------------------------------------------------------------- #
def extract_features(record: Dict[str, Any]) -> Dict[str, Any]:
    v = record.get("vitals") or {}
    t30 = record.get("trend30") or {}
    us = record.get("ultrasound") or {}
    sys_bp, dia_bp = _bp(record)
    height = _num(record.get("height"))
    weight = _num(record.get("weight"))
    bmi = _num(record.get("bmi"))
    if bmi is None and height and weight:
        bmi = weight / ((height / 100.0) ** 2)
    cycle_len = _num(record.get("cycleLen"))
    cycles = record.get("cycleHistory") or []
    cyc_var = None
    lens = [_num(c.get("length")) for c in cycles if _num(c.get("length"))]
    if len(lens) >= 3:
        mean = sum(lens) / len(lens)
        cyc_var = (sum((x - mean) ** 2 for x in lens) / len(lens)) ** 0.5
    return {
        "age": _num(record.get("age")),
        "bmi": bmi,
        "waist": _num(record.get("waist")),
        "hr": _num(v.get("hr")),
        "hrv": _num(v.get("hrv")),
        "temp": _num(v.get("temp")),
        "gsr": _num(v.get("gsr")),
        "spo2": _num(v.get("spo2")),
        "steps": _num(v.get("steps")),
        "sleep": _num(v.get("sleep")),
        "resp": _num(v.get("resp")),
        "sys_bp": sys_bp, "dia_bp": dia_bp,
        "cycle_len": cycle_len,
        "cycle_var": cyc_var,
        "hrv_trend": _slope(t30.get("hrv") or []),
        "weight_trend": _slope(t30.get("weight") or []),
        "risk_trend": _slope(t30.get("risk") or []),
        "follicles": _num(us.get("follicles")),
        "ovary_volume": _num(us.get("volume")),
        "glucose": _lab(record, "glucose"),
        "hba1c": _lab(record, "hba1c", "a1c"),
        "lh_fsh": _lab(record, "lh / fsh", "lh/fsh", "lh / fsh ratio"),
        "testosterone": _lab(record, "testosterone"),
        "tsh": _lab(record, "tsh"),
        "hdl": _lab(record, "hdl"),
        "ldl": _lab(record, "ldl"),
        "triglycerides": _lab(record, "triglyceride"),
        "alt": _lab(record, "alt", "sgpt"),
        "vitd": _lab(record, "vitamin d"),
        "sym_fatigue": _sym(record, "fatigue", "tired"),
        "sym_acne": _sym(record, "acne"),
        "sym_hair": _sym(record, "hirsut", "hair"),
        "sym_pain": _sym(record, "pain", "cramp"),
        "sym_mood": _sym(record, "mood", "anxiet", "depress", "irritab"),
        "sym_sleep": _sym(record, "insomnia", "sleep", "snor"),
        "sym_thirst": _sym(record, "thirst", "urinat"),
        "sym_bleed": _sym(record, "heavy", "bleed", "spotting"),
        "family_diabetes": record.get("familyDiabetes"),
        "family_pcos": record.get("familyPcos"),
        "family_cvd": record.get("familyCvd"),
        "smoker": record.get("smoker"),
        "quality": _num(record.get("quality")),
        "signals": bool(record.get("hasSignals")),
        "sessions": _num(record.get("sessionCount")) or 0,
    }


def _flag(v) -> Optional[float]:
    if v is None or v == "":
        return None
    if isinstance(v, str):
        return 1.0 if v.strip().lower() in ("yes", "true", "1", "y") else 0.0
    return 1.0 if v else 0.0


# --------------------------------------------------------------------------- #
#  complication definitions
# --------------------------------------------------------------------------- #
def _defs(f: Dict[str, Any]) -> List[Dict[str, Any]]:
    age, bmi = f["age"], f["bmi"]

    def F(key, label, weight, value, score, detail, unit="", need=""):
        return Factor(key, label, weight, value, score, detail, unit, need)

    ir_factors = [
        F("bmi", "Body-mass index", 2.2, bmi, _ramp(bmi, 23, 35), "Adiposity is the strongest modifiable driver of insulin resistance.", "kg/m²", "Height and weight"),
        F("hba1c", "HbA1c", 2.6, f["hba1c"], _ramp(f["hba1c"], 5.2, 6.5), "Glycation over ~3 months.", "%", "HbA1c lab value"),
        F("glucose", "Fasting glucose", 2.0, f["glucose"], _ramp(f["glucose"], 90, 126), "Fasting hyperglycaemia.", "mg/dL", "Fasting glucose lab value"),
        F("hrv", "Resting HRV (RMSSD)", 1.4, f["hrv"], _ramp(f["hrv"], 55, 20), "Low vagal tone tracks metabolic strain.", "ms", "Wearable HRV recording"),
        F("steps", "Daily activity", 1.2, f["steps"], _ramp(f["steps"], 8000, 2500), "Sedentary behaviour reduces glucose disposal.", "steps", "Activity from the wearable"),
        F("cycle", "Cycle irregularity", 1.1, f["cycle_len"], _ramp(f["cycle_len"], 30, 60), "Anovulation and insulin resistance co-travel in PCOS.", "days", "Cycle length"),
        F("acanthosis", "Skin / hair androgen signs", 0.7, f["sym_hair"], _ramp(f["sym_hair"], 1, 5), "Clinical hyperandrogenism.", "severity", "Symptom log"),
        F("family", "Family history of diabetes", 1.0, _flag(f["family_diabetes"]), _flag(f["family_diabetes"]), "First-degree family history.", "", "Family history in the clinical profile"),
    ]

    t2d_factors = ir_factors + [
        F("age", "Age", 0.9, age, _ramp(age, 25, 55), "Incidence rises with age.", "years", "Age"),
        F("weight_trend", "30-day weight trend", 0.8, f["weight_trend"], _ramp(f["weight_trend"], 0.0, 0.08), "Weight gain accelerates progression.", "kg/day", "Weight logged over time"),
    ]

    mets_factors = [
        F("bmi", "Body-mass index", 2.0, bmi, _ramp(bmi, 23, 35), "Central adiposity.", "kg/m²", "Height and weight"),
        F("waist", "Waist circumference", 1.4, f["waist"], _ramp(f["waist"], 80, 100), "Asian-Indian cut-off is 80 cm for women.", "cm", "Waist measurement"),
        F("sbp", "Systolic blood pressure", 1.6, f["sys_bp"], _ramp(f["sys_bp"], 120, 145), "Elevated BP is a syndrome criterion.", "mmHg", "Blood pressure"),
        F("tg", "Triglycerides", 1.6, f["triglycerides"], _ramp(f["triglycerides"], 120, 200), "Criterion ≥150 mg/dL.", "mg/dL", "Lipid panel"),
        F("hdl", "HDL cholesterol", 1.4, f["hdl"], _ramp(f["hdl"], 55, 35), "Criterion <50 mg/dL in women.", "mg/dL", "Lipid panel"),
        F("glucose", "Fasting glucose", 1.6, f["glucose"], _ramp(f["glucose"], 95, 126), "Criterion ≥100 mg/dL.", "mg/dL", "Fasting glucose lab value"),
        F("hrv", "Autonomic tone (HRV)", 0.8, f["hrv"], _ramp(f["hrv"], 55, 20), "Supportive, not a criterion.", "ms", "Wearable HRV recording"),
    ]

    cv_factors = [
        F("sbp", "Systolic blood pressure", 2.4, f["sys_bp"], _ramp(f["sys_bp"], 118, 150), "Chronic pressure load.", "mmHg", "Blood pressure"),
        F("dbp", "Diastolic blood pressure", 1.2, f["dia_bp"], _ramp(f["dia_bp"], 76, 95), "Chronic pressure load.", "mmHg", "Blood pressure"),
        F("hr", "Resting heart rate", 1.4, f["hr"], _ramp(f["hr"], 65, 95), "Elevated resting HR predicts events.", "bpm", "Wearable heart-rate recording"),
        F("hrv", "Resting HRV (RMSSD)", 1.6, f["hrv"], _ramp(f["hrv"], 55, 18), "Reduced vagal tone.", "ms", "Wearable HRV recording"),
        F("bmi", "Body-mass index", 1.2, bmi, _ramp(bmi, 23, 35), "Adiposity.", "kg/m²", "Height and weight"),
        F("gsr", "Sustained sympathetic arousal", 0.9, f["gsr"], _ramp(f["gsr"], 0.25, 0.6), "Electrodermal tone as a stress proxy.", "µS", "GSR recording"),
        F("sleep", "Sleep duration", 0.9, f["sleep"], _ramp(f["sleep"], 7.5, 5.0), "Short sleep raises pressure load.", "h", "Sleep logging"),
        F("smoker", "Smoking", 1.3, _flag(f["smoker"]), _flag(f["smoker"]), "Major independent risk factor.", "", "Smoking status in the clinical profile"),
        F("family", "Family history of CVD", 0.8, _flag(f["family_cvd"]), _flag(f["family_cvd"]), "First-degree family history.", "", "Family history in the clinical profile"),
        F("age", "Age", 0.9, age, _ramp(age, 30, 60), "Risk rises with age.", "years", "Age"),
    ]

    dys_factors = [
        F("ldl", "LDL cholesterol", 2.4, f["ldl"], _ramp(f["ldl"], 100, 160), "Atherogenic particle load.", "mg/dL", "Lipid panel"),
        F("hdl", "HDL cholesterol", 1.8, f["hdl"], _ramp(f["hdl"], 55, 35), "Protective fraction.", "mg/dL", "Lipid panel"),
        F("tg", "Triglycerides", 2.0, f["triglycerides"], _ramp(f["triglycerides"], 120, 220), "Insulin-resistant pattern.", "mg/dL", "Lipid panel"),
        F("bmi", "Body-mass index", 1.0, bmi, _ramp(bmi, 23, 33), "Adiposity.", "kg/m²", "Height and weight"),
    ]

    fert_factors = [
        F("cycle", "Cycle length", 2.6, f["cycle_len"], _ramp(f["cycle_len"], 32, 70), "Oligomenorrhoea implies anovulatory cycles.", "days", "Cycle length"),
        F("cycle_var", "Cycle variability", 1.6, f["cycle_var"], _ramp(f["cycle_var"], 4, 14), "Irregularity across logged cycles.", "days SD", "Three or more logged cycles"),
        F("follicles", "Antral follicle count", 1.8, f["follicles"], _ramp(f["follicles"], 12, 25), "Polycystic morphology (≥20 per ovary).", "count", "Ultrasound study"),
        F("lhfsh", "LH / FSH ratio", 1.4, f["lh_fsh"], _ramp(f["lh_fsh"], 1.5, 3.0), "Gonadotropin imbalance.", "ratio", "LH and FSH lab values"),
        F("testosterone", "Total testosterone", 1.3, f["testosterone"], _ramp(f["testosterone"], 45, 90), "Biochemical hyperandrogenism.", "ng/dL", "Testosterone lab value"),
        F("bmi", "Body-mass index", 1.2, bmi, _ramp(bmi, 24, 35), "Adiposity lowers ovulation rate.", "kg/m²", "Height and weight"),
        F("temp", "Ovulatory temperature shift", 1.0, f["temp"], _ramp(f["temp"], 34.6, 33.4), "A flat biphasic pattern suggests anovulation.", "°C", "Continuous skin-temperature recording"),
        F("age", "Age", 1.0, age, _ramp(age, 30, 42), "Ovarian reserve declines with age.", "years", "Age"),
    ]

    endo_factors = [
        F("cycle", "Cycle length / amenorrhoea", 2.8, f["cycle_len"], _ramp(f["cycle_len"], 35, 90), "Unopposed oestrogen from chronic anovulation.", "days", "Cycle length"),
        F("bmi", "Body-mass index", 1.8, bmi, _ramp(bmi, 26, 38), "Peripheral oestrogen production in adipose tissue.", "kg/m²", "Height and weight"),
        F("bleed", "Abnormal bleeding", 1.6, f["sym_bleed"], _ramp(f["sym_bleed"], 1, 5), "Heavy or intermenstrual bleeding.", "severity", "Symptom log"),
        F("age", "Age", 1.0, age, _ramp(age, 30, 50), "Risk accumulates with exposure years.", "years", "Age"),
        F("ir", "Insulin-resistance signal", 1.2, f["hba1c"], _ramp(f["hba1c"], 5.3, 6.5), "Hyperinsulinaemia is an independent driver.", "%", "HbA1c lab value"),
    ]

    osa_factors = [
        F("bmi", "Body-mass index", 2.4, bmi, _ramp(bmi, 26, 40), "Strongest predictor of obstructive events.", "kg/m²", "Height and weight"),
        F("snoring", "Snoring / witnessed apnoea", 2.0, f["sym_sleep"], _ramp(f["sym_sleep"], 1, 5), "Reported airway symptoms.", "severity", "Symptom log"),
        F("fatigue", "Daytime fatigue", 1.2, f["sym_fatigue"], _ramp(f["sym_fatigue"], 1, 5), "Non-restorative sleep.", "severity", "Symptom log"),
        F("sleep", "Sleep duration", 0.8, f["sleep"], _ramp(f["sleep"], 7.5, 5.0), "Fragmented short sleep.", "h", "Sleep logging"),
        F("hrv", "Nocturnal HRV", 1.2, f["hrv"], _ramp(f["hrv"], 55, 20), "Autonomic disruption from arousals.", "ms", "Overnight wearable recording"),
        F("hr", "Resting heart rate", 0.8, f["hr"], _ramp(f["hr"], 65, 95), "Sympathetic drive.", "bpm", "Wearable heart-rate recording"),
        F("spo2", "Overnight SpO₂", 1.6, f["spo2"], _ramp(f["spo2"], 96, 90), "Desaturation index. Needs a red+IR oximeter — the analog pulse sensor cannot measure it.", "%", "SpO₂ from a red+IR oximeter"),
    ]

    nafld_factors = [
        F("bmi", "Body-mass index", 2.2, bmi, _ramp(bmi, 25, 36), "Hepatic fat tracks adiposity.", "kg/m²", "Height and weight"),
        F("alt", "ALT", 2.0, f["alt"], _ramp(f["alt"], 25, 60), "Hepatocellular enzyme.", "U/L", "Liver function lab value"),
        F("tg", "Triglycerides", 1.4, f["triglycerides"], _ramp(f["triglycerides"], 120, 220), "Lipid overflow.", "mg/dL", "Lipid panel"),
        F("hba1c", "HbA1c", 1.4, f["hba1c"], _ramp(f["hba1c"], 5.3, 6.5), "Insulin resistance.", "%", "HbA1c lab value"),
        F("steps", "Daily activity", 0.8, f["steps"], _ramp(f["steps"], 8000, 2500), "Exercise reduces hepatic fat.", "steps", "Activity from the wearable"),
    ]

    mood_factors = [
        F("mood", "Mood / anxiety symptoms", 2.4, f["sym_mood"], _ramp(f["sym_mood"], 1, 5), "Self-reported burden.", "severity", "Symptom log"),
        F("hrv", "Resting HRV", 1.6, f["hrv"], _ramp(f["hrv"], 55, 20), "Vagal withdrawal accompanies affective load.", "ms", "Wearable HRV recording"),
        F("gsr", "Electrodermal arousal", 1.4, f["gsr"], _ramp(f["gsr"], 0.25, 0.6), "Sustained sympathetic activation.", "µS", "GSR recording"),
        F("sleep", "Sleep duration", 1.2, f["sleep"], _ramp(f["sleep"], 7.5, 5.0), "Sleep loss amplifies symptoms.", "h", "Sleep logging"),
        F("fatigue", "Fatigue", 0.8, f["sym_fatigue"], _ramp(f["sym_fatigue"], 1, 5), "Energy depletion.", "severity", "Symptom log"),
    ]

    cyst_factors = [
        F("size", "Largest follicle / cyst", 2.6, None, None, "Torsion risk rises steeply above ~50 mm.", "mm", "Ultrasound study"),
        F("pain", "Pelvic pain severity", 2.2, f["sym_pain"], _ramp(f["sym_pain"], 1, 5), "Acute pain is the dominant warning sign.", "severity", "Symptom log"),
        F("volume", "Ovarian volume", 1.4, f["ovary_volume"], _ramp(f["ovary_volume"], 10, 20), "Enlarged ovary.", "cm³", "Ultrasound study"),
        F("hr", "Resting heart rate", 0.8, f["hr"], _ramp(f["hr"], 70, 105), "Tachycardia can accompany an acute event.", "bpm", "Wearable heart-rate recording"),
    ]

    gdm_factors = [
        F("bmi", "Pre-conception BMI", 2.2, bmi, _ramp(bmi, 24, 35), "Pre-pregnancy adiposity.", "kg/m²", "Height and weight"),
        F("hba1c", "HbA1c", 2.0, f["hba1c"], _ramp(f["hba1c"], 5.2, 6.2), "Pre-conception glycaemia.", "%", "HbA1c lab value"),
        F("cycle", "Anovulatory pattern", 1.2, f["cycle_len"], _ramp(f["cycle_len"], 32, 60), "PCOS phenotype raises GDM risk 2-3×.", "days", "Cycle length"),
        F("family", "Family history of diabetes", 1.2, _flag(f["family_diabetes"]), _flag(f["family_diabetes"]), "First-degree family history.", "", "Family history in the clinical profile"),
        F("age", "Age", 0.8, age, _ramp(age, 28, 40), "Maternal age.", "years", "Age"),
    ]

    return [
        dict(key="insulin_resistance", name="Insulin resistance", category="Metabolic", horizon="Current state",
             base=0.30, factors=ir_factors, action="Fasting insulin/glucose pair or HOMA-IR; strength training and sleep regularity.",
             basis="Rotterdam/AE-PCOS metabolic literature; HRV–insulin sensitivity associations."),
        dict(key="type2_diabetes", name="Type 2 diabetes", category="Metabolic", horizon="5 years",
             base=0.12, factors=t2d_factors, action="Annual HbA1c; 7% weight reduction halves progression in high-risk cohorts.",
             basis="IDF/ADA risk-factor weighting adapted to continuously monitored features."),
        dict(key="metabolic_syndrome", name="Metabolic syndrome", category="Metabolic", horizon="Current state",
             base=0.22, factors=mets_factors, action="Measure waist, BP and a fasting lipid panel to complete the criteria.",
             basis="IDF harmonised criteria (waist, BP, triglycerides, HDL, glucose)."),
        dict(key="cardiovascular", name="Hypertension / cardiovascular strain", category="Cardiovascular", horizon="10 years",
             base=0.10, factors=cv_factors, action="Home BP series for 7 days; aerobic base training.",
             basis="Resting HR and HRV as continuous predictors alongside classical factors."),
        dict(key="dyslipidaemia", name="Dyslipidaemia", category="Metabolic", horizon="Current state",
             base=0.25, factors=dys_factors, action="Fasting lipid panel.",
             basis="Standard lipid thresholds."),
        dict(key="anovulatory_infertility", name="Anovulatory subfertility", category="Reproductive", horizon="12 months",
             base=0.18, factors=fert_factors, action="Mid-luteal progesterone, or ovulation tracking with temperature plus LH strips.",
             basis="Cycle-length distribution, antral follicle count and androgen markers."),
        dict(key="endometrial_hyperplasia", name="Endometrial hyperplasia", category="Reproductive", horizon="5 years",
             base=0.06, factors=endo_factors, action="Discuss cycle regulation / progestin withdrawal with a gynaecologist; TVS endometrial thickness.",
             basis="Unopposed-oestrogen exposure model driven by anovulation duration and BMI."),
        dict(key="sleep_apnoea", name="Obstructive sleep apnoea", category="Sleep", horizon="Current state",
             base=0.15, factors=osa_factors, action="STOP-BANG questionnaire and, if positive, an overnight oximetry or home sleep test.",
             basis="Anthropometric plus symptom screening; oximetry needs a red+IR sensor."),
        dict(key="nafld", name="Fatty liver disease (NAFLD)", category="Metabolic", horizon="5 years",
             base=0.20, factors=nafld_factors, action="ALT/AST and an abdominal ultrasound if persistently raised.",
             basis="Adiposity + transaminase + insulin-resistance pattern."),
        dict(key="mood_anxiety", name="Mood / anxiety burden", category="Neuro-affective", horizon="Current state",
             base=0.25, factors=mood_factors, action="PHQ-9 / GAD-7 screening; protect sleep window and daylight exposure.",
             basis="Autonomic (HRV, EDA) markers combined with symptom severity."),
        dict(key="ovarian_event", name="Ovarian cyst rupture / torsion", category="Acute", horizon="Acute (30 days)",
             base=0.04, factors=cyst_factors, action="Sudden severe unilateral pain, vomiting or fainting is an emergency — seek urgent care.",
             basis="Cyst diameter and acute pain severity; torsion risk rises above ~50 mm."),
        dict(key="gestational_diabetes", name="Gestational diabetes (if conceiving)", category="Reproductive", horizon="Next pregnancy",
             base=0.14, factors=gdm_factors, action="Pre-conception HbA1c and weight optimisation.",
             basis="Pre-conception metabolic state; PCOS phenotype multiplier."),
    ]


# --------------------------------------------------------------------------- #
#  scoring
# --------------------------------------------------------------------------- #
def _band(p: Optional[float]) -> str:
    if p is None:
        return "unknown"
    if p >= 60:
        return "high"
    if p >= 30:
        return "moderate"
    if p >= 12:
        return "low"
    return "minimal"


def predict(record: Dict[str, Any]) -> Dict[str, Any]:
    f = extract_features(record)
    us = record.get("ultrasound") or {}
    largest = _num(us.get("largest"))
    quality = f["quality"] if f["quality"] is not None else (0.6 if f["signals"] else 0.0)

    items: List[Dict[str, Any]] = []
    for d in _defs(f):
        factors: List[Factor] = d["factors"]
        if d["key"] == "ovarian_event":
            for fac in factors:
                if fac.key == "size":
                    fac.value = largest
                    fac.score = _ramp(largest, 25, 60)

        total_w = sum(x.weight for x in factors)
        avail_w = sum(x.weight for x in factors if x.available)
        coverage = (avail_w / total_w) if total_w else 0.0
        drivers = sorted([x for x in factors if x.available and (x.score or 0) > 0.02],
                         key=lambda x: -(x.score or 0) * x.weight)
        missing = []
        for x in factors:
            if not x.available and x.need and x.need not in missing:
                missing.append(x.need)   # one line per distinct input, not per factor

        if coverage < 0.34 or avail_w == 0:
            items.append({
                "key": d["key"], "name": d["name"], "category": d["category"], "horizon": d["horizon"],
                "status": "insufficient", "probability": None, "band": "unknown", "confidence": 0.0,
                "coverage": round(coverage, 2), "drivers": [x.as_dict() for x in drivers],
                "missing": missing, "action": d["action"], "basis": d["basis"],
                "note": "Not enough recorded evidence to estimate this yet.",
            })
            continue

        weighted = sum((x.score or 0) * x.weight for x in factors if x.available) / avail_w
        prob = 100.0 * min(0.97, d["base"] + (1.0 - d["base"]) * (weighted ** 1.35))
        confidence = round(min(1.0, coverage * (0.55 + 0.45 * min(quality, 1.0))), 2)
        items.append({
            "key": d["key"], "name": d["name"], "category": d["category"], "horizon": d["horizon"],
            "status": "ok", "probability": round(prob, 1), "band": _band(prob),
            "confidence": confidence, "coverage": round(coverage, 2),
            "drivers": [x.as_dict() for x in drivers[:6]],
            "protective": [x.as_dict() for x in factors if x.available and (x.score or 0) <= 0.02][:4],
            "missing": missing, "action": d["action"], "basis": d["basis"],
            "baseRate": round(d["base"] * 100, 1),
        })

    scored = [i for i in items if i["status"] == "ok"]
    composite = None
    if scored:
        ordered = sorted(scored, key=lambda i: -(i["probability"] or 0))
        top = ordered[:5]
        w = sum(i["confidence"] for i in top) or 1.0
        composite = round(sum((i["probability"] or 0) * i["confidence"] for i in top) / w, 1)

    horizon_series = []
    trend = f["risk_trend"]
    if scored and trend is not None:
        for i in sorted(scored, key=lambda x: -(x["probability"] or 0))[:3]:
            base = i["probability"] or 0
            horizon_series.append({
                "name": i["name"],
                "data": [round(max(0.0, min(99.0, base + trend * 30 * m * 0.6)), 1) for m in range(0, 13)],
            })

    inputs = [
        {"k": "Age", "v": f["age"], "unit": "years", "have": f["age"] is not None},
        {"k": "BMI", "v": None if f["bmi"] is None else round(f["bmi"], 1), "unit": "kg/m²", "have": f["bmi"] is not None},
        {"k": "Waist", "v": f["waist"], "unit": "cm", "have": f["waist"] is not None},
        {"k": "Blood pressure", "v": (record.get("vitals") or {}).get("bp"), "unit": "mmHg", "have": f["sys_bp"] is not None},
        {"k": "Resting HR", "v": f["hr"], "unit": "bpm", "have": f["hr"] is not None},
        {"k": "HRV (RMSSD)", "v": f["hrv"], "unit": "ms", "have": f["hrv"] is not None},
        {"k": "Skin temperature", "v": f["temp"], "unit": "°C", "have": f["temp"] is not None},
        {"k": "Electrodermal tone", "v": f["gsr"], "unit": "µS", "have": f["gsr"] is not None},
        {"k": "Sleep", "v": f["sleep"], "unit": "h", "have": f["sleep"] is not None},
        {"k": "Activity", "v": f["steps"], "unit": "steps", "have": f["steps"] is not None},
        {"k": "Cycle length", "v": f["cycle_len"], "unit": "days", "have": f["cycle_len"] is not None},
        {"k": "Antral follicles", "v": f["follicles"], "unit": "count", "have": f["follicles"] is not None},
        {"k": "HbA1c", "v": f["hba1c"], "unit": "%", "have": f["hba1c"] is not None},
        {"k": "Fasting glucose", "v": f["glucose"], "unit": "mg/dL", "have": f["glucose"] is not None},
        {"k": "Lipid panel", "v": f["ldl"], "unit": "mg/dL LDL", "have": f["ldl"] is not None},
        {"k": "SpO₂", "v": f["spo2"], "unit": "%", "have": f["spo2"] is not None},
    ]
    completeness = round(sum(1 for i in inputs if i["have"]) / len(inputs), 2)

    return {
        "patientId": record.get("id"),
        "model": MODEL_NAME, "version": MODEL_VERSION,
        "generatedAt": time.time(),
        "dataCompleteness": completeness,
        "signalQuality": round(quality, 2) if quality is not None else None,
        "hasSignals": bool(f["signals"]),
        "composite": composite,
        "compositeBand": _band(composite),
        "items": sorted(items, key=lambda i: (i["status"] != "ok", -(i["probability"] or 0))),
        "inputs": inputs,
        "projection": {"labels": [f"+{m}m" for m in range(0, 13)], "series": horizon_series},
        "limitations": ("Rule-based research estimates from the participant's own recorded data. "
                        "Not externally validated, not a diagnosis, and no substitute for laboratory "
                        "testing or clinical examination."),
    }
