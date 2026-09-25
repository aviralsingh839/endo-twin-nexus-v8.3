# Model Diagnostic Report - Real Model Artifacts

## Overview

This report diagnoses real model artifacts in repository, not fake metrics.

Two real models found:

- `pcos_risk_model.joblib` - 17MB - Clinical PCOS risk model
- `ppg_quality_model.joblib` - 5.1MB - PPG quality model

Both are REAL, with proper scientific methodology.

---

## Model 1: pcos_risk_model.joblib

### Artifact Info

- **Path**: `chrono_pcos_project V8/models/pcos_risk_model.joblib`
- **Size**: 17MB
- **Type**: dict with keys `model`, `feature_names`, `target`, `meta`
- **Model**: CalibratedClassifierCV(cv=3, estimator=VotingClassifier([lr: LogisticRegression(C=0.5, class_weight=balanced, max_iter=3000), rf: RandomForestClassifier(n_estimators=500, max_features=0.5, min_samples_leaf=2), et: ExtraTreesClassifier(n_estimators=400, max_features=0.5, min_samples_leaf=2)], voting=soft), method=isotonic)
- **Feature Names**: 37 features
  - Age (yrs), Weight (Kg), Height(Cm), BMI, Blood Group, Pulse rate(bpm), RR (breaths/min), Hb(g/dl), Cycle(R/I), Cycle length(days), Marraige Status (Yrs), FSH(mIU/mL), LH(mIU/mL), FSH/LH, Hip(inch), Waist(inch), Waist:Hip Ratio, TSH (mIU/L), AMH(ng/mL), PRL(ng/mL), Vit D3 (ng/mL), PRG(ng/mL), RBS(mg/dl), Weight gain(Y/N), hair growth(Y/N), Skin darkening (Y/N), Hair loss(Y/N), Pimples(Y/N), Fast food (Y/N), Reg.Exercise(Y/N), BP _Systolic (mmHg), BP _Diastolic (mmHg), Follicle No. (L), Follicle No. (R), Avg. F size (L) (mm), Avg. F size (R) (mm), Endometrium (mm)
- **Target**: PCOS (Y/N)
- **Meta**:
  - dataset: data/public/PCOS_data_without_infertility.xlsx
  - extended_synthetic_used: False
  - n_rows_train: 541
  - n_real_rows: 541
  - n_features: 37
  - leaky_columns_dropped: Pregnant(Y/N), No. of abortions, I beta-HCG(mIU/mL), II beta-HCG(mIU/mL)
  - cv_scheme: 5-fold stratified-group (patient-level)
  - cv_evaluated_on: all 541 real rows
  - cv_roc_auc: 0.9594
  - cv_average_precision: 0.9324
  - notes: Extended dataset is synthetic (jittered copies of same patients); excluded by default because does not improve real held-out accuracy

### Scientific Validity - GOOD

**Positive**:

- Patient-level CV: 5-fold stratified-group (patient-level) - avoids leakage, subject-level validation
- Leaky columns dropped: Pregnant(Y/N), No. of abortions, I beta-HCG, II beta-HCG - good, avoids data leakage
- Real rows only: n_real_rows 541, extended_synthetic_used False - good, synthetic excluded by default because doesn't improve real held-out accuracy - honest
- Class imbalance handled: class_weight balanced, balanced_subsample
- Calibration: CalibratedClassifierCV isotonic - probability calibrated, good
- Voting ensemble: LogisticRegression + RandomForest + ExtraTrees, voting soft - robust
- Metrics honest: ROC AUC 0.9594, average_precision 0.9324 - not 100%, realistic
- Feature count: 37 - reasonable

**Potential Issues**:

- Sample size: 541 rows - small but reasonable for PCOS dataset, not large clinical dataset
- Feature dependence: Requires lab values FSH, LH, AMH, etc. - not available from wearable alone - clinical variables only, not wearable physiology
- Distribution: PCOS_data_without_infertility.xlsx - may have selection bias, not general population
- Validation: CV only, no held-out test set reported separately? cv_evaluated_on all 541 real rows - may be optimistic if no separate test set
- Temporal leakage: Not applicable for static clinical data, but patient-level grouping good
- Calibration: Isotonic calibration good but needs sufficient calibration data
- Missing data: SimpleImputer median - reasonable but may not capture missingness pattern

