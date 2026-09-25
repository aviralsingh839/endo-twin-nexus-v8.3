# 05 - Feature Engineering - V8.3+

## Established Measurements (Directly Measured)
- HR bpm: Generic Analog Pulse Sensor PPG (single-channel analog waveform) peak detection, quality 0-1, source MEASURED
- Skin temp C: DS18B20 direct, quality, source MEASURED
- Motion: MPU6050 accelerometer magnitude, activity level, source MEASURED
- GSR raw: direct, source MEASURED

## Derived Features (Calculated)
- HRV RMSSD ms: from HR time series, quality, source DERIVED, limitations PPG-derived less accurate than ECG
- HRV SDNN, pNN50: derived
- Resting HR: derived low activity
- GSR tonic: lowpass filtered, derived
- GSR phasic per min: highpass, derived
- Activity level %: classified from motion, derived
- Temp slope C per min: derivative, derived
- Pulse amplitude, SpO2: IR/RED ratio, derived

## Experimental Research Signals
- Circadian rhythm: sleep-wake estimation HR/HRV 24h pattern, model-inferred, experimental, limitations not polysomnography
- Autonomic regulation: HRV+GSR combination, experimental
- Metabolic signal: multimodal HR, HRV, activity, temp, GSR hypothesized metabolic regulation, experimental, not clinical
- Chrono-metabolic fingerprint: combination circadian, autonomic, variability, activity, temp, metabolic, longitudinal, experimental, not diagnosis
- Longitudinal trend: deviation from personal baseline, experimental, requires history

## ML Predictions
- PCOS associated risk: PCOSModule v8.3.0 low/moderate/high, NOT diagnosis, clinical validation NOT ESTABLISHED
- Sleep circadian disruption: SleepModule
- Cardiometabolic risk signal: CardiometabolicModule
- Autonomic regulation signal: AutonomicModule
All ML: model name/version, input data, data quality, confidence, features, limitations, never hide uncertainty.

## Clinical Interpretation
Requires professional evaluation, Rotterdam criteria, not provided by system, research/risk-screening only.

## Baseline Calibration
BaselineCalibrator: personal baseline, population not used for diagnosis, longitudinal tracking, deviation personal baseline.

## Explainability
Each feature: source, quality, confidence if ML, limitations, explainability text. Example: RMSSD reflects parasympathetic activity, lower values may indicate autonomic dysregulation research signal.


## V8.8 Analog Pulse Sensor migration

The current wearable build can use the generic analog Pulse Sensor module shown in the project hardware reference image instead of the MAX3010x optical PPG. The module is a single-channel analog pulse waveform source: SIG connects to an ADC-capable GPIO, VCC to the sensor's supported supply, and GND to common ground. ENDO-TWIN keeps the existing $CP2 transport so the rest of the desktop/BLE pipeline remains compatible. The primary waveform is carried in the existing `ir` slot for transport compatibility and is explicitly marked as `ANALOG_PULSE`/status bit 12. The `red` field is `-1` because there is no optical red channel.

The processing layer continues to support heart-rate and pulse-timing/HRV-style analysis from the waveform, with motion-aware quality scoring. It must not estimate SpO2 from this single-channel analog sensor. This hardware is suitable for an educational research prototype, not for diagnosis or clinical measurement.
