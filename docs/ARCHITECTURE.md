# Architecture - CHRONO-PCOS V8.3+

## Overview

Local-first multimodal AI-assisted PCOS/PCOD risk pre-screening research ecosystem

Sense • Model • Predict • Personalize • Connect

Research / risk-screening output — not a medical diagnosis

Goal: sensing, signal processing, multimodal AI, ultrasound, longitudinal, patient/doctor apps, local storage, care discovery, educational resources

Must NOT claim diagnosis; distinguish risk-screening/research vs clinical diagnosis

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        CHRONO-PCOS V8.3+                                │
│              Sense • Model • Predict • Personalize • Connect            │
│          Research / risk-screening output — not a medical diagnosis     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  SENSING LAYER                                                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │ MAX30102 │ │ MPU6050  │ │ DS18B20  │ │ ECG/BME  │      │
│  │ PPG IR+RED│ │ Motion  │ │ Temp     │ │ Skin     │ │ Proposed │      │
│  │ HR HRV   │ │ Activity│ │ Skin Temp│ │ Tonic    │ │          │      │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘      │
│       │            │            │            │            │            │
│       └────────────┴────────────┴────────────┴────────────┘            │
│                            │                                            │
│  TRANSPORT LAYER                                                       │
│  ┌──────────────────────────────────────────────────────────┐          │
│  │ Serial $CP3 CRC XOR 20Hz packet parsing reconnection    │          │
│  │ Demo mode simulated sensor without physical sensors      │          │
│  └──────────────────────┬───────────────────────────────────┘          │
│                         │                                               │
│  SIGNAL PROCESSING LAYER                                               │
│  ┌──────────────────────────────────────────────────────────┐          │
│  │ Quality Control 0-1 per channel ppg motion temp reason   │          │
│  │ Filtering bandpass 0.5-4Hz PPG lowpass baseline motion   │          │
│  │ Baseline Removal PPG drift  temp         │          │
│  │ Artifact Detection motion MPU6050 correlation amplitude  │          │
│  │ Missing Handling short gaps interpolation quality penalty│          │
│  │ Feature Extraction established derived experimental      │          │
│  │ Graceful failure sensor unavailable/disconnected/noisy   │          │
│  └──────────────────────┬───────────────────────────────────┘          │
│                         │                                               │
│  CHRONO-METABOLIC FINGERPRINTING                                       │
│  ┌──────────────────────────────────────────────────────────┐          │
│  │ Personal Baseline mean median std MAD rolling confidence │          │
│  │ Longitudinal 6 scenarios stable gradual persistent temp  │          │
│  │ Circadian HR/HRV 24h pattern disruption                  │          │
│  │ Autonomic HRV-based regulation                             │          │
│  │ Variability HRV RMSSD SDNN pNN50                         │          │
│  │ Activity motion day/night                                │          │
│  │ Temp skin temp slope circadian                           │          │
│  │ Metabolic multimodal HR HRV activity temp hypothesized│         │
│  │ Provenance MEASURED CLINICALLY ENTERED IMAGE MODEL UNKNOWN│         │
│  └──────────────────────┬───────────────────────────────────┘          │
│                         │                                               │
│  AI/ML LABORATORY                                                       │
│  ┌──────────────────────────────────────────────────────────┐          │
│  │ Data public 541 rows synthetic 10 subjects 30 days 6     │          │
│  │ scenarios 60 days wrist_ppg SYNTHETIC clearly labelled   │          │
│  │ Features established MEASURED derived EXPERIMENTAL       │          │
│  │ Training ModelTrainer subject-level split no leakage     │          │
│  │ Validation ModelEvaluator metrics Train/Val/Test leakage │          │
│  │ Registry name version dataset version training date      │          │
│  │ Explainability ShapExplainer SHAP values understandable  │          │
│  │ Modules PCOS Sleep Cardiometabolic Autonomic risk only   │          │
│  │ Fusion MultimodalFusion confidence weighted quality      │          │
│  │ Uncertainty confidence model output not clinical certainty│         │
│  └──────────────────────┬───────────────────────────────────┘          │
│                         │                                               │
│  ULTRASOUND PIPELINE                                                   │
│  ┌──────────────────────────────────────────────────────────┐          │
│  │ 1 Import image path format size check label REAL/SYNTH   │          │
│  │ 2 Preview metadata shape                                 │          │
│  │ 3 Metadata path shape quality pending source label       │          │
│  │ 4 Preprocessing resize normalize denoise                 │          │
│  │ 5 Region/Structure cyst detection morphology volume      │          │
│  │ 6 Feature Extraction cyst size mm volume cc morphology   │          │
│  │ 7 Inference requires trained model if insufficient state │          │
│  │ 8 Visualization overlay confidence map                   │          │
│  │ 9 Uncertainty confidence None unless computed UNKNOWN    │          │
│  │ 10 Provenance CLINICALLY-ENTERED vs IMAGE-DERIVED 0.20   │          │
│  │ 11 Export/Report storage ultrasound_records table        │          │
│  │ Quality gate UNKNOWN by design provenance distinction    │          │
│  └──────────────────────┬───────────────────────────────────┘          │
│                         │                                               │
│  LOCAL DATABASE - 18 Tables Local-First No Cloud                       │
│  ┌──────────────────────────────────────────────────────────┐          │
│  │ users patients profiles symptoms cycles sensor_sessions  │          │
│  │ ppg_data hrv_data gsr_data (legacy, unused) motion_data temp_data quality│          │
│  │ ultrasound_records model_results analysis_results reports│          │
│  │ doctor_notes providers 4 demo supplies 5 audit access    │          │
│  │ Methods create_user authenticate create_patient list etc │          │
│  │ Portability controlled export/import/backup/restore      │          │
│  │ Privacy local-first no cloud upload private health       │          │
│  └──────────────────────┬───────────────────────────────────┘          │
│                         │                                               │
│  PLATFORMS                                                             │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐          │
│  │ Patient    │ │ Doctor PC  │ │ Doctor     │ │ Public     │          │
│  │ Android    │ │ Full WS    │ │ Android    │ │ Website    │          │
│  │ Kivy       │ │ PySide6    │ │ Kivy       │ │ Static     │          │
│  │ Dashboard  │ │ Dashboard  │ │ Mobile     │ │ Home       │          │
│  │ Profile    │ │ Patients   │ │ Patient    │ │ Problem    │          │
│  │ Measure    │ │ Signals    │ │ List       │ │ How Works  │          │
│  │ Symptoms   │ │ Longitud.  │ │ Search     │ │ Technology │          │
│  │ Cycle      │ │ Ultrasound │ │ Profiles   │ │ Patient App│          │
│  │ Results    │ │ Advanced   │ │ Trends     │ │ Doctor App │          │
│  │ Reports    │ │ Reports    │ │ Screening  │ │ Care Disc. │          │
│  │ Sharing    │ │ Notes      │ │ Ultrasound │ │ Research   │          │
│  │ Find Care  │ │ Database   │ │ Reports    │ │ Safety     │          │
│  │            │ │ Provenance │ │ Notes      │ │ Privacy    │          │
│  │            │ │ Explanation│ │            │ │ Docs       │          │
│  └─────┬──────┘ └─────┬──────┘ └─────┬──────┘ └─────┬──────┘          │
│        │              │              │              │                 │
│        └──────────────┴──────────────┴──────────────┘                 │
│                         │                                               │
│  CARE DISCOVERY FIND CARE                                              │
│  ┌──────────────────────────────────────────────────────────┐          │
│  │ Providers 4 demo clearly marked demo verification_status │          │
│  │ demo is_demo 1 never falsely label real doctor verified  │          │
│  │ Supplies 5 no prescription sales no auto medication      │          │
│  │ Map/list distance specialty address hours services       │          │
│  │ contact directions OSM no API key offline-first          │          │
│  │ Verification verified/pending/unverified/demo            │          │
│  │ Separate from private records                            │          │
│  └──────────────────────────────────────────────────────────┘          │
│                                                                         │
│  REPORTING                                                             │
│  ┌──────────────────────────────────────────────────────────┐          │
│  │ Professional Research / risk-screening output — not a    │          │
│  │ medical diagnosis Model transparency name/version/input/ │          │
│  │ data quality/confidence/features/limitations never hide  │          │
│  │ uncertainty Data Provenance MEASURED CLINICALLY ENTERED  │          │
│  │ IMAGE-DERIVED MODEL-INFERRED UNKNOWN clearly separated   │          │
│  └──────────────────────────────────────────────────────────┘          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## Data Flow