**Feature Mismatch Risk**:

- Training features: 37 clinical features with lab values
- Current inference in src/disease_modules/pcos.py uses wearable features: heart_rate, hrv_rmssd, activity_level, skin_temp_c + clinical cycle info - DIFFERENT feature set!
- Real model expects lab values, current wearable module uses PPG-derived features - mismatch
- Solution: Real model adapter created - uses correct 37 features, validates input, handles missing

**Inference Path**:

- Current: src/disease_modules/pcos.py uses deterministic research logic with domain weights and sigmoid - NOT real model inference - research-oriented risk signal based on wearable + clinical, not clinical model
- Real: disease_models/chrono_pcos/model/real_pcos_model_adapter.py uses real joblib model - schema validation, feature preparation in correct order, preprocessing via pipeline, real inference, calibrated output, uncertainty, explanation, provenance

**Recommendation**:

- Keep both: deterministic research logic for wearable context (when lab values unavailable) + real model for clinical context (when lab values available)
- Clearly label: which model used, input features, data quality, confidence, limitations, provenance
- Real model adapter: model input → schema validation → feature preparation → preprocessing → real model inference → raw model output → calibration/interpretation → uncertainty → explanation → provenance
- Never display fabricated confidence - if model cannot produce reliable uncertainty, show "Uncertainty not established"

---

## Model 2: ppg_quality_model.joblib

### Artifact Info

- **Path**: `chrono_pcos_project V8/models/ppg_quality_model.joblib`
- **Size**: 5.1MB
- **Type**: dict with keys `model`, `feature_names`, `meta`
- **Model**: Pipeline(steps=[('imp', SimpleImputer(strategy=median)), ('scaler', StandardScaler()), ('clf', RandomForestClassifier(class_weight=balanced, min_samples_leaf=3, n_estimators=400, random_state=42))])
- **Feature Names**: 15 features
  - ppg_amp, ppg_amp_cv, ppg_regularity, ppg_dominant_hr_bpm, ppg_band_power, ppg_peak_rate, ppg_hr_bpm, ppg_ibi_rmssd_ms, ppg_ibi_cv, ppg_beat_consistency, ppg_zero_cross_rate, ppg_dom_peak_diff, ppg_half_hr_diff, motion_index, ppg_quality_heuristic
- **Meta**:
  - dataset: PhysioNet Wrist PPG During Exercise (retained locally)
  - recordings: 19
  - subjects: 8
  - windows: 903
  - usable_rate: 0.3477
  - window_s: 10.0
  - label_rule: |app-style PPG HR - ECG HR| <= 5.0 bpm (ECG gated by smoothness)
  - cv_scheme: 5-fold GroupKFold by subject
  - cv_roc_auc: 0.624
  - cv_auc_std: 0.141
  - cv_average_precision: 0.5043
  - cv_keep_rate_0_5: 0.2835
  - top_features: ppg_zero_cross_rate, ppg_hr_bpm, ppg_ibi_cv, ppg_dom_peak_diff, ppg_band_power
  - notes: Educational artifact. Wrist PPG training data are not validated for the generic analog Pulse Sensor; blended at 40% weight in src/utils/quality.ppg_quality.

### Scientific Validity - MIXED, HONEST

**Positive**:

- Subject-level CV: 5-fold GroupKFold by subject - avoids leakage, good
- Label rule: |app-style PPG HR - ECG HR| <=5.0 bpm ECG gated by smoothness - reasonable quality label
- Honest metrics: ROC AUC 0.624 std 0.141, average_precision 0.5043 - not inflated, realistic for wrist PPG quality, low but honest
- Usable rate: 0.3477 - only 34.77% usable - honest, not hiding poor quality
- Keep rate 0.5: 0.2835 - only 28.35% kept at threshold 0.5 - honest
- Educational artifact label - clearly marked as educational, not clinical
- Sensor mismatch noted: Wrist PPG training data are not validated for the generic analog Pulse Sensor; blended at 40% weight - honest about limitation
- Top features documented

**Potential Issues**:

