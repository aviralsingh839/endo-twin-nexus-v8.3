# MULTI-DISEASE MODEL - V8.3

## Philosophy

**Do NOT make one giant black-box model that claims to diagnose everything.**

Use:
```
CORE PHYSIOLOGICAL ENGINE
+
DISEASE-SPECIFIC MODULES
```

**Core learns personal baseline, shared representation feeds disease modules.**

---

## Architecture

```
                SENSOR DATA
                     │
                     ▼
            QUALITY CONTROL
                     │
                     ▼
           SIGNAL PROCESSING
                     │
                     ▼
         FEATURE EXTRACTION
                     │
                     ▼
          PERSONAL BASELINE
                     │
                     ▼
         LONGITUDINAL ENGINE
                     │
                     ▼
      SHARED PHYSIOLOGICAL FEATURES
                     │
      ┌──────────────┼──────────────┐
      │              │              │
      ▼              ▼              ▼
   PCOS/S          SLEEP       CARDIOMETABOLIC
   MODULE          MODULE          MODULE
      │              │              │
      │         AUTONOMIC          │
      │         MODULE             │
      └──────────────┼──────────────┘
                     ▼
             MULTIMODAL FUSION
                     │
                     ▼
             EXPLANATION ENGINE
                     │
                     ▼
          RISK SIGNALS + TRENDS
```

---

## Disease Module API

```python
class DiseaseModule(ABC):
    @property
    def name(self) -> str: ...

    @property
    def version(self) -> str: ...

    @property
    def required_features(self) -> List[str]: ...

    @property
    def optional_features(self) -> List[str]: ...

    def predict(self, shared: SharedPhysiologicalFeatures,
                clinical: Optional[Dict] = None,
                ultrasound: Optional[Dict] = None,
                history: Optional[List] = None) -> DiseaseModuleResult: ...

    def explain(self, result: DiseaseModuleResult) -> str: ...

    def confidence(self, shared: SharedPhysiologicalFeatures,
                   result: Optional[DiseaseModuleResult] = None) -> float: ...

    def limitations(self) -> str: ...
```

**Returns:**

```json
{
  "module": "sleep",
  "signal": "circadian_deviation",
  "level": "moderate",
  "confidence": 0.72,
  "data_quality": 0.85,
  "clinical_status": "research_only",
  "clinical_validation": "NOT ESTABLISHED",
  "drivers": [{"domain": "...", "score": ..., "description": "..."}],
  "explanation": "...",
  "provenance": {"wearable": 0.6, "longitudinal": 0.3},
  "limitations": "Research-only...",
  "extra": {}
}
```

**Never returns "DISEASE DETECTED"**

---

## Implemented Modules

### Module A - PCOS / Reproductive-Metabolic

**Keeps and improves V8.1 pipeline.**

**Inputs:**
- Age, BMI, menstrual-cycle info, clinical variables, glucose/metabolic where available, HR, HRV, activity, sleep/circadian, temp trends, stress, ultrasound structured features

**Distinguishes:**
1. Clinical-variable prediction (age, BMI, cycle regularity)
2. Wearable physiological signals (HR, HRV, activity, temp, sleep)
3. Ultrasound-derived features (CLINICALLY-ENTERED or IMAGE-DERIVED, quality-gated, UNKNOWN until validated dataset)
4. Combined/fused research estimate (with provenance breakdown)

**Domains (research priors, same as V8.1 but documented):**
- cycle: self-reported menstrual regularity only (CYCLE_NEUTRAL 15 when no data)
- metabolic: insulin-resistance tendency proxy (BMI, glucose, sleep, stress)
- glucose: manual glucose risk (optional)
- bp: manual BP risk (optional)
- stress_autonomic: HR/HRV-derived
- sleep: sleep/wake quality
- circadian: cosinor rhythm stability
- temperature_rhythm: skin-temp rhythm disruption
- low_activity: IMU inactivity

**Formula:**
```
z = INTERCEPT + CYCLE_W*c + METABOLIC_W*m + AUTONOMIC_W*a + SLEEP_W*s + CIRCADIAN_W*ci + TEMPERATURE_W*t + GLUCOSE_W*g + ACTIVITY_W*l + BP_W*b
risk = 100 * sigmoid(z)
Weights: CYCLE 1.20, METABOLIC 0.90, AUTONOMIC 0.60, SLEEP 0.50, CIRCADIAN 0.50, TEMPERATURE 0.35, GLUCOSE 0.35, ACTIVITY 0.30, BP 0.20, INTERCEPT -3.0
```

**Language:**
- Use: "PCOS-associated physiological and clinical risk signals"
- Never: "wearable detects PCOS"

**Limitations:**
- Research-only, not diagnostic, requires Rotterdam criteria and clinician
- Wearable alone cannot diagnose PCOS
- Ultrasound UNKNOWN by design until validated labelled dataset
- Not clinically validated

---

### Module B - Sleep / Circadian Health

**Uses:**
- Activity, movement, HR, HRV, resting HR, temp trends, sleep duration, timing, regularity, day/night activity pattern

**Assesses:**
- Duration: 7-9h normal, 6-7 or 9-10 mild deviation, 5-6 or 10-11 moderate, <5 or >11 significant
- Regularity: 100 - sleep_regularity, higher irregularity = higher score
- Circadian: circadian_disruption directly
- Recovery: 100 - recovery_score

**Weighted:**
```
overall = 0.30*regularity + 0.30*circadian + 0.25*duration + 0.15*recovery
```

**Persistence:**
- Checks last 20 points, if avg regularity <60 for 5+ days → persistent

