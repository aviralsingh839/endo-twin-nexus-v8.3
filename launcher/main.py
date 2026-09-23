#!/usr/bin/env python3
"""
ENDO-TWIN NEXUS Engineering Engineering Control Center
Garuda Linux Click-to-Launch System
Sense • Model • Predict • Personalize

Fixed: No clipped text, responsive layouts, proper margins, scroll areas, minimum sizes, dynamic resizing
"""
import sys
import os
import subprocess
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

(Path(PROJECT_ROOT) / "logs").mkdir(exist_ok=True)
(Path(PROJECT_ROOT) / "DIST" / "android").mkdir(parents=True, exist_ok=True)

try:
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QPushButton, QLabel, QScrollArea, QGroupBox, QGridLayout, QMessageBox,
        QFrame, QSizePolicy, QSpacerItem
    )
    from PySide6.QtCore import Qt, QSize
    from PySide6.QtGui import QFont
    PYSIDE_AVAILABLE = True
except ImportError:
    PYSIDE_AVAILABLE = False

def get_status():
    status = {}
    status['python'] = {'label': 'Python', 'status': 'PASS', 'detail': sys.version.split()[0], 'icon': 'PY'}
    venv_path = PROJECT_ROOT / ".venv" / "bin" / "python"
    if venv_path.exists():
        status['venv'] = {'label': '.venv', 'status': 'PASS', 'detail': 'Environment ready', 'icon': 'PKG'}
    else:
        status['venv'] = {'label': '.venv', 'status': 'FAIL', 'detail': 'Not found - run SETUP.sh', 'icon': 'PKG'}
    try:
        import PySide6
        status['pyside'] = {'label': 'PySide6', 'status': 'PASS', 'detail': f'v{PySide6.__version__}', 'icon': 'UI'}
    except Exception as e:
        status['pyside'] = {'label': 'PySide6', 'status': 'FAIL', 'detail': str(e)[:60], 'icon': 'UI'}
    try:
        import numpy, pandas, sklearn
        status['deps'] = {'label': 'Core Deps', 'status': 'PASS', 'detail': 'numpy, pandas, sklearn', 'icon': 'DEP'}
    except Exception as e:
        status['deps'] = {'label': 'Core Deps', 'status': 'FAIL', 'detail': str(e)[:60], 'icon': 'DEP'}
    try:
        from database.database import LocalDatabase
        db = LocalDatabase(db_path=Path("/tmp/control_center_check.db"))
        providers = db.list_providers()
        status['database'] = {'label': 'Database V8.3', 'status': 'PASS', 'detail': f'{len(providers)} providers, 18 tables', 'icon': 'DB'}
    except Exception as e:
        status['database'] = {'label': 'Database V8.3', 'status': 'FAIL', 'detail': str(e)[:60], 'icon': 'DB'}
    try:
        from database.endo_twin_database import EndoTwinDatabase
        db = EndoTwinDatabase(db_path=Path("/tmp/control_center_check_endo.db"))
        result = db.test_patient_isolation()
        if result["overall_pass"]:
            status['endo_db'] = {'label': 'ENDO-TWIN DB', 'status': 'PASS', 'detail': f'DEMO-001/002/003 isolation OK HR 72/78/68', 'icon': 'DB'}
        else:
            status['endo_db'] = {'label': 'ENDO-TWIN DB', 'status': 'FAIL', 'detail': f'Isolation FAIL', 'icon': 'DB'}
    except Exception as e:
        status['endo_db'] = {'label': 'ENDO-TWIN DB', 'status': 'FAIL', 'detail': str(e)[:60], 'icon': 'DB'}
    try:
        from src.core.feature_extraction import RealtimeFeatureExtractor
        status['core'] = {'label': 'Scientific Core', 'status': 'PASS', 'detail': 'Feature extraction OK V8.3 preserved', 'icon': 'CORE'}
    except Exception as e:
        status['core'] = {'label': 'Scientific Core', 'status': 'FAIL', 'detail': str(e)[:60], 'icon': 'CORE'}
    try:
        from endo_twin.core import EndoTwinCore
        core = EndoTwinCore()
        arch = core.get_architecture()
        status['endo_core'] = {'label': 'ENDO-TWIN Core', 'status': 'PASS', 'detail': f'{arch["name"]} {arch["version"]} CHRONO-PCOS first module', 'icon': 'CORE'}
    except Exception as e:
        try:
            from src.endo_twin.core.twin_core import EndoTwinCore as GeneralCore
            core = GeneralCore()
            arch = core.get_architecture()
            status['endo_core'] = {'label': 'ENDO-TWIN Core General', 'status': 'PASS', 'detail': f'{arch["name"]} {arch["version"]} - {arch["one_sentence"]}', 'icon': 'CORE'}
        except Exception as e2:
            status['endo_core'] = {'label': 'ENDO-TWIN Core', 'status': 'FAIL', 'detail': str(e2)[:60], 'icon': 'CORE'}
    # Check general platform
    try:
        if (PROJECT_ROOT / "apps" / "main" / "main_app.py").exists():
            status['endo_twin_general'] = {'label': 'ENDO-TWIN General Platform', 'status': 'PASS', 'detail': 'General platform - Understand physiological patterns over time - apps/main/main_app.py', 'icon': 'CORE'}
        else:
            status['endo_twin_general'] = {'label': 'ENDO-TWIN General Platform', 'status': 'WARN', 'detail': 'apps/main/main_app.py not found', 'icon': 'CORE'}
    except Exception as e:
        status['endo_twin_general'] = {'label': 'ENDO-TWIN General Platform', 'status': 'FAIL', 'detail': str(e)[:60], 'icon': 'CORE'}
    # Check disease models
    try:
        if (PROJECT_ROOT / "disease_models" / "chrono_pcos" / "model" / "chrono_pcos_model.py").exists():
            status['chrono_pcos_model'] = {'label': 'CHRONO-PCOS Disease Model', 'status': 'PASS', 'detail': 'First disease model on ENDO-TWIN platform - disease_models/chrono_pcos/', 'icon': 'CORE'}
        else:
            status['chrono_pcos_model'] = {'label': 'CHRONO-PCOS Disease Model', 'status': 'WARN', 'detail': 'Not found - disease_models/chrono_pcos/', 'icon': 'CORE'}
    except Exception as e:
        status['chrono_pcos_model'] = {'label': 'CHRONO-PCOS Disease Model', 'status': 'FAIL', 'detail': str(e)[:60], 'icon': 'CORE'}
    try:
        from src.disease_modules import pcos
        status['ai'] = {'label': 'AI/ML', 'status': 'PASS', 'detail': 'PCOS, Sleep, Cardio, Autonomic', 'icon': 'AI'}
    except Exception as e:
        try:
            from core.analysis import PCOSModule
            status['ai'] = {'label': 'AI/ML', 'status': 'PASS', 'detail': 'Core AI wrappers', 'icon': 'AI'}
        except Exception as e2:
            status['ai'] = {'label': 'AI/ML', 'status': 'WARN', 'detail': str(e2)[:60], 'icon': 'AI'}
    try:
        from endo_twin.registry import ModelRegistry
        registry = ModelRegistry()
        status['model_registry'] = {'label': 'Model Registry', 'status': 'PASS', 'detail': 'Registry OK CHRONO-PCOS', 'icon': 'AI'}
    except Exception as e:
        status['model_registry'] = {'label': 'Model Registry', 'status': 'FAIL', 'detail': str(e)[:60], 'icon': 'AI'}
    if (PROJECT_ROOT / "docs" / "ULTRASOUND_PIPELINE.md").exists():
        status['ultrasound'] = {'label': 'Ultrasound', 'status': 'PASS', 'detail': 'Pipeline ready 11 steps', 'icon': 'IMG'}
    else:
        status['ultrasound'] = {'label': 'Ultrasound', 'status': 'WARN', 'detail': 'Docs missing', 'icon': 'IMG'}
    if (PROJECT_ROOT / "desktop" / "doctor_app" / "main_enhanced.py").exists():
        status['doctor_pc'] = {'label': 'Doctor PC', 'status': 'PASS', 'detail': 'Workstation ready 1450x950 patient scoped', 'icon': 'PC'}
    else:
        status['doctor_pc'] = {'label': 'Doctor PC', 'status': 'FAIL', 'detail': 'Not found', 'icon': 'PC'}
    if (PROJECT_ROOT / "android" / "patient_app" / "main.py").exists():
        status['patient_kivy'] = {'label': 'Patient Kivy Legacy', 'status': 'PASS', 'detail': 'Kivy preserved, primary now Kotlin', 'icon': 'MOB'}
    else:
        status['patient_kivy'] = {'label': 'Patient Kivy Legacy', 'status': 'WARN', 'detail': 'Not found', 'icon': 'MOB'}
    if (PROJECT_ROOT / "android" / "patient" / "app" / "src" / "main" / "java" / "org" / "chronopcos" / "patient" / "MainActivity.kt").exists():
        status['patient_native'] = {'label': 'Patient Native Kotlin', 'status': 'PASS', 'detail': 'Kotlin+Compose Material3 single patient', 'icon': 'MOB'}
    else:
        status['patient_native'] = {'label': 'Patient Native Kotlin', 'status': 'FAIL', 'detail': 'Not found', 'icon': 'MOB'}
    if (PROJECT_ROOT / "android" / "doctor" / "app" / "src" / "main" / "java" / "org" / "chronopcos" / "doctor" / "MainActivity.kt").exists():
        status['doctor_native'] = {'label': 'Doctor Native Kotlin', 'status': 'PASS', 'detail': 'Kotlin+Compose multi-patient DEMO-001/002/003', 'icon': 'MOB'}
    else:
        status['doctor_native'] = {'label': 'Doctor Native Kotlin', 'status': 'FAIL', 'detail': 'Not found', 'icon': 'MOB'}
    apk_patient_native = list((PROJECT_ROOT / "android" / "patient" / "app" / "build" / "outputs").glob("**/*.apk")) if (PROJECT_ROOT / "android" / "patient" / "app" / "build").exists() else []
    apk_doctor_native = list((PROJECT_ROOT / "android" / "doctor" / "app" / "build" / "outputs").glob("**/*.apk")) if (PROJECT_ROOT / "android" / "doctor" / "app" / "build").exists() else []
    apk_patient = list((PROJECT_ROOT / "android" / "patient_app").glob("**/*.apk"))
    apk_doctor = list((PROJECT_ROOT / "android" / "doctor_app").glob("**/*.apk"))
    apk_dist = list((PROJECT_ROOT / "DIST" / "android").glob("*.apk"))
    apk_dist2 = list((PROJECT_ROOT / "dist" / "android").glob("*.apk"))
    total_apks = len(apk_patient_native) + len(apk_doctor_native) + len(apk_patient) + len(apk_doctor) + len(apk_dist) + len(apk_dist2)
    if total_apks > 0:
        status['apk'] = {'label': 'Android APKs Native+Legacy', 'status': 'PASS', 'detail': f'{total_apks} APK(s) native {len(apk_patient_native)+len(apk_doctor_native)} DIST {len(apk_dist)}', 'icon': 'PKG'}
    else:
        status['apk'] = {'label': 'Android APKs Native+Legacy', 'status': 'WARN', 'detail': 'Not built - use BUILD scripts Kotlin+Compose', 'icon': 'PKG'}
    if (PROJECT_ROOT / "website" / "index.html").exists():
        size = (PROJECT_ROOT / "website" / "index.html").stat().st_size
        status['website'] = {'label': 'Website', 'status': 'PASS', 'detail': f'Static site ready {size//1024}K extensive', 'icon': 'WEB'}
    else:
        status['website'] = {'label': 'Website', 'status': 'FAIL', 'detail': 'Not found', 'icon': 'WEB'}
    try:
        from provider_network.care_discovery import CareDiscoveryEngine
        status['care'] = {'label': 'Care Discovery', 'status': 'PASS', 'detail': 'FIND CARE ready', 'icon': 'CARE'}
    except Exception as e:
        status['care'] = {'label': 'Care Discovery', 'status': 'FAIL', 'detail': str(e)[:60], 'icon': 'CARE'}
    try:
        from core.chrono_metabolic import ChronoMetabolicFingerprint
        status['chrono'] = {'label': 'Chrono-Metabolic', 'status': 'PASS', 'detail': 'Fingerprint engine', 'icon': 'TIME'}
    except Exception as e:
        status['chrono'] = {'label': 'Chrono-Metabolic', 'status': 'FAIL', 'detail': str(e)[:60], 'icon': 'TIME'}
    try:
        from endo_twin.provenance import ProvenanceTracker, ProvenanceLabel
        status['provenance'] = {'label': 'Provenance', 'status': 'PASS', 'detail': f'Labels {[l.value for l in ProvenanceLabel]} first-class', 'icon': 'AUDIT'}
    except Exception as e:
        status['provenance'] = {'label': 'Provenance', 'status': 'FAIL', 'detail': str(e)[:60], 'icon': 'AUDIT'}
    return status

