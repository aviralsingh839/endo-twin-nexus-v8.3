# DATASET CARD - V8.3

## Overview

CHRONO-TWIN NEXUS V8.3 uses multiple datasets, clearly labelled.

## Public Datasets (PUBLIC DATASET)

### PCOS_data.csv

- **Source:** Kaggle PCOS cohort
- **Label:** PUBLIC DATASET
- **Rows:** 541
- **Columns:** Age, BMI, cycle length, etc., plus infertility columns
- **Target:** PCOS (0/1) - clinical diagnosis from dataset, not wearable
- **Usage:** Reference for PCOS risk model training, not wearable diagnosis
- **Limitations:** Not longitudinal wearable, no sensor data, clinical variables only, small, not clinically validated for wearable
- **File:** `data/public/PCOS_data.csv` and `chrono_pcos_project V8/data/public/PCOS_data.csv` (legacy)

### PCOS_infertility.csv

- **Source:** Infertility subset of same cohort
- **Label:** PUBLIC DATASET
- **Usage:** Same as above

### PCOS_data_without_infertility.xlsx

- **Source:** Original xlsx, training input for risk baseline model
- **Label:** PUBLIC DATASET
- **File:** Legacy only `chrono_pcos_project V8/data/public/PCOS_data_without_infertility.xlsx`

### wrist_ppg_during_exercise

- **Source:** PhysioNet wrist PPG during exercise (WFDB)
- **Label:** PUBLIC DATASET
- **Files:** s1_walk, s1_high_resistance_bike, etc., .dat, .hea, .atr, RECORDS, ANNOTATORS, SHA256SUMS
- **Usage:** PPG quality model training - HR reliability |PPG HR - ECG HR| <=5 bpm
- **Limitations:** Different sensor and sampling rate than MAX30102, so model only used as soft correction 40% weight, heuristic dominant, source page withdrawn so local copy only source
- **File:** `chrono_pcos_project V8/data/public/wrist_ppg_during_exercise/` (legacy) - not copied to new data/public to avoid large files, but reference preserved

## Synthetic Datasets (SYNTHETIC)

### Cohort - 10 Subjects

- **Source:** `src/utils/synthetic.py` `generate_synthetic_cohort`
- **Label:** SYNTHETIC
- **Subjects:** 10, diverse baselines age 16-45, BMI 18.5-32, RHR 60-80, HRV 30-60, temp 31.5-33.5, activity 20-50, sleep 6.5-8.5, cycle 21-35 days, 20% irregular
- **Timeline:** 30 days, 12 samples/day, realistic longitudinal variation not random
- **Features per sample:** hr_bpm, resting_hr_bpm, rmssd_ms, skin_temp_c, activity_level, sleep_duration_h, sleep_regularity, circadian_stability_index, stress_index, signal_quality, scenario, label SYNTHETIC
- **Scenarios mix:** stable 40%, gradual 20%, persistent 15%, temporary 15%, recovery 10%
- **Realism:** individual baselines, circadian modulation, sensor noise, missing data 2%, motion artifacts 3%, gradual changes, temporary disturbances, recovery periods
- **Files:** `data/synthetic/cohort/SYNTH_000.json` ... `SYNTH_009.json`
- **Format:** JSON with subject_id, label SYNTHETIC, data array

### Scenarios - 6 Required

- **Source:** `src/utils/synthetic.py` `generate_scenario_dataset`
- **Label:** SYNTHETIC
- **Scenarios:**
  1. scenario_1_stable: stable, LOW CHANGE SIGNAL, physiology within normal variation
  2. scenario_2_gradual: gradual, EARLY CHANGE SIGNAL, parameter slowly moves away, hr_slope 0.12 bpm/day, hrv -0.25
  3. scenario_3_persistent: persistent, PERSISTENT MULTIMODAL SIGNAL, multiple signals abnormal extended, start day 20, HR +8, HRV -12, temp +0.4, activity -10, sleep -0.8h
  4. scenario_4_temporary: temporary, TEMPORARY EVENT not disease, brief change then return, days 30-33 HR +15, HRV -15, temp +0.6
  5. scenario_5_sensor_failure: sensor_failure, LOW SENSOR CONFIDENCE, one sensor stops, must not be interpreted as physiological, day 25 HR missing 70% or flatline quality 0.2
  6. scenario_6_recovery: recovery, RECOVERY TREND, abnormal returns toward baseline, start day 10 duration 25 days
