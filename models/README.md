# Models - CHRONO-TWIN NEXUS V8.3

## Current Models

### Transparent Fallback Equations (Research Prototype)

- **PCOS risk**: Transparent fallback equation with research-prior weights, not trained calibrated model. Formula: `risk = 100 * sigmoid(INTERCEPT + sum(W_i * domain_i))`. Weights: CYCLE 1.20, METABOLIC 0.90, AUTONOMIC 0.60, SLEEP 0.50, CIRCADIAN 0.50, TEMPERATURE 0.35, GLUCOSE 0.35, ACTIVITY 0.30, BP 0.20, INTERCEPT -3.0. Confidence via bootstrap CI 5-95 percentile over 250 samples with noise sigma 5 + (1-quality)*14. Confidence breakdown: 30% data quality, 20% baseline, 20% CI width, 20% feature completeness, 10% cycle completeness.

- **Sleep**: Formula-based wearable sleep estimation (approximate, not polysomnography). Uses HR z-score, RMSSD z-score, motion z-score, GSR z-score, temp stability, time prior 22:00-07:00 high, user sleep window prior.

- **Stress**: Formula-based stress estimation from autonomic and arousal features. HR z, RMSSD z, motion z, temp drop z, phasic GSR z, GSR z. Motion gate activity >45 reduces stress 0.65.

- **PPG Quality**: Heuristic + trained model blended 60/40. Heuristic: amplitude, saturation, motion penalty. Model: trained on wrist_ppg_during_exercise (different sensor and sampling rate than the active generic analog Pulse Sensor; retained only for legacy optical PPG quality experiments) - features: ppg_amp, ppg_amp_cv, ppg_regularity, ppg_dominant_hr_bpm, ppg_band_power, ppg_peak_rate, ppg_hr_bpm, ppg_ibi_rmssd_ms, ppg_ibi_cv, ppg_beat_consistency, ppg_zero_cross_rate, ppg_dom_peak_diff, ppg_half_hr_diff, motion_index, ppg_quality_heuristic. Target: |PPG HR - ECG HR| <=5 bpm reliable. Model only soft correction, heuristic dominant.

### Legacy Models (Preserved from V8.1)

- `pcos_risk_model.joblib` (17MB) - Legacy, in `chrono_pcos_project V8/models/`, trained on PCOS_data.csv, reference only, not used as primary in V8.3 (transparent fallback is primary)
- `ppg_quality_model.joblib` (5MB) - Legacy, used as soft correction in quality.py

## No New Large Models in V8.3

V8.3 prioritizes Science, Clarity, Reproducibility, Explainability, Honest Limitations over fake AI features. No new large black-box models claiming to diagnose everything.

All modules are research-only signals, not diagnostic, not clinically validated.

## Training Documentation

For every model, document:
- dataset, target, features, preprocessing, train/test split, cross-validation, metrics, limitations
- Avoid data leakage: subject-level split
- See docs/MODEL_VALIDATION.md

## Model Status

- Engineering validation: Implemented (baseline, longitudinal, quality, fusion, module isolation, etc.)
- Clinical validation: NOT ESTABLISHED (requires ethics-approved prospective study)

## Usage

```python
from src.disease_modules.registry import GLOBAL_REGISTRY
mod = GLOBAL_REGISTRY.create("pcos")
result = mod.predict(shared=shared_features, clinical=clinical_data, history=history)
print(result.explanation)
```
