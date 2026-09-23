# 25 - Research Methodology - V8.3+

## Hypothesis
Chrono-metabolic fingerprinting combining circadian, autonomic, variability, activity, temp, metabolic, longitudinal may show research signals related to PCOS-associated patterns, but requires clinical validation, not diagnosis.

## Methodology

### Physiological Sensing
- Hardware: Nano pod MAX30102 PPG HR SpO2 pulse amplitude MPU6050 motion ax ay az gx gy gz motion index activity level DS18B20 skin temp room temp temp slope 
- Sampling 20Hz $CP3 packet CRC XOR
- Lab hub Mega ECG mic FSR BME280 OLED relay mode expanded validation
- Quality: PPG quality affected motion pressure skin tone ambient light, HRV from PPG less accurate than ECG, skin temp not core temp affected environment, skin temperature affected by probe contact
- Failure handling: sensor unavailable/disconnected/noisy/missing/invalid/serial failure/partial graceful handling notify user demo mode

### Signal Processing
- Filtering: PPG bandpass 0.5-4Hz HR lowpass baseline, motion lowpass activity, temp median outliers, 
- Baseline removal: PPG baseline drift,  separation, temp baseline
- Artifact detection: motion artifact MPU6050 correlation PPG, PPG artifact amplitude HR outlier, temp sudden jumps, quality scores 0-1 per channel, source labeling
- Missing handling: short gaps interpolation quality penalty, long gaps mark missing not fabricate
- Quality control: SensorQualityControl channel quality per timestamp overall session quality artifact flags reason codes

### Feature Engineering
- Established: HR bpm MAX30102 MEASURED, skin temp C DS18B20 MEASURED, motion MPU6050 MEASURED,  MEASURED
- Derived: HRV RMSSD SDNN pNN50 derived limitations PPG less accurate than ECG, resting HR derived low activity, , activity level classified derived, temp slope derivative derived, pulse amplitude SpO2 IR/RED ratio derived
- Experimental: circadian sleep-wake estimation HR/HRV 24h pattern model-inferred experimental limitations not polysomnography, autonomic HRV-based experimental, metabolic multimodal HR HRV activity temp hypothesized metabolic regulation experimental not clinical, chrono-metabolic fingerprint combination experimental not diagnosis, longitudinal trend personal baseline deviation experimental requires history
- ML predictions: PCOS associated risk PCOSModule v8.3.0 low/moderate/high NOT diagnosis clinical validation NOT ESTABLISHED, sleep circadian disruption SleepModule, cardiometabolic risk CardiometabolicModule, autonomic regulation AutonomicModule, model name/version/input/data quality/confidence/features/limitations never hide uncertainty
- Clinical interpretation: requires professional evaluation Rotterdam criteria not provided by system research risk-screening only
- Baseline calibration: BaselineCalibrator personal baseline population not used for diagnosis longitudinal tracking deviation personal baseline
- Explainability: each feature source quality confidence if ML limitations explainability text

### AI/ML Models
- Modules: PCOSModule SleepModule CardiometabolicModule AutonomicModule risk signals only versioned confidence limitations
- Training: ModelTrainer input features quality scores data public PCOS_data.csv 541 rows wrist_ppg synthetic cohort 10 subjects 30 days 6 scenarios 60 days split subject-level not row-level avoid leakage validation 12 categories engineering vs clinical separation no fabricated accuracy state if insufficient
- Evaluation: ModelEvaluator metrics accuracy precision recall F1 AUC classification MAE regression never fabricate percentages if insufficient state insufficient model transparency
- Fusion: MultimodalFusion combines module outputs confidence weighted quality no hard-coded fake confidence
- Explainability: ShapExplainer feature drivers SHAP values understandable language
- Limitations: engineering validation only clinical validation NOT ESTABLISHED small datasets synthetic labeled SYNTHETIC not replacement clinical evaluation confidence model output not clinical certainty

### Ultrasound
- Pipeline: loading image path format size check, preprocessing resize normalize denoise, quality checks blur exposure anatomy visibility quality score UNKNOWN by design unless computed provenance CLINICALLY-ENTERED vs IMAGE-DERIVED, segmentation cyst detection morphology if model, inference requires trained model if insufficient state insufficient never fabricate percentages confidence None unless computed, visualization overlay confidence map, storage ultrasound_records table patient_id image_path cyst_size_mm volume_cc morphology quality source confidence label REAL/SYNTHETIC/DEMO provenance
- Quality gate UNKNOWN by design provenance distinction
- Training: need clinical ultrasound dataset not synthetic as clinical never label synthetic as clinical never fabricate patient records
- Evaluation: if model exists evaluate held-out clinical data if not state model accuracy not established no 100% accurate claims
- Storage: local SQLite image path not BLOB performance label REAL vs SYNTHETIC
- Safety: ultrasound analysis research not diagnosis requires clinical evaluation Rotterdam requires ultrasound + clinical

### Chrono-Metabolic Fingerprinting
- Definition: combines circadian autonomic variability activity temp metabolic longitudinal into fingerprint with clear provenance explainability
- Components: circadian sleep-wake estimation experimental research quality PPG source PPG-derived limitations not polysomnography explainability HR/HRV circadian variation 24h, autonomic HRV RMSSD derived+experimental quality HRV source PPG-derived RMSSD  limitations PPG less accurate than ECG motion artifacts explainability RMSSD parasympathetic, variability HRV activity derived quality PPG source PPG HR variability limitations requires good quality PPG explainability variability metrics, activity MPU6050 established measurement quality motion 0.8 source MPU6050 activity counts limitations wrist not whole-body calorimetry explainability accelerometer magnitude sedentary/light/moderate, temperature DS18B20 established quality temp 0.8 source DS18B20 limitations skin not core affected environment explainability direct circadian variation, metabolic multimodal HR HRV activity temp experimental quality min quality source multimodal hypothesized metabolic limitations experimental not clinical requires validation explainability research combination autonomic activity temperature, longitudinal personal baseline deviation experimental quality 0.6 requires history source personal baseline comparison limitations requires sufficient history baseline calibration explainability deviation personal baseline not population norm
- Implementation: ChronoMetabolicFingerprint class add_component build_from_features features quality_scores get_summary_text understandable language
- Output: fingerprint dict version components name value category quality confidence source limitations explainability disclaimer research/experimental not diagnosis provenance V8.3+
- Why distinguish established/derived/experimental/ML/clinical: scientific integrity honest limitations explainability avoid false claims

### Local Database, Patient Android, Doctor PC, Doctor Android, Care Discovery, Public Website, Security, Offline-First, Testing, Safety Ethics
See docs 12-23 for detailed methodology per component.

### Why This Research Matters
Class 11 research innovation demonstrating physiological sensing signal processing AI/ML for health research local-first privacy patient accessibility doctor review scientific honesty limitations provenance explainability. One coherent ecosystem common terminology/data model/scientific foundation/identity/UI/safety language polished Class 11 research/innovation scientifically honest. Sense•Model•Predict•Personalize•Connect. Research / risk-screening output — not a medical diagnosis.
