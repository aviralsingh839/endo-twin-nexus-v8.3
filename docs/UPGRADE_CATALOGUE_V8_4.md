# ENDO-TWIN V8.4 upgrade map

This file maps the uploaded ENDO-TWIN Master GitHub Upgrade Catalogue to the existing V8.3 codebase. The catalogue explicitly says not to install every repository: components are to be integrated, adapted, studied, or deferred according to their role.

## Implemented in this branch
- **Pydantic:** strict patient/measurement boundary schemas with provenance and quality validation.
- **NeuroKit2 / pyHRV:** dependency-gated adapters for PPG and richer HRV processing; no synthetic fallback is presented as measured data.
- **pydicom / MONAI:** imaging backend capability detection, ready for the existing ultrasound layer.
- **Plugin discovery:** optional Python entry-point discovery for future disease modules, while preserving CHRONO-PCOS as the first module.
- **Testing:** regression tests for schema validation and optional-backend behavior.
- **Ruff / mypy:** added to the development dependency foundation; existing CI remains the quality gate.

## Preserved architecture
- ENDO-TWIN remains the umbrella/core platform and CHRONO-PCOS remains a disease-specific branch/module, matching the catalogue.
- Existing PySide6/PyQtGraph desktop UI and native Kotlin/Compose patient/doctor apps are not replaced.
- Existing patient isolation, provenance, uncertainty, demo-data separation and no-fabrication behavior remain mandatory.

## Staged rather than forced
- **FastAPI:** kept as a future service boundary because the catalogue itself says "integrate later / adapt now" and the current project is explicitly offline-first. A network server is not introduced merely to satisfy a dependency list.
- **Flutter + Riverpod + Dio + Drift + Melos:** retained as the target future mobile monorepo architecture. The current native Kotlin apps are working assets and are not discarded in favor of a rewrite.
- **SQLAlchemy + Alembic:** added as the dependency foundation for a future database-engine migration; the existing database implementation is preserved until schema migration can be tested against the complete application.
- **MONAI Label, nnU-Net, TorchIO, Captum, SHAP, tsfresh, sktime, MLflow, DVC, Optuna, Hypothesis:** staged research capabilities. They are not silently treated as trained clinical models.
- **Bleak / FlutterBluePlus:** staged device/BLE integration. Existing serial hardware support remains intact.

## Safety rules carried forward
1. Never treat another anatomy's ultrasound model as an ovarian model.
2. Never turn DEMO_DATA into real patient data.
3. Never fabricate missing signals or model probabilities.
4. Keep CHRONO-PCOS-specific logic out of ENDO-TWIN core.
5. Preserve provenance, data quality, uncertainty and model/dataset version information.
6. Review licenses before redistributing third-party components.

The branch is an incremental V8.4 foundation, not a claim that every catalogue item is already implemented.
