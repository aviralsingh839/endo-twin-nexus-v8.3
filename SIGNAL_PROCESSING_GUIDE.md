# Signal Processing Guide

Target pipeline:
SENSOR → DEVICE DRIVER → RAW PACKET → PACKET VALIDATION → TIMESTAMP → SIGNAL BUFFER → QUALITY CONTROL → FILTERING → FEATURE EXTRACTION → BASELINE → LONGITUDINAL → FUSION → MODEL → REPORT

## Current preservation rule
Existing PPG, ECG, HRV, GSR, IMU, temperature and SpO2 processors remain in place. NeuroKit2 and pyHRV are adapters, not a forced replacement.

## Quality contract
Features carry patient_id, timestamp, source, sensor, quality, provenance and algorithm_version where available. Missing/invalid data remain explicit; interpolation is bounded and quality-penalized.