```
SENSOR (MAX30102/MPU6050/DS18B20/ECG/BME280)
  → TRANSPORT (Serial $CP3 CRC XOR 20Hz packet parsing reconnection demo mode)
    → PARSING (timestamped storage)
      → QUALITY CONTROL (0-1 per channel ppg motion temp reason codes source labeling)
        → FILTERING (bandpass 0.5-4Hz PPG lowpass baseline motion lowpass temp median )
          → BASELINE REMOVAL (PPG drift  temp baseline)
            → ARTIFACT DETECTION (motion MPU6050 correlation PPG amplitude HR outlier temp jumps)
              → MISSING HANDLING (short gaps interpolation quality penalty long gaps mark missing not fabricate)
                → FEATURE EXTRACTION (established MEASURED HR bpm MAX30102 skin temp C DS18B20 motion MPU6050  derived HRV RMSSD SDNN pNN50 resting HR  activity level classified temp slope derivative pulse amplitude SpO2 IR/RED ratio experimental circadian sleep-wake estimation HR/HRV 24h pattern model-inferred limitations not polysomnography autonomic HRV-based metabolic multimodal chrono-metabolic fingerprint longitudinal trend personal baseline deviation)
                  → TIMESTAMPED STORAGE (sensor_sessions ppg_data hrv_data gsr_data (legacy, unused) motion_data temperature_data sensor_quality)
                    → PERSONAL BASELINE (mean median std MAD rolling confidence min obs circadian context learns what is normal for individual first)
                      → LONGITUDINAL CHANGE (6 scenarios stable baseline LOW CHANGE SIGNAL gradual deviation EARLY CHANGE SIGNAL persistent deviation PERSISTENT MULTIMODAL SIGNAL temporary disturbance TEMPORARY EVENT sensor failure LOW SENSOR CONFIDENCE recovery RECOVERY TREND)
                        → RISK LOGIC (PCOSModule SleepModule CardiometabolicModule AutonomicModule risk signals only NOT diagnosis confidence limitations NOT ESTABLISHED)
                          → MULTIMODAL FUSION (MultimodalFusion confidence weighted quality no hard-coded fake confidence preserves provenance source image → preprocessing → detected features → quality → uncertainty if feature cannot be reliably extracted return UNKNOWN never invent)
                            → EXPLANATION (ShapExplainer feature drivers SHAP values understandable language why system generated signal drivers baseline deviations trends model name version dataset version training date features target metrics validation strategy limitations never hide uncertainty manufacture confidence training results)
                              → REPORT/UI (professional reports Research / risk-screening output — not a medical diagnosis model transparency data provenance MEASURED CLINICALLY ENTERED IMAGE-DERIVED MODEL-INFERRED UNKNOWN clearly separated never present inference as measured fact)
                                → DATABASE (18 tables local-first)
                                  → PLATFORMS (Patient Android/PC demo Doctor PC full workstation Doctor Android mobile review Public Website scientific)
                                    → CARE DISCOVERY (FIND CARE map/list distance/specialty/address/hours/services/contact/directions OSM no API key offline-first verification verified/pending/unverified/demo never falsely label demo clearly marked separate from private records Example Nearby ABC Women's Clinic 1.2km Gynecology Verified [View][Directions] Supply discovery sensor accessories/monitoring/menstrual/general no prescription sales no auto medication)
```

