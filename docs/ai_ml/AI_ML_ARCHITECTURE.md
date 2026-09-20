# AI/ML ARCHITECTURE - ENDO-TWIN V8.3+

Date: 2026-09-19
Version: 8.3+
Status: IMPLEMENTED

## Real Model Pipeline

For every model:

```
Input
 ↓
Schema validation
 ↓
Feature mapping
 ↓
Preprocessing
 ↓
Model inference
 ↓
Raw output
 ↓
Calibration if justified
 ↓
Uncertainty
 ↓
Explanation
 ↓
Provenance
```

Models loaded once and reused rather than reloaded for every prediction.

## Current Implementation

### Real Artifacts

- pcos_risk_model.joblib 17M dict CalibratedClassifierCV VotingClassifier lr LogisticRegression C=0.5 balanced max_iter 3000 + rf RandomForest n_estimators 500 + et ExtraTrees n_estimators 400 voting soft isotonic, 37 features, target PCOS Y/N, meta dataset PCOS_data_without_infertility.xlsx 541 rows leaky dropped Pregnant/Abortions/HCG CV 5-fold stratified-group patient-level ROC AUC 0.9594 AP 0.9324 notes synthetic excluded
- ppg_quality_model.joblib 5.1M Pipeline median+StandardScaler+RandomForest balanced 15 features PhysioNet wrist PPG 19 rec 8 subj 903 windows usable_rate 0.3477 window 10s label |PPG HR - ECG HR|<=5 bpm CV GroupKFold by subject ROC AUC 0.624 std 0.141 AP 0.5043 keep_rate_0_5 0.2835 top_features zero_cross_rate/hr_bpm/ibi_cv/dom_peak_diff/band_power notes educational artifact wrist differs MAX30102 blended 40% weight

Both REAL, honest metrics not 100%, no fake AI.

### Adapter

- disease_models/chrono_pcos/model/real_pcos_model_adapter.py implements required pipeline with honest uncertainty no fabricated confidence model transparency provenance TRAINED MODEL limitations research only
- Methods: _load_model, get_model_info, validate_input coverage check, prepare_features correct order DataFrame, infer real model inference proba calibrated isotonic level low<0.25 moderate<0.5 elevated<0.75 high>=0.75 signal pcos_associated_risk vs elevated, uncertainty model_confidence data_quality coverage validation ROC AUC, explanation real importances not invented, fallback Explanation unavailable if no SHAP

### Deterministic Research Logic

- src/disease_modules/pcos.py CYCLE_W 1.20 METABOLIC_W 0.90 AUTONOMIC_W 0.60 SLEEP_W 0.50 CIRCADIAN_W 0.50 TEMPERATURE_W 0.35 GLUCOSE_W 0.35 ACTIVITY_W 0.30 BP_W 0.20 INTERCEPT -3.0 CYCLE_NEUTRAL 15.0 sigmoid risk, not real joblib, research risk signal wearable+clinical, preserved separate purpose
- Confidence from coverage and quality 0.5*coverage+0.2*optional+0.3*quality not hard-coded 0.75

### Model Registry

Each model must record: model_id, name, version, dataset, dataset_version, training date, features, target, preprocessing, validation method, metrics, limitations, software version, status

Statuses: EXPERIMENTAL, RESEARCH, VALIDATION_PENDING, DEMO, RETIRED

Do not call clinically validated without evidence.

Current: disease_models/chrono_pcos/manifest.py, src/endo_twin/models/model_registry.py ModelRegistry with general_models and disease_models, register_disease_model, list_disease_models, get_registry_info, analyze_with_disease_model, global registry instance GLOBAL_MODEL_REGISTRY

- General models: personal_baseline, longitudinal, physiological_state, signal_processing, feature_extraction, chrono_metabolic
- Disease models: CHRONO-PCOS first implemented, Future Cardio/Sleep concept extensible TEST4 PASS

Model transparency: name/version/input/data quality/confidence/features/limitations never hide uncertainty/manufacture confidence/training results.

### Hard-Coded Investigation

Search entire repo for hard-coded predictions, confidence, static results, placeholder scores, fake explanations, simulated inference, UI-only AI outputs, model outputs disconnected from artifacts.

Any value hard-coded classified as REAL, DETERMINISTIC, DEMO, SIMULATED, PLACEHOLDER.

Remove hard-coded values from real inference paths, do not show fake confidence such as 0.75 merely because confidence field expected.

Found: src/endo_twin/uncertainty/general_uncertainty.py pcos_risk 0.75 example, endo_twin/longitudinal/longitudinal_engine.py confidence 0.75 demo timeline, database/endo_twin_database.py confidence 0.75 data quality 0.85 DEMO_DATA clearly labeled DEMO-001,002,003, etc.

Fixed: Labeled EXAMPLE_DATA/DEMO_DATA where appropriate, real path uses computed confidence and calibrated probability, no hard-coded 0.75 in real_pcos_model_adapter.py.

### Model Diagnostics

Investigate why models may underperform: feature mismatch, feature order, preprocessing mismatch, scaling mismatch, leakage, patient-level leakage, temporal leakage, duplicate records, class imbalance, synthetic-data dependence, label quality, dataset shift, calibration, target formulation, missing features, training/inference inconsistency

Created docs/ai_ml/MODEL_DIAGNOSTIC_REPORT.md with real metrics, feature mismatch, hard-coded investigation, explainability, uncertainty, recommendations.

### Explainability

Every prediction should expose model, version, input, features, output, uncertainty, data quality, provenance, limitations, use SHAP permutation importance model-specific attribution counterfactual, only show explanations that actually correspond to model.

Current: Real adapter drivers from real feature_importances sorted top 3 actual influence not plausible medical explanations, Explanation unavailable if no SHAP not invented.

Enhance with SHAP waterfall like HDT and PCOS_project.

### Ultrasound

Modular Image→Validation→Preprocessing→Quality→Feature Extraction→Segmentation/Model→Uncertainty→Explanation→CHRONO-PCOS, never present experimental imaging as clinically validated diagnosis.

Current: disease_models/chrono_pcos/ultrasound/pcos_ultrasound.py, UltrasoundViewer quality UNKNOWN by design unless computed, provenance distinction, if insufficient state insufficient never fabricate.

### Performance

- Model loading 2386 ms bottleneck, real inference 993 ms moderate, deterministic 0.3 ms extremely fast
- Optimize via background preload, caching, array not DataFrame, lazy deterministic first then real
- Model preloading at app startup background, not on first inference
- Result caching, incremental

See docs/performance/PERFORMANCE_REPORT.md real measurements not fabricated.

### Safety

Research / risk-screening output — not a medical diagnosis, clinical validation NOT ESTABLISHED, engineering validation only, not replacement for professional evaluation, avoid definitive diagnosis/meds/treatment orders/unsupported claims, encourage professional consult.
