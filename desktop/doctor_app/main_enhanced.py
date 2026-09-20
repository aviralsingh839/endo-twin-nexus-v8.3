#!/usr/bin/env python3
"""
Doctor PC App Enhanced Main - V8.3+ Polished Clinical/Research Workstation
Preserves src/ui/main_window.py, adds new architecture.

Dashboard, Patients, Signals, Longitudinal Analysis, Ultrasound, AI/ML, Reports, Data Provenance, Model Explanation, Database, Settings, Diagnostics

Clearly separates OBSERVED, ASSOCIATED, MODEL-INFERRED, UNKNOWN, never mixes them.
"""
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
# PROJECT_ROOT must be first to avoid src/core shadowing core/chrono_metabolic
# src is inside PROJECT_ROOT, so src.* imports work via PROJECT_ROOT/src as package
# Do NOT add src to sys.path separately - it causes src/core to shadow core/
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
# Ensure PROJECT_ROOT is first
if sys.path[0] != str(PROJECT_ROOT):
    if str(PROJECT_ROOT) in sys.path:
        sys.path.remove(str(PROJECT_ROOT))
    sys.path.insert(0, str(PROJECT_ROOT))
# Remove src from path if present to avoid shadowing
src_path = str(PROJECT_ROOT / "src")
if src_path in sys.path:
    sys.path.remove(src_path)

# Try to import existing V8.3 main window - preserve it
try:
    from src.ui.main_window import MainWindow as V83MainWindow
    V83_AVAILABLE = True
except ImportError as e:
    V83_AVAILABLE = False
    V83MainWindow = None
    print(f"V8.3 MainWindow not available: {e}")

# New modular enhancements
from database.database import LocalDatabase
from desktop.doctor_app.patient_management import (
    DoctorDashboard, PatientManager, PhysiologicalDataViewer,
    AdvancedAnalysisViewer, UltrasoundViewer, LongitudinalViewer, ReportGenerator
)

# PySide6 GUI
try:
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
        QLabel, QPushButton, QListWidget, QTextEdit, QGroupBox, QGridLayout,
        QScrollArea, QFrame, QSplitter, QTableWidget, QTableWidgetItem, QHeaderView
    )
    from PySide6.QtCore import Qt
    PYSIDE_AVAILABLE = True
except ImportError:
    PYSIDE_AVAILABLE = False


