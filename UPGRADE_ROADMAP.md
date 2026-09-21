# ENDO-TWIN NEXUS V8.4 — UPGRADE ROADMAP

## Milestone 1 — Repository audit
Status: COMPLETE
- PROJECT_AUDIT.md added.

## Milestone 2 — Architecture cleanup
Status: IN PROGRESS
- Pydantic boundary schemas added.
- Optional disease-model entry-point discovery added.
- ENDO-TWIN/CHRONO-PCOS separation retained.

## Milestone 3 — Wearable hardware + firmware + wiring
Status: DOCUMENTATION FOUNDATION
- Dedicated hardware/wearable, firmware, wiring, enclosure, calibration and testing directories established through guides and README files.
- Exact board pin assignments are only documented where the hardware variant is explicitly known.

## Milestone 4 — Measurement specification + sensor testing
Status: STARTED
- Wearable measurement contract defined for PPG/HR/IBI/HRV/SpO2/GSR/temperature/motion/ECG.

## Milestone 5 — Signal-processing upgrade
Status: FOUNDATION
- Existing processors retained.
- NeuroKit2/pyHRV adapters are dependency-gated.

## Milestone 6 — Personal baseline
Status: EXISTING + HARDENING
- Existing baseline engine retained; future work adds versioned recalibration and stronger quality weighting.

## Milestone 7 — Longitudinal engine
Status: EXISTING + HARDENING
- Existing trend/persistence/recovery infrastructure retained; explicit states are documented.

## Milestone 8 — Multimodal fusion
Status: EXISTING + HARDENING
- Existing fusion engine retained; missing modalities must remain missing rather than becoming zero.

## Milestone 9 — Ultrasound/imaging
Status: FOUNDATION
- pydicom/MONAI capability adapters established; ovarian/PCOS models remain separate from generic ultrasound references.

## Milestone 10 — Model registry + AI lifecycle
Status: FOUNDATION
- Plugin discovery added; model lineage research is staged for MLflow/DVC/Optuna.

## Milestone 11 — Database/security/API
Status: FOUNDATION
- SQLAlchemy/Alembic dependency foundation added; migration is staged until existing data compatibility is tested.
- Security review remains focused on data/service-layer authorization.
- FastAPI remains a future service boundary because the current system is local-first/offline.

## Milestone 12 — Doctor workstation
Status: IN PROGRESS
- Existing patient-scoped workflow retained.
- Next implementation slice: persistent Add Patient → Test Session → Sensor Test → Analysis → Report workflow, replacing demo-card-only paths where backed by real services.

## Milestone 13 — Patient application
Status: IN PROGRESS
- Native Kotlin/Compose application retained.
- Future shared-client architecture may use Flutter/Riverpod/Dio/Drift/Melos.

## Milestone 14 — Testing
Status: IN PROGRESS
- Existing tests retained.
- V8.4 integration-boundary tests added.

## Milestone 15 — Build system
Status: EXISTING + CI HARDENING
- Existing setup/build scripts and Android Gradle wrappers retained.

## Milestone 16 — Documentation
Status: IN PROGRESS
- The hardware and implementation guides are being made explicit and traceable to actual capabilities.

## Completion rule
A milestone is complete only when code, tests and documentation describe the same implemented behavior. No document should claim a feature that the repository does not implement.