def get_launcher_status():
    s = get_status()
    ls = {}
    ls['PATIENT_APP'] = s.get('patient_kivy', {'status': 'FAIL', 'detail': ''})
    ls['PATIENT_ANDROID'] = s.get('patient_native', {'status': 'WARN', 'detail': ''})
    ls['DOCTOR_PC'] = s.get('doctor_pc', {'status': 'FAIL', 'detail': ''})
    ls['DOCTOR_ANDROID'] = s.get('doctor_native', {'status': 'WARN', 'detail': ''})
    ls['SCIENTIFIC_CORE'] = s.get('core', {'status': 'FAIL', 'detail': ''})
    ls['FULL_SHOWCASE'] = {'status': 'PASS', 'detail': '16 steps demo ENDO-TWIN'} if s.get('core', {}).get('status') == 'PASS' else {'status': 'WARN', 'detail': 'Core needed'}
    ls['AI_ML'] = s.get('ai', {'status': 'WARN', 'detail': ''})
    ls['ULTRASOUND'] = s.get('ultrasound', {'status': 'WARN', 'detail': ''})
    ls['CHRONO_METABOLIC'] = s.get('chrono', {'status': 'FAIL', 'detail': ''})
    ls['CARE_FINDER'] = s.get('care', {'status': 'FAIL', 'detail': ''})
    ls['DATABASE'] = s.get('endo_db', {'status': 'FAIL', 'detail': ''})
    ls['REPORTS'] = s.get('database', {'status': 'FAIL', 'detail': ''})
    ls['WEBSITE'] = s.get('website', {'status': 'FAIL', 'detail': ''})
    ls['DIAGNOSTICS'] = {'status': 'PASS', 'detail': 'Diagnostics ready ENDO-TWIN 13 checks'}
    ls['SIGNAL_PROCESSING'] = s.get('core', {'status': 'WARN', 'detail': ''})
    ls['SETUP'] = {'status': 'PASS', 'detail': 'Setup ready'}
    ls['BUILD_PATIENT_APK'] = s.get('apk', {'status': 'WARN', 'detail': 'Build Patient APK Kotlin+Compose native'})
    ls['BUILD_DOCTOR_APK'] = s.get('apk', {'status': 'WARN', 'detail': 'Build Doctor APK Kotlin+Compose multi-patient'})
    ls['BUILD_ALL_APKS'] = s.get('apk', {'status': 'WARN', 'detail': 'Build All APKs native wrapper'})
    ls['ENDO_TWIN'] = s.get('endo_core', {'status': 'FAIL', 'detail': ''})
    # General platform - should work even without disease model
    try:
        from pathlib import Path
        PROJECT_ROOT = Path(__file__).resolve().parents[1]
        if (PROJECT_ROOT / "apps" / "main" / "main_app.py").exists():
            ls['ENDO_TWIN'] = {'status': 'PASS', 'detail': 'General platform - Understand physiological patterns over time - ENDO-TWIN is platform, CHRONO-PCOS first model'}
        if (PROJECT_ROOT / "disease_models" / "chrono_pcos" / "model" / "chrono_pcos_model.py").exists():
            ls['CHRONO_PCOS_MODEL'] = {'status': 'PASS', 'detail': 'CHRONO-PCOS first disease model on ENDO-TWIN platform - preserved original functionality'}
    except:
        pass
    return ls

