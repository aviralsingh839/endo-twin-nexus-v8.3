# ENDO-TWIN NEXUS V8.x — Professional UI redesign inventory

This branch implements the first ecosystem-wide visual-system pass while preserving the V8.4 application architecture and science/data guardrails.

## Inventory
### Desktop
- ENDO-TWIN main PySide6 application: src/ui/main_window.py
- Shared Qt visual system: src/ui/theme.py
- Reusable vitals: src/ui/vital_cards.py
- PyQtGraph charts: src/ui/live_plots.py
- Research/analysis tabs: src/ui/main_window.py, src/ui/research_tab.py
- Reports: src/utils/report.py and reports/report_generator.py
- Doctor workstation: desktop/doctor_app/main_enhanced.py
- Launcher/control center: launcher/main.py
- Diagnostics: launcher/diagnostics.py where present
- Public website: website/index.html, website/style.css, website/script.js

### Android
- Patient native: android/patient/
  - Compose + Material 3
  - Room/DataStore/repository/viewmodel structure preserved
  - patient-scoped workflows preserved
- Doctor native: android/doctor/
  - Compose + Material 3
  - multi-patient registry/workspace preserved
  - patient-scoped review preserved
- Legacy Kivy applications remain preserved as fallback/demo paths:
  - android/patient_app/
  - android/doctor_app/

## Design-system changes
- Desktop Qt palette moved from gradient-heavy dark UI to a restrained clinical light system.
- Shared semantic tokens now emphasize neutral surfaces, teal scientific brand color, readable text, and explicit semantic state colors.
- Android Patient and Doctor Material 3 themes now use the same core palette and typography direction.
- Launcher status markers no longer rely on emoji icons; status is expressed with short textual markers.
- Existing data provenance, research-only boundary, and DEMO/LIVE separation are retained.

## Safety/functional guardrails
The redesign must not create synthetic live observations, diagnostic claims, fake model confidence, or cross-patient leakage. UI must remain a presentation layer over the existing data/repository/model pipeline.

## Verification status
Repository changes were committed to this branch. GitHub Actions reported no workflow run for the new commits, so no remote CI build result is claimed from this branch. Native APK compilation and local runtime tests require a checkout with the project's Android/Python build environment; they were not executed through the GitHub connector in this session.

## Next local verification
Run the existing project diagnostics/tests and both native Android Gradle builds from a prepared checkout, then inspect the actual screens at desktop and multiple Android widths.
