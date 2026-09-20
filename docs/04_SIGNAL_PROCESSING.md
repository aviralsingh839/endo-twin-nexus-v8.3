# 04 - Signal Processing - V8.3+

## Overview
Preserves src/signal_processing/*

## Filtering
- PPG: bandpass 0.5-4 Hz for HR, lowpass for baseline
- Motion: lowpass for activity
- Temp: median filter for outliers
- GSR: lowpass tonic, highpass phasic

## Baseline Removal
- PPG baseline drift removal
- GSR tonic/phasic separation
- Temp baseline

## Artifact Detection
- Motion artifact: MPU6050 correlation with PPG
- PPG artifact: amplitude, HR outlier
- GSR artifact: sudden jumps
- Quality scores 0-1 per channel
- Source labeling

## Missing Handling
- Short gaps: interpolation with quality penalty
- Long gaps: mark missing, not fabricate
- Graceful handling unavailable/disconnected/noisy/missing/invalid/serial failure/partial

## Quality Control
SensorQualityControl:
- Channel quality per timestamp
- Overall session quality
- Artifact flags
- Reason codes

## Feature Extraction
RealtimeFeatureExtractor:
- HR bpm, resting HR
- HRV RMSSD, SDNN, pNN50 (derived)
- GSR tonic, phasic per min
- Motion index, activity level (established)
- Skin temp C, room temp C, temp slope (established)
- Pulse amplitude, SpO2
- Quality scores

Distinguishes established/derived/experimental/ML/clinical, explainability.

## Why?
Scientific clarity, reproducibility, explainability, honest limitations.