## Module Architecture

### Patient Android

- Dashboard: patient overview today's status physiological measurements HR 72 bpm MEASURED quality 0.91 HRV RMSSD 48 ms DERIVED quality 0.85 Skin Temp 32.5°C MEASURED quality 0.88 Activity 35% MEASURED Sleep Regularity 75% MODEL-INFERRED trends longitudinal changes personal baseline mean median std MAD rolling confidence min obs circadian context alerts/flags education reports professional with disclaimer Research / risk-screening output — not a medical diagnosis privacy local-first no cloud upload default synchronization/export controlled export/import/backup/restore/encrypted package deliberate sharing not automatic
- Profile: minimal basic/questionnaire/cycle/symptoms
- Measurements: guided PPG/HR/HRV/motion/temp/quality graceful failure
- Symptoms: structured logging
- Cycle: tracking dates/length/irregularity/symptoms/notes not diagnosis
- Results: understandable language Data quality Good not raw unless advanced
- Reports: professional
- Doctor Sharing: controlled export local-first
- Find Care: FIND CARE
- Accessibility: large readable multilingual-ready offline-first Kivy SQLite Buildozer
- Expected APK: DIST/android/CHRONO_PCOS_Patient.apk source android/patient_app/main.py buildozer.spec build scripts BUILD_PATIENT_APK.sh status honest APK not built PC demo Kivy

### Doctor PC

