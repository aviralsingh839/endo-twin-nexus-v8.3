# Changelog

## V8.4 catalogue foundation — 2026-09-21
- Added executable Doctor Test Workstation with patient/session creation and explicit sensor/infrastructure failure states.
- Replaced placeholder Doctor patient archive/history behavior with real database operations.
- Hardened new-account password hashing with salted PBKDF2-HMAC-SHA256 while retaining legacy verification.
- Made report labels explicit so DEMO_DATA cannot silently become REAL.
- Added patient-scoped session retrieval and quality-aware feature schema.
- Added Pydantic boundary schemas.
- Added dependency-gated NeuroKit2/pyHRV and imaging capability adapters.
- Added optional disease-model entry-point discovery.
- Added V8.4 repository audit and roadmap.
- Added wearable build, wiring, measurement, calibration and testing documentation.
- Added AI/ML, model, ultrasound, database, API, Android, workstation, patient, demo, testing, security and limitations guides.
- Preserved existing applications and patient-isolation architecture.

Pending milestones remain explicitly documented rather than represented as completed features.