- **Timeline:** 60 days, 24 samples/day, 1440 points per scenario
- **Files:** `data/synthetic/scenarios/scenario_1_stable.json` ... `scenario_6_recovery.json`
- **Format:** JSON with scenario, type, expected_result, description, label SYNTHETIC, subject_profile, data array

### Demo Stream

- **Source:** `src/utils/demo_stream.py` DemoSensorStream
- **Label:** SIMULATED
- **Usage:** Dashboard demo mode, clearly labelled synthetic
- **Not counted as REAL**

## Clinical Data (USER-ENTERED)

- **Source:** Manual entry in UI Clinical Inputs tab
- **Label:** USER-ENTERED
- **Fields:** age, BMI, height, weight, waist, systolic/diastolic BP, cycle day, usual length, days since last period, years post menarche, cycle irregular bool, glucose mg/dL, glucose context, time since meal, sex, smoking, family history
- **Storage:** `data/clinical/` or SQLite `history_store`, labelled USER-ENTERED
- **Never treated as MEASURED**

## Physiological Data (REAL or SYNTHETIC)

- **Source:** Wearable pod, Mega hub, or synthetic generator
- **Label:** REAL if from hardware, SYNTHETIC if from generator
- **Fields:** FeatureVector attributes
- **Storage:** `data/physiological/` or SQLite, with quality metadata

## Longitudinal Data (REAL or SYNTHETIC)

- **Source:** Timeline per subject
- **Label:** REAL or SYNTHETIC
- **Storage:** `data/longitudinal/` or SQLite
- **Split:** Subject-level for validation, no leakage

## Ultrasound Data (REAL or CLINICAL)

- **Source:** Ultrasound images or clinically-entered structured features
- **Label:** REAL (image) or CLINICALLY-ENTERED / IMAGE-DERIVED
- **Fields:** cyst_size_mm, volume_cc, morphology, quality, source
- **Storage:** `data/ultrasound/`
- **Provenance preserved:** source image → preprocessing → detected features → quality → uncertainty
- **If cannot be reliably extracted:** UNKNOWN, never invented

## Baselines (REAL)

- **Source:** Personal baseline engine from user's own data
- **Label:** REAL (personal)
- **Files:** `data/baselines/personal_baseline_v8_3.json`, `calibration_history_v8_3.json`, gitignored
- **Contains:** captured_at, duration_s, samples, days_covered, quality, confidence, stats per metric with median, mean, std, mad, p05, p95, etc.

## Raw Data (REAL)

- **Source:** Raw sensor exports, packet logs
- **Label:** REAL
- **Files:** `data/raw/`, gitignored
- **Format:** CSV with timestamp, ir, red, ax, ay, az, etc.

## Data Honesty - Critical

- Never create fake clinical results and present as real
- Never modify public datasets to make metrics look better
- Never fabricate patient records
- Never label synthetic as clinical
- Never claim diagnosis unless clinically validated
- Use: "research risk signal", "physiological deviation", "screening-oriented estimate", "requires clinical evaluation"
- All synthetic clearly labelled SYNTHETIC
- Public clearly labelled PUBLIC DATASET
- User-entered clearly labelled USER-ENTERED
- Real clearly labelled REAL
- Tests verify labels

## Training Audit

- File: `data/training_audit.jsonl`, gitignored
- Logs training runs with dataset, target, features, split, metrics, limitations

## Model Files

- `models/pcos_risk_model.joblib` (legacy, 17MB) - trained on PCOS_data.csv, reference
- `models/ppg_quality_model.joblib` (legacy, 5MB) - trained on wrist_ppg, soft correction
- New V8.3: no new large models, transparent fallback equations, research priors, not claiming calibrated models

## Reproducibility

- Seeds fixed
- Same seed → same synthetic timeline
- Subject-level split
- Requirements.txt pinned

## Limitations

- No large clinically labelled longitudinal wearable dataset publicly exists
- PCOS risk model is transparent fallback, not trained calibrated model - needs ethics-approved pilot
- PPG quality model trained on different sensor, used as soft correction only
- Ultrasound UNKNOWN by design until validated labelled dataset
- Model A-E experiment PENDING by design
- All unproven labelled PENDING or UNKNOWN

## Usage

```python
from src.utils.synthetic import generate_synthetic_cohort, generate_scenario_dataset
cohort = generate_synthetic_cohort(n_subjects=10, days=30, samples_per_day=12, output_dir=Path("data/synthetic/cohort"))
scenarios = generate_scenario_dataset(Path("data/synthetic/scenarios"))
```