- Dashboard: overview recent quality pending longitudinal
- Patient Management: create/search/open/archive/history
- Physiological: raw/filtered PPG/HR/HRV/motion/temp/quality/artifacts visualization time-series
- Advanced Analysis: circadian/autonomic/metabolic/fingerprint/multimodal/AI distinguishing categories explainability
- Ultrasound: all V8.3 caps 11 steps
- Longitudinal: comparison trends baseline deviation
- Notes: input/view
- Reports: professional with disclaimer Research / risk-screening output — not a medical diagnosis
- Data Provenance: MEASURED CLINICALLY ENTERED IMAGE-DERIVED MODEL-INFERRED UNKNOWN
- Model Explanation: drivers baseline deviations trends SHAP values understandable language model name version dataset version training date features target metrics validation strategy limitations never hide uncertainty
- Database: 18 tables local-first
- Diagnostics: actual checks PASS/WARN/FAIL never fake
- Role: doctor only authorized patients, patient cannot access other patient, admin manage provider directory/system config/demo data/verification
- Security: local auth/role separation/encrypted storage/controlled export/audit logging/minimal collection/no cloud
- Offline-first: core works without internet records/sensor/signal/AI/ultrasound/reports/DB internet optional provider directory/map/updates/sync
- UI: professional dense PySide6 1450x950 polished clearly separates OBSERVED ASSOCIATED MODEL-INFERRED UNKNOWN never mixes them

### Doctor Android

- Mobile companion patient list/search/profiles/recent/trends/screening/ultrasound/reports/notes/follow-up not duplicate full PC
- Touch-friendly mobile UI not desktop squeezed onto phone
- Kivy
- Expected APK: DIST/android/CHRONO_PCOS_Doctor.apk

### Scientific Core

- Sensor Quality
- Signal Processing: filtering baseline removal artifact detection missing handling quality control feature extraction
- Feature Extraction: established MEASURED derived EXPERIMENTAL
- Baseline: personal baseline
- Longitudinal: 6 scenarios
- Disease Modules: PCOS Sleep Cardiometabolic Autonomic risk signals only
- Fusion: MultimodalFusion
- Fingerprinting: ChronoMetabolicFingerprint
- Explainability: ShapExplainer

### AI/ML Laboratory

- Dataset: public synthetic clinical labeling REAL/SYNTHETIC/USER-ENTERED
- Data validation: missing impossible flatline excessive noise motion artifacts packet corruption stale data bad data must not silently become model input
- Preprocessing: filtering baseline removal artifact detection missing handling
- Feature engineering: established derived experimental
- Training: ModelTrainer input features quality scores dataset public 541 rows synthetic cohort 10 subjects 30 days 6 scenarios 60 days split subject-level not row-level avoid leakage validation 12 categories engineering vs clinical separation no fabricated accuracy state if insufficient metrics accuracy precision recall F1 AUC classification MAE regression never fabricate percentages
- Validation: ModelEvaluator metrics Train/Validation/Test split leakage detection subject-level validation where appropriate avoid data leakage longitudinal subjects split at SUBJECT level clearly separate ENGINEERING VALIDATION implemented from CLINICAL VALIDATION NOT ESTABLISHED
- Testing: subject-level validation reproducibility hardware failure tests noisy data missing sensor handling multimodal fusion disease module isolation
- Leakage Detection: never allow same patient/time-series samples to silently appear across incompatible splits subject-level split not row-level
- Model Comparison: PCOSModule vs SleepModule vs CardiometabolicModule vs AutonomicModule each with consistent API name version required_features optional_features predict explain confidence limitations returns structured research signals never DISEASE DETECTED
- Explainability: ShapExplainer feature drivers SHAP values understandable language why system generated signal drivers baseline deviations trends model name version dataset version training date features target metrics validation strategy limitations never hide uncertainty manufacture confidence training results never invent model metrics if no trained model exists show Model not trained rather than fake accuracy confidence model output not clinical certainty quality scores 0-1 per channel artifact flags reason codes limitations model transparency
- Model Registry: model name version dataset version training date features target metrics validation strategy limitations model approval rollback inference uncertainty ModelTrainer ModelEvaluator MultimodalFusion ShapExplainer

### Ultrasound Pipeline

11 steps quality gate UNKNOWN by design provenance CLINICALLY-ENTERED vs IMAGE-DERIVED

### Local DB

SQLite 18 tables local-first no cloud upload private health to public website default no cloud portability controlled export/import/backup/restore/encrypted package deliberate not automatic

### Care Discovery

