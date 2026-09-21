# Sensor Calibration Guide

## Generic protocol
1. POWER TEST
2. CONNECTION TEST
3. RAW SIGNAL TEST
4. QUALITY TEST
5. CALIBRATION
6. KNOWN-GOOD REFERENCE
7. STRESS TEST
8. LONG-DURATION TEST
9. DATA STORAGE TEST

### MAX30102
Check stable contact, raw waveform continuity, sample timing and saturation/outlier behavior. Compare heart-rate output only against a suitable reference for research validation.

### MPU6050
Check zero/known-orientation behavior, axis direction, sample timing and drift. Record firmware scaling.

### DS18B20
Use a known reference thermometer for a bounded temperature-comparison experiment. Record environmental conditions and warm-up time.

### GSR
Document electrode placement, contact condition, module gain/scale and baseline stabilization time. GSR is sensitive to contact and environment.

### ECG
Follow the exact module manufacturer's test procedure and use appropriate electrical safety precautions.

Calibration results are device/setup-specific and do not constitute clinical validation.