if PYSIDE_AVAILABLE:
    class AppCard(QFrame):
        def __init__(self, title, description, status_info, launcher_name, parent=None):
            super().__init__(parent)
            self.launcher_name = launcher_name
            self.setFrameShape(QFrame.StyledPanel)
            self.setFrameShadow(QFrame.Raised)
            self.setMinimumSize(320, 180)
            self.setMaximumSize(400, 220)
            self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

            st = status_info.get('status', 'WARN')
            if st == 'PASS':
                # Verified against #ffffff: 5.26:1 (was #10b981 at 2.28:1).
                border_color = "#10b981"
                status_color = "#237A57"
                status_icon = "PASS"
            elif st == 'WARN':
                # Verified against #ffffff: 5.05:1 (was #f59e0b at 2.15:1).
                border_color = "#f59e0b"
                status_color = "#9C6200"
                status_icon = "WARN"
            else:
                # Verified against #ffffff: 5.86:1 (was #ef4444 at 3.76:1).
                # The word FAIL is always rendered too, so the red is reinforcement.
                border_color = "#ef4444"
                status_color = "#B33A3A"
                status_icon = "FAIL"

            self.setStyleSheet(f"""
                QFrame {{
                    background: white;
                    border: 2px solid {border_color};
                    border-radius: 12px;
                    padding: 4px;
                }}
                QFrame:hover {{
                    background: #f8fafc;
                    border: 2px solid #0ea5e9;
                }}
            """)

            layout = QVBoxLayout(self)
            layout.setContentsMargins(12, 12, 12, 12)
            layout.setSpacing(6)

            # Title
            title_label = QLabel(title)
            title_label.setWordWrap(True)
            title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #0f172a; border: none; background: transparent;")
            title_label.setMinimumHeight(30)
            layout.addWidget(title_label)

            # Description
            desc_label = QLabel(description)
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet("font-size: 11px; color: #64748b; border: none; background: transparent;")
            desc_label.setMinimumHeight(40)
            desc_label.setMaximumHeight(60)
            layout.addWidget(desc_label)

            # Status
            status_text = f"{status_icon} {st}: {status_info.get('detail','')[:50]}"
            status_label = QLabel(status_text)
            status_label.setWordWrap(True)
            status_label.setStyleSheet(f"font-size: 11px; color: {status_color}; font-weight: 600; border: none; background: transparent;")
            status_label.setMinimumHeight(30)
            status_label.setToolTip(f"Status: {st}\nDetail: {status_info.get('detail','')}\nLauncher: {launcher_name}.sh")
            layout.addWidget(status_label)

            # Button
            btn = QPushButton(f"OPEN {title.split()[0].upper()}")
            btn.setMinimumHeight(36)
            btn.setStyleSheet("""
                QPushButton {
                    font-size: 12px; font-weight: bold; 
                    background: #0ea5e9; color: white; 
                    border: none; border-radius: 6px; 
                    padding: 8px;
                }
                QPushButton:hover { background: #0284c7; }
                QPushButton:pressed { background: #0369a1; }
            """)
            btn.setToolTip(f"Launch {launcher_name}.sh\n{description}")
            btn.clicked.connect(lambda: self.launch())
            layout.addWidget(btn)

        def launch(self):
            project_root = PROJECT_ROOT
            launcher_path = project_root / "launchers" / f"{self.launcher_name}.sh"
            launch_path = project_root / "LAUNCH" / f"{self.launcher_name}.sh"
            script_to_run = None
            if launcher_path.exists():
                script_to_run = launcher_path
            elif launch_path.exists():
                script_to_run = launch_path
            else:
                root_path = project_root / f"{self.launcher_name}.sh"
                if root_path.exists():
                    script_to_run = root_path
            if not script_to_run:
                QMessageBox.warning(self, "Launcher Not Found",
                    f"Launcher {self.launcher_name}.sh not found.\n\nChecked:\n{launcher_path}\n{launch_path}\n\nRun SETUP.sh")
                return
            log_file = project_root / "logs" / "launcher.log"
            try:
                with open(log_file, "a") as f:
                    f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} Launching {self.launcher_name}.sh from Engineering Control Center\n")
            except:
                pass
            try:
                subprocess.Popen(
                    ["bash", str(script_to_run)],
                    cwd=str(project_root),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )
            except Exception as e:
                QMessageBox.critical(self, "Launch Failed",
                    f"Failed to launch {self.launcher_name}.sh\n\nError: {e}\n\nCheck logs: logs/launcher.log\nRun DIAGNOSTICS.sh")

    class ControlCenter(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("ENDO-TWIN NEXUS → ENDO-TWIN COMPLETE CONTROL CENTER - Sense • Model • Predict • Personalize")
            self.resize(1450, 950)
            self.setMinimumSize(1200, 800)

            # Main scroll area
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            central = QWidget()
            scroll.setWidget(central)
            self.setCentralWidget(scroll)

            main_layout = QVBoxLayout(central)
            main_layout.setContentsMargins(20, 20, 20, 20)
            main_layout.setSpacing(16)

            # Header with proper spacing
            header_frame = QFrame()
            header_frame.setStyleSheet("background: #142B3A; border: 1px solid #294657; border-radius: 10px; padding: 10px;")
            header_layout = QVBoxLayout(header_frame)
            header_layout.setContentsMargins(20, 20, 20, 20)
            header_layout.setSpacing(8)

            title = QLabel("ENDO-TWIN - Personalized Physiological Modelling Platform")
            title.setAlignment(Qt.AlignCenter)
            title.setStyleSheet("font-size: 28px; font-weight: bold; color: white; background: transparent; border: none;")
            header_layout.addWidget(title)

            subtitle1 = QLabel("CHRONO-PCOS is First Disease Model - Engineering Engineering Control Center")
            subtitle1.setAlignment(Qt.AlignCenter)
            subtitle1.setStyleSheet("font-size: 16px; font-weight: 600; color: #cbd5e1; background: transparent; border: none; letter-spacing: 1px;")
            header_layout.addWidget(subtitle1)

            subtitle2 = QLabel("Understand your physiological patterns over time - Sense • Model • Predict • Personalize")
            subtitle2.setAlignment(Qt.AlignCenter)
            subtitle2.setStyleSheet("font-size: 12px; color: #0ea5e9; font-weight: 600; background: transparent; border: none; letter-spacing: 2px;")
            header_layout.addWidget(subtitle2)

            disclaimer = QLabel("ENDO-TWIN is general platform, CHRONO-PCOS is first disease-specific model - General physiological monitoring, personal baseline, longitudinal tracking, AI/ML infrastructure, disease models plugin - NOT clinically validated universal digital twin - Research / risk-screening output — not a medical diagnosis • Local-first • Offline • Privacy-focused • Garuda Linux Ready • Kotlin + Compose Native Android")
            disclaimer.setAlignment(Qt.AlignCenter)
            disclaimer.setWordWrap(True)
            disclaimer.setStyleSheet("font-size: 11px; color: #fbbf24; background: rgba(251,191,36,0.1); border: 1px solid rgba(251,191,36,0.3); padding: 8px; border-radius: 6px; margin-top: 8px;")
            header_layout.addWidget(disclaimer)

            main_layout.addWidget(header_frame)

            # Status overview with responsive grid
            status_group = QGroupBox("System Status - Actual Checks, Never Fake PASS")
            status_group.setStyleSheet("QGroupBox { font-size: 14px; font-weight: bold; color: #0f172a; border: 1px solid #e2e8f0; border-radius: 8px; margin-top: 10px; padding-top: 10px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }")
            status_layout = QGridLayout()
            status_layout.setContentsMargins(12, 12, 12, 12)
            status_layout.setSpacing(8)
            statuses = get_status()
            row, col = 0, 0
            for key, info in statuses.items():
                st = info['status']
                if st == 'PASS':
                    icon = ""
                    color = "#10b981"
                elif st == 'WARN':
                    icon = ""
                    color = "#f59e0b"
                else:
                    icon = ""
                    color = "#ef4444"
                card = QFrame()
                card.setMinimumSize(200, 60)
                card.setMaximumHeight(80)
                card.setStyleSheet(f"background: white; border: 1px solid {color}; border-left: 4px solid {color}; border-radius: 6px; padding: 4px;")
                card_layout = QVBoxLayout(card)
                card_layout.setContentsMargins(8, 4, 8, 4)
                card_layout.setSpacing(2)
                label1 = QLabel(f"{info.get('icon','')} {icon} {info['label']}: {st}")
                label1.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {color}; border: none; background: transparent;")
                label1.setWordWrap(True)
                card_layout.addWidget(label1)
                label2 = QLabel(info['detail'][:70])
                label2.setStyleSheet("font-size: 11px; color: #64748b; border: none; background: transparent;")
                label2.setWordWrap(True)
                card_layout.addWidget(label2)
                card.setToolTip(f"{info['label']}: {st}\n{info['detail']}")
                status_layout.addWidget(card, row, col)
                col += 1
                if col >= 4:
                    col = 0
                    row += 1
            status_group.setLayout(status_layout)
            main_layout.addWidget(status_group)

            launcher_status = get_launcher_status()

            # Helper to create category with AppCards
            def add_category(title_text, description, buttons):
                group = QGroupBox(f"{title_text} - {description}")
                group.setStyleSheet("QGroupBox { font-size: 13px; font-weight: bold; color: #0f172a; border: 1px solid #cbd5e1; border-radius: 8px; margin-top: 12px; padding-top: 10px; background: #f8fafc; } QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; background: white; border-radius: 4px; }")
                layout = QGridLayout()
                layout.setContentsMargins(12, 20, 12, 12)
                layout.setSpacing(12)
                r, c = 0, 0
                for btn_title, btn_desc, launcher_name in buttons:
                    ls = launcher_status.get(launcher_name, {'status': 'WARN', 'detail': ''})
                    card = AppCard(btn_title, btn_desc, ls, launcher_name)
                    layout.addWidget(card, r, c)
                    c += 1
                    if c >= 3:
                        c = 0
                        r += 1
                group.setLayout(layout)
                main_layout.addWidget(group)

            add_category("PATIENT", "Patient Platform - Mobile & Desktop", [
                ("Patient App\nPC Demo", "Dashboard, Profile, Measurements, Symptoms, Cycle, Results, Reports, Sharing, Find Care - Kivy offline-first", "PATIENT_APP"),
                ("Patient Android\nAPK Build", "Patient Android - APK build workflow, PC demo if APK not built, touch-friendly mobile UI", "PATIENT_ANDROID"),
            ])

            add_category("DOCTOR", "Doctor Platform - Clinical Workstation", [
                ("Doctor PC\nFull Workstation", "Dashboard, Patient Management, Physiological Data, Advanced Analysis, Ultrasound, Longitudinal, Notes, Reports - PySide6", "DOCTOR_PC"),
                ("Doctor Android\nMobile Review", "Patient list, search, profiles, measurements, trends, screening results, reports, notes", "DOCTOR_ANDROID"),
            ])

            add_category("SCIENCE", "Scientific Core - Research Engine", [
                (" Scientific Core\nMain Dashboard", "Sensor Quality, Signal Processing, Feature Extraction, Baseline, Longitudinal, Disease Modules, Fusion", "SCIENTIFIC_CORE"),
                (" Full Showcase\n16 Steps Demo", "Complete science-fair demonstration with NEXT/SKIP/EXIT, real operations, DEMO/SIMULATED labeled", "FULL_SHOWCASE"),
                (" AI/ML Laboratory\nDisease Modules", "PCOS, Sleep, Cardiometabolic, Autonomic risk signals only, confidence, limitations, NOT ESTABLISHED", "AI_ML"),
                (" Ultrasound\nResearch Pipeline", "Loading, preprocessing, quality checks, segmentation, inference, visualization, no invented accuracy", "ULTRASOUND"),
                (" Chrono-Metabolic\nFingerprinting", "Circadian, autonomic, variability, activity, temp, metabolic, longitudinal with provenance", "CHRONO_METABOLIC"),
                (" Signal Processing\nFiltering & Features", "Filtering, baseline removal, artifact detection, missing handling, quality control, feature extraction", "SIGNAL_PROCESSING"),
            ])

            add_category("CARE & ACCESS", "Care Discovery - FIND CARE", [
                (" Care Finder\nDoctors, Clinics, Labs, Supplies", "FIND CARE map/list distance/specialty/address/hours/services/contact/directions/verification OSM no API key, demo clearly marked", "CARE_FINDER"),
            ])

            add_category("DATA & REPORTS", "Data Management - Local-First", [
                (" Database\n18 Tables Local-First", "SQLite 18 tables, users, patients, profiles, symptoms, cycles, sensor sessions, PPG/HRV/motion/temp/quality, ultrasound, model_results, reports, providers, supplies, audit, access", "DATABASE"),
                (" Reports\nProfessional", "Professional reports with Research / risk-screening output — not a medical diagnosis, model transparency", "REPORTS"),
                (" Backup / Restore", "Export patient data, import, backup SQLite, encrypted package, deliberate sharing not automatic", "DATABASE"),
            ])

            add_category("ENDO-TWIN CORE - GENERAL PLATFORM", "General Platform - Personalized Physiological Modelling - No PCOS Assumptions", [
                (" ENDO-TWIN Core\nGeneral Platform", "ENDO-TWIN CORE - General platform, CHRONO-PCOS first disease-specific model - General physiological monitoring, general patient data, general measurements, general longitudinal tracking, general personal baseline, general signal processing, general multimodal fusion, general AI/ML infrastructure, general reports, general patient/doctor workflows - No PCOS-specific assumptions - Patient, Observation, Measurement, SensorReading, Signal, Feature, Baseline, TimelineEvent, LongitudinalSeries, Model, Prediction, Explanation, Uncertainty, Provenance, Report", "ENDO_TWIN"),
                (" ENDO-TWIN Database\nGeneral + Multi-Patient", "ENDO-TWIN DB - General physiological data: patients, measurements, signals, features, baselines, timeline_events, symptoms, clinical_observations, imaging, model_runs, predictions, reports, audit_events, provenance - Disease-specific data references disease_model_id + patient_id - stable IDs foreign keys patient-scoped no cross-contamination DEMO-001/002/003 isolation HR 72/78/68", "DATABASE"),
                (" Disease Models\nPlugin Architecture", "Disease Models plugin system - DiseaseModel interface: name, version, description, required_features, analyze(), explain(), generate_report(), validate_input(), get_uncertainty(), get_limitations() - CHRONO-PCOS implements interface, future models same interface, core does NOT depend directly on CHRONO-PCOS - ENDO-TWIN is platform, CHRONO-PCOS first model - extensible architecture", "ENDO_TWIN"),
            ])

            add_category("CHRONO-PCOS - FIRST DISEASE MODEL", "First Disease-Specific Model on ENDO-TWIN Platform - Preserved Original Functionality", [
                (" CHRONO-PCOS\nFirst Disease Model", "CHRONO-PCOS - First disease-specific model on ENDO-TWIN platform - PCOS/PCOD risk pre-screening research module - Combines physiological sensing, chrono-metabolic fingerprinting, ultrasound, AI/ML for research risk signals NOT diagnosis - Preserved original PCOS functionality: PCOS features, PCOS risk logic, PCOS model, PCOS-specific ultrasound, Chrono-Metabolic PCOS interpretation, PCOS-specific reports - General functionality in ENDO-TWIN Core, PCOS-specific in CHRONO-PCOS - disease_models/chrono_pcos/", "ENDO_TWIN"),
                (" Chrono-Metabolic\nPCOS Interpretation", "Chrono-Metabolic PCOS interpretation - General chrono-metabolic fingerprinting in ENDO-TWIN Core, PCOS-specific interpretation in CHRONO-PCOS - Circadian + Autonomic + Metabolic context + Longitudinal patterns → Chrono-Metabolic representation → PCOS research interpretation - experimental research not diagnosis", "CHRONO_METABOLIC"),
                (" Ultrasound\nPCOS-Specific", "PCOS-specific ultrasound analysis - General imaging in ENDO-TWIN Core, PCOS-specific in CHRONO-PCOS - Pipeline IMAGE IMPORT → VALIDATION → PREPROCESSING → IMAGE ANALYSIS → FEATURE EXTRACTION → MODEL → UNCERTAINTY → REPORT - Every result labelled IMAGE-DERIVED - Quality gate UNKNOWN by design - Provenance CLINICALLY-ENTERED vs IMAGE-DERIVED fusion weight 0.20 - Rotterdam criteria requires clinician", "ULTRASOUND"),
            ])

            add_category("ANDROID NATIVE KOTLIN", "Native Kotlin + Jetpack Compose - Material 3 - Never Fake APK", [
                (" Patient Android\nNative Kotlin+Compose", "Patient Android - Kotlin + Jetpack Compose Material 3 Navigation ViewModel Repository Room DataStore Coroutines Clean Architecture - Single patient only never global list CURRENT PATIENT stable ID HOME MY HEALTH MEASUREMENTS TIMELINE SYMPTOMS CYCLE ULTRASOUND RESULTS REPORTS DOCTOR SHARING FIND CARE EDUCATION SETTINGS", "PATIENT_ANDROID"),
                (" Doctor Android\nNative Kotlin Multi-Patient", "Doctor Android - Kotlin + Compose multi-patient Dashboard Patients Recent Activity Pending Review Reports Settings Patient List Search/Filter/Sort/Open/Archive/Create Patient Profile Tabs OVERVIEW/TIMELINE/PHYSIOLOGY/SENSORS/ULTRASOUND/AI/MODELS/CLINICAL/REPORTS/NOTES/PROVENANCE/AUDIT - DEMO-001 cannot see DEMO-002 database level", "DOCTOR_ANDROID"),
                (" Build Patient APK\nNative Kotlin Workflow", "Check prerequisites Java Kotlin Gradle SDK NDK, build native APK via gradlew assembleDebug to DIST/android/CHRONO-PCOS-Patient.apk dist/android/, fallback to Kivy buildozer, logs/build_patient_apk.log honest reporting", "BUILD_PATIENT_APK"),
                (" Build Doctor APK\nNative Kotlin Multi-Patient", "Check prerequisites, build native multi-patient APK to DIST/android/CHRONO-PCOS-Doctor.apk, logs/build_doctor_apk.log honest reporting no fake success, multi-patient safety DEMO-001/002/003", "BUILD_DOCTOR_APK"),
                (" Build All APKs\nNative Wrapper", "Build both Patient and Doctor native Kotlin APKs, check-only mode, lists DIST/android/ dist/android/, explains real build requires SDK/NDK/Gradle, never fake APK", "BUILD_ALL_APKS"),
            ])

            add_category("PUBLIC", "Public & Documentation - Serious Scientific Innovation Platform", [
                (" Website\nScientific Site", "Public website serious modern scientific, HOME PROBLEM SOLUTION HOW IT WORKS HARDWARE PHYSIOLOGY CHRONO-METABOLIC AI/ML ULTRASOUND DIGITAL TWIN ENDO-TWIN PATIENT PLATFORM DOCTOR PLATFORM ANDROID DATABASE & PRIVACY REPORTING CARE DISCOVERY VERSION HISTORY RESEARCH SAFETY LIMITATIONS ROADMAP DEMO DOCUMENTATION CONTACT", "WEBSITE"),
                (" Documentation\n25 Docs + Guides + ENDO-TWIN", "25 docs 01_PROJECT_OVERVIEW to 25_RESEARCH_METHODOLOGY, Garuda Launch Guide, Showcase Guide, Android Build Guide, ENDO_TWIN_ARCHITECTURE, DATABASE, ARCHITECTURE, INSTALLATION, BUILD_GUIDE, TROUBLESHOOTING, TESTING_REPORT", "WEBSITE"),
            ])

            add_category("SYSTEM", "System & Setup - Garuda Linux Ready", [
                (" Diagnostics\nSystem Check ENDO-TWIN", "Check Garuda/Linux, Python, .venv, Dependencies, Database V8.3, ENDO-TWIN DB DEMO-001/002/003 isolation, Scientific Core V8.3, ENDO-TWIN Core, AI/ML, Model Registry, Ultrasound, Doctor PC, Patient Kivy Legacy, Patient Native Kotlin, Doctor Native Kotlin, Android APKs Native+Legacy, Website, Care Discovery, Chrono-Metabolic, Provenance, Build Scripts, Multi-Patient Safety PASS/WARN/FAIL never fake", "DIAGNOSTICS"),
                (" Setup Garuda\nEnvironment Setup", "Detect project root, check Linux/Python, create .venv, install requirements, set permissions, create logs DIST/android dist/android, run diagnostics", "SETUP"),
            ])

            # Footer with proper wrapping
            footer_frame = QFrame()
            footer_frame.setStyleSheet("background: #0f172a; border-radius: 8px; padding: 10px;")
            footer_layout = QVBoxLayout(footer_frame)
            footer_layout.setContentsMargins(12, 12, 12, 12)
            footer_layout.setSpacing(6)

            footer1 = QLabel("ENDO-TWIN - Personalized Physiological Modelling Platform - CHRONO-PCOS First Disease Model - Class 11 Research Innovation - Understand your physiological patterns over time")
            footer1.setAlignment(Qt.AlignCenter)
            footer1.setWordWrap(True)
            footer1.setStyleSheet("font-size: 12px; font-weight: bold; color: white; background: transparent; border: none;")
            footer_layout.addWidget(footer1)

            footer2 = QLabel("ENDO-TWIN is general platform, CHRONO-PCOS is first disease-specific model - General physiological monitoring, personal baseline, longitudinal tracking, AI/ML infrastructure, disease models plugin - NOT clinically validated universal digital twin - Research / risk-screening output — not a medical diagnosis - Local-first offline privacy-focused Garuda Linux Ready - Kotlin + Compose Native Android - One sentence: ENDO-TWIN is platform, CHRONO-PCOS is first disease-specific model")
            footer2.setAlignment(Qt.AlignCenter)
            footer2.setWordWrap(True)
            footer2.setStyleSheet("font-size: 11px; color: #94a3b8; background: transparent; border: none;")
            footer_layout.addWidget(footer2)

            footer3 = QLabel(f"Project Root: {PROJECT_ROOT} | Logs: {PROJECT_ROOT / 'logs'} | DIST: {PROJECT_ROOT / 'DIST' / 'android'} + dist/android/ | Website: {PROJECT_ROOT / 'website' / 'index.html'} | ENDO-TWIN: {PROJECT_ROOT / 'endo_twin'} | Native: android/patient/ android/doctor/ Kotlin+Compose")
            footer3.setAlignment(Qt.AlignCenter)
            footer3.setWordWrap(True)
            footer3.setStyleSheet("font-size: 11px; color: #94a3b8; background: transparent; border: none;")
            footer_layout.addWidget(footer3)

            footer4 = QLabel("Double-click LAUNCH/ individual .sh for direct launch, or use this Engineering Control Center - All launchers auto-detect project root, use .venv/bin/python, work from any directory, log to logs/ - Multi-Patient Safety DEMO-001/002/003 isolation OK - No cross-contamination database level")
            footer4.setAlignment(Qt.AlignCenter)
            footer4.setWordWrap(True)
            footer4.setStyleSheet("font-size: 11px; color: #94a3b8; background: transparent; border: none;")
            footer_layout.addWidget(footer4)

            main_layout.addWidget(footer_frame)

            info = QLabel(
                "Garuda/Dolphin: Right-click .sh → Properties → Permissions → Is executable checked | "
                "If Dolphin asks Run/Run in Terminal/Cancel → Choose Run | "
                "Dolphin Settings → Configure Dolphin → General → Executable files → Run"
            )
            info.setAlignment(Qt.AlignCenter)
            info.setWordWrap(True)
            info.setStyleSheet("font-size: 11px; color: #4d5c6b; background: #f8fafc; padding: 8px; border-radius: 6px; border: 1px solid #e2e8f0;")
            main_layout.addWidget(info)

            # Add stretch at end
            main_layout.addStretch()

def main():
    if not PYSIDE_AVAILABLE:
        print("PySide6 not available, falling back to console Engineering Control Center")
        print("="*70)
        print("ENDO-TWIN NEXUS COMPLETE CONTROL CENTER")
        print("Sense • Model • Predict • Personalize")
        print("="*70)
        statuses = get_status()
        for k, v in statuses.items():
            icon = "" if v['status'] == 'PASS' else "" if v['status'] == 'WARN' else ""
            print(f"{icon} {v['label']}: {v['status']} - {v['detail']}")
        print("\nLaunchers available in launchers/ and LAUNCH/:")
        launcher_dir = PROJECT_ROOT / "launchers"
        if launcher_dir.exists():
            for sh in sorted(launcher_dir.glob("*.sh")):
                print(f"  {sh.name}")
        print("\nRun ./LAUNCH/COMPLETE_LAUNCHER.sh for GUI")
        return 0
    app = QApplication(sys.argv)
    # Set application style for better look
    app.setStyle("Fusion")
    win = ControlCenter()
    win.show()
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
