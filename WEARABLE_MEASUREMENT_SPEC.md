# ENDO-TWIN Wearable Measurement Specification

## PPG
Sensor: MAX30102
Raw signal: optical PPG channels
Sampling: prototype target may use the repository's existing 20 Hz acquisition profile; firmware must advertise actual rate.
Unit: ADC/raw units
Processing: quality gate → cleaning/filtering → pulse peak detection
Provenance: MEASURED only when actually acquired; otherwise DEMO_DATA/UNKNOWN
Limitations: motion, contact, sensor placement and skin/tissue optical properties affect quality.

## Heart rate
Source: PPG or ECG derived beat timing
Unit: bpm
Quality: inherited from source signal + beat plausibility checks

## IBI/RR
Source: detected beats from PPG/ECG
Unit: ms
Quality: beat-to-beat validity and source quality

## HRV
Source: validated IBI/RR sequence
Features: RMSSD, SDNN and, when suitable data are available, frequency/nonlinear/Poincaré measures
Processing: remove or flag invalid intervals rather than fabricating beats
Limitations: pulse-derived HRV has different error characteristics from ECG-derived HRV.

## SpO2
Source: MAX30102 red/IR channels if the actual firmware supports it
Unit: %
Status: model/algorithm-specific; do not display a number unless the signal and algorithm are available.

## GSR/EDA
Source: GSR module
Raw: analog conductance-related signal
Derived: tonic/phasic components where algorithm supports them
Quality: contact/stability/noise checks

## Skin temperature
Source: DS18B20
Unit: °C
Use: temperature trend
Limitation: probe temperature is not automatically core body temperature.

## Motion/activity
Source: MPU6050
Raw: ax/ay/az + gx/gy/gz
Derived: motion index/activity features
Quality: sample-rate validity and sensor availability

## ECG
Source: compatible ECG module
Raw: ECG waveform
Derived: beat timing and HRV only after signal-quality validation
Safety: electrical arrangement must be reviewed for the exact hardware.

## Respiration / sleep
Only compute when an actual supported sensor/algorithm provides sufficient evidence. Otherwise return UNKNOWN or INSUFFICIENT_DATA rather than estimating a value without a validated basis.

## Common metadata contract
Every stored measurement/feature should include patient_id, timestamp, source, sensor, quality, provenance and algorithm_version where applicable.
