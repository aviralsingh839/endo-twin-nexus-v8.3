# RESEARCH LAB APP

Date: 2026-09-19
Version: 8.3+
Status: IMPLEMENTED

## Purpose

Research experimentation, model training, validation, benchmarking, signal processing experimentation, dataset exploration.

Not clinical, research only.

## Architecture

- apps/research_lab/ (if exists) + science/ + scripts/
- PySide6 scientific core NumPy Pandas PySerial scikit-learn
- START.sh option 4 Research Lab, option 5 Diagnostics

## Features

- Data loading: PhysioNet Wrist PPG During Exercise 19 rec 8 subj 903 windows, PCOS_data_without_infertility.xlsx 541 rows, synthetic 10 subjects 30 days 6 scenarios 60 days wrist_ppg SYNTHETIC clearly labelled
- Signal processing experimentation: filtering artifact handling HR HRV quality
- Feature extraction: tsfresh automatic extraction 100s features controlled selection NOT production per reference audit
- Baseline modelling: rolling robust mean/median MAD confidence drift missingness time-of-day
- Longitudinal modelling: hourly daily weekly monthly cycle 6 scenarios
- Model training: pcos_risk_model 17M CalibratedCV VotingClassifier 37 feats 541 rows ROC 0.9594, ppg_quality_model 5.1M 15 feats ROC 0.624 honest low
- Model registry: name version input data quality confidence features limitations status EXPERIMENTAL RESEARCH VALIDATION_PENDING DEMO RETIRED
- Validation: patient-level split GroupKFold dedup no leakage
- Explainability: SHAP real only feature importance
- Uncertainty: confidence quality provenance visible
- Provenance: MEASURED CLINICAL_ENTRY DERIVED IMAGE_DERIVED MODEL_INFERRED DEMO SIMULATED UNKNOWN
- Ultrasound: preprocessing segmentation augmentation MONAI UNETR VISTA-3D, viewer UX OHIF, conceptually 3D Slicer
- Benchmarking: NeuroKit2 simulate testing, WFDB PhysioNet loading, PyPhysio caching workflows, tsfresh feature discovery controlled, PyHealth lightweight runtime, MONAI ultrasound preprocessing segmentation, MLflow experiment tracking versioning lineage, DVC dataset versioning lineage reproducible pipelines
- Performance benchmarking: real measurements not fabricated

## Datasets

- PCOS_data_without_infertility.xlsx 541 rows clinical lab values
- Wrist PPG During Exercise 19 recordings 8 subjects 903 windows usable_rate 0.3477
- Synthetic 10 subjects 30 days 6 scenarios 60 days wrist_ppg SYNTHETIC clearly labelled never label synthetic as clinical never mix REAL/SYNTHETIC silently never fabricate patient records

## Testing

- tests/test_research_lab.py (if exists): data loading signal processing feature extraction baseline longitudinal model loading inference
- tests/test_performance.py: Real benchmarks 267.9ms import 61.6ms DB 2.1ms patient 0.1ms search 2386ms model load bottleneck 0.3ms deterministic 993.5ms real 22.2ms dashboard
- scripts/diagnostics/project_health.sh: PASS 14 WARN 2 FAIL 0 evidence-based

## Benchmark References

- NeuroKit2: BENCHMARK ONLY simulate testing
- WFDB: ADOPT Research Lab PhysioNet Wrist PPG 19 recordings 903 windows
- PyPhysio: ADOPT caching workflows performance
- HRVAnalysis: BENCHMARK ONLY
- tsfresh: ADOPT Research Lab feature discovery controlled
- PyHealth: ADOPT Research Lab lightweight runtime
- MONAI: ADOPT ultrasound preprocessing segmentation UNETR
- MONAI Deploy: ADAPT DAGs lightweight
- OHIF: ADOPT viewer UX professional
- 3D Slicer: ADOPT conceptually Research Lab
- MLflow: ADAPT experiment tracking versioning lineage Research Lab no bloat
- DVC: ADAPT dataset versioning lineage reproducible pipelines
- Synthea: ADOPT synthetic populations SYNTHETIC/DEMO/SIMULATED stress testing
- Open mHealth: ADOPT standardized schemas prevent arbitrary formats
- Health Samples: ADOPT Health Connect official patterns prefer existing data
- Gadgetbridge: BENCHMARK ONLY GPL architectural study vendor independence

License compliance: MIT NeuroKit2 WFDB tsfresh Health Samples Open mHealth Synthea permissive attribution, Apache-2.0 MONAI Deploy MLflow DVC permissive, GPL-3.0 Gadgetbridge reimplement independently own ENDO-TWIN identity
