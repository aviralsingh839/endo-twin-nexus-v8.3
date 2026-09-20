# ENDO-TWIN Concept - General Platform

## One Sentence

**ENDO-TWIN is the platform; CHRONO-PCOS is its first disease-specific model.**

## Core Product Concept

The final product is:

**ENDO-TWIN — a general personalized physiological modelling platform/application.**

**CHRONO-PCOS is the FIRST disease-specific model/module available inside ENDO-TWIN.**

The application must therefore support:

- General physiological monitoring
- General patient data
- General measurements
- General longitudinal tracking
- General personal baseline
- General signal processing
- General multimodal fusion
- General AI/ML infrastructure
- General reports
- General patient/doctor workflows

AND THEN optionally:

- Disease-specific models

The first available disease model:

**CHRONO-PCOS**

Future disease models should be able to plug into same platform.

## Brand / UI Rule

Main application should NOT display only "ENDO-TWIN" as if it were empty platform.

It should feel like complete general-purpose application.

Suggested identity:

```
ENDO-TWIN
Personalized Physiological Modelling Platform
```

Home/dashboard should communicate:

```
"Understand your physiological patterns over time."
```

rather than:

```
"PCOS detection"
```

or:

```
"CHRONO-PCOS"
```

unless user has explicitly selected CHRONO-PCOS model.

## General Application

Main application should contain general sections such as:

- Dashboard - Personal Physiological Overview
- My Profile - General patient data
- Measurements - General measurements
- Sensors - General sensors
- Health Timeline - Chronological health events
- Personal Baseline - What is normal for YOU
- Trends - Longitudinal trends
- Physiological Patterns - Circadian, autonomic, metabolic, multisystem
- Sleep/Circadian - General sleep
- Activity - General activity
- Stress/Autonomic - General stress
- Metabolic Data - General metabolic
- Reports - General reports
- AI & Models - General and disease-specific
- Disease Models - Plugin architecture
- Doctor Sharing - General sharing
- Data & Privacy - Local-first privacy
- Settings - General settings

Exact terminology may be adapted to existing implementation.

## Disease Model System

Create disease-model/plugin architecture.

Example:

```
Disease Models

├── CHRONO-PCOS
│   ├── Overview
│   ├── PCOS-specific analysis
│   ├── Chrono-Metabolic analysis
│   ├── Ultrasound
│   ├── PCOS research model
│   └── PCOS report
│
├── Future Model A (concept)
├── Future Model B (concept)
└── Future Model C (concept)
```

Main ENDO-TWIN application must work even when no disease model selected.

## CHRONO-PCOS Migration

Existing original PCOS application must be migrated into:

```
disease_models/chrono_pcos/
```

BUT do NOT simply move entire old folder.

Separate:

**GENERAL FUNCTIONALITY** from **PCOS-SPECIFIC FUNCTIONALITY**

For example:

**GENERAL** (belongs in ENDO-TWIN Core):
- patient management
- sensors
- signal acquisition
- signal processing
- feature extraction
- baseline
- longitudinal analysis
- database
- reports
- provenance
- model registry
- uncertainty
- visualization

**PCOS-SPECIFIC** (belongs in CHRONO-PCOS):
- PCOS features
- PCOS risk logic
- PCOS model
- PCOS-specific ultrasound analysis
- Chrono-Metabolic PCOS interpretation
- PCOS-specific reports

General functionality belongs in ENDO-TWIN Core.
PCOS functionality belongs in CHRONO-PCOS.

## Important: Do NOT Lose Original Application

Original PCOS application's useful functionality is valuable.

Before migration, audit it.

Identify:

- screens
- workflows
- scientific modules
- sensors
- signal processing
- AI/ML
- ultrasound
- reports
- database
- patient management
- doctor workflow
- demos

Then migrate each component appropriately.

Do not replace working functionality with empty placeholder screens.

## Main Dashboard - General

Main dashboard should be general.

Example:

```
--------------------------------
ENDO-TWIN
Personal Physiological Overview
--------------------------------

Personal Baseline
[ View ]

Today's Measurements
[ View ]

Longitudinal Trends
[ View ]

Physiological Patterns
[ View ]

AI & Models
[ View ]

Disease Models
[ View ]

Reports
[ View ]

Doctor Sharing
[ View ]

--------------------------------

If CHRONO-PCOS is enabled:

Disease Models
→ CHRONO-PCOS
→ Open Analysis

But main dashboard itself remains general.
```

## AI & Models - General

Do NOT hard-code entire AI system around PCOS.

Create:

```
AI & Models

├── General Physiological Models
│
├── Personal Baseline Models
│
├── Longitudinal Models
│
└── Disease Models
      └── CHRONO-PCOS
```

This allows future models to be added without rewriting application.

## ENDO-TWIN Core

ENDO-TWIN Core should provide reusable infrastructure:

- Patient
- Observation
- Measurement
- SensorReading
- Signal
- Feature
- Baseline
- TimelineEvent
- LongitudinalSeries
- Model
- Prediction
- Explanation
- Uncertainty
- Provenance
- Report

No PCOS-specific assumptions should exist in these classes.

## General Data Model

Database must support general physiological data.

Example:

