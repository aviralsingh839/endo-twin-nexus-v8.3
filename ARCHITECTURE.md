# ENDO-TWIN NEXUS Architecture

## Platform boundary
ENDO-TWIN is the general personalized physiological modelling platform. CHRONO-PCOS is the first disease-specific module.

Desktop and Android clients consume shared concepts: patient, session, sensor/device data, signal, feature, baseline, longitudinal state, imaging, model result, report, provenance and audit.

## Core flow
SENSOR → DEVICE DRIVER → RAW PACKET → VALIDATION → TIMESTAMP → BUFFER → QUALITY → FILTERING → FEATURES → BASELINE → LONGITUDINAL → FUSION → MODEL REGISTRY → EXPLANATION → REPORT

## Disease modules
Disease modules implement the shared DiseaseModel contract and register with the model registry. They must declare manifest/version/features/capabilities/validation status/limitations.

## Data boundary
All health records are patient-scoped. Demo data is labelled DEMO_DATA. Missing or unsupported values remain UNKNOWN/INSUFFICIENT_DATA.

## Clients
- Existing PySide6/PyQtGraph desktop scientific interface.
- Existing native Kotlin/Compose patient and doctor applications.
- Doctor Test Workstation for deterministic prototype/hardware checks.
- Future Flutter/Riverpod/Dio/Drift/Melos shared-mobile architecture is staged, not a destructive rewrite.

## Storage
The existing SQLite/local-first database remains preserved. SQLAlchemy/Alembic are prepared as migration targets; migration is not considered complete until existing data compatibility is tested.

## Imaging
pydicom/MONAI are infrastructure layers. Generic ultrasound repositories are not treated as validated ovarian/PCOS models.