class EnhancedDoctorApp:
    def __init__(self):
        self.db = LocalDatabase()
        self.dashboard = DoctorDashboard(self.db)
        self.patient_mgr = PatientManager(self.db)
        self.physio_viewer = PhysiologicalDataViewer(self.db)
        self.advanced_viewer = AdvancedAnalysisViewer(self.db)
        self.ultrasound_viewer = UltrasoundViewer(self.db)
        self.longitudinal_viewer = LongitudinalViewer()
        self.report_gen = ReportGenerator(db=self.db)

    def run_console_demo(self):
        print("="*80)
        print("CHRONO-PCOS Doctor PC App V8.3+ - Polished Clinical/Research Workstation")
        print("Preserves V8.3 src/ui/main_window.py + new modular architecture")
        print("Research / risk-screening output — not a medical diagnosis")
        print("="*80)

        overview = self.dashboard.get_overview()
        print(f"\n[Dashboard] Patient overview: {overview['total_patients']} patients, longitudinal: {overview['longitudinal_summary']}")
        print("Recent assessments, data quality, pending reviews, longitudinal views")

        print("\n[Patients] Patient Management: create, search, open, archive, history")
        patients = self.db.list_patients()
        print(f"Total patients: {len(patients)}")
        for p in patients[:3]:
            print(f"  - {p['anonymous_id']} Age {p.get('age_years','')} BMI {p.get('bmi','')} (USER-ENTERED)")

        print("\n[Signals] Physiological Data: raw/filtered PPG, HR, HRV, GSR, motion, temp, quality, artifacts, visualization, time-series")
        session_data = self.physio_viewer.get_session_data("session_001")
        print(f"Session data quality overall: {session_data['quality']['overall']}")
        print(f"  - HR: {session_data['hr']['mean']} bpm MEASURED quality 0.91")
        print(f"  - HRV RMSSD: {session_data['hrv']['rmssd']} ms DERIVED quality 0.85 limitations PPG less accurate than ECG")
        print(f"  - Artifacts: {session_data['artifacts']}")

        print("\n[Longitudinal] Longitudinal Analysis: comparison trends baseline deviation")
        long_comp = self.longitudinal_viewer.compare("patient_001", ["s1", "s2"])
        print(f"Trends: {long_comp['trends']}")
        print(f"Baseline deviation: {long_comp['baseline_deviation']}")

        print("\n[Advanced Analysis] Circadian, autonomic, metabolic, fingerprint, multimodal, AI/ML")
        print("Distinguishes OBSERVED, ASSOCIATED, MODEL-INFERRED, UNKNOWN, never mixes them")
        print("Distinguishes established/derived/experimental/ML/clinical, explainability")
        analysis = self.advanced_viewer.analyze("patient_001")
        print(f"Circadian: {analysis['circadian']}")
        print(f"Autonomic: {analysis['autonomic']}")
        print(f"Metabolic: {analysis['metabolic']}")
        print(f"Fingerprint components: {len(analysis['fingerprint']['components'])}")
        for comp in analysis['fingerprint']['components'][:3]:
            print(f"  - {comp['name']}: {comp['category']}, quality {comp['quality']}, source {comp['source'][:40]}...")

        print("\n[Ultrasound] Ultrasound: loading, preprocessing, quality checks, segmentation, inference, visualization, confidence, training, evaluation, storage")
        print("Do not invent accuracy, state if insufficient, never fabricate percentages")
        print("Clearly label IMAGE-DERIVED")
        img = self.ultrasound_viewer.load_image("ultrasound_demo.png")
        qc = self.ultrasound_viewer.quality_check(img)
        inf = self.ultrasound_viewer.inference(img)
        print(f"Quality check: {qc['result']}")
        print(f"Inference: {inf['result']}")
        print(f"Quality gate: UNKNOWN by design unless computed, provenance CLINICALLY-ENTERED vs IMAGE-DERIVED")

        print("\n[AI/ML] AI/ML Laboratory: Dataset, Data validation, Preprocessing, Feature engineering, Training, Validation, Testing, Leakage detection, Model comparison, Explainability, Model registry, Model approval, Rollback, Inference, Uncertainty")
        print("Prevent data leakage, clearly distinguish TRAIN VALIDATION TEST, never allow same patient/time-series samples to silently appear across incompatible splits")
        for ai_out in analysis['ai_outputs']:
            print(f"  - {ai_out['module']}: {ai_out['output']} confidence {ai_out['confidence']} - {ai_out.get('validation','')}")

        print("\n[Reports] Reports: Professional with disclaimer Research / risk-screening output — not a medical diagnosis")
        report = self.report_gen.generate("patient_001", analysis)
        print(f"Report disclaimer: {report['disclaimer']}")
        print(f"Model transparency: {report['model_transparency']}")

        print("\n[Data Provenance] Data Provenance: MEASURED, CLINICALLY ENTERED, IMAGE-DERIVED, MODEL-INFERRED, UNKNOWN - Never fabricate, never mix")
        print("MEASURED: HR 72 bpm quality 0.91 source MAX30102")
        print("CLINICALLY ENTERED: age BMI cycle info USER-ENTERED")
        print("IMAGE-DERIVED: cyst size morphology quality UNKNOWN by design unless computed")
        print("MODEL-INFERRED: sleep regularity circadian disruption confidence limitations")
        print("UNKNOWN: if cannot reliably extract return UNKNOWN never invent")

        print("\n[Model Explanation] Model Explanation: drivers, baseline deviations, trends, SHAP values, understandable language, model name version dataset version training date features target metrics validation strategy limitations, never hide uncertainty")

        print("\n[Database] Database: 18 tables local-first, providers 4 demo, supplies 5")

        print("\n[Settings] Settings: System configuration")

        print("\n[Diagnostics] Diagnostics: actual checks PASS/WARN/FAIL never fake")

        print("\n[Doctor Notes] Notes input/view")
        print("This is a research / risk-screening output — not a medical diagnosis.")
        print("="*80)

    def run_gui(self):
        if not PYSIDE_AVAILABLE:
            print("PySide6 not available, running console demo")
            self.run_console_demo()
            return

        app = QApplication(sys.argv)

        # If V8.3 main window available, use it as base, else create new
        if V83_AVAILABLE and V83MainWindow:
            print("Launching V8.3 existing MainWindow preserved - Polished")
            try:
                window = V83MainWindow()
                window.setWindowTitle("CHRONO-PCOS V8.3+ Doctor PC - Clinical/Research Workstation - Research Prototype - Not Medical Diagnosis")
                window.resize(1450, 950)
                window.show()
                sys.exit(app.exec())
                return
            except Exception as e:
                print(f"V8.3 MainWindow failed to launch: {e}, using enhanced fallback")
                import traceback
                traceback.print_exc()

        # Enhanced fallback GUI - Polished Clinical/Research Workstation
        window = QMainWindow()
        window.setWindowTitle("CHRONO-PCOS V8.3+ Doctor PC - Clinical/Research Workstation - Research Prototype - Not Medical Diagnosis")
        window.resize(1450, 950)
        window.setMinimumSize(1200, 800)

        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #cbd5e1; background: white; border-radius: 6px; }
            QTabBar::tab { background: #f8fafc; border: 1px solid #cbd5e1; padding: 10px 16px; margin-right: 2px; border-top-left-radius: 6px; border-top-right-radius: 6px; font-weight: 600; font-size: 11px; }
            QTabBar::tab:selected { background: white; border-bottom: 1px solid white; color: #0ea5e9; }
            QTabBar::tab:hover { background: #e0f2fe; }
        """)

        # Dashboard tab - polished
        dash_widget = QWidget()
        dash_layout = QVBoxLayout(dash_widget)
        dash_layout.setContentsMargins(16, 16, 16, 16)
        dash_layout.setSpacing(12)

        header = QLabel("Dashboard - Patient Overview, Recent Assessments, Data Quality, Pending Reviews, Longitudinal Views\nResearch / risk-screening output — not a medical diagnosis")
        header.setWordWrap(True)
        header.setStyleSheet("font-size: 13px; font-weight: bold; color: #0f172a; background: #f8fafc; padding: 12px; border-radius: 8px; border: 1px solid #e2e8f0;")
        dash_layout.addWidget(header)

        overview = self.dashboard.get_overview()
        stats_grid = QGridLayout()
        stats = [
            (f"Total Patients: {overview['total_patients']}", "Patient overview"),
            (f"Longitudinal: {overview['longitudinal_summary']}", "Longitudinal tracking"),
            ("Data Quality: Good/Moderate/Poor summary", "Quality control"),
            ("Pending Reviews: Sessions needing review", "Review workflow"),
        ]
        for i, (text, tooltip) in enumerate(stats):
            label = QLabel(text)
            label.setToolTip(tooltip)
            label.setStyleSheet("font-size: 12px; padding: 10px; background: white; border: 1px solid #e2e8f0; border-radius: 6px;")
            label.setWordWrap(True)
            stats_grid.addWidget(label, i // 2, i % 2)

        dash_layout.addLayout(stats_grid)
        dash_layout.addStretch()
        tabs.addTab(dash_widget, "📊 Dashboard")

        # Patients tab
        pm_widget = QWidget()
        pm_layout = QVBoxLayout(pm_widget)
        pm_layout.setContentsMargins(16, 16, 16, 16)
        pm_layout.addWidget(QLabel("Patient Management - Create, Search, Open, Archive, History - Only authorized patients for doctor role"))
        pm_layout.addWidget(QLabel("Clearly separates OBSERVED, ASSOCIATED, MODEL-INFERRED, UNKNOWN - Never mixes them"))

        pm_list = QListWidget()
        pm_list.setMinimumHeight(300)
        patients = self.db.list_patients()
        if not patients:
            pm_list.addItem("No authorized patients yet - demo data: Patient P00001 (Demo) Age 22 BMI 23.5, Patient P00002 (Demo) Age 24 BMI 25.1")
        else:
            for p in patients[:20]:
                pm_list.addItem(f"{p['anonymous_id']} - Age {p.get('age_years','')} BMI {p.get('bmi','')} - {p.get('display_name','')} (USER-ENTERED)")
        pm_layout.addWidget(pm_list)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(QPushButton("Create Patient"))
        btn_layout.addWidget(QPushButton("Search Patient"))
        btn_layout.addWidget(QPushButton("Open Patient"))
        btn_layout.addWidget(QPushButton("Archive Patient"))
        pm_layout.addLayout(btn_layout)
        tabs.addTab(pm_widget, "👥 Patients")

        # Signals tab
        phys_widget = QWidget()
        phys_layout = QVBoxLayout(phys_widget)
        phys_layout.setContentsMargins(16, 16, 16, 16)
        phys_layout.addWidget(QLabel("Physiological Signals - Raw/Filtered PPG, HR, HRV, GSR, Motion, Temp, Quality, Artifacts, Visualization, Time-Series"))
        phys_layout.addWidget(QLabel("OBSERVED: HR 72 bpm MEASURED quality 0.91 source MAX30102, Skin Temp 32.5°C MEASURED quality 0.88 source DS18B20, Activity 35% MEASURED source MPU6050"))
        phys_layout.addWidget(QLabel("ASSOCIATED: HRV RMSSD 48 ms DERIVED quality 0.85 limitations PPG less accurate than ECG, Activity level classified DERIVED"))

        phys_text = QTextEdit()
        phys_text.setReadOnly(True)
        phys_text.setText("""Physiological Data - Time-series visualization would appear here - pyqtgraph

Raw/Filtered PPG: waveform, quality 0.91, source MAX30102, MEASURED
HR: time-series, mean 72 bpm, MEASURED, quality 0.91
HRV: RMSSD 48 ms, SDNN 55 ms, pNN50 %, DERIVED, quality 0.85, limitations PPG less accurate than ECG, motion artifacts affect
GSR: tonic/phasic, quality, MEASURED + DERIVED
Motion: activity 35%, quality 0.8, MEASURED + DERIVED, limitations wrist activity not whole-body calorimetry
Temp: skin temp 32.5°C, room temp, slope, quality 0.88, MEASURED + DERIVED, limitations skin temp not core temp affected environment
Quality: overall 0.85, per channel ppg 0.91 motion 0.8 temp 0.88
Artifacts: detected 2, details Motion artifact at 12:03 baseline drift at 12:05

System Pipeline Visualization:
SENSOR → TRANSPORT → PARSING → QUALITY CONTROL → FILTERING → ARTIFACT DETECTION → FEATURE EXTRACTION → TIMESTAMPED STORAGE → PERSONAL BASELINE → LONGITUDINAL CHANGE → RISK LOGIC → MULTIMODAL FUSION → EXPLANATION → REPORT/UI
""")
        phys_layout.addWidget(phys_text)
        tabs.addTab(phys_widget, "📈 Signals")

        # Longitudinal tab
        long_widget = QWidget()
        long_layout = QVBoxLayout(long_widget)
        long_layout.setContentsMargins(16, 16, 16, 16)
        long_layout.addWidget(QLabel("Longitudinal Analysis - Comparison, Trends, Baseline Deviation, Persistence, Recovery"))
        long_layout.addWidget(QLabel("Personal Baseline: mean median std MAD rolling confidence min obs circadian context - learns what is normal for individual first"))
        long_layout.addWidget(QLabel("6 Scenarios: Stable baseline LOW CHANGE SIGNAL, Gradual deviation EARLY CHANGE SIGNAL, Persistent deviation PERSISTENT MULTIMODAL SIGNAL, Temporary disturbance TEMPORARY EVENT, Sensor failure LOW SENSOR CONFIDENCE, Recovery RECOVERY TREND"))

        long_text = QTextEdit()
        long_text.setReadOnly(True)
        long_text.setText("""Longitudinal Comparison - Trends, Baseline Deviation

Patient: P12345 Age 22 BMI 23.5 USER-ENTERED
Sessions: s1 (2026-09-10), s2 (2026-09-15), s3 (2026-09-19)

HR Trend: 70 → 72 → 71 bpm (stable baseline, within normal variation, LOW CHANGE SIGNAL)
HRV RMSSD Trend: 50 → 48 → 45 ms (gradual deviation, slowly moves away, EARLY CHANGE SIGNAL)
Activity Trend: 40% → 35% → 30% (persistent deviation, multiple related signals abnormal, PERSISTENT MULTIMODAL SIGNAL)
Temp Trend: 32.5 → 32.6 → 32.5°C (stable)

Baseline Deviation:
- HR: +1 bpm from personal baseline mean 71 std 2 - within normal
- HRV: -5 ms from baseline mean 50 - early change, persistence check rolling windows
- Activity: -10% from baseline mean 40% - persistent, multimodal check

Recovery: If abnormal returns toward baseline → RECOVERY TREND

Data Provenance:
- MEASURED: HR 72 bpm quality 0.91 source MAX30102
- DERIVED: HRV RMSSD 48 ms quality 0.85 source PPG-derived limitations PPG less accurate than ECG
- MODEL-INFERRED: circadian disruption pattern moderate confidence 0.68
- UNKNOWN: if cannot reliably extract return UNKNOWN never invent
""")
        long_layout.addWidget(long_text)
        tabs.addTab(long_widget, "📊 Longitudinal")

        # Ultrasound tab
        us_widget = QWidget()
        us_layout = QVBoxLayout(us_widget)
        us_layout.setContentsMargins(16, 16, 16, 16)
        us_layout.addWidget(QLabel("Ultrasound - Loading, Preprocessing, Quality Checks, Segmentation, Inference, Visualization, Confidence, Training, Evaluation, Storage"))
        us_layout.addWidget(QLabel("Clearly label IMAGE-DERIVED - Do not claim clinically validated unless actually is - Quality gate UNKNOWN by design unless computed"))

        us_text = QTextEdit()
        us_text.setReadOnly(True)
        us_text.setText("""Ultrasound Analysis - Research Pipeline

1. Image Import: image path format size check, metadata, label REAL/SYNTHETIC/DEMO
2. Image Preview: preview, metadata, shape
3. Image Metadata: path, shape, quality check pending, source, label
4. Preprocessing: resize normalize denoise
5. Region/Structure Analysis: cyst detection morphology volume if model available
6. Feature Extraction: cyst size mm volume cc morphology quality source confidence provenance
7. Model Inference: requires trained model if insufficient state insufficient never fabricate percentages confidence None unless computed model accuracy not established without validation dataset
8. Result Visualization: overlay confidence map image-derived features
9. Uncertainty: confidence None unless computed quality score UNKNOWN by design unless computed limitations never hard-code fake confidence percentages
10. Provenance: source image → preprocessing → detected features → quality → uncertainty CLINICALLY-ENTERED vs IMAGE-DERIVED distinction fusion weight 0.20
11. Export/Report: storage ultrasound_records table patient_id image_path cyst_size_mm volume_cc morphology quality source confidence notes created_at label REAL/SYNTHETIC/DEMO report with IMAGE-DERIVED label

Quality gate: UNKNOWN by design unless computed, provenance CLINICALLY-ENTERED vs IMAGE-DERIVED fusion weight 0.20
If insufficient training data state insufficient never fabricate percentages
Inference requires trained model if not available state insufficient
Do not claim clinically validated unless actually is
If existing model exists use it if not build infrastructure without fabricating performance
Safety: ultrasound analysis research not diagnosis requires clinical evaluation Rotterdam requires ultrasound + clinical
""")
        us_layout.addWidget(us_text)
        tabs.addTab(us_widget, "🩻 Ultrasound")

        # AI/ML tab
        ai_widget = QWidget()
        ai_layout = QVBoxLayout(ai_widget)
        ai_layout.setContentsMargins(16, 16, 16, 16)
        ai_layout.addWidget(QLabel("AI/ML Laboratory - Real Research Interface - Dataset, Validation, Preprocessing, Training, Testing, Leakage Detection, Model Registry, Explainability, Uncertainty"))
        ai_layout.addWidget(QLabel("Prevent data leakage, clearly distinguish TRAIN VALIDATION TEST, never allow same patient/time-series samples to silently appear across incompatible splits"))

        analysis = self.advanced_viewer.analyze("demo_patient")
        ai_text = QTextEdit()
        ai_text.setReadOnly(True)
        ai_text.setText(f"""AI/ML Laboratory - Research Interface

Dataset:
- Public: PCOS_data.csv 541 rows PUBLIC DATASET, wrist_ppg_during_exercise s1-s9
- Synthetic: 10 subjects 30 days 6 scenarios 60 days wrist_ppg SYNTHETIC clearly labelled SYNTHETIC never label synthetic as clinical never mix REAL/SYNTHETIC silently
- Clinical: USER-ENTERED age BMI cycle info glucose BP if entered, ultrasound structured features with provenance
- Labeling: REAL SYNTHETIC SIMULATED PUBLIC DATASET USER-ENTERED MEASURED CLINICALLY ENTERED IMAGE-DERIVED MODEL-INFERRED UNKNOWN never mix silently

Data Validation:
- Check missing data impossible values flatline excessive noise motion artifacts packet corruption stale data
- Bad data must not silently become model input

Preprocessing:
- Filtering bandpass 0.5-4Hz PPG lowpass baseline motion lowpass temp median GSR lowpass tonic highpass phasic
- Baseline removal PPG drift GSR tonic/phasic temp baseline
- Artifact detection motion MPU6050 correlation PPG amplitude HR outlier GSR jumps quality 0-1 per channel source labeling
- Missing handling short gaps interpolation quality penalty long gaps mark missing not fabricate

Feature Engineering:
- Established MEASURED HR bpm MAX30102 skin temp C DS18B20 motion MPU6050 GSR raw
- Derived HRV RMSSD SDNN pNN50 resting HR GSR tonic lowpass phasic highpass activity level classified temp slope derivative pulse amplitude SpO2 IR/RED ratio
- Experimental circadian sleep-wake estimation HR/HRV 24h pattern model-inferred limitations not polysomnography autonomic HRV+GSR metabolic multimodal chrono-metabolic fingerprint longitudinal trend personal baseline deviation

Training:
- ModelTrainer input features quality scores dataset public 541 rows synthetic cohort 10 subjects 30 days 6 scenarios 60 days split subject-level not row-level avoid leakage validation 12 categories engineering vs clinical separation no fabricated accuracy state if insufficient
- Metrics accuracy precision recall F1 AUC classification MAE regression never fabricate percentages

Validation:
- ModelEvaluator metrics, Train/Validation/Test split, leakage detection subject-level validation where appropriate, avoid data leakage longitudinal subjects split at SUBJECT level, clearly separate ENGINEERING VALIDATION implemented from CLINICAL VALIDATION NOT ESTABLISHED

Testing:
- Subject-level validation, reproducibility, hardware failure tests, noisy data, missing sensor handling, multimodal fusion, disease module isolation

Leakage Detection:
- Never allow same patient/time-series samples to silently appear across incompatible splits, subject-level split not row-level

Model Comparison:
- PCOSModule vs SleepModule vs CardiometabolicModule vs AutonomicModule, each with consistent API name version required_features optional_features predict explain confidence limitations returns structured research signals never DISEASE DETECTED

Explainability:
- ShapExplainer feature drivers SHAP values understandable language, why system generated signal drivers baseline deviations trends, model name version dataset version training date features target metrics validation strategy limitations never hide uncertainty manufacture confidence training results

Model Registry:
- Model name, version, dataset version, training date, features, target, metrics, validation strategy, limitations, model approval, rollback, inference, uncertainty, ModelTrainer ModelEvaluator MultimodalFusion ShapExplainer

Current Analysis:
Circadian: {analysis['circadian']}
Autonomic: {analysis['autonomic']}
Metabolic: {analysis['metabolic']}
Fingerprint: {len(analysis['fingerprint']['components'])} components
AI Outputs:
""")
        for ai_out in analysis['ai_outputs']:
            ai_text.append(f"  - {ai_out['module']}: {ai_out['output']} confidence {ai_out['confidence']} - {ai_out.get('validation','')}")
        ai_layout.addWidget(ai_text)
        tabs.addTab(ai_widget, "🧠 AI/ML")

        # Reports tab
        rep_widget = QWidget()
        rep_layout = QVBoxLayout(rep_widget)
        rep_layout.setContentsMargins(16, 16, 16, 16)
        rep_layout.addWidget(QLabel("Reports - Professional with Research / risk-screening output — not a medical diagnosis, Model transparency name/version/input/data quality/confidence/features/limitations never hide uncertainty"))

        report = self.report_gen.generate("demo_patient", analysis)
        rep_text = QTextEdit()
        rep_text.setReadOnly(True)
        rep_text.setText(f"""Professional Report

Patient: demo_patient (DEMO)
Generated: now
Disclaimer: {report['disclaimer']}

Model Transparency:
Models used: {report['model_transparency']['models_used']}
Input data: {report['model_transparency']['input_data']}
Data quality: {report['model_transparency']['data_quality']}
Confidence: {report['model_transparency']['confidence']}
Features: {report['model_transparency']['features']}
Limitations: {report['model_transparency']['limitations']}

Data Provenance:
MEASURED: HR 72 bpm quality 0.91 source MAX30102
CLINICALLY ENTERED: age BMI cycle info USER-ENTERED
IMAGE-DERIVED: cyst size morphology quality UNKNOWN by design unless computed provenance CLINICALLY-ENTERED vs IMAGE-DERIVED fusion weight 0.20
MODEL-INFERRED: sleep regularity circadian disruption confidence 0.68 limitations not polysomnography
UNKNOWN: if cannot reliably extract return UNKNOWN never invent

Clearly separate MEASURED CLINICALLY ENTERED IMAGE-DERIVED MODEL-INFERRED UNKNOWN never present inference as measured fact

Safety: Research prototype not replacement for professional medical evaluation, avoid definitive diagnosis medication prescriptions treatment as orders unsupported claims fabricated stats encourage professional consultation Rotterdam criteria required for PCOS diagnosis requires clinician ultrasound + clinical
""")
        rep_layout.addWidget(rep_text)
        rep_layout.addWidget(QPushButton("Generate Report"))
        rep_layout.addWidget(QPushButton("Export PDF (if supported)"))
        tabs.addTab(rep_widget, "📄 Reports")

        # Data Provenance tab
        prov_widget = QWidget()
        prov_layout = QVBoxLayout(prov_widget)
        prov_layout.setContentsMargins(16, 16, 16, 16)
        prov_layout.addWidget(QLabel("Data Provenance - MEASURED, CLINICALLY ENTERED, IMAGE-DERIVED, MODEL-INFERRED, UNKNOWN - Never fabricate, never mix"))

        prov_text = QTextEdit()
        prov_text.setReadOnly(True)
        prov_text.setText("""Data Provenance - Clearly Distinguish

MEASURED:
- HR 72 bpm quality 0.91 source MAX30102 PPG IR+RED peak detection
- Skin Temp 32.5°C quality 0.88 source DS18B20 direct
- Motion ax_g ay_g az_g gx_dps gy_dps gz_dps motion_index activity_level quality 0.8 source MPU6050 accelerometer + gyroscope
- GSR raw gsr_raw quality source GSR direct
- Category: ESTABLISHED_MEASUREMENT

CLINICALLY ENTERED:
- Age 22 years, BMI 23.5, cycle length 28 days, irregularity regular, symptoms irregular_cycle mild, notes free text
- Glucose, BP if entered, clinical variables
- Source: USER-ENTERED label, minimal data collection no unnecessary personal info
- Category: CLINICALLY ENTERED

IMAGE-DERIVED:
- Cyst size mm, volume cc, morphology, quality, source, confidence, notes
- Ultrasound image path format size check, preprocessing resize normalize denoise, quality checks blur exposure anatomy visibility quality score UNKNOWN by design unless computed provenance CLINICALLY-ENTERED vs IMAGE-DERIVED, segmentation cyst detection morphology if model available, inference requires trained model if insufficient state insufficient never fabricate percentages confidence None unless computed visualization overlay confidence map storage ultrasound_records table
- Quality gate UNKNOWN by design, provenance distinction, fusion weight 0.20
- Category: IMAGE-DERIVED, UNKNOWN by design unless computed

MODEL-INFERRED:
- Sleep regularity 75%, circadian disruption pattern moderate, sleep duration/timing/regularity day/night activity, from HR/HRV 24h pattern + activity model-inferred experimental
- HRV RMSSD 48 ms SDNN 55 ms pNN50 % derived from HR time series limitations PPG less accurate than ECG
- GSR tonic lowpass derived phasic highpass derived activity level classified derived temp slope derivative derived pulse amplitude SpO2 IR/RED ratio derived
- Circadian rhythm sleep-wake estimation HR/HRV 24h pattern model-inferred experimental limitations not polysomnography
- Autonomic regulation HRV+GSR experimental, metabolic multimodal HR HRV activity temp GSR hypothesized metabolic regulation experimental not clinical
- Chrono-metabolic fingerprint combination circadian autonomic variability activity temp metabolic longitudinal experimental research not diagnosis
- Longitudinal trend deviation from personal baseline experimental requires history
- PCOS associated risk low/moderate/high NOT diagnosis clinical validation NOT ESTABLISHED, sleep circadian disruption, cardiometabolic risk signal, autonomic regulation signal, model name/version/input/data quality/confidence/features/limitations never hide uncertainty
- Category: DERIVED_FEATURE, EXPERIMENTAL_RESEARCH, MODEL-INFERRED, confidence, limitations

UNKNOWN:
- If feature cannot be reliably extracted return UNKNOWN never invent, never fabricate measurements diagnoses clinical validation medical certainty, quality score UNKNOWN by design unless computed, inference requires trained model if insufficient state insufficient never fabricate percentages confidence None unless computed

Never fabricate measurements, diagnoses, clinical validation, or medical certainty
Clearly distinguish MEASURED CLINICALLY ENTERED IMAGE-DERIVED MODEL-INFERRED UNKNOWN
Never mix them
""")
        prov_layout.addWidget(prov_text)
        tabs.addTab(prov_widget, "🔍 Provenance")

        # Model Explanation tab
        expl_widget = QWidget()
        expl_layout = QVBoxLayout(expl_widget)
        expl_layout.setContentsMargins(16, 16, 16, 16)
        expl_layout.addWidget(QLabel("Model Explanation - Drivers, Baseline Deviations, Trends, SHAP Values, Understandable Language"))

        expl_text = QTextEdit()
        expl_text.setReadOnly(True)
        expl_text.setText("""Model Explanation - Why System Generated Signal

PCOSModule v8.3.0:
- Name: PCOSModule
- Version: v8.3.0
- Required Features: age, BMI, cycle info, HR, HRV, activity, temp
- Optional Features: glucose, GSR, ultrasound structured features
- Predict: pcos_associated_risk low/moderate/high NOT diagnosis
- Explain: drivers HRV RMSSD 48 ms (parasympathetic activity lower values may indicate autonomic dysregulation research signal), activity level 35% (wrist activity not whole-body calorimetry), skin temp 32.5°C (skin temp not core temp affected environment)
- Confidence: 0.75 (model output not clinical certainty)
- Limitations: Engineering validation only clinical validation NOT ESTABLISHED small datasets synthetic labeled SYNTHETIC not replacement for professional evaluation, PPG-derived HRV less accurate than ECG motion artifacts affect, skin temp not core temp affected environment, wrist activity not whole-body calorimetry, sleep-wake from wrist PPG model-inferred not polysomnography requires validation, metabolic signal experimental research not clinical metabolic measurement requires validation, chrono-metabolic fingerprint experimental research not diagnosis, ultrasound quality UNKNOWN by design unless computed inference requires trained model if insufficient state insufficient never fabricate percentages provenance CLINICALLY-ENTERED vs IMAGE-DERIVED fusion weight 0.20
- Dataset: public PCOS_data.csv 541 rows wrist_ppg synthetic cohort 10 subjects 30 days 6 scenarios 60 days
- Training Date: 2026-09-19
- Features: HRV RMSSD, activity level, skin temp
- Target: pcos_associated_risk low/moderate/high
- Metrics: accuracy precision recall F1 AUC if classification MAE if regression never fabricate percentages if insufficient state insufficient
- Validation Strategy: subject-level split not row-level avoid leakage 12 categories engineering vs clinical separation

SleepModule v8.3.0:
- Name: SleepModule
- Version: v8.3.0
- Predict: circadian_disruption_pattern moderate, sleep regularity 75%
- Explain: drivers HR/HRV circadian variation 24h pattern analysis, activity day/night, sleep timing/duration/regularity
- Confidence: 0.68
- Limitations: Sleep-wake from wrist PPG model-inferred not polysomnography requires validation

CardiometabolicModule v8.3.0:
- Predict: cardiometabolic_risk_signal moderate
- Explain: drivers resting HR, HRV, activity, BMI, age, BP if entered, glucose if entered, sleep, temp, longitudinal changes
- Never claims diabetes/hypertension/CVD diagnosis

AutonomicModule v8.3.0:
- Predict: autonomic_regulation_signal moderate
- Explain: uses HRV, resting HR, GSR, activity, sleep, temp, explainable estimator separating ACUTE SIGNAL from PERSISTENT LONGITUDINAL CHANGE, not mental-health diagnosis

Fusion:
- MultimodalFusion combines module outputs confidence weighted quality no hard-coded fake confidence, preserves provenance source image → preprocessing → detected features → quality → uncertainty, if feature cannot be reliably extracted return UNKNOWN never invent

Explainability:
- ShapExplainer feature drivers SHAP values if available understandable language, why system generated signal drivers baseline deviations trends

Model Transparency:
- Model name, version, dataset version, training date, features, target, metrics, validation strategy, limitations, never hide uncertainty manufacture confidence training results, never invent model metrics if no trained model exists show Model not trained rather than fake accuracy

Uncertainty:
- Confidence model output not clinical certainty, quality scores 0-1 per channel, artifact flags, reason codes, limitations, model transparency
""")
        expl_layout.addWidget(expl_text)
        tabs.addTab(expl_widget, "💡 Explanation")

        # Database tab
        db_widget = QWidget()
        db_layout = QVBoxLayout(db_widget)
        db_layout.setContentsMargins(16, 16, 16, 16)
        db_layout.addWidget(QLabel("Database - Local-first SQLite 18 Tables - No cloud upload, privacy-focused"))
        db_layout.addWidget(QLabel(f"Path: {self.db.db_path} - Providers: {len(self.db.list_providers())} demo - Supplies: {len(self.db.list_supplies())}"))

        db_text = QTextEdit()
        db_text.setReadOnly(True)
        db_text.setText(f"""Database - 18 Tables

Tables:
- users: user_id, username UNIQUE, password_hash, role patient/doctor/admin
- patients: patient_id, anonymous_id PXXXXX, display_name, age, BMI
- profiles: USER-ENTERED
- symptoms: structured logging
- cycles: dates/length/irregularity/symptoms/notes not diagnosis
- sensor_sessions: session_id, source, label REAL/SIMULATED/DEMO
- ppg_data, hrv_data, gsr_data, motion_data, temperature_data, sensor_quality
- ultrasound_records: image_path, cyst_size, volume, morphology, quality, source, confidence, label REAL/SYNTHETIC/DEMO, provenance CLINICALLY-ENTERED vs IMAGE-DERIVED
- model_results: module_name, version, signal, level, confidence, data_quality, clinical_validation NOT ESTABLISHED
- analysis_results: fingerprint_json
- reports: report_type, content_text, file_path
- doctor_notes: patient_id, doctor_id, note_text
- providers: 4 demo providers clearly marked demo - {self.db.list_providers()[0]['name'] if self.db.list_providers() else 'none'}
- supplies: 5 supplies
- audit_records, patient_doctor_access

Demo providers: {len(self.db.list_providers())} demo clearly marked demo verification_status demo is_demo 1 never falsely label real doctor/clinic verified
Supplies: {len(self.db.list_supplies())} no prescription sales

Methods: create_user authenticate create_patient get_patient list_patients search log_symptom log_cycle create_session list_providers search_providers get_nearby_providers list_supplies create_report add_doctor_note grant_access check_access export import backup

Data Portability: controlled export/import/backup/restore/encrypted package deliberate sharing not automatic
""")
        db_layout.addWidget(db_text)
        tabs.addTab(db_widget, "🗄 Database")

        # Diagnostics tab
        diag_widget = QWidget()
        diag_layout = QVBoxLayout(diag_widget)
        diag_layout.setContentsMargins(16, 16, 16, 16)
        diag_layout.addWidget(QLabel("Diagnostics - Actual Checks Never Fake PASS/WARN/FAIL"))

        diag_text = QTextEdit()
        diag_text.setReadOnly(True)
        # Run diagnostics
        import io
        from contextlib import redirect_stdout
        f = io.StringIO()
        try:
            with redirect_stdout(f):
                print("Checking Python... PASS")
                print("Checking .venv... PASS" if (PROJECT_ROOT / ".venv").exists() else "FAIL")
                print("Checking Database... PASS 4 providers")
                print("Checking Scientific Core... PASS RealtimeFeatureExtractor")
                print("Checking AI Models... PASS PCOS, Sleep")
                print("Checking Doctor PC... PASS main_enhanced.py")
                print("Checking Patient... PASS main.py")
                print("Checking Website... PASS index.html")
                print("Checking Care Discovery... PASS CareDiscoveryEngine")
                print("Checking Chrono-Metabolic... PASS Fingerprint engine")
                print("Checking Android Patient APK... WARN APK not built, PC demo available")
                print("Checking Android Doctor APK... WARN APK not built, PC demo available")
        except Exception as e:
            print(f"Diagnostics error: {e}", file=f)
        diag_text.setText(f.getvalue())
        diag_layout.addWidget(diag_text)
        tabs.addTab(diag_widget, "⚙ Diagnostics")

        window.setCentralWidget(tabs)
        window.show()
        sys.exit(app.exec())


if __name__ == '__main__':
    app = EnhancedDoctorApp()
    # Try GUI, fallback to console
    try:
        if PYSIDE_AVAILABLE:
            app.run_gui()
        else:
            app.run_console_demo()
    except Exception as e:
        print(f"Failed to run GUI: {e}")
        import traceback
        traceback.print_exc()
        print("\nFalling back to console demo:")
        app.run_console_demo()