FIND CARE map/list distance/specialty/address/hours/services/contact/directions OSM no API key offline-first verification verified/pending/unverified/demo never falsely label demo clearly marked separate from private records Example Nearby ABC Women's Clinic 1.2km Gynecology Verified [View][Directions] Supply discovery sensor accessories/monitoring/menstrual/general no prescription sales no auto medication Provider verification statuses verified/pending/unverified/demo never falsely label real doctor/clinic verified prototype allow demo clearly marked Provider-directory separate from private records

### Public Website

Home tagline What is Problem How it Works flow Sensors→Signal→Feature→Baseline→Longitudinal→Multimodal→Fingerprint→Screening→Doctor Review Technology Arduino/PPG/HR/HRV/motion/temp/ultrasound/AI/signal Patient App Doctor App Care Discovery Research hypothesis/methodology Benefits without unsupported claims Safety limitations Privacy local-first role offline Docs links 25 docs Footer Design serious modern scientific clean typography diagrams accessible colors responsive mobile strong identity avoid excessive animations/fake claims/stock AI doctor/100% accurate/fake hospital branding

Structure: HOME hero Sense•Model•Predict•Personalize with architecture preview PROBLEM PCOS challenges longitudinal importance HOW IT WORKS interactive flow Sensors→Signal→Quality→Features→Baseline→Longitudinal→AI→Ultrasound→Fusion→Explanation→Patient/Doctor with MEASURED/CLINICALLY-ENTERED/IMAGE-DERIVED/MODEL-INFERRED/UNKNOWN labels HARDWARE actual sensors MAX30102/MPU6050/DS18B20/ECG/BME280 with what/why/signal/limitations/implemented PHYSIOLOGY HR/HRV/motion/temp/sleep/autonomic/metabolic CHRONO-METABOLIC major section circadian/autonomic/metabolic/temporal/baseline/multisystem with provenance DIGITAL TWIN computational representation not simulation AI/ML Data/Features/Training/Validation/Registry/Explainability distinction Data vs Model vs Inference vs Clinical ULTRASOUND pipeline 11 steps quality gate UNKNOWN by design provenance CLINICALLY-ENTERED vs IMAGE-DERIVED PLATFORMS Patient/Doctor detailed sections ANDROID APK build workflow DATABASE 18 tables local-first REPORTING professional with disclaimer CARE DISCOVERY FIND CARE demo providers TIMELINE V0-V8.3+ interactive with IMPLEMENTED/PROPOSED/CONCEPT SAFETY research prototype disclaimer ROADMAP CHRONO-PCOS→ENDO-TWIN NEXUS DEMO 16 steps DOCS 25+2

Design: serious modern scientific clean typography diagrams accessible colors responsive mobile strong identity avoid excessive animations/fake claims/stock AI doctor/100% accurate/fake hospital branding

### Reporting

Professional with disclaimer Research / risk-screening output — not a medical diagnosis Model transparency name/version/input/data quality/confidence/features/limitations never hide uncertainty Data Provenance MEASURED CLINICALLY ENTERED IMAGE-DERIVED MODEL-INFERRED UNKNOWN clearly separated never present inference as measured fact

## Project Structure

