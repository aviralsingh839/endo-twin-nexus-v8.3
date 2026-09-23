# MODEL VALIDATION - V8.3

## Engineering vs Clinical

Clearly separate:

- **ENGINEERING VALIDATION**: Does system work as designed? (Implemented)
- **CLINICAL VALIDATION**: Does system diagnose disease? (NOT ESTABLISHED)

Project may have engineering validation without clinical validation.

## Engineering Validation - Implemented

### 1. Baseline Accuracy

- Test: `test_baseline_accuracy`
- Synthetic subject with known baseline (RHR 70, HRV 50), 10 days stable
- Capture baseline, check median close to known (<15 bpm), confidence >0.5, metrics present
- Also tests min observations required (rejects insufficient data)

### 2. Trend Detection

- Test: `test_gradual_deviation`
- Gradual scenario: HR slope 0.2 bpm/day over 30 days
- Longitudinal engine should detect deviation, persistence >0
- Slope per day computed via polyfit over recent 12 points

### 3. Persistence Detection

- Test: `test_persistent_deviation`
- Persistent scenario: after day 15, HR +8, HRV -12, etc. for extended period
- Should detect deviation, multimodal True (multiple metrics), persistence high
- Trailing consecutive out-of-band points >=3

### 4. Recovery Detection

- Test: `test_recovery_detection`
- Recovery scenario: abnormal then returns toward baseline
- Should detect recovery_detected True or overall_kind recovery
- Recovery_progress 0..1 based on max_z_early vs latest_z

### 5. Missing Sensor Handling

- Tests: `test_missing_data`, `test_missing_sensors_no_crash`, `test_disconnected_sensors`, `test_sensor_reconnection`, `test_missing_data_not_physiological`
- Quality control: missing → quality 0, artifact missing
- Overall quality: mean over present only, optional channels never drag down
- Fusion: missing groups weight 0, does not drag estimate down, absence visible
- App continues rather than crashing
- Sensor failure scenario: quality drops after failure day, not interpreted as physiological abnormality

### 6. Noisy Data

- Tests: `test_noisy_data`, `test_noisy_ppg`, `test_excessive_motion`
- Quality control: z >5 → excessive noise, quality penalty 0.3, artifact
- PPG quality: heuristic + trained model blended 60/40, noisy → quality low
- Motion: motion_index >1.5 → quality penalty, activity 100%
- IMU processor: high motion → motion_index >0.5

### 7. Multimodal Fusion

- Tests: `test_fusion_provenance`, `test_fusion_combines_modules`
- FusionContext: overall_quality mean present, coverage fraction present, present_groups, missing_groups, group_weights coverage*avg_q
- Provenance summary: counts per provenance
- FusionResult: overall_signals elevated/high modules, confidence_breakdown model_confidence, data_quality, clinical_validation, fusion_coverage, fusion_quality, explanation, recommendations
- Provenance preserved: WHERE DID INFO COME FROM?

### 8. Disease Module Isolation

- Tests: `test_module_api`, `test_module_isolation`, `test_pcos_module_provenance`, `test_future_modules_not_implemented`, `test_no_diagnostic_claims`
- API: name, version, required_features, optional_features, predict, explain, confidence, limitations
- Isolation: same shared features, different modules give different signals (at least 2 unique), no crash
- PCOS provenance: clinical_variables, wearable_physiology, longitudinal, ultrasound, metabolic breakdown computed, not hard-coded fake
- Future: create returns None, status not implemented, description not implemented
- No diagnostic claims: limitations contain research-only, not diagnosis, no "DISEASE DETECTED"

### 9. Subject-Level Validation

- Test: `test_subject_level_validation`
- Synthetic cohort 10 subjects, split train 7 test 3 at subject level
- No overlap, subject_id preserved in shared_features
- Prevents leakage: same person not in both folds

### 10. Reproducibility

- Test: `test_reproducibility`
- Same seed → same timeline, same HR, HRV for first 5 samples
- Seeds fixed for synthetic generation

### 11. Data Honesty

- Tests: `test_data_honesty_labels`, `test_no_fake_clinical`, `test_ultrasound_provenance`
- All synthetic clearly labelled SYNTHETIC, synthetic True
- Scenario files labelled SYNTHETIC
- Clinical folder should not contain synthetic labelled as REAL
- Ultrasound provenance CLINICALLY-ENTERED vs IMAGE-DERIVED preserved

### 12. Hardware Failure

- Test: `test_hardware_failures.py`
- Packet parser: corrupted CRC, missing fields correctly rejected, valid packet parsed
- Disconnected sensors: ir 0 → quality 0 artifact, temp None → artifact, flatline detection, reconnection recovers
- Noisy PPG: quality <1
- Excessive motion: motion_index >0.5
- Sensor failure scenario: quality before > after

## Clinical Validation - NOT ESTABLISHED

- All modules research-only signals
- No diagnostic claims
- Requires ethics-approved prospective study
- Model confidence vs data quality vs clinical validation separated
- PCOS: needs Rotterdam criteria and clinician
- Sleep: does not replace polysomnography
- Cardiometabolic: not diabetes/hypertension/CVD diagnosis
- Autonomic: not mental-health diagnosis

## Model Training Documentation

For every model, document:

- dataset: e.g. PCOS_data.csv (PUBLIC DATASET), wrist_ppg (PUBLIC), synthetic (SYNTHETIC)
- target: e.g. PCOS risk, sleep status, HRV
- features: e.g. HR, HRV, activity, temp, clinical
- preprocessing: filtering, peak detection, etc.
- train/test split: subject-level where appropriate
- cross-validation: e.g. LOSOCV
- metrics: e.g. accuracy, R^2, etc.
- limitations: e.g. not clinically validated, transparent fallback equation, etc.

Current status V8.3:

- Live risk engine: transparent fallback equation with research-prior weights, not trained calibrated model (labelled longitudinal wearable data does not exist publicly, ethics-approved pilot only realistic path)
- PPG quality model: trained on wrist_ppg_during_exercise (different sensor and sampling rate than MAX30102), used as soft correction 40% weight, heuristic dominant
- Ultrasound: UNKNOWN by design until validated labelled dataset
- Model A-E experiment (does longitudinal or ultrasound add value?): PENDING by design
- All unproven labelled PENDING or UNKNOWN in interface, code, docs

## Avoid Data Leakage

- Longitudinal subjects splitting at SUBJECT level
- Same person measurements not in both training and validation when would leak
- Test `test_subject_level_validation` verifies

## Validation Tab in UI

Shows engineering vs clinical status, lists implemented.

## Running Tests

```bash
python -m pytest tests/ -q
python tests/test_baseline.py
python tests/test_longitudinal.py
python tests/test_sensor_quality.py
python tests/test_disease_modules.py
python tests/test_fusion.py
python tests/test_hardware_failures.py
python tests/test_validation.py
```

124 tests in V8.1 legacy, plus 7 new test files in V8.3 covering required validation.

## Safety

- When signal quality or model confidence insufficient, risk number withheld with banner instead of guess (V8.1 behavior preserved)
- Bad data must not silently become model input
- Missing sensors do not crash system
- No medical decisions from this prototype alone
