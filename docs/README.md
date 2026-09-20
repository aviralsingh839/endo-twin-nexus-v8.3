# ENDO-TWIN V8.6 Documentation

## Current operating guides
- `getting_started/QUICKSTART.md`
- `BUILD.md`
- `BUILD_GUIDE.md`
- `ANDROID_BUILD_GUIDE.md`
- `WORKSTATIONS_AND_CONNECTION.md`
- `LIVE_SENSOR_PROCESSING.md`
- `V8.6_RELEASE_NOTES.md`
- `applications/PATIENT_ANDROID.md`
- `applications/PATIENT_DESKTOP.md`
- `applications/DOCTOR_DESKTOP.md`
- `11_DOCTOR_ANDROID_APP.md`
- `SCIENCE_GUARDRAILS.md`

V8.6 workstation flow: startup-only DEMO/LIVE selection, processed live sensor monitoring, richer Doctor review, single-patient Patient Workstation and explicit provenance.

`docs/legacy/` remains historical reference, not the current workflow.

## V8.6.1 reference UI + science

- [UI System](UI_SYSTEM_V8_6_1.md) — reference-inspired design language, component rules, responsive Android strategy.
- [Scientific Methods](SCIENTIFIC_METHODS_V8_6_1.md) — evidence gates, PPG/HRV methodology, PCOS reasoning and engineering performance notes.
- [Science Guardrails](SCIENCE_GUARDRAILS.md) — provenance, diagnostic boundaries, validation requirements and safety language.

## Website

The static ENDO-TWIN research portal lives in `../website/`. Launch it with `./START.sh website` from the project root. The legacy launcher paths `LAUNCH/WEBSITE.sh` and `launchers/WEBSITE.sh` are preserved for compatibility.