```
patients
measurements
signals
features
baselines
timeline_events
symptoms
clinical_observations
imaging
model_runs
predictions
reports
audit_events
provenance
```

Disease-specific data may then reference:

```
disease_model_id
patient_id
```

## Disease Model Interface

Create common interface such as:

```
DiseaseModel

with concepts like:

name
version
description
required_features
analyze()
explain()
generate_report()
validate_input()
get_uncertainty()
get_limitations()
```

CHRONO-PCOS implements this interface.
Future disease models can implement same interface.
Do NOT make core depend directly on CHRONO-PCOS.

## Application Navigation

Navigation should communicate:

```
GENERAL HEALTH / PHYSIOLOGY
        ↓
PERSONAL BASELINE
        ↓
LONGITUDINAL DATA
        ↓
AI & MODELS
        ↓
DISEASE MODELS
        ↓
CHRONO-PCOS
```

rather than making every screen PCOS-specific.

## Doctor Application - General

Doctor Desktop and Doctor Android should also be general.

Doctor selects:

```
Patient
↓
General physiological overview
↓
Measurements
↓
Timeline
↓
Baseline
↓
Trends
↓
Models
↓
Disease Models
↓
CHRONO-PCOS
```

This prevents doctor application from becoming permanently tied to PCOS.

## Patient Application - General

Patient Android should primarily be general.

Sections:

- Home - General
- Measurements - General
- Timeline - General
- Trends - General
- Baseline - General
- Symptoms - General
- Reports - General
- AI & Models - General
- Disease Models → CHRONO-PCOS
- Doctor Sharing - General
- Find Care - General
- Privacy - General
- Settings - General

Under Disease Models:

```
CHRONO-PCOS
```

If patient has not enabled disease model, general application still functions.

## Future Expansion

Architecture must make it possible to eventually have:

```
ENDO-TWIN

├── CHRONO-PCOS
├── Future Disease Model
├── Future Disease Model
├── Future Disease Model
└── Research Models
```

without creating:

- separate databases
- separate patient systems
- duplicate signal-processing pipelines
- duplicate baseline engines
- duplicate report engines
- duplicate authentication
- duplicate applications

Shared infrastructure remains ENDO-TWIN.

## Project Structure

Use clean structure similar to:

```
src/
└── endo_twin/
    ├── core/
    ├── data/
    ├── physiology/
    ├── signals/
    ├── features/
    ├── baseline/
    ├── longitudinal/
    ├── fusion/
    ├── ai/
    ├── models/
    ├── provenance/
    ├── explainability/
    └── uncertainty/

disease_models/
└── chrono_pcos/
    ├── model/
    ├── features/
    ├── ultrasound/
    ├── chrono_metabolic/
    ├── reports/
    └── tests/

apps/
├── main/
├── doctor_desktop/
├── patient_android/
├── doctor_android/
└── research_lab/

database/
docs/
tests/
scripts/
website/
archive/
```

## Documentation

Rewrite documentation to explain distinction clearly.

Create:

```
docs/endo_twin/
    CONCEPT.md
    PLATFORM_ARCHITECTURE.md
    CORE.md
    DISEASE_MODEL_SYSTEM.md

docs/chrono_pcos/
    MODEL.md
    FEATURES.md
    ULTRASOUND.md
    CHRONO_METABOLIC.md
```

README should say clearly:

```
"ENDO-TWIN is the general platform."

"CHRONO-PCOS is the first disease-specific model built on the platform."
```

Do NOT describe ENDO-TWIN as merely another name for CHRONO-PCOS.

## Version History

Preserve historical evolution:

```
V0 Original PCOS concept
V1+ Physiological sensing and data collection
V2+ Multisensor development
...
V8.x Integrated CHRONO-PCOS ecosystem
NEXT ENDO-TWIN platform architecture
```

Migration should preserve historical PCOS work while making architecture general.

## No Overengineering

Do not create unnecessary abstraction just for sake of saying "platform".

If general component currently used only by CHRONO-PCOS but clearly reusable, move it into Core.

If something genuinely PCOS-specific, keep it inside CHRONO-PCOS.

Use evidence from actual codebase to decide.

## Final Acceptance Test

Final project must pass conceptual tests:

**TEST 1**: Launch main application. It should make sense even if user knows nothing about PCOS. PASS = general physiological platform.

**TEST 2**: Open Disease Models. CHRONO-PCOS appears. PASS = disease-specific module.

**TEST 3**: Disable/remove CHRONO-PCOS temporarily. Main ENDO-TWIN application must still launch and function. PASS = true general architecture.

**TEST 4**: Add dummy future disease model. Possible without rewriting core application. PASS = extensible architecture.

**TEST 5**: Open CHRONO-PCOS. Original useful PCOS functionality must still exist. PASS = migration preserved scientific functionality.

**TEST 6**: Patient A and Patient B. No cross-patient data. PASS = isolation.

## Most Important Final Principle

Do not build:

```
"an ENDO-TWIN app with a PCOS feature."
```

Build:

```
"A general ENDO-TWIN physiological modelling platform whose first disease-specific intelligence module is CHRONO-PCOS."
```

User should understand project in one sentence:

```
"ENDO-TWIN is the platform; CHRONO-PCOS is its first disease-specific model."
```

Everything else should follow this architecture.
