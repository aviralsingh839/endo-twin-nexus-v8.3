# ENDO-TWIN Scientific & Safety Guardrails

## Scope

ENDO-TWIN is a general personalized physiological modelling platform. CHRONO-PCOS is its first disease-specific research module.

This software is a research prototype. It is not a medical device, has no established clinical diagnostic performance, and must not be represented as a diagnostic test.

## Evidence and provenance

Every observation/result should carry one source class:

- **MEASURED** — directly acquired by a sensor/device.
- **DERIVED** — mathematically/computationally calculated from measured data.
- **CLINICALLY_ENTERED** — supplied through an authorized clinical workflow.
- **PATIENT-REPORTED** — supplied by the patient.
- **IMAGE-DERIVED** — extracted from a supplied image by an explicit image-analysis step.
- **MODEL-INFERRED** — produced by a model from supported inputs.
- **DEMO_DATA** — synthetic/illustrative showcase content.
- **UNKNOWN** — source, validity, or support cannot be established.

Provenance must never be silently changed.

## Data quality is a separate axis

A measurement can be real but low quality. Low quality should not be replaced with a convenient default.

Engineering quality controls should identify, where applicable:

- missing values
- stale packets
- impossible values
- flatlines
- excessive/noisy segments
- motion contamination
- packet/CRC failures
- sensor-specific status flags

Long gaps remain missing unless an explicit imputation method is documented and its quality penalty is carried downstream.

## PPG / HR / HRV reasoning

PPG can support pulse-rate estimation and some pulse-rate-variability features, but PPG-derived variability is not interchangeable with ECG-derived HRV. Evidence shows agreement is better under controlled/resting conditions and can degrade with motion or free-living conditions.

V8.6.1 therefore:

1. detects peaks from a robustly centred filtered waveform;
2. removes implausible beat intervals;
3. rejects intervals with large deviation from the local median;
4. allows a short-window HR estimate at moderate quality;
5. withholds RMSSD/SDNN when there are fewer than 10 clean beat intervals or when PPG quality is below the stronger HRV gate;
6. withholds SpO2 when the combined quality is below its engineering gate.

These thresholds are **engineering gates**, not clinical thresholds.

References:
- Systematic review of wearable HRV accuracy: https://pubmed.ncbi.nlm.nih.gov/29668452/
- 2024 free-living PPG vs ECG validation study: https://pubmed.ncbi.nlm.nih.gov/39517723/
- 2026 systematic review/meta-analysis of PPG pulse-rate variability vs ECG HRV: https://pubmed.ncbi.nlm.nih.gov/42655500/
- Review of uncertainty in HRV analysis: https://pubmed.ncbi.nlm.nih.gov/37186539/

## SpO2 boundary

The current SpO2 estimator is an educational/research approximation. It is not calibrated to a reference oximeter and must not be represented as medical-grade oxygen saturation.

A future validation study should compare simultaneous sensor output with an appropriate reference device across relevant saturation ranges and motion conditions before any accuracy statement is made.

## CHRONO-PCOS evidence gate

Wearable physiology is **context**, not a standalone PCOS diagnostic criterion.

For adults, the international evidence-based guideline uses a diagnostic framework based on combinations of:
- ovulatory dysfunction,
- clinical/biochemical hyperandrogenism,
- polycystic ovarian morphology or, in adults, appropriately used AMH,

with appropriate exclusion of alternative disorders.

For adolescents, the diagnostic pathway differs: irregular menstrual cycles are defined in relation to time after menarche and clinical/biochemical hyperandrogenism is required. Pelvic ultrasound and AMH should not be used for PCOS diagnosis in adolescence.

Therefore CHRONO-PCOS V8.6.1:

- does not generate a disease-specific exploratory result from wearable physiology alone;
- records missing disease-specific evidence as UNKNOWN/insufficient evidence;
- distinguishes adult and adolescent context when years-post-menarche is available;
- treats ultrasound/AMH as non-diagnostic for adolescents;
- requires evidence that relevant mimicking disorders have been considered/excluded before a disease-specific context result is treated as supported;
- labels its current contextual index as **heuristic and uncalibrated**, never as a probability.

References:
- 2023 International Evidence-Based PCOS Guideline: https://www.monash.edu/__data/assets/pdf_file/0003/3379521/Evidence-Based-Guidelines-2023.pdf
- Adolescent-specific international recommendations: https://research.monash.edu/en/publications/international-evidence-based-recommendations-for-polycystic-ovary/
- Monash guideline resource page: https://www.monash.edu/medicine/mchri/pcos/guideline

## Ultrasound

An ultrasound result must follow:

**IMPORT → SOURCE/QUALITY CHECK → PREPROCESS → ANALYZE → FEATURE EXTRACTION → MODEL → UNCERTAINTY → REPORT**

Anatomical findings such as follicle counts, ovarian morphology, ovarian volume, or similar features must remain UNKNOWN until the software actually has a validated labelled imaging pipeline supporting those outputs.

Do not invent:
- training performance
- validation accuracy
- anatomical findings
- confidence values
- cohort sizes
- p-values or confidence intervals

## Clinical metabolic context

For a future clinical integration, the model should ingest laboratory/clinical measurements as entered values rather than pretending that wearable proxies are equivalent.

The 2023 international guideline identifies the 75-g OGTT as the most accurate glycaemic-status test in PCOS and notes reduced accuracy when substituting fasting glucose/HbA1c. This prototype therefore labels glucose-related fields as clinical input rather than wearable-derived diagnosis.

Reference:
https://www.monash.edu/__data/assets/pdf_file/0003/3379521/Evidence-Based-Guidelines-2023.pdf

## Validation plan before clinical claims

A scientifically credible future validation study should include:

- patient-level train/validation/test separation;
- independent external validation;
- prospective/temporal validation where possible;
- pre-specified inclusion/exclusion criteria;
- missing-data and artifact reporting;
- calibration analysis, not just discrimination;
- sensitivity, specificity, PPV/NPV with confidence intervals;
- ROC-AUC and precision-recall analysis where appropriate;
- subgroup analysis across relevant age/life-stage and sensor-quality strata;
- comparison against reference measurements and accepted clinical workflows;
- reproducible model and preprocessing versions.

A model with good engineering performance is not automatically clinically accurate.

## Demo boundary

Anything synthetic must say **DEMO_DATA** or equivalent.

Synthetic patients, scores, distances, sensor values, reports, timelines, and image examples must never be inserted into clinical records or presented as measured patient data.

## Privacy/security

The default architecture is local-first and patient-scoped.

The current mobile bridge is trusted-LAN research infrastructure. Production deployment would require transport encryption, strong authentication, authorization, audit logging, key management, threat modelling, and a documented security architecture.

## Preferred scientific language

Use:

- physiological pattern
- contextual signal
- research index
- model-inferred
- measured
- derived
- patient-reported
- image-derived
- insufficient evidence
- unknown
- clinical validation not established

Avoid:

- “detects PCOS”
- “proves PCOS”
- “clinically accurate”
- “100% accurate”
- “diagnostic wearable”
- invented validation metrics
- causal claims from correlation alone
