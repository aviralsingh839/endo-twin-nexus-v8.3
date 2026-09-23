# ENDO-TWIN V8.6.1 — Live Sensor Processing

## Acquisition

The workstation live path is desktop/workstation_runtime.py.

Arduino $CP3 packets (and legacy $CP/$CP2 frames) are accepted only after the existing parser and XOR CRC check succeed.

The canonical firmware sends approximately one workstation packet every 50 ms (about 20 packets/s). This is the PC transport rate; it is not automatically the same as an internal sensor sampling rate.

## Processing path

Packet → CRC/decode → channel checks → filtering → artifact rejection → features → quality → provenance → workstation

### PPG
- DC blocker and exponential smoothing.
- Robust median-centred peak detection.
- Physiological refractory interval.
- IBI range filtering and local-median artifact rejection.
- HR can be withheld at lower quality.
- RMSSD/SDNN require a larger clean interval set and a stronger PPG quality gate.
- PPG-derived variability is labelled as a derived pulse-rate-variability feature, not an ECG measurement.

### SpO2
The existing red/IR ratio-of-ratios estimator is educational/research-only. It is withheld below its quality gate and is not a clinically calibrated oxygen-saturation measurement.

### IMU
Acceleration and gyroscope signals feed the activity/motion processor. Motion is also used as a context signal for PPG quality.

### Skin temperature
The probe channel is slow by design (1 Hz conversion) and is not oversampled per packet.

### Temperature
Temperature is processed at approximately 1 Hz and range/validity-gated before a feature is exposed.

## Quality

Quality and provenance are separate.

Examples:
- a live PPG sample may be MEASURED but poor quality;
- HR/HRV may be DERIVED and withheld because the source is unusable;
- a disease result may be MODEL-INFERRED only after its evidence gate passes.

Firmware status bits are surfaced for absent/saturated/error states.

## Update cadence

The processing layer can receive approximately 20 packets/s, while the feature layer emits at a slower cadence for UI stability. This prevents unnecessary repeated model/UI work and keeps chart histories bounded.

## Performance improvements in V8.6.1

- NumPy vectorized peak candidates instead of scanning the waveform entirely in Python.
- Bounded deques for signal history and chart data.
- Slower temperature/environment channels are not oversampled.
- Feature processing remains off the GUI thread through the reader/session architecture.
- Quality gates short-circuit downstream outputs when source evidence is inadequate.

## Scientific accuracy boundary

Engineering improvements can reduce software artefacts and improve reproducibility, but they do not establish clinical accuracy.

A future clinical validation study would need reference-device comparison, pre-specified protocols, participant-level separation, independent validation, calibration, uncertainty reporting, subgroup analysis, and appropriate statistical confidence intervals.

## References

PPG/ECG HRV agreement and uncertainty:
- https://pubmed.ncbi.nlm.nih.gov/29668452/
- https://pubmed.ncbi.nlm.nih.gov/39517723/
- https://pubmed.ncbi.nlm.nih.gov/42655500/
