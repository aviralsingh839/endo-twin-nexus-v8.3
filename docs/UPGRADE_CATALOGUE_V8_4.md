# ENDO-TWIN V8.4 upgrade map

This file maps the catalogue to the existing V8.3 codebase. Libraries are integrated only where they have a clear shared-platform role; other repositories remain references or future work.

## Core
- Pydantic: strict boundary schemas for patient and measurement payloads.
- Plugin discovery: optional Python entry-point discovery for disease modules.
- FastAPI: planned service boundary; not forced into offline desktop runtime.

## Physiology
- NeuroKit2: optional PPG/ECG/EDA backend adapter.
- pyHRV: optional advanced HRV adapter.
- WFDB: future research-data interoperability.

## Imaging
- pydicom + MONAI are dependency-gated and intended for DICOM/image-processing layers.
- Other-anatomy ultrasound repositories stay study-only and are not treated as ovarian models.

## Explainability / ML lifecycle
- Captum, SHAP, tsfresh, sktime, MLflow, DVC, Optuna remain staged additions. Existing research outputs retain provenance and uncertainty.

## Desktop
- PyQtGraph remains the live signal plotting layer. Existing PySide6 UI is preserved.

## Mobile
- Existing native Kotlin/Compose apps are preserved. Flutter/Riverpod/Dio/Drift/Melos remain a future mobile-client architecture rather than a forced rewrite of the working Android apps.

## Safety / data boundaries
- Patient-scoped records, provenance labels, uncertainty, demo-data separation and no-fabrication behavior remain mandatory.
- Heavy dependencies must be optional or CI-supported so the offline prototype does not fail simply because a research package is absent.
