# ARCHITECTURE - ENDO-TWIN V8.3+

Date: 2026-09-19
Version: 8.3+
Status: IMPLEMENTED

## One Sentence

ENDO-TWIN is the platform; CHRONO-PCOS is its first disease-specific model.

## Relationship

```
ENDO-TWIN
│
├── Core physiological platform
│   ├── identity
│   ├── observations
│   ├── signals
│   ├── features
│   ├── baseline
│   ├── longitudinal modelling
│   ├── multimodal fusion
│   ├── AI/model infrastructure
│   ├── explainability
│   ├── uncertainty
│   └── provenance
│
├── Applications
│   ├── ENDO-TWIN Desktop
│   ├── Doctor Desktop
│   ├── Patient Android
│   ├── Doctor Android
│   ├── Research / ML Lab
│   └── Diagnostics
│
└── Disease Models
    └── CHRONO-PCOS
        ├── PCOS modelling
        ├── chrono-metabolic analysis
        ├── ultrasound
        ├── longitudinal features
        └── reports
```

ENDO-TWIN disease-neutral, CHRONO-PCOS first disease-specific, not renamed PCOS application.

## Correct Architecture

```
ENDO-TWIN Core
 ↓
Disease Model Interface
 ↓
CHRONO-PCOS
```

Not:

```
ENDO-TWIN Core
 ↓
PCOS-specific imports everywhere
```

Verified by tests/test_endo_twin_isolation.py: Core no direct PCOS import PASS, true general architecture, extensible without rewriting core TEST4 PASS, main without disease model works TEST3 PASS.

## Layers

### Data Layer

patients, patient_identity, observations, measurements, signals, sensor_sessions, features, baselines, timeline_events, symptoms, cycles, clinical_observations, ultrasound_studies, ultrasound_features, model_versions, model_runs, predictions, reports, providers, doctor_notes, audit_events, provenance_records

Foreign keys, migrations, repositories, transactions, indexes, validation, UI not randomly manipulate raw tables.

### Twin Engine

identity, physiology, baseline, longitudinal, provenance, uncertainty

General engines no disease-specific assumptions.

### AI/ML Layer

General Physiological Models: personal_baseline, longitudinal, physiological_state, signal_processing, feature_extraction, chrono_metabolic

Disease Models: CHRONO-PCOS (first, implemented), Future Cardio, Future Sleep (concept, extensible)

### Applications

ENDO-TWIN Desktop, Doctor Desktop, Patient Android, Doctor Android, Research Lab, Diagnostics

### Flow

```
Sensor / Clinical Input / Image
        ↓
Observation
        ↓
Validation
        ↓
Signal / Measurement
        ↓
Quality Assessment
        ↓
Feature Extraction
        ↓
Personal Baseline
        ↓
Longitudinal Context
        ↓
Multimodal Fusion
        ↓
Disease Model
        ↓
Prediction
        ↓
Explanation
        ↓
Uncertainty
        ↓
Provenance
        ↓
Report / UI
```

Every layer independently testable.

## Folder Structure Target

```
ENDO-TWIN/
│
├── README.md
├── CHANGELOG.md
├── START.sh
├── pyproject.toml
├── requirements.txt
├── .gitignore
│
├── platform/
│   └── endo_twin/
│       ├── core/
│       ├── identity/
│       ├── data/
│       ├── physiology/
│       ├── signals/
│       ├── features/
│       ├── baseline/
│       ├── longitudinal/
│       ├── fusion/
│       ├── ai/
│       ├── model_registry/
│       ├── explainability/
│       ├── uncertainty/
│       ├── provenance/
│       ├── security/
│       └── services/
│
├── disease_models/
│   └── chrono_pcos/
│       ├── model/
│       ├── features/
│       ├── chrono_metabolic/
│       ├── ultrasound/
│       ├── reports/
│       ├── configs/
│       └── tests/
│
├── apps/
│   ├── endo_twin_desktop/
│   ├── doctor_desktop/
│   ├── patient_android/
│   ├── doctor_android/
│   ├── research_lab/
│   └── diagnostics/
│
├── science/
│   ├── datasets/
│   ├── signal_processing/
│   ├── training/
│   ├── evaluation/
│   └── validation/
│
├── models/
│   ├── registry/
│   ├── production/
│   ├── experimental/
│   └── metadata/
│
├── database/
│   ├── schema/
│   ├── migrations/
│   ├── repositories/
│   └── seed/
│
├── hardware/
│   ├── arduino/
│   ├── sensors/
│   └── wiring/
│
├── data/
│   ├── demo/
│   ├── synthetic/
│   └── public/
│
├── scripts/
│   ├── run/
│   ├── build/
│   ├── test/
│   ├── diagnostics/
│   └── setup/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── database/
│   ├── cross_patient/
│   ├── architecture/
│   ├── apps/
│   └── end_to_end/
│
├── docs/
│   ├── recovery/
│   ├── benchmarks/
│   ├── getting_started/
│   ├── architecture/
│   ├── science/
│   ├── ai_ml/
│   ├── applications/
│   ├── hardware/
│   ├── testing/
│   └── archive/
│
├── artifacts/
│   └── android/
│
└── archive/
    ├── legacy_versions/
    ├── legacy_launchers/
    └── obsolete_prototypes/
```

