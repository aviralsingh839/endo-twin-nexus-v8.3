# SIGNAL PROCESSING - ENDO-TWIN V8.3+

Date: 2026-09-19
Version: 8.3+
Status: IMPLEMENTED

## Pipeline

```
Raw PPG
 ↓
Validation
 ↓
Signal quality
 ↓
Filtering
 ↓
Artifact handling
 ↓
Peak detection
 ↓
IBI
 ↓
HR
 ↓
HRV
 ↓
Feature extraction
```

## Current Implementation

- src/signal_processing/ ppg.py ecg.py gsr.py hrv.py imu.py spo2.py temperature.py filters.py
- Filtering: bandpass 0.5-4Hz PPG, lowpass baseline, motion lowpass temp, median GSR, lowpass tonic, highpass phasic
- Baseline removal, artifact detection motion MPU6050 correlation PPG amplitude HR outlier GSR jumps, missing handling short gaps interpolation quality penalty long gaps mark missing not fabricate, quality control 0-1 per channel
- PPG: filtering, peak detection, HR, HRV, quality
- ECG: ecg.py
- GSR: gsr.py
- HRV: hrv.py RMSSD SDNN pNN50, PPG-derived HRV less accurate than ECG limitations documented
- IMU: imu.py MPU6050 motion
- SpO2: spo2.py generic analog Pulse Sensor
- Temperature: temperature.py DS18B20
- Filters: filters.py baseline calibration filtering
- Quality: quality.py ppg_quality heuristic + ppg_quality_model 5.1M 15 features blended 40%, artifact handling missing handling reconnection

## Benchmark Against References

- NeuroKit2: Simulate physiological signals, filtering, detrending, HRV time domain RMSSD MeanNN SDNN frequency domain ULF VLF LF HF, complexity entropy fractal, ECG delineation P Q S T, bio_process bio_analyze 2 lines code, MIT, field tested unit tested. Benchmark: Compare accuracy robustness speed edge cases dependencies test coverage scientific appropriateness, keep better implementation. Our deterministic inference 0.3 ms extremely fast vs NeuroKit2 may be slower - keep fast path. Use NeuroKit2 simulate artificial signals for testing in Research Lab.
- E2E-PPG: End-to-end pipeline filtering→SQA→reconstruction→peak→IBI→HR/HRV, one-class SVM SQA Reliable/Unreliable, GAN reconstruction, MIT, IEEE BIBM 2023. Benchmark: Enhance quality.py with SQA concepts, filtering, artifact handling, reconstruction experimental, ensure pipeline Sensor→Validation→Signal→Quality→Feature→Baseline→Longitudinal→Fusion→Disease Model matches.
- HRVAnalysis: RR/NN cleanup, outlier handling, ectopic-beat handling, HRV time/frequency. Benchmark: Compare our hrv.py RMSSD SDNN pNN50, keep better.
- WFDB: Physiological signal formats, biomedical signal loading, annotations, waveform datasets, PhysioNet workflows, used for Wrist PPG During Exercise dataset in ppg_quality_model. Use in Research Lab for loading PhysioNet data.

Record accuracy where valid reference exists, robustness, runtime, failure behaviour, dependencies. Keep scientifically strongest implementation. Do NOT replace existing science without comparative evidence.

## Performance

- Import core 267.9 ms, deterministic inference 0.3 ms extremely fast, real inference 993 ms moderate
- Use caching, memoization, incremental updates, indexed queries, batch processing, background workers, vectorized numerical operations, ring buffers, streaming, lazy loading, async model inference, model preloading, result caching
- See docs/performance/PERFORMANCE_REPORT.md real measurements not fabricated
