# Synthetic Longitudinal Scenarios - CHRONO-TWIN NEXUS V8.3

All data in this folder is SYNTHETIC - clearly labelled.
Never presented as real clinical data.

## Scenarios

### scenario_1_stable
- Type: stable
- Expected: LOW CHANGE SIGNAL
- Description: Physiology stays within normal personal variation.

### scenario_2_gradual
- Type: gradual
- Expected: EARLY CHANGE SIGNAL
- Description: A parameter slowly moves away from baseline.

### scenario_3_persistent
- Type: persistent
- Expected: PERSISTENT MULTIMODAL SIGNAL
- Description: Multiple related signals remain abnormal for extended period.

### scenario_4_temporary
- Type: temporary
- Expected: TEMPORARY EVENT, not disease signal
- Description: Signals change briefly and return to baseline.

### scenario_5_sensor_failure
- Type: sensor_failure
- Expected: LOW SENSOR CONFIDENCE
- Description: One sensor stops producing valid data. Must not be interpreted as physiological abnormality.

### scenario_6_recovery
- Type: recovery
- Expected: RECOVERY TREND
- Description: Previously abnormal pattern gradually returns toward baseline.

## Usage

Each file contains 60 days of 24 samples/day with realistic:
- individual baselines
- circadian modulation
- sensor noise, missing data, motion artifacts
- scenario-specific deviations