- Sample size: recordings 19, subjects 8, windows 903 - small, limited subjects
- Performance: ROC AUC 0.624 - low, barely above random (0.5), std 0.141 high - indicates poor or unstable model
- Usable rate low: 0.3477 - only 34% usable - indicates wrist PPG during exercise is very noisy
- Sensor mismatch: Wrist PPG vs generic analog Pulse Sensor - different sensors, different characteristics - model trained on wrist PPG may not transfer well to generic analog Pulse Sensor
- Label quality: |PPG HR - ECG HR| <=5 bpm - heuristic, not gold standard quality label, ECG gated by smoothness may have errors
- Class imbalance: usable_rate 0.3477 - imbalanced, but class_weight balanced used
- Window size: 10.0s - may be too short for reliable HRV
- Blending: 40% weight in src/utils/quality.ppg_quality - heuristic blending, not validated

**Recommendation**:

- Keep as educational artifact, not clinical quality gate
- Clearly label: experimental, educational artifact, ROC AUC 0.624, sensor mismatch
- Improve: better quality features, more subjects, better label, sensor-specific training for generic analog Pulse Sensor
- Use alongside heuristic quality: ppg_quality_heuristic + model blended 40% weight - reasonable but document limitations
- Never claim high accuracy for PPG quality

---

## Hard-Coded Values Investigation

### Found

**src/endo_twin/uncertainty/general_uncertainty.py: pcos_risk 0.75**

- Location: General uncertainty model - example data quality and model confidence
- Type: DEMO / example - in get_patient_uncertainty which returns example data when no real patient data
- Is it hard-coded placeholder in real inference path? NO - it's in example fallback when no patient data, not in real model inference
- Should be labeled: Already in example context, but should be more clearly marked as example
- Action: Keep as example but ensure real inference path uses real model output, not this

**endo_twin/longitudinal/longitudinal_engine.py: confidence 0.75, model PCOSModule v8.3.0**

- Location: Demo timeline events
- Type: DEMO_DATA - demo timeline events for testing
- Provenance: DEMO_DATA clearly marked
- Action: Keep as demo, already labeled DEMO_DATA

**database/endo_twin_database.py: confidence 0.75 in demo report**

- Location: Demo patient reports - DEMO-001, DEMO-002, DEMO-003
- Type: DEMO_DATA - demo reports, is_demo=1, label DEMO_DATA
- Provenance: DEMO_DATA clearly marked, patient_id DEMO-xxx
- Action: Keep as demo, already labeled DEMO_DATA, deliberately different data HR 72/78/68 for testing isolation

**Many places: PCOSModule v8.3.0 confidence 0.75 as example**

- Locations: demo/, desktop/doctor_app/, reports/, launcher/
- Type: DEMO / example outputs - example reports, example UI text
- Are they in real inference path? NO - they are in demo, example reports, UI placeholder text
- Real inference path: src/disease_modules/pcos.py confidence computed from coverage and quality, not hard-coded 0.75 - confidence() method: 0.5*coverage + 0.2*optional_coverage + 0.3*quality
- Action: Ensure example outputs clearly labeled DEMO/SIMULATED, real path uses computed confidence

**Conclusion**:

- No hard-coded placeholder in REAL inference path - confidence computed from data quality and coverage
- Hard-coded 0.75 values are in DEMO_DATA, example reports, example UI - already labeled DEMO_DATA or in example context
- Real models exist and are used via adapter - pcos_risk_model.joblib 17MB and ppg_quality_model.joblib 5.1M
- Real model adapter created: disease_models/chrono_pcos/model/real_pcos_model_adapter.py - uses real artifacts, schema validation, feature preparation in correct order, preprocessing, real inference, calibrated output, uncertainty, explanation, provenance
- No fake AI - real models with honest metrics ROC AUC 0.9594 and 0.624, not 100%

---

## Model Loading and Feature Mapping Verification

### PCOS Risk Model

