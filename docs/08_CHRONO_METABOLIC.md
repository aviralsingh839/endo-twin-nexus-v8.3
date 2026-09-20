# 08 - Chrono-Metabolic Fingerprinting - V8.3+

## Definition
Combines circadian, autonomic, variability, activity, temp, metabolic, longitudinal into fingerprint with clear provenance and explainability.

## Components

### Circadian
- Sleep-wake estimation from HR/HRV 24h pattern
- Category: experimental_research, model-inferred
- Quality: PPG quality
- Source: PPG-derived sleep-wake estimation
- Limitations: not polysomnography, requires validation
- Explainability: estimated from HR/HRV circadian variation, 24h pattern

### Autonomic
- HRV RMSSD, GSR
- Category: derived_feature + experimental_research
- Quality: HRV quality, GSR quality
- Source: PPG-derived HRV time-domain RMSSD, GSR tonic/phasic
- Limitations: PPG-derived HRV less accurate than ECG, motion artifacts
- Explainability: RMSSD reflects parasympathetic activity

### Variability
- HRV metrics, activity variability
- Category: derived_feature
- Quality: PPG quality
- Source: PPG HR variability
- Limitations: requires good quality PPG
- Explainability: variability metrics from HR time series

### Activity
- MPU6050 accelerometer
- Category: established_measurement
- Quality: motion quality 0.8
- Source: MPU6050 accelerometer activity counts
- Limitations: wrist activity not whole-body calorimetry
- Explainability: accelerometer magnitude classified sedentary/light/moderate

### Temperature
- DS18B20 skin temp
- Category: established_measurement
- Quality: temp quality 0.8
- Source: DS18B20 skin temperature sensor
- Limitations: skin temp not core temp, affected by environment
- Explainability: direct temperature measurement circadian variation

### Metabolic
- Multimodal combination HR, HRV, activity, temp, GSR
- Category: experimental_research
- Quality: min quality scores
- Source: multimodal combination hypothesized relate to metabolic regulation
- Limitations: experimental not clinical metabolic measurement requires validation
- Explainability: research combination autonomic, activity, temperature patterns

### Longitudinal
- Personal baseline deviation
- Category: experimental_research
- Quality: 0.6 requires history
- Source: personal baseline comparison longitudinal tracking
- Limitations: requires sufficient history baseline calibration needed
- Explainability: deviation from personal baseline not population norm

## Implementation
ChronoMetabolicFingerprint class in core/chrono_metabolic/__init__.py
- add_component, build_from_features(features, quality_scores), get_summary_text understandable language

## Output
Fingerprint dict version, components (name, value, category, quality, confidence, source, limitations, explainability), disclaimer research/experimental not diagnosis, provenance V8.3+.

## Disclaimer
Research / experimental chrono-metabolic fingerprint - not a medical diagnosis, requires clinical evaluation.
