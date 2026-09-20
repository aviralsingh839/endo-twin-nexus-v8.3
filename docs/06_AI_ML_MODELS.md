# 06 - AI/ML Models - V8.3+

## Modules
- PCOSModule v8.3.0: pcos_associated_risk low/moderate/high, NOT diagnosis, clinical validation NOT ESTABLISHED, engineering validation only
- SleepModule v8.3.0: circadian_disruption_pattern, sleep regularity, model-inferred
- CardiometabolicModule v8.3.0: cardiometabolic_risk_signal
- AutonomicModule v8.3.0: autonomic_regulation_signal

## Training
ModelTrainer:
- Input: features from RealtimeFeatureExtractor, quality scores
- Data: public PCOS_data.csv 541 rows, wrist_ppg synthetic cohort 10 subjects 30 days 6 scenarios 60 days
- Split: subject-level split, not row-level, avoid leakage
- Validation: 12 categories engineering vs clinical separation
- No fabricated accuracy, state if insufficient

## Evaluation
ModelEvaluator:
- Metrics: accuracy, precision, recall, F1, AUC if classification, MAE if regression
- Never fabricate percentages
- If insufficient data: state insufficient
- Model transparency: name/version/input/data quality/confidence/features/limitations

## Fusion
MultimodalFusion:
- Combines module outputs
- Confidence weighted by quality
- No hard-coded fake confidence

## Explainability
ShapExplainer:
- Feature drivers
- SHAP values if available
- Understandable language

## Limitations
- Engineering validation only, clinical validation NOT ESTABLISHED
- Small datasets, synthetic labeled SYNTHETIC
- Not replacement for clinical evaluation
- Confidence is model output, not clinical certainty

## Why?
Science/clarity/reproducibility/explainability/honest limitations over enterprise architecture, keep offline.
