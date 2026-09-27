# ENDO-TWIN NEXUS — Patient Web Portal

## Purpose

The website under `website/` is now a patient-facing, local-first web portal using the supplied dashboard references as the visual direction.

The web portal deliberately removes live sensor/wearable signal panels. It does not expose PPG, GSR, IMU, serial, Wi-Fi or sensor connection controls.

The portal focuses on patient-facing functionality that works without hardware:

- Patient profile and multi-person local records
- Personal Twin summary
- Cycle and symptom logging
- Sleep and weight logging
- Longitudinal trend graphs
- PCOD Healing / Longitudinal Progress research view
- PCOD Complication Context gated by patient-reported PCOD/PCOS status
- Local reports and print view
- Patient JSON export/import
- Full local backup export/import
- Local privacy/settings view

## Patient-specific local storage

The web portal uses browser `localStorage` under:

`endoTwinPatientWeb_v1`

The stored object contains:

- `people` keyed by local patient ID
- patient profile
- cycle records
- symptom records
- sleep records
- weight records
- notes
- local events
- Personal Twin sample count/status
- patient-reported PCOD/PCOS status

A patient never shares the in-browser record with another patient unless an exported JSON backup is explicitly imported.

## Cross-device portability

A static public website cannot privately synchronize health records across devices without a server/backend. This version therefore uses:

1. local browser storage for normal use;
2. patient JSON export/import for one-patient transfer;
3. full local backup export/import for the complete local people registry.

No patient record is sent to a website backend by the portal.

## PCOD gate

The portal has three patient-reported states:

| Status | Healing view | Complication context |
| --- | --- | --- |
| Unknown | Inactive / asks for confirmation | Off |
| No | Not applicable | Off |
| Yes | Enabled | Enabled |

The portal never infers PCOD/PCOS from sensor signals because this web version intentionally has no live sensor stream.

The PCOD Healing view is a clearly labelled research visualization of local longitudinal entries, not proof of disease resolution. The Complication Context page reports whether relevant patient-entered context is available for review; it is not a diagnosis.

## Deployment

The repository contains `.github/workflows/patient-web-pages.yml`. It publishes the `website/` directory using GitHub Pages.

The workflow is triggered by pushes to:

`feature/patient-web-portal-local-first`

and can also be started manually from GitHub Actions.

A repository administrator may need to enable GitHub Pages with **GitHub Actions** as the source the first time. The workflow output is the authoritative deployment URL.

## Design

The patient UI follows the supplied reference style:

- deep navy background
- electric blue / violet active navigation
- pink, cyan, green, orange and purple data accents
- compact KPI cards
- radial progress visuals
- large trend charts
- cycle tracker
- quick action tiles
- timeline
- PCOD research views
- compact data tables only when useful

## Backend boundary

This website redesign does not modify the Python wearable/acquisition/model backend. It is a static front-end experience with its own patient-local browser store for web-only patient-entered records.

The project remains a research prototype and the website does not represent itself as a medical device or diagnostic service.
