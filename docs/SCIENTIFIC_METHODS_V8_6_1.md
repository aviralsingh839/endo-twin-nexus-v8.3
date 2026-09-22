# ENDO-TWIN V8.6.1 — Scientific Methods & Performance Notes

## 1. Platform boundary

ENDO-TWIN is the general personalized physiological modelling platform.

CHRONO-PCOS is the first disease-specific module.

The platform can acquire and process physiological signals without requiring a disease model. Disease-model outputs are a separate evidence layer.

## 2. Evidence layers

The intended data flow is:

**Sensor / user / image source → provenance → quality → feature extraction → personal baseline → longitudinal context → disease-model gate → model output → uncertainty → report**

The UI exposes this separation so that a derived feature cannot be mistaken for a direct measurement and a model result cannot be mistaken for either.

## 3. PPG, HR and HRV

### Pulse/heart rate

The workstation uses filtered PPG and local peak detection to estimate pulse rate.

The peak detector:
- uses a primed DC blocker to avoid startup transients;
- removes a short warm-up segment from detection;
- robustly centres the waveform using its median;
- uses a noise-scaled threshold;
- uses a refractory period constrained by configured physiological HR bounds;
- rejects implausible inter-beat intervals;
- removes intervals with large local-median deviation.

Candidate peak detection is vectorized with NumPy, reducing Python-level iteration over the full waveform.

### HRV

HRV is more sensitive to timing errors and motion/artifact than simple pulse rate.

V8.6.1 therefore refuses to report RMSSD/SDNN when:
- fewer than 10 clean beat intervals are available; or
- the PPG quality gate is below the stronger HRV threshold.

The displayed HRV is a **PPG-derived pulse-rate-variability feature**, not an ECG-equivalent measurement.

References:
- https://pubmed.ncbi.nlm.nih.gov/29668452/
- https://pubmed.ncbi.nlm.nih.gov/39517723/
- https://pubmed.ncbi.nlm.nih.gov/42655500/

## 4. SpO2

The current SpO2 estimator uses the red/IR ratio-of-ratios as an educational approximation.

It is intentionally:
- quality-gated;
- clearly labelled as research/educational;
- not calibrated to a clinical reference device;
- not suitable for a clinical accuracy claim.

A future validation protocol should use a reference oximeter and pre-specified error metrics.

## 5. Sensor quality

Quality and provenance are independent.

Example:
- A live PPG sample can be **MEASURED** and simultaneously have poor quality.
- A calculated HR can be **DERIVED** and be withheld when the source quality is inadequate.
- A disease result can be **MODEL-INFERRED** only when model evidence gates pass.

Missing values are not replaced with convenient physiological defaults.

## 6. CHRONO-PCOS

The disease module does not treat wearable physiology as a PCOS diagnostic criterion.

The 2023 international guideline describes adult assessment around combinations of ovulatory dysfunction, hyperandrogenism, and polycystic ovarian morphology/appropriately used AMH, with consideration of disorders that mimic PCOS.

For adolescents, the guideline uses both irregular menstrual cycles defined according to time after menarche and clinical/biochemical hyperandrogenism. Ultrasound and AMH are not used for adolescent diagnosis.

The software uses these concepts as an **evidence gate**, not as an automated diagnosis.

When required evidence is absent, CHRONO-PCOS returns an explicit insufficient/unknown state rather than fabricating a risk score.

Reference:
https://www.monash.edu/__data/assets/pdf_file/0003/3379521/Evidence-Based-Guidelines-2023.pdf

Adolescent-specific recommendations:
https://research.monash.edu/en/publications/international-evidence-based-recommendations-for-polycystic-ovary/

## 7. Why the current research index is not a probability

The internal contextual index retains the legacy heuristic structure for research continuity, but V8.6.1 explicitly marks it:

**heuristic / uncalibrated / not a probability**

It must not be compared numerically with clinical prevalence, sensitivity/specificity, PPV/NPV, or diagnostic probability.

Before a future numerical clinical risk score is claimed, the project needs:
- a fixed development cohort;
- patient-level separation;
- locked preprocessing;
- held-out validation;
- external validation;
- calibration;
- confidence intervals;
- prespecified threshold selection;
- subgroup evaluation;
- prospective/temporal validation where feasible.

## 8. Performance / responsiveness

V8.6.1 keeps acquisition and UI work separate:
- packet ingestion is threaded;
- sensor-specific processors operate at intended rates;
- desktop feature updates are throttled to a human-readable cadence;
- PPG peak candidates are found with vectorized NumPy operations;
- UI drawing uses bounded histories so charts cannot grow indefinitely;
- slower channels such as GSR and temperature are not oversampled to transport frequency.

The goal is to reduce latency without inventing extra information.

## 9. Reproducibility

Future studies should freeze:
- model version;
- preprocessing version;
- sensor firmware version;
- sampling configuration;
- inclusion/exclusion rules;
- train/validation/test subjects;
- random seeds;
- software environment.

## 10. Engineering benchmark targets

Useful engineering targets are:
- packet parse/CRC acceptance: deterministic and loss-aware;
- feature update interval: approximately 0.5–1 s on desktop;
- bounded processing queues;
- explicit stale-data state after timeout;
- no unbounded chart memory;
- no silent fallback to fabricated sensor values.

These are software-engineering targets, not clinical accuracy claims.