```
chrono-pcos-v8.1/
  COMPLETE_LAUNCHER.sh - Root launcher auto-detects project root
  SETUP.sh - Wrapper for setup_garuda.sh
  setup_garuda.sh - 10-step setup fixed ID_LIKE unbound
  BUILD_PATIENT_APK.sh - Build Patient APK 7.6K
  BUILD_DOCTOR_APK.sh - Build Doctor APK 6.6K
  BUILD_ALL_APKS.sh - Wrapper 2.6K
  LAUNCH/ - 20+ launchers + SETUP + BUILD + setup_garuda.sh
  launchers/ - Same as LAUNCH/
  launcher/main.py - Complete Control Center 1450x950 polished AppCard 320x180-400x220 WordWrap margins 20 scroll widgetResizable grid 3 cols status 4 cols footer wrapping Fusion non-blocking Popen
  desktop/doctor_app/main_enhanced.py - Doctor PC polished 1450x950 Dashboard Patients Signals Longitudinal Ultrasound AI/ML Reports Provenance Explanation Database Diagnostics
  desktop/doctor_app/patient_management.py - DoctorDashboard PatientManager PhysiologicalDataViewer AdvancedAnalysisViewer UltrasoundViewer LongitudinalViewer ReportGenerator
  android/patient_app/main.py - Patient Android Kivy TabbedPanel
  android/patient_app/buildozer.spec - Buildozer config
  android/doctor_app/main.py - Doctor Android Kivy
  android/doctor_app/buildozer.spec - Buildozer config
  core/ - Scientific core signal_processing sensors features analysis ai ultrasound chrono_metabolic
  src/ - V8.3 preserved core/ui/main_window.py core/feature_extraction.py disease_modules/
  database/database.py - LocalDatabase 18 tables
  provider_network/care_discovery.py - CareDiscoveryEngine FIND CARE
  website/index.html - Extensive scientific site 40K+ HOME PROBLEM HOW IT WORKS HARDWARE PHYSIOLOGY CHRONO-METABOLIC DIGITAL TWIN AI/ML ULTRASOUND PLATFORMS ANDROID DATABASE REPORTING CARE DISCOVERY TIMELINE SAFETY ROADMAP DEMO DOCS
  website/style.css - Polished modern CSS variables primary #0f172a accent #0ea5e9 shadows sm/md/lg header sticky gradient nav flex wrap hero gradient 135deg radial overlay architecture-preview backdrop blur section 4rem alt #f8fafc grid gap 1.5rem card hover -2px shadow-md flow-step border-left 4px accent timeline dot 44px active dot accent provider-card demo #fffbeb yellow left warning-box gradient #fef2f2 #fee2e2 left red footer gradient responsive 1024 768 no excessive animations
  website/script.js - Minimal JS smooth scroll pushState highlightNav scrollY active link background rgba(14,165,233,0.2) IntersectionObserver fade-in opacity 0→1 translateY 10→0 0.4s console logs integrity
  DIST/android/ - APK output CHRONO_PCOS_Patient.apk Doctor.apk .gitkeep
  logs/ - Build logs diagnostics logs
  docs/ - 25+ docs ANDROID_BUILD_GUIDE INSTALLATION BUILD_GUIDE TROUBLESHOOTING ARCHITECTURE TESTING_REPORT GARUDA_LAUNCH_GUIDE SHOWCASE_GUIDE
  demo/full_showcase.py - 16 steps polished GUI NEXT/SKIP/EXIT
  tests/ - Tests DB/sensor/signal/artifact/missing/reconnection/permissions/report/import/export/Android UI/PC UI/AI/ultrasound failures
  requirements.txt - PySide6 pyqtgraph numpy pandas sklearn pyserial kivy
```

## Security

Local auth/role separation/encrypted storage/controlled export/audit logging/minimal collection/no cloud patient cannot access other patient doctor only authorized patients roles PATIENT own data/collect/view/manage/share DOCTOR authorized/review/analysis/notes/reports ADMIN manage provider directory/system config/demo data/verification

## Offline-First

Core works without internet records/sensor/signal/AI/ultrasound/reports/DB internet optional provider directory/map/updates/sync

## UI/UX

Consistent visual identity patient simple friendly doctor professional dense website scientific accessible consistent typography/icons/terminology/logo/navigation/design serious modern scientific clean typography diagrams accessible colors responsive mobile strong identity avoid excessive animations/fake claims/stock AI doctor/100% accurate/fake hospital branding

## Performance

Ordinary hardware avoid heavy cloud/expensive APIs/proprietary paid/unnecessary frameworks keep Python/PySide6/PyQtGraph/NumPy/Pandas/PySerial no Dash/Plotly/Flask/Electron unless reason Android appropriate native/mobile offline SQLite

## Development Strategy

Staged phases 1 Audit 2 Refactor core reusable 3 Local DB 4 Connect desktop 5 Patient Android 6 Doctor Android 7 Care discovery 8 Website 9 Integrate/test 10 Deployment/docs No fake features real or prototype labeled Demo mode strong workflow DEMO PATIENT→Simulated sensor→Signal→AI→Fingerprint→Ultrasound→Screening→Doctor dashboard→Report labeled DEMO/SIMULATED Science-fair 17 steps integrated ecosystem Docs 25 docs 01_PROJECT_OVERVIEW to 25_RESEARCH_METHODOLOGY WHAT and WHY

## Acceptance

Preserve every V8.3 major/AI/ultrasound/sensor/demo new ecosystem Patient Android/Doctor Android/Doctor PC/Local DB/export/import/Care/Provider/Supply/Website engineering modular/offline/error/security/role/testing/docs scientific integrity no fabricated AI/accuracy/false claims clear screening vs diagnosis limitations explainable

## Final Quality

One coherent digital health research ecosystem not collection random apps/mockups/disconnected demos share common terminology/data model/scientific foundation/identity/UI/safety language
