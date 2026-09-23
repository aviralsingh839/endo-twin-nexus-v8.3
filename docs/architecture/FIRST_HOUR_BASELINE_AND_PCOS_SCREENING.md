# First-Hour Personal Baseline + CHRONO-PCOS Screening

## Product behavior

ENDO-TWIN now treats the **first hour** of quality-gated wearable observation as the initial personal calibration window.

```
WEARABLE START
    ↓
sensor/contact + packet quality gates
    ↓
feature extraction: HR / HRV / skin temperature / motion / optional ECG
    ↓
~1 hour quality-gated personal baseline
    ↓
PERSONAL BASELINE READY
    ↓
live readings are compared with the person's own reference
    ↓
longitudinal adaptation from high-quality observations
    ↓
CHRONO-PCOS research screening surface
```

The one-hour window is an engineering calibration period. It is **not** a clinical reference interval.

## Baseline requirements

- Target window: 3600 seconds.
- Minimum accepted elapsed coverage: 3300 seconds.
- Minimum feature observations for automatic capture: 300.
- Poor-quality, missing or unusable measurements must not silently become baseline values.
- The baseline stores median, mean, standard deviation, MAD, percentiles, quality and confidence.
- Subsequent updates use quality gates and an outlier guard rather than replacing the baseline from a single reading.
- A longer longitudinal history remains useful after the first hour; the first hour is the initial personal reference, not the end of learning.

## CHRONO-PCOS / PCOD research screening

The platform already contains a CHRONO-PCOS disease-specific research module. The application surfaces should expose its state after sufficient data:

- `INSUFFICIENT_DATA`
- `LOWER_RESEARCH_SIGNAL`
- `ELEVATED_RESEARCH_SIGNAL`

These are **research screening signals**, not diagnoses and not calibrated probabilities.

The UI must never display:

- "PCOS = YES" as a diagnosis
- "PCOS = NO" as a diagnosis
- a wearable-only percentage described as the probability of disease
- inferred hormone measurements presented as laboratory measurements

Clinical information such as menstrual history, hyperandrogenism assessment, relevant laboratory data and imaging (where clinically appropriate) stays separately labelled and auditable.

For adolescents, the international guideline distinguishes diagnosis from adult criteria: irregular menstrual cycles are interpreted according to time since menarche and clinical/biochemical hyperandrogenism is central; pelvic ultrasound/PCOM and AMH are not diagnostic tests during adolescence. urlInternational PCOS/PMOS guideline resourceshttps://www.monash.edu/medicine/mchri/pcos/guideline

## Application surfaces

### Patient Android

Show:

1. **Baseline**
   - "1 HOUR CALIBRATION"
   - progress / readiness
   - signal quality
   - baseline confidence
   - "Personal reference ready"

2. **CHRONO-PCOS screening**
   - research state
   - data quality
   - model version
   - provenance
   - explanation and limitations

3. **Longitudinal**
   - deviations from personal baseline
   - persistent changes
   - recovery
   - observation coverage

### Doctor Android

For each selected patient show:

- baseline readiness
- baseline confidence and quality
- screening state
- model/provenance
- missing clinical evidence
- longitudinal changes
- audit trail

### Doctor Desktop

The command center should expose:

- Personal Baseline: 1 HOUR → READY
- CHRONO-PCOS Screening: WAITING / DATA READY
- Adaptation: LOCKED UNTIL BASELINE → ACTIVE
- patient-scoped baseline/trend details
- model provenance and limitations

## Safety / validation boundary

A wearable-only physiological signal should be treated as contextual evidence. A disease-specific diagnostic claim requires an appropriately validated clinical pathway and model.

FDA guidance notes that software analyzing physiological signals for medical purposes and software producing disease-specific risk outputs can fall within medical-device oversight depending on intended use. urlFDA Clinical Decision Support guidancehttps://www.fda.gov/medical-devices/digital-health-center-excellence/step-6-software-function-intended-provide-clinical-decision-support

For this school/research prototype, the correct product language is:

> "ENDO-TWIN builds a personal physiological baseline after approximately one hour of quality-gated observation and then provides longitudinal research context. CHRONO-PCOS can expose a research screening signal when sufficient evidence is available; it does not diagnose PCOS/PCOD."

