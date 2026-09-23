# ENDO-TWIN NEXUS — documentation index

Start with **[PROJECT_STATUS.md](PROJECT_STATUS.md)**: current state, what is
verified and what is not, version timeline, and a short note per feature area.

> Research prototype. Not a medical device. Not clinically validated. Not a diagnosis.

## Understand the system

- [HOW_IT_WORKS.md](HOW_IT_WORKS.md) — acquisition → quality → features → baselines → models → reports
- [ARCHITECTURE.md](ARCHITECTURE.md) — layers, data flow, module boundaries
- [architecture/APPLICATION_ARCHITECTURE.md](architecture/APPLICATION_ARCHITECTURE.md)
- [architecture/DATABASE_ARCHITECTURE.md](architecture/DATABASE_ARCHITECTURE.md)
- [architecture/FIRST_HOUR_BASELINE_AND_PCOS_SCREENING.md](architecture/FIRST_HOUR_BASELINE_AND_PCOS_SCREENING.md)
- [endo_twin/CONCEPT.md](endo_twin/CONCEPT.md), [endo_twin/PLATFORM_ARCHITECTURE.md](endo_twin/PLATFORM_ARCHITECTURE.md), [endo_twin/DISEASE_MODEL_SYSTEM.md](endo_twin/DISEASE_MODEL_SYSTEM.md)
- [DATA_ARCHITECTURE.md](DATA_ARCHITECTURE.md) — local-first storage layout

## Hardware and live sensing

- [CARDBOARD_POD_BUILD.md](CARDBOARD_POD_BUILD.md) — **start here**: the cardboard build (no battery, no screws), sensor placement for a real pulse, stills and trim test
- [WEARABLE_AND_MEGA_BUILD_MANUAL.md](WEARABLE_AND_MEGA_BUILD_MANUAL.md) — reference: sensor placement logic, wiring, firmware, bench hub, acceptance
- [MEGA_HUB_BUILD.md](MEGA_HUB_BUILD.md) — bench hub detail (use `CARDBOARD_POD_BUILD.md` section 7 with it)
- [hardware/WIRING.md](hardware/WIRING.md) — pin-level wiring and probe placement
- [HARDWARE_BUILD_GUIDE.md](HARDWARE_BUILD_GUIDE.md), [hardware/HARDWARE.md](hardware/HARDWARE.md)
- [MEGA_HUB_BUILD.md](MEGA_HUB_BUILD.md), [hardware/MEGA_ESP_CONNECTION_V8_7.md](hardware/MEGA_ESP_CONNECTION_V8_7.md)
- [hardware/ESP8266_SENSOR_POD.md](hardware/ESP8266_SENSOR_POD.md) — the older Wi-Fi pod
- [WEAR_SITES.md](WEAR_SITES.md) — wrist or shoulder mounting, and what each measurement means on each site
- [WIRE_FORMAT_CP3.md](WIRE_FORMAT_CP3.md) — the `$CP3` frame, legacy `$CP2`, status bits
- [LIVE_SENSOR_PROCESSING.md](LIVE_SENSOR_PROCESSING.md) — live path from packet to feature
- [PROTOTYPE_LAB.md](PROTOTYPE_LAB.md), [WORKSTATIONS_AND_CONNECTION.md](WORKSTATIONS_AND_CONNECTION.md)
- [PUBLIC_3_DAY_TEST_PROTOCOL.md](PUBLIC_3_DAY_TEST_PROTOCOL.md) — fix the wear site for every participant

## Science and models

