# SAFETY AND LIMITATIONS - V8.3

## Medical Safety Note

**This is a research / pre-screening estimate, NOT a diagnosis. Clinical evaluation by a qualified professional is required for any diagnosis.**

- PCOS diagnosis requires clinician and accepted diagnostic criteria (Rotterdam)
- No sensor measures hormones
- App never starts, stops, changes or prescribes medication
- No ultrasound image is converted into diagnosis
- No cyst-rupture prediction exists or is claimed
- Sleep module does not diagnose sleep disorders, does not replace polysomnography
- Cardiometabolic module does not diagnose diabetes, hypertension, cardiovascular disease
- Autonomic module does not diagnose mental-health conditions

Every score is research estimate.

## Safety

- Educational physiological monitoring only, not diagnostic medical device
- Keep wearable pod on battery or laptop's own USB when on person, never mains
- LiPo: protected cell, TP4056 charger, boost, fuse
- Clean sensors with alcohol, not water
- If skin irritation, remove
- No medical decisions from prototype alone
- Discuss relevant findings with qualified healthcare professional if symptomatic

## Limitations - Engineering

- Baseline needs min 60 samples, 5 min calm data, good quality >0.5, days_covered >=3 for stable, confidence >=0.5
- Longitudinal needs min 5 points per metric, quality >=0.5, persistence >=3 points
- Signal quality: mean over PRESENT sensors only, optional channels never drag down
- Sensor failure: low quality, not physiological abnormality, must not be interpreted as disease
- Missing data: handled, not crash, but lowers confidence and coverage
- Noisy data: quality penalty, not crash
- Motion artifacts: motion_index >1.5 → quality penalty
- Packet corruption: CRC mismatch → discarded, app continues
- Stale data: >6s → quality 0.2 artifact stale
- Flatline: 5+ identical → artifact flatline quality 0.1
- Impossible values: HR 35-210, skin temp 20-42°C, etc. → artifact impossible quality 0
- Hardware: Nano pod primary, Mega hub expanded lab, ESP8266 bridge optional, all preserved from V8.1, software gracefully handles missing sensors

## Limitations - Models

- Live risk engine: transparent fallback equation with research-prior weights, not trained calibrated model, labelled longitudinal wearable data does not exist publicly, ethics-approved pilot only realistic path
- PPG quality model: trained on wrist_ppg_during_exercise (different sensor and sampling rate than the active generic analog Pulse Sensor; retained only for legacy optical PPG quality experiments), used as soft correction 40% weight, heuristic dominant
- Ultrasound: image-derived features UNKNOWN by design until validated, labelled, patient-grouped dataset exists, quality gate works on real images today, nothing invented
- Model A-E experiment (does longitudinal or ultrasound add value?): PENDING by design
- Python BLE client not written yet, pod connects over USB serial or ESP8266 bridge
- Care-plan reminders bookkeeping only
- All unproven labelled PENDING or UNKNOWN in interface, code, docs

## Limitations - Data

- No large clinically labelled longitudinal wearable dataset publicly exists
- Public PCOS datasets not longitudinal wearable, clinical variables only
- Synthetic data realistic longitudinal but still synthetic, clearly labelled, never presented as real
- Subject-level validation used where appropriate to avoid leakage
- Reproducibility via seeds

## Limitations - Clinical Validation

- NOT ESTABLISHED for all V8.3 modules
- All signals research-only, not diagnostic
- Requires ethics-approved prospective study
- Model confidence vs data quality vs clinical validation separated, never conflated
- Never display "78% chance of PCOS" unless calibrated probability for exact target
- Instead: level low/moderate/elevated/high + confidence + data quality + validation status

## Language Rules

**Never claim:**

- "diagnoses PCOS"
- "detects diabetes"
- "detects heart disease"
- "detects sleep apnea"
- "wearable detects PCOS"
- "DISEASE DETECTED"

**Use:**

- "research risk signal"
- "physiological deviation"
- "screening-oriented estimate"
- "requires clinical evaluation"
- "PCOS-associated physiological and clinical risk signals"
- "sleep-related risk signal" or "circadian disruption pattern"
- "cardiometabolic research signal"
- "autonomic/stress regulation signal"

## Data Honesty - Critical

- Never create fake clinical results and present as real
- Never modify public datasets to make metrics look better
- Never fabricate patient records
- Never label synthetic as clinical data
- Never claim diagnosis unless genuine clinical validation supporting exact claim
- Every dataset labelled: REAL, SYNTHETIC, SIMULATED, PUBLIC DATASET, USER-ENTERED, never mix silently

## Confidence Must Mean Something

Separate:

- MODEL CONFIDENCE: based on coverage and quality
- DATA QUALITY: mean quality of present features
- CLINICAL VALIDATION: NOT ESTABLISHED

Three different concepts, never conflated.

## Report Limitations Section

Every report includes limitations and recommended next step: "Discuss relevant findings with qualified healthcare professional."

## Future Modules

Do not add arbitrary modules such as cancer detection, Alzheimer's diagnosis, infectious disease diagnosis, kidney disease diagnosis, liver disease diagnosis, thyroid diagnosis unless appropriate dataset, validated features, scientifically defensible target labels actually available.

If future module not currently supported, create interface but mark "Future research module - not implemented" and do not generate fake datasets to make unsupported modules appear validated.

Current future modules: thyroid, renal, hepatic, infectious, oncology, neurodegenerative - all marked not implemented, no fake data.

## Code Quality

Before finishing:

- Remove dead code where safe
- Remove duplicated implementations
- Consolidate configuration
- Remove temporary files, caches, obsolete docs from primary path
- Fix imports
- Run tests
- Run syntax checks
- Check startup
- Verify all model paths, data paths, hardware simulation, report generation
- Do not delete anything important merely because looks unused, first determine whether referenced

## Do Not Overbuild

Project is Class 11 student innovation/research demonstration.

Prioritize: Science, Clarity, Reproducibility, Explainability, Honest Limitations over unnecessary enterprise architecture.

Do not add: cloud infrastructure, paid APIs, unnecessary web servers, unnecessary databases, blockchain, complex microservices, fake AI features

System should remain capable of running offline wherever possible - it does, SQLite local, no cloud.

## Final Checklist

See README.md acceptance checklist - all checked.

Most important: Do not simply add four disease names to README. Actually refactor architecture so CHRONO-TWIN NEXUS V8.3 is reusable longitudinal physiological platform with modular disease-specific research models. PCOS functionality becomes one module within larger system rather than entire identity. Preserve working V8.1 functionality, improve data realism and longitudinal structure, make project technically coherent, reproducible, explainable and honest about what has and has not been clinically validated.

Done.
