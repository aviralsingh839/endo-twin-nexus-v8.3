# VALIDATION - ENDO-TWIN V8.3+

Date: 2026-09-19
Version: 8.3+
Status: IMPLEMENTED

## Validation Strategy

- CV: 5-fold stratified-group patient-level split, GroupKFold by subject for PPG quality
- No leakage: patient-level split, synthetic excluded, leaky columns Pregnant/Abortions/HCG dropped
- Honest metrics: ROC AUC 0.9594 not 100%, ROC AUC 0.624 low disclosed
- Engineering validation only, clinical validation NOT ESTABLISHED

## Tests

- tests/test_model_loading.py: Real artifact loading verified, dict model feature_names target meta, calibrated probability not hard-coded
- tests/test_pcos_model.py: Inference works, output low/moderate/high, confidence from model not hard-coded
- tests/test_ppg_quality.py: Quality model loading, 15 features, blended 40%
- tests/test_determinism.py: Deterministic path 0.3 ms, confidence computed not hard-coded

## Isolation

- tests/test_cross_patient_isolation.py: DEMO-001/002/003 HR 72/78/68 different, DB-backed, no leakage
- tests/test_architecture_isolation.py: Core no direct PCOS import, dynamic importlib, general dashboard no PCOS knowledge

## What We Do NOT Claim

- Clinical validation NOT ESTABLISHED
- Not diagnosis, research risk signal
- No 100% accuracy, no fake confidence
- No clinical superiority, regulatory approval
- Encourage professional consultation

## Future Validation

- Separate test set not just CV
- Prospective data
- Clinical collaboration
- Dataset versioning DVC
- Experiment tracking MLflow Research Lab