- [science/SCIENTIFIC_CORE.md](science/SCIENTIFIC_CORE.md), [science/SIGNAL_PROCESSING.md](science/SIGNAL_PROCESSING.md)
- [science/BASELINE.md](science/BASELINE.md), [science/LONGITUDINAL.md](science/LONGITUDINAL.md)
- [science/CHRONO_METABOLIC.md](science/CHRONO_METABOLIC.md), [LONGITUDINAL_ENGINE.md](LONGITUDINAL_ENGINE.md)
- [SCIENCE_GUARDRAILS.md](SCIENCE_GUARDRAILS.md), [SAFETY_AND_LIMITATIONS.md](SAFETY_AND_LIMITATIONS.md), [science/LIMITATIONS.md](science/LIMITATIONS.md)
- [SCIENTIFIC_METHODS_V8_6_1.md](SCIENTIFIC_METHODS_V8_6_1.md), [MODEL_VALIDATION.md](MODEL_VALIDATION.md)
- [DISEASE_MODULES.md](DISEASE_MODULES.md), [MULTI_DISEASE_MODEL.md](MULTI_DISEASE_MODEL.md), [chrono_pcos/MODEL.md](chrono_pcos/MODEL.md)
- [SELF_LEARNING.md](SELF_LEARNING.md) — wearable capability ladder and its limits
- [ai_ml/AI_ML_ARCHITECTURE.md](ai_ml/AI_ML_ARCHITECTURE.md), [ai_ml/MODEL_REGISTRY.md](ai_ml/MODEL_REGISTRY.md), [ai_ml/VALIDATION.md](ai_ml/VALIDATION.md), [ai_ml/MODEL_DIAGNOSTIC_REPORT.md](ai_ml/MODEL_DIAGNOSTIC_REPORT.md)
- [ULTRASOUND_PIPELINE.md](ULTRASOUND_PIPELINE.md) — research-only imaging path
- [DATASET_CARD.md](DATASET_CARD.md)

## Apps and interface

- [applications/PATIENT_ANDROID.md](applications/PATIENT_ANDROID.md), [applications/PATIENT_DESKTOP.md](applications/PATIENT_DESKTOP.md)
- [applications/DOCTOR_ANDROID.md](applications/DOCTOR_ANDROID.md), [applications/DOCTOR_DESKTOP.md](applications/DOCTOR_DESKTOP.md)
- [applications/ENDO_TWIN.md](applications/ENDO_TWIN.md), [applications/RESEARCH_LAB.md](applications/RESEARCH_LAB.md), [applications/DIAGNOSTICS.md](applications/DIAGNOSTICS.md)
- [hardware/UNIFIED_WORKSTATION_V8_7.md](hardware/UNIFIED_WORKSTATION_V8_7.md)
- [UI_DESIGN_SYSTEM.md](UI_DESIGN_SYSTEM.md) — palette, components, per-surface flows, acceptance checklist
- [UI_ARCHITECTURE.md](UI_ARCHITECTURE.md), [UI_COMPONENT_CATALOG.md](UI_COMPONENT_CATALOG.md)
- [UI_MASTER_AUDIT.md](UI_MASTER_AUDIT.md), [UI_RESPONSIVE_GUIDE.md](UI_RESPONSIVE_GUIDE.md), [UI_HARDWARE_UX.md](UI_HARDWARE_UX.md)
- [UI_ACCESSIBILITY.md](UI_ACCESSIBILITY.md) — thresholds and how to run the audit

## Build, run, test

- [../BUILD.md](../BUILD.md) (project root)
- [BUILD_GUIDE.md](BUILD_GUIDE.md), [INSTALLATION.md](INSTALLATION.md), [getting_started/QUICKSTART.md](getting_started/QUICKSTART.md), [getting_started/RUNNING.md](getting_started/RUNNING.md), [getting_started/INSTALLATION.md](getting_started/INSTALLATION.md)
- [ANDROID_BUILD_GUIDE.md](ANDROID_BUILD_GUIDE.md)
- [GARUDA_LAUNCH_GUIDE.md](GARUDA_LAUNCH_GUIDE.md), [LOCAL_UPDATE.md](LOCAL_UPDATE.md)
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- [testing/TESTING.md](testing/TESTING.md), [performance/PERFORMANCE_REPORT.md](performance/PERFORMANCE_REPORT.md)
- [V8.6_RELEASE_NOTES.md](V8.6_RELEASE_NOTES.md)

## Research notes

- [benchmarks/REFERENCE_REPOSITORY_AUDIT.md](benchmarks/REFERENCE_REPOSITORY_AUDIT.md) — prior-art audit of reference repositories
- [benchmarks/ENDO_TWIN_BENCHMARK_MATRIX.md](benchmarks/ENDO_TWIN_BENCHMARK_MATRIX.md)

## History and archives

- `git log` — the full record, including the docs consolidated into PROJECT_STATUS.md
- [legacy/](legacy/) — V8.1 documents (also preserved in `chrono_pcos_project V8/`)
- `hardware/legacy/` — superseded firmwares