**Outputs:**
- sleep_regularity_deviation
- circadian_disruption_pattern
- sleep_duration_deviation
- reduced_recovery_signal
- persistent_* variants

**Language:**
- "sleep-related risk signal" or "circadian disruption pattern"
- Never sleep disorder diagnosis

---

### Module C - Cardiometabolic Risk (research-oriented)

**Features:**
- Resting HR, HRV, activity, BMI, age, BP if entered, glucose if entered, sleep, temp, longitudinal changes

**Assesses:**
- Resting HR: <50 low (athletic), 50-70 normal, 70-80 mild elevated, 80-90 elevated, >90 high (age-adjusted)
- HRV: >=50 good, 35-50 moderate, 20-35 reduced, <20 low
- Activity: <15 low, 15-30 moderate, >30 good, plus trend recent vs older (<0.8 = reduced trend)
- Clinical metabolic: BMI >=30 +40, >=25 +20, sys BP >=130 +30, dia >=85 +20, glucose >=126 +40, >=100 +20
- Baseline deviations: RHR +1.5 SD, HRV -1.5 SD → +15 each

**Overall:**
```
overall = 0.30*rhr + 0.25*hrv + 0.25*activity + 0.20*metabolic + baseline_penalty*0.3
```

**Signals:**
- reduced_activity_trend (when recent <0.8*older)
- elevated_resting_hr_trend (rhr >60)
- metabolic_data_flag (clinical flags present)
- cardiometabolic_risk_signal (default)

**Never claims diabetes/hypertension/CVD diagnosis**

---

### Module D - Autonomic / Stress Regulation

**Uses:**
- HRV, resting HR, activity, sleep, temp

**Assesses:**
- HRV: >=50 good, 35-50 moderate, 20-35 reduced, <20 low
- Stress index: direct

**Acute vs Persistent Separation:**
- No history: acute if stress >70 or HRV <25
- With history (last 10): avg_stress, persistent_count >60
  - persistent_count >=5 and avg >60 → persistent
  - >=3 → intermittent
  - current > avg+20 → acute spike
  - else none

**Overall:**
```
overall = 0.467*hrv + 0.533*stress + (10 if persistent else 0)   # was 0.35/0.25/0.40 before the GSR component was removed
```

**Signals:**
- acute_autonomic_signal
- persistent_autonomic_deviation
- intermittent_stress_pattern
- autonomic_regulation_signal

**Not mental-health diagnosis**

**Recovery and Sleep Notes:**
- recovery >70 good, <40 reduced
- sleep <6h may affect autonomic balance

---

## Future Modules

**Placeholder interface, marked "Future research module - not implemented":**
- thyroid, renal, hepatic, infectious, oncology, neurodegenerative

**Requirements to implement:**
- Appropriate dataset
- Validated features
- Scientifically defensible target labels
- No fake datasets to make unsupported modules appear validated

**Registry:**
```python
GLOBAL_REGISTRY.list_future() → ["thyroid", "renal", ...]
GLOBAL_REGISTRY.create("thyroid") → None
```

---

## Why Modular?

**Benefits:**
- Avoid duplicating signal-processing code (shared representation)
- Allow additional disease modules without rewriting core
- Isolate failures (one module failing doesn't crash others)
- Preserve provenance per module
- Testable in isolation
- Honest about what is and isn't implemented

**Vs Monolith:**
- Monolith: one giant black-box claiming to diagnose everything, hard to explain, hard to extend, hides data quality
- Modular: transparent, explainable, extensible, provenance-aware, honest limitations

---

## Confidence Separation

**Three different concepts, never conflated:**

- **Model Confidence:** based on coverage of required/optional features + overall quality (0.5*coverage_required + 0.2*coverage_optional + 0.3*quality)
- **Data Quality:** mean quality of present features, 0..1, from sensor quality control
- **Clinical Validation:** NOT ESTABLISHED for all V8.3 modules (honest)

**Never display "78% chance of PCOS" unless model genuinely produces calibrated probability for exact target.**

Instead: level low/moderate/elevated/high + confidence + data quality + validation status

---

## Testing Module Isolation

```python
# Same shared features, different modules give different signals
shared = SharedFeatureExtractor().extract(fv, history)
for mod_name in registry.list_implemented():
    result = registry.create(mod_name).predict(shared, clinical, history)
    assert result.module contains mod_name
    assert result.signal differs per module (at least 2 unique signals)
    assert "DISEASE DETECTED" not in result
```

---

## Provenance in Modules

Each module returns provenance dict showing where info came from:

- PCOS: clinical 40%, wearable 25%, longitudinal 25%, ultrasound 20%, metabolic 15% (example, actual computed)
- Sleep: wearable 60%, longitudinal 30%, clinical 10%
- Cardiometabolic: wearable 50%, clinical 30%, longitudinal 20%
- Autonomic: wearable 60%, longitudinal 30%, clinical 10%

Values only used if actually generated by implemented model, not hard-coded fake percentages (PCOS example normalizes real weights).

---

## Limitations Honesty

Every module's `limitations()` method returns explicit research-only disclaimer:

- PCOS: requires Rotterdam criteria, wearable alone cannot diagnose, ultrasound UNKNOWN until validated dataset, not clinically validated
- Sleep: not diagnosis, does not replace polysomnography, wearable approximate, needs multiple days, not clinically validated
- Cardiometabolic: not diabetes/hypertension/CVD diagnosis, HR/HRV influenced by many factors, activity trends need multiple days, clinical data user-entered not validated, not clinically validated
- Autonomic: not mental-health diagnosis, HRV influenced by many factors, acute signals normal, persistent needs multiple days, not psychiatric diagnosis, not clinically validated