Current structure is close: src/endo_twin/ maps to platform/endo_twin/, disease_models/chrono_pcos/ already matches, apps/ main/doctor_desktop/patient_android/doctor_android/research_lab/diagnostics/ already exists, science/ is src/signal_processing/ + disease_models/ features, models/ is chrono_pcos_project V8/models/, database/ exists, hardware/ is arduino/, data/ exists, scripts/run/build/diagnostics/ exists, tests/ exists, docs/ exists, artifacts/android/ exists, archive/ is docs/legacy/ + LAUNCH/ legacy.

Principle: ONE CANONICAL LOCATION FOR EACH PURPOSE.

## Language Strategy

Python canonical for physiology, signal processing, numerical analysis, ML/AI, ultrasound research, feature engineering, baseline, longitudinal modelling, scientific backend, desktop scientific applications - NumPy, SciPy, Pandas, scikit-learn, PyTorch, OpenCV, PySide6.

Kotlin + Jetpack Compose canonical for Patient Android, Doctor Android - do NOT move scientific engine to Kotlin simply to have one language.

C/C++ for Arduino/embedded firmware.

## Security / Privacy

Local auth, role separation, encrypted storage (Fernet if available else prototype labeled), controlled export, audit logging, minimal collection, no cloud upload, patient cannot access other patient, doctor only authorized, role system PATIENT own data/measurements/results/manage/share DOCTOR authorized/review/analysis/notes/reports ADMIN provider directory/system config/demo data/verification.

No secrets in source, .env.example with no real secrets, .env not committed.

## Performance

Make it extremely fast engineering requirement: Application shell → cached state immediately → critical data → charts → advanced analysis → heavy model/imaging computation, async background workers lazy loading database indexes caching memoization vectorized numerical operations batch operations incremental feature calculation incremental signal processing model preloading result caching ring buffers streaming buffers, never repeatedly load entire database → recompute everything → redraw everything for every screen.

Real measurements: DB init 61 ms, patient creation 2 ms, list/search 0.1 ms, deterministic inference 0.3 ms, dashboard 22 ms, model loading 2386 ms bottleneck background preload, real inference 993 ms.

See docs/performance/PERFORMANCE_REPORT.md

## Offline-First

Core works without internet, demo/research works locally, no unnecessary cloud dependencies, if network unavailable degrade gracefully.

## UI/UX

Scientific Premium Calm Modern Fast Clear Trustworthy, strong typography hierarchy consistent spacing professional iconography meaningful cards charts with purpose progressive disclosure responsive grids clear navigation accessible contrast deliberate empty states loading states error states.

Shared design system: typography, icon language, spacing, semantic colors, chart language, terminology, status indicators, animation principles, but optimize for each role Patient simple understandable Doctor dense analytical Researcher technical exploratory.

See src/ui/theme_v83_premium.py

## Testing

Core unit physiology signal feature baseline longitudinal provenance uncertainty, database migrations CRUD foreign keys patient isolation, AI model loading schema validation preprocessing inference missing invalid metadata, applications navigation state patient selection error handling, Android Gradle build unit Compose tests where practical, end-to-end complete patient workflow ingest through report.

See docs/testing/TESTING.md

## Acceptance

ENDO-TWIN Launches, Dashboard opens, Navigation works, Demo data loads, Baseline works, Longitudinal works, AI/models works, Provenance visible, Errors handled.

Patient Android Real project Real Gradle wrapper assembleDebug succeeds APK generated Installation tested where possible Dashboard opens Patient data loads Patient isolation enforced.

Doctor Android Real project Real Gradle wrapper assembleDebug succeeds APK generated Patient registry works Search works Patient selection works Patient workspace works.

Doctor Desktop Launches, Multipatient registry, Search, Patient switching, Patient-scoped data, Reports, Models, Ultrasound, Notes, Provenance, Audit.

AI Real artifacts inspected Real inference verified hard-coded outputs removed from inference path feature mapping verified model metadata recorded explainability verified uncertainty represented honestly.

Science Original signal processing preserved Original models preserved Original datasets preserved Original hardware functionality preserved Original ultrasound work preserved No valuable scientific capability silently removed.

Performance Benchmarks created bottlenecks identified major bottlenecks optimized before/after measured.
