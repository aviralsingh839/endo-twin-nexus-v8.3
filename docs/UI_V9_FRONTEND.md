# ENDO-TWIN NEXUS V9 — Front-End Workstation Specification

## Reference-inspired UI

The Doctor and Patient desktop workstations now use the supplied dark navy / blue-violet dashboard as the visual reference. The redesign adds a persistent left navigation, patient/session headers, KPI cards, live signal cards, quick actions, Personal Twin state, and a combined PCOD progress/complication workspace.

The redesign is presentation-layer work. Existing acquisition, feature extraction, disease modules, database operations and longitudinal algorithms remain the source of truth.

## Self-Learning Model

./START.sh opens the normal launcher menu. Self-Learning Model is an explicit menu option.

The Self-Learning Model asks for: patient name, optional local alias, sex, patient-reported PCOD/PCOS status, age, height, weight, waist, blood pressure, glucose, menstrual-cycle context and years post-menarche.

Each participant has a stable local participant ID. Profile, adaptive learning state, raw event history and personal baseline are associated with that ID.

Baseline capture is available from the Self-Learning Model. Demo data is explicitly rejected as baseline input. Live capture uses the existing USB or ESP32 Wi-Fi transport and the existing quality-gated wearable feature pipeline.

## PCOD status gate

| UI status | PCOD longitudinal view | Complication context |
| --- | --- | --- |
| Unknown | Ask / insufficient context | Disabled |
| No | Disabled / not applicable | Disabled |
| Yes | Enabled | Enabled |

The UI never infers that a person has PCOD from wearable data.

## PCOD Healing / Longitudinal Progress table

When PCOD is marked Yes, the UI presents the existing LongitudinalEngine output for selected physiological metrics.

Columns: Metric, Baseline, Current, Change, Trend, Existing State, Recovery.

Existing engine states shown by the UI include normal, single, persistent, progressive, recovery, insufficient and missing.

Overall wording is conservative: Improving toward personal baseline when recovery classifications are present; Stable within personal baseline when the report is normal; No recovery confirmed yet for persistent/deviating change; Insufficient longitudinal data when evaluation is not possible.

This is a longitudinal research indicator, not proof that PCOD/PCOS has resolved.

## PCOD complication-context table

The complication table calls the existing PCOSComplicationContextEngine only when PCOD/PCOS is marked Yes.

Columns: Domain, Status, Finding, Data needed.

When PCOD is No or Unknown, the table shows a disabled gate message and does not evaluate the complication engine.

## Cross-workstation synchronization

Self-Learning Model -> Personal Twin state -> Unified Workstation / Doctor Workstation / Patient Workstation.

Participant ID is carried into live sessions and local HistoryStore sessions. Doctor and Patient read the same patient-scoped adaptive state and personal baseline.

## Patient Workstation

Startup asks which patient is present. The dashboard now exposes patient identity, PCOD status, heart rate, HRV, temperature, GSR, activity, baseline status, Personal Twin summary, quick actions, and the PCOD Healing & Complications page.

## Doctor Workstation

The Doctor dashboard keeps the research command-center layout and adds patient-state presentation, a PCOD progress quick action, shared Personal Twin state, and the same combined PCOD progress/complication table inside the selected patient workspace.

## Backend boundary

The front-end does not replace or duplicate the physiological/disease algorithms. Existing sources of truth remain PersonalBaselineEngine, LongitudinalEngine, PCOSComplicationContextEngine, PersonalAdaptiveModel, the existing wearable acquisition/feature pipeline, and the existing LocalDatabase/HistoryStore.

## Safety / research boundary

This project is a research prototype. PCOD/PCOS status is patient-reported context. Wearable data does not establish a diagnosis. The progress table describes movement relative to the patient's own stored baseline using the existing longitudinal research logic; it does not certify healing or disease resolution. Complication rows are contextual prompts and data requirements, not diagnoses.

## UI backup

The pre-redesign feature branch is preserved as backup/pre-ui-redesign-2026-09-27.