# DISEASE MODULES - V8.3

## Initial Modules

### Module A - PCOS / Reproductive-Metabolic

Keeps and improves V8.1 PCOS pipeline.

**Inputs:**
- age, BMI, menstrual-cycle info, clinical variables, glucose/metabolic where available, HR, HRV, activity, sleep/circadian, temp trends, GSR/stress, ultrasound structured features

**Distinguishes:**
1. Clinical-variable prediction
2. Wearable physiological signals
3. Ultrasound-derived features
4. Combined/fused research estimate

**Language:** PCOS-associated physiological and clinical risk signals, never "wearable detects PCOS"

**Formula:** See MULTI_DISEASE_MODEL.md

**Provenance breakdown:** clinical, wearable, longitudinal, ultrasound, metabolic - computed, not hard-coded

**Limitations:** Research-only, requires Rotterdam criteria, wearable alone cannot diagnose, ultrasound UNKNOWN until validated dataset, not clinically validated

---

### Module B - Sleep / Circadian

**Uses:** activity, movement, HR, HRV, resting HR, temp trends, sleep duration/timing/regularity, day/night activity pattern

**Outputs:** sleep regularity signal, circadian disruption signal, recovery signal, persistent deviation

**Never diagnoses sleep disorders**

**Language:** sleep-related risk signal or circadian disruption pattern

**Method:** See MULTI_DISEASE_MODEL.md - duration, regularity, circadian, recovery weighted

**Persistence:** Checks last 20 points, avg regularity <60 for 5+ days → persistent

---

### Module C - Cardiometabolic (research-oriented)

**Features:** resting HR, HRV, activity, BMI, age, BP if entered, glucose if entered, sleep, temp, longitudinal changes

**Outputs:** cardiometabolic risk signal, reduced activity trend, elevated RHR trend, metabolic data flag

**Never claims diabetes/hypertension/CVD diagnosis**

**Method:** See MULTI_DISEASE_MODEL.md - RHR, HRV, activity, clinical metabolic, baseline deviations

**Signals:** reduced_activity_trend, elevated_resting_hr_trend, metabolic_data_flag, cardiometabolic_risk_signal

---

### Module D - Autonomic / Stress Regulation

**Uses:** HRV, resting HR, GSR, activity, sleep, temp

**Explainable estimator separating ACUTE SIGNAL from PERSISTENT LONGITUDINAL CHANGE**

**Not mental-health diagnosis**

**Method:** See MULTI_DISEASE_MODEL.md - HRV, GSR, stress, acute vs persistent separation

**Signals:** acute_autonomic_signal, persistent_autonomic_deviation, intermittent_stress_pattern, autonomic_regulation_signal

**Notes:** Recovery score, sleep <6h may affect autonomic balance

---

## Future Modules

Marked "Future research module - not implemented" - no fake datasets:

- thyroid, renal, hepatic, infectious, oncology, neurodegenerative

**Requirements to implement:**
- Appropriate dataset
- Validated features
- Scientifically defensible target labels

**Registry:** GLOBAL_REGISTRY.list_future() returns future modules, create returns None

---

## Module API

Consistent interface for all modules, allows adding without rewriting core.

See MULTI_DISEASE_MODEL.md for details.

---

## Confidence Separation

Model confidence vs data quality vs clinical validation - three different concepts, never conflated.

Never display "78% chance of PCOS" unless calibrated probability for exact target.

Instead: level low/moderate/elevated/high + confidence + data quality + validation NOT ESTABLISHED

---

## Explainability Mandatory

Every risk signal explains main contributing factors with drivers list and limitations.

Example:
```
Persistent change detected
Drivers:
- resting HR increased from baseline
- HRV decreased
- sleep regularity decreased
- activity decreased

These changes are not specific to one disease and should not be interpreted as a diagnosis.
```
