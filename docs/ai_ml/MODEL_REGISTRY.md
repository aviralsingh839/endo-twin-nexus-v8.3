# MODEL REGISTRY - ENDO-TWIN V8.3+

Date: 2026-09-19
Version: 8.3+
Status: IMPLEMENTED

## Pipeline

```
Data source
  ↓
Feature map
  ↓
Preprocessing
  ↓
Model inference
  ↓
Calibration
  ↓
Uncertainty estimation
  ↓
Explanation
  ↓
Provenance
  ↓
Report / UI
```

Loaded once and reused, cached, lazy loading, background preload, array not DataFrame for fast path, result caching

## Registry Metadata

- Name
- Version
- Input features
- Data quality expectations
- Confidence methodology
- Status: EXPERIMENTAL / RESEARCH / VALIDATION_PENDING / DEMO / RETIRED
- Validation: NOT ESTABLISHED / ENGINEERING ONLY / CLINICAL PENDING
- Limitations
- Training date
- Dataset version
- Features / target
- Metrics
- Validation strategy

## Models

### pcos_risk_model.joblib - REAL

- Path: models/pcos_risk_model.joblib
- Size: 17613145 bytes (17M)
- Type: dict {model, feature_names, target, meta}
- Model: CalibratedClassifierCV(VotingClassifier(lr+rf+et)) cv=3
- RF: n_estimators 500 random_state 42
- ET: n_estimators 400 random_state 42
- Features: 37 clinical + lab (FSH LH etc) - requires lab values
- Target: PCOS Y/N
- Meta: dataset PCOS_data_without_infertility.xlsx 541 rows leaky dropped Pregnant/Abortions/HCG
- Training: CV 5-fold stratified-group patient-level
- Metrics: ROC AUC 0.9594 AP 0.9324
- Notes: synthetic excluded
- Status: RESEARCH
- Validation: NOT ESTABLISHED - engineering only
- Limitations: Small dataset 541, requires lab values not wearable alone, CV only no separate test set may be optimistic, selection bias possible
- Data quality: Good if lab values available, Unknown if not
- Provenance: MODEL_INFERRED from CLINICALLY_ENTERED lab values where available, DEMO_DATA where demo
- Input: 37 features clinical+lab
- Output: pcos_associated_risk low/moderate/high + probability + explanation
- Confidence: Calibrated probability from CalibratedClassifierCV, not hard-coded 0.75
- Explanation: SHAP real only when model available, feature importance
- Uncertainty: confidence = calibrated probability, quality = coverage + input quality, not fake
- Loading: Once reused, background preload recommended, real inference 993 ms moderate bottleneck 2386 ms first load due to VotingClassifier 500+400 trees cv=3, target after optimization <500 ms cached
- Honest: Not 100%, ROC 0.9594 realistic, not clinical diagnosis

### ppg_quality_model.joblib - REAL but LOW

- Path: models/ppg_quality_model.joblib
- Size: 5323939 bytes (5.1M)
- Type: Pipeline RF 15 features
- Dataset: PhysioNet Wrist PPG During Exercise 19 rec 8 subj 903 windows usable_rate 0.3477 window 10s label |PPG HR - ECG HR|<=5 bpm
- CV: GroupKFold by subject
- Metrics: ROC AUC 0.624 std 0.141 AP 0.5043 keep_rate_0_5 0.2835 top_features zero_cross_rate/hr_bpm/ibi_cv/dom_peak_diff/band_power
- Notes: educational artifact wrist PPG sensor differs from MAX30102 blended at 40% weight
- Status: EXPERIMENTAL / RESEARCH
- Validation: NOT ESTABLISHED
- Limitations: Small sample 19 rec 8 subj, performance low 0.624 barely above random 0.5 std 0.141 high unstable, usable_rate low 34% wrist PPG during exercise very noisy, sensor mismatch wrist vs MAX30102 different characteristics may not transfer, label quality heuristic not gold standard, educational artifact
- Honest: Low metrics disclosed, not hidden, not 100%
- Use: Blended 40% with heuristic quality.py, not sole quality gate

### Deterministic research logic

- Path: src/disease_modules/pcos.py + disease_models/chrono_pcos/model/chrono_pcos_model.py fallback
- Type: Deterministic CYCLE_W 1.20 etc sigmoid
- Purpose: Research risk signal when lab values unavailable, wearable PPG+cycle only
- Input: hr, hrv_rmssd, cycle_regularity, activity etc.
- Output: pcos_associated_risk low/moderate/high + confidence from coverage+quality not hard-coded 0.75
- Status: RESEARCH
- Validation: NOT ESTABLISHED
- Limitations: Research priors not clinical model, wearable alone cannot diagnose PCOS, requires clinical evaluation Rotterdam criteria
- Confidence: Computed from coverage and quality, not hard-coded 0.75, None if unavailable
- Data quality: overall from quality scores
- Provenance: MODEL_INFERRED from MEASURED PPG + CLINICALLY_ENTERED cycle
- Performance: 0.3 ms extremely fast

## Inference Path

- Real: real_pcos_model_adapter.py load once reuse, dict model feature_names target meta, array not DataFrame fast path, calibrated probability, SHAP real only, provenance visible
- Deterministic fallback: when real model unavailable or lab values missing, deterministic research logic with honest confidence
- No hard-coded 0.75 in real inference path - verified via grep, only threshold 0.75 for level classification not confidence, demo paths explicitly labelled DEMO_DATA/EXAMPLE_DATA

## Diagnostics

- docs/ai_ml/MODEL_DIAGNOSTIC_REPORT.md
- scripts/diagnostics/project_health.sh checks model artifacts loading
- tests/test_model_loading.py real loading verified
- sklearn version 1.9.0 artifact vs 1.9.1 runtime warning documented works

## Explainability

- Model name/version/input/data quality/confidence/features/limitations, never hide uncertainty/manufacture confidence/training results
- SHAP real only when model available, feature importance from RF/ET
- Provenance visible MEASURED/CLINICAL_ENTRY/DERIVED/IMAGE_DERIVED/MODEL_INFERRED/DEMO/SIMULATED/UNKNOWN
- Ultrasound: modular Image→Validation→Preprocess→Quality→Feature→Segmentation→Uncertainty→Explanation→CHRONO-PCOS no clinical claim UNKNOWN quality unless computed fusion weight 0.20

## Retraining

- Dedup patient-level split, no leakage
- Patient-level GroupKFold, synthetic excluded, leaky columns dropped
- Future: dataset versioning DVC, experiment tracking MLflow Research Lab only no bloat
