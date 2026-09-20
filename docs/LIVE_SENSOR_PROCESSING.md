# ENDO-TWIN V8.6 — Live Sensor Processing

The canonical workstation live path is `desktop/workstation_runtime.py`.

## Acquisition
The reader accepts the existing Arduino `$CP` / `$CP2` protocol and requires a valid XOR CRC before emitting a sample to the processing layer.

## Processing
For each accepted packet:
1. PPG samples are filtered and pulse peaks are detected.
2. Beat intervals are cleaned before HRV features are calculated.
3. SpO2 is computed by the existing dual-channel research estimator and withheld when quality is insufficient.
4. IMU acceleration and gyro are converted into a motion/activity index.
5. GSR produces tonic level and phasic event rate.
6. Temperature is range-checked and a recent slope/stability estimate is calculated.
7. Firmware status flags and channel metrics contribute to a combined quality gate.
8. HR/HRV are withheld when the PPG channel is unusable.

## Provenance
- Raw live sensor channels: **MEASURED**.
- HR/HRV/activity/SpO2/GSR features: **DERIVED**.
- Disease-module outputs: **MODEL-INFERRED**.
- Demonstration stream: **DEMO_DATA**.

## Sampling
The canonical firmware packet interval is about 50 ms (20 Hz). Desktop PPG/IMU processors therefore operate on the received 20 Hz packet stream. The MAX30102's internal sampling configuration is not treated as the PC acquisition rate.

## Accuracy boundary
Quality gates can reject poor or missing measurements, but they cannot make a low-cost sensor clinically validated. Clinical use would require controlled protocols, calibration, reference-device comparison, labelled datasets, patient-level validation and independent clinical research.