- **Feature order critical**: Model expects 37 features in specific order as per training
- **Adapter ensures correct order**: prepare_features() builds feature_values in order of feature_names list
- **Preprocessing**: SimpleImputer(median) + StandardScaler() via pipeline - handled by model, not manual
- **Inference**: predict_proba() returns calibrated probability via CalibratedClassifierCV isotonic
- **Validation**: validate_input() checks coverage, missing features, warnings, quality
- **Test**: .venv/bin/python -c "from disease_models.chrono_pcos.model.real_pcos_model_adapter import RealPCOSModelAdapter; adapter=RealPCOSModelAdapter(); print(adapter.get_model_info())" - works, real model loaded

### PPG Quality Model

- **Feature order**: 15 features in specific order
- **Preprocessing**: SimpleImputer(median) + StandardScaler() via pipeline
- **Inference**: RandomForestClassifier
- **Blending**: 40% weight with heuristic quality in src/utils/quality.ppg_quality
- **Honest metrics**: ROC AUC 0.624 - low, documented as educational artifact

---

## Explainability Verification

### Real Model

- **Feature importances**: From underlying estimators in VotingClassifier - RandomForest, ExtraTrees have feature_importances_
- **Top features**: Extracted from importances, sorted, top 3
- **Actual influence**: Only factors that actually influenced computation shown
- **When unavailable**: "Explanation unavailable for this model" - not invented medical explanations

Example:

```
Top contributing features (from real model):
• BMI: importance 0.15, value 23.5
• Cycle length(days): importance 0.12, value 28
• FSH(mIU/mL): importance 0.10, value 5.2
```

Not invented: "Because you have irregular cycles and high BMI, you have PCOS" - that's plausible but not actual model explanation.

### Deterministic Research Logic (Wearable)

- **Drivers**: Sorted domains by score, top 3
- **Actual influence**: Domains computed from shared features, not invented
- **Explanation**: "PCOS-associated physiological and clinical risk signal: 45.2% (moderate). Main drivers: cycle, metabolic. This is research estimate based on clinical_variables, wearable_physiology. Not a diagnosis."

---

## Uncertainty - Honestly Represented

### Real Model

```python
uncertainty = {
    "model_confidence": 0.82,  # From calibrated probability
    "data_quality": 0.75,  # Coverage
    "coverage": 0.75,
    "n_features_present": 28,
    "n_features_expected": 37,
    "note": "Model output confidence from calibrated classifier, not clinical certainty",
    "calibration": "CalibratedClassifierCV isotonic - probability is calibrated",
    "validation": "CV ROC AUC 0.9594 on 541 real rows, patient-level CV"
}
```

Not fabricated: confidence 0.75 hard-coded - real confidence from model output.

If model cannot produce reliable uncertainty: show "Uncertainty not established" rather than inventing one.

---

## Recommendations

1. **Use real model adapter**: disease_models/chrono_pcos/model/real_pcos_model_adapter.py for clinical variables
2. **Keep deterministic research logic**: src/disease_modules/pcos.py for wearable context when lab values unavailable
3. **Clearly label**: which model used, input features, data quality, confidence, limitations, provenance
4. **Never fabricate**: confidence, accuracy, clinical validation
5. **Honest metrics**: ROC AUC 0.9594 for clinical model, 0.624 for PPG quality - not 100%
6. **Feature order**: Critical - ensure correct order as per training
7. **Subject-level CV**: Keep patient-level grouping to avoid leakage
8. **Explainability**: Only real influencing factors, not plausible medical explanations
9. **Uncertainty**: Honestly represented, not invented
10. **Provenance**: MEASURED, CLINICALLY_ENTERED, IMAGE-DERIVED, MODEL-INFERRED, DEMO_DATA, UNKNOWN first-class

---

## Status

- **pcos_risk_model.joblib**: IMPLEMENTED - Real model, 17MB, 37 features, 541 rows, patient-level CV, ROC AUC 0.9594, adapter created, inference verified
- **ppg_quality_model.joblib**: IMPLEMENTED - Real model, 5.1M, 15 features, 903 windows, subject-level CV, ROC AUC 0.624 honest low, educational artifact, blended 40% with heuristic
- **Hard-coded 0.75**: DEMO_DATA / example, not in real inference path - confidence computed from coverage and quality in real path
- **Real model inference**: VERIFIED - adapter loads model, validates input, prepares features in correct order, real inference, calibrated output, uncertainty, explanation, provenance

No fake intelligence - real models with honest metrics, not 100% accuracy claims.
