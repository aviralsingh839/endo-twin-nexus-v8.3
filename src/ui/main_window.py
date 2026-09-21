"""Main Window for CHRONO-TWIN NEXUS V8.3.

Dashboard sections:
- Overview: personal physiological status
- Baseline: what is normal for user
- Trends: changes over time
- Health Signals: PCOS, Sleep, Cardiometabolic, Autonomic
- Data Quality: sensor status and confidence
- Clinical Inputs: manual clinical measurements
- Ultrasound: image and structured features
- Explanation: why system generated signal
- Report: research report

Keeps V8.1 wearable pod and mega hub working.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from collections import deque
from dataclasses import fields

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QStackedWidget, QButtonGroup, QLabel, QPushButton, QGroupBox, QGridLayout, QTextEdit,
    QDoubleSpinBox, QSpinBox, QComboBox, QScrollArea, QFrame,
    QLineEdit, QProgressBar, QSplitter
)

from src.config import APP_VERSION, APP_VERSION_LABEL, APP_NAME, APP_TAGLINE, UserProfile, DATA_DIR
from database.database import LocalDatabase
from src.ml.self_learning import SelfLearningEngine
from src.data_models import FeatureVector, SensorSample, SharedPhysiologicalFeatures
from src.core.personal_baseline import PersonalBaselineEngine
from src.core.longitudinal_engine import LongitudinalEngine
from src.core.feature_extraction import RealtimeFeatureExtractor
from src.core.shared_features import SharedFeatureExtractor
from src.core.quality_control import SensorQualityControl
from src.disease_modules.registry import GLOBAL_REGISTRY
from src.fusion.multimodal_fusion import FusionEngine
from src.explainability.explanation_engine import ExplanationEngine
from src.serial_io.arduino_reader import ArduinoReader
from src.serial_io.network_reader import NetworkReader
from src.ui.theme import DARK_QSS, GREEN, ORANGE, RED, YELLOW, TEXT_MUTED
from src.ui.gauges import GaugeWidget
from src.ui.vital_cards import VitalCard
from src.ui.live_plots import TimeSeriesPlot
from src.ui.voice_vasc_tab import VoiceVascTab
from src.utils.demo_stream import DemoSensorStream
from src.utils.history_store import HistoryStore
from src.utils.synthetic import generate_subject_timeline, SyntheticSubjectProfile

DISCLAIMER = "Research prototype, NOT a diagnosis. Clinical evaluation required."


class MainWindow(QMainWindow):
    def __init__(self, start_demo: bool = False, port: str | None = None, net: str | None = None, db_path=None):
        super().__init__()
        self.setWindowTitle(f"ENDO-TWIN NEXUS {APP_VERSION} • Research Workstation • {APP_VERSION_LABEL}")
        self.resize(1600, 1000)
        self.setStyleSheet(DARK_QSS)

        # Core engines
        self.profile = UserProfile()
        self.baseline_engine = PersonalBaselineEngine()
        self.longitudinal_engine = LongitudinalEngine(baseline=self.baseline_engine)
        self.extractor = RealtimeFeatureExtractor(profile=self.profile, baseline_engine=self.baseline_engine)
        self.shared_extractor = SharedFeatureExtractor(baseline_engine=self.baseline_engine)
        self.fusion_engine = FusionEngine()
        self.explanation_engine = ExplanationEngine()
        self.quality_control = SensorQualityControl()

        # State
        self.feature_history: list[FeatureVector] = []
        self.shared_history: list[SharedPhysiologicalFeatures] = []
        self.module_results = {}
        self.fusion_result = None
        self.current_shared: SharedPhysiologicalFeatures | None = None
        self.clinical_data: dict = {}
        self.ultrasound_data: dict | None = None
        self.demo_stream: DemoSensorStream | None = None
        self.arduino_reader: ArduinoReader | None = None
        self.network_reader: NetworkReader | None = None
        self.history_store = HistoryStore(db_path) if db_path else HistoryStore()
        self.local_db = LocalDatabase(db_path)
        self.self_learning = SelfLearningEngine()
        self.active_patient_id: str | None = None
        self.active_study_id: str | None = None
        self.active_session_id: str | None = None
        self.active_device_id: str | None = None

        # Timers
        self.feature_timer = QTimer()
        self.feature_timer.timeout.connect(self._update_features)
        self.feature_timer.start(1000)

        self.risk_timer = QTimer()
        self.risk_timer.timeout.connect(self._update_risk)
        self.risk_timer.start(2000)

        # Modern application shell: persistent branding + left navigation + stacked workspaces.
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(14, 14, 14, 10)
        layout.setSpacing(10)

        layout.addWidget(self._build_header())

        body = QHBoxLayout()
        body.setSpacing(12)

        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setMinimumWidth(218)
        sidebar.setMaximumWidth(250)
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(10, 12, 10, 12)
        side_layout.setSpacing(5)

        section = QLabel("WORKSPACES")
        section.setObjectName("SectionEyebrow")
        side_layout.addWidget(section)
        side_layout.addSpacing(4)

        self.stack = QStackedWidget()
        self.tabs = self.stack  # Compatibility alias for existing integrations.

        pages = [
            ("⌂  Overview", self._build_overview_tab()),
            ("♙  Patients", self._build_patients_tab()),
            ("◉  Wearable & Sync", self._build_wearable_tab()),
            ("◌  Personal Baseline", self._build_baseline_tab()),
            ("⌁  Longitudinal Trends", self._build_trends_tab()),
            ("◈  Health Signals", self._build_health_signals_tab()),
            ("◉  VoxVasc", VoiceVascTab()),
            ("✦  Self-Learning", self._build_self_learning_tab()),
            ("◇  Data Quality", self._build_data_quality_tab()),
            ("▦  Clinical Inputs", self._build_clinical_tab()),
            ("◉  Ultrasound", self._build_ultrasound_tab()),
            ("✦  Explanation", self._build_explanation_tab()),
            ("▤  Report", self._build_report_tab()),
            ("✓  Validation", self._build_validation_tab()),
            ("⌘  Care & Supplies", self._build_care_tab()),
            ("▣  Database", self._build_database_tab()),
            ("◫  Audit", self._build_audit_tab()),
        ]
        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        self.nav_buttons = []

        for idx, (label, page) in enumerate(pages):
            button = QPushButton(label)
            button.setObjectName("NavButton")
            button.setCheckable(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            self.nav_group.addButton(button, idx)
            self.nav_buttons.append(button)
            side_layout.addWidget(button)
            self.stack.addWidget(page)

        side_layout.addStretch(1)

        context = QFrame()
        context.setObjectName("StatusPill")
        context_layout = QVBoxLayout(context)
        context_layout.setContentsMargins(10, 9, 10, 9)
        context_layout.addWidget(QLabel("ACTIVE CONTEXT"))
        self.context_label = QLabel("ENDO-TWIN core → CHRONO-PCOS")
        self.context_label.setStyleSheet("font-weight: 750;")
        context_layout.addWidget(self.context_label)
        context_layout.addWidget(QLabel("Local-first • provenance-aware"))
        side_layout.addWidget(context)

        self.nav_group.idClicked.connect(self._switch_workspace)
        self.nav_buttons[0].setChecked(True)
        self.stack.setCurrentIndex(0)

        body.addWidget(sidebar)
        body.addWidget(self.stack, 1)
        layout.addLayout(body, 1)

        self.status_label = QLabel(
            f"● {APP_NAME} V8.3  •  ENDO-TWIN platform  •  Research prototype  •  {DISCLAIMER}"
        )
        self.status_label.setObjectName("FooterText")
        layout.addWidget(self.status_label)


        if start_demo:
            self.start_demo()
        if port:
            self.connect_serial(port)
        if net:
            self.connect_network(net)

    def _switch_workspace(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        if 0 <= index < len(self.nav_buttons):
            self.nav_buttons[index].setChecked(True)

    def _build_header(self):
        header = QFrame()
        header.setObjectName("AppHeader")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(12)

        mark = QFrame()
        mark.setObjectName("BrandMark")
        mark.setFixedSize(52, 52)
        mark_layout = QVBoxLayout(mark)
        mark_layout.setContentsMargins(0, 0, 0, 0)
        logo = QLabel("ET")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet("color: white; font-size: 17pt; font-weight: 900;")
        mark_layout.addWidget(logo)
        layout.addWidget(mark)

        brand = QVBoxLayout()
        title = QLabel("ENDO-TWIN NEXUS")
        title.setObjectName("BrandTitle")
        subtitle = QLabel(
            "Personalized physiological modelling platform  •  CHRONO-PCOS first disease module"
        )
        subtitle.setObjectName("BrandSubtitle")
        brand.addWidget(title)
        brand.addWidget(subtitle)
        layout.addLayout(brand, 1)

        local = QFrame()
        local.setObjectName("StatusPill")
        local_layout = QVBoxLayout(local)
        local_layout.setContentsMargins(10, 6, 10, 6)
        local_layout.addWidget(QLabel("LOCAL • RESEARCH"))
        local_label = local.findChild(QLabel)
        if local_label:
            local_label.setObjectName("Good")
        local_layout.addWidget(QLabel("No cloud upload by default"))
        layout.addWidget(local)

        self.port_combo = QComboBox()
        self.port_combo.setEditable(True)
        self.port_combo.addItems(["/dev/ttyACM0", "/dev/ttyUSB0", "COM5"])
        self.port_combo.setToolTip("Serial port for the wearable controller")
        layout.addWidget(self.port_combo)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.setObjectName("Secondary")
        refresh_btn.clicked.connect(self._refresh_ports)
        layout.addWidget(refresh_btn)

        connect_btn = QPushButton("Connect wearable")
        connect_btn.setObjectName("Primary")
        connect_btn.clicked.connect(self.connect_serial)
        layout.addWidget(connect_btn)

        demo_btn = QPushButton("Run synthetic demo")
        demo_btn.setObjectName("Secondary")
        demo_btn.clicked.connect(self.start_demo)
        layout.addWidget(demo_btn)

        stop_btn = QPushButton("Stop")
        stop_btn.setObjectName("Danger")
        stop_btn.clicked.connect(self.stop_stream)
        layout.addWidget(stop_btn)

        self.net_edit = QLineEdit()
        self.net_edit.setPlaceholderText("Wi-Fi bridge IP:port")
        self.net_edit.setMaximumWidth(190)
        layout.addWidget(self.net_edit)

        net_btn = QPushButton("Bridge")
        net_btn.setObjectName("Secondary")
        net_btn.clicked.connect(lambda: self.connect_network(self.net_edit.text().strip()))
        layout.addWidget(net_btn)

        scenario_btn = QPushButton("Scenario")
        scenario_btn.setObjectName("Secondary")
        scenario_btn.clicked.connect(self._load_scenario_dialog)
        layout.addWidget(scenario_btn)

        return header

    def _set_active_patient(self, patient_id: str | None) -> None:
        self.active_patient_id = patient_id
        patient = self.local_db.get_patient(patient_id) if patient_id else None
        alias = patient.get("anonymous_id") if patient else "none"
        study = self.local_db.get_active_study(patient_id) if patient_id else None
        self.active_study_id = study.get("study_id") if study else None
        if hasattr(self, "context_label"):
            self.context_label.setText(
                f"ENDO-TWIN core → CHRONO-PCOS  •  Patient {alias}"
                if patient else "ENDO-TWIN core → CHRONO-PCOS  •  No patient selected"
            )
        if hasattr(self, "patient_context_label"):
            self.patient_context_label.setText(
                f"Active patient: {alias}  •  study: {'ACTIVE' if study else 'none'}"
            )
        self._refresh_session_table(patient_id)

    def _selected_patient_id(self) -> str | None:
        if not hasattr(self, "patient_table"):
            return self.active_patient_id
        row = self.patient_table.currentRow()
        if row < 0:
            return self.active_patient_id
        item = self.patient_table.item(row, 0)
        return str(item.data(Qt.ItemDataRole.UserRole)) if item else self.active_patient_id

    def _refresh_patient_table(self) -> None:
        if not hasattr(self, "patient_table"):
            return
        patients = self.local_db.list_patients()
        self.patient_table.setRowCount(0)
        for patient in patients:
            row = self.patient_table.rowCount()
            self.patient_table.insertRow(row)
            cells = [
                patient.get("anonymous_id", ""),
                patient.get("display_name") or "Research participant",
                patient.get("age_years") if patient.get("age_years") is not None else "—",
                patient.get("bmi") if patient.get("bmi") is not None else "—",
                "ARCHIVED" if patient.get("is_archived") else "ACTIVE",
            ]
            for col, value in enumerate(cells):
                item = QTableWidgetItem(str(value))
                if col == 0:
                    item.setData(Qt.ItemDataRole.UserRole, patient["patient_id"])
                self.patient_table.setItem(row, col, item)
        self.patient_status.setText(
            f"{len(patients)} active local patient record(s). Real observations and DEMO_DATA remain explicitly separated."
        )

    def _refresh_session_table(self, patient_id: str | None = None) -> None:
        if not hasattr(self, "session_table"):
            return
        pid = patient_id or self.active_patient_id
        self.session_table.setRowCount(0)
        if not pid:
            return
        for session in self.local_db.list_sessions(pid):
            row = self.session_table.rowCount()
            self.session_table.insertRow(row)
            values = [
                str(session.get("session_id", ""))[:12] + "…",
                time.strftime("%Y-%m-%d %H:%M", time.localtime(session["start_at"])),
                time.strftime("%Y-%m-%d %H:%M", time.localtime(session["end_at"])) if session.get("end_at") else "ACTIVE",
                session.get("sample_count", 0),
                "—" if session.get("data_quality") is None else f"{float(session['data_quality']):.2f}",
            ]
            for col, value in enumerate(values):
                self.session_table.setItem(row, col, QTableWidgetItem(str(value)))

    def _create_patient_dialog(self) -> None:
        alias, ok = QInputDialog.getText(self, "Create research participant", "Anonymous participant ID:")
        if not ok:
            return
        alias = alias.strip()
        if not alias:
            QMessageBox.warning(self, "Missing participant ID", "Enter an anonymous participant ID.")
            return
        age, ok = QInputDialog.getDouble(self, "Participant age", "Age (years):", 18.0, 10.0, 100.0, 1)
        if not ok:
            return
        bmi, ok = QInputDialog.getDouble(self, "Participant BMI", "BMI (0 = unknown):", 0.0, 0.0, 80.0, 1)
        if not ok:
            return
        try:
            pid = self.local_db.create_patient(
                anonymous_id=alias,
                display_name="Research participant",
                age_years=age,
                bmi=bmi if bmi > 0 else None,
            )
            self._set_active_patient(pid)
            self._refresh_patient_table()
            self.patient_status.setText(f"Created {alias}. Start a 48-hour research study when ready.")
        except Exception as exc:
            QMessageBox.critical(self, "Patient creation failed", str(exc))

    def _load_stored_features(self, patient_id: str) -> int:
        """Load patient-scoped stored features into the live analysis view."""
        rows = list(reversed(self.local_db.list_feature_vectors(patient_id, limit=5000)))
        vectors = []
        feature_names = {f.name for f in fields(FeatureVector)}
        for row in rows:
            try:
                data = json.loads(row.get("data_json", "{}"))
                if not isinstance(data, dict):
                    continue
                kwargs = {name: data[name] for name in feature_names if name in data}
                vectors.append(FeatureVector(**kwargs))
            except Exception:
                continue

        self.feature_history = vectors[-5000:]
        self.shared_history = []
        self.current_shared = None
        if self.feature_history:
            try:
                self.current_shared = self.shared_extractor.extract(
                    self.feature_history[-1],
                    self.feature_history[-50:],
                )
                self.shared_history.append(self.current_shared)
            except Exception:
                self.current_shared = None
            try:
                self._update_risk()
            except Exception:
                pass
        return len(self.feature_history)

    def _open_selected_patient(self) -> None:
        pid = self._selected_patient_id()
        if not pid:
            QMessageBox.information(self, "Select a patient", "Select a patient row first.")
            return
        self._set_active_patient(pid)
        patient = self.local_db.get_patient(pid) or {}
        sessions = self.local_db.list_sessions(pid)

        # Restore this participant's entered context before running any module.
        self.profile.age_years = patient.get("age_years") or self.profile.age_years
        self.profile.bmi = patient.get("bmi")
        self.clinical_data = {
            "age_years": self.profile.age_years,
            "bmi": self.profile.bmi,
            "profile": self.profile,
        }
        self.extractor.set_profile(self.profile)

        loaded = self._load_stored_features(pid)
        self.patient_status.setText(
            f"Active patient {patient.get('anonymous_id', pid)} • {len(sessions)} stored wear session(s) • "
            f"{loaded} stored feature vector(s) loaded • study {'ACTIVE' if self.local_db.get_active_study(pid) else 'none'}"
        )
        self._switch_workspace(0)

    def _start_48h_study(self) -> None:
        pid = self._selected_patient_id() or self.active_patient_id
        if not pid:
            QMessageBox.information(self, "Select a patient", "Create/select a participant first.")
            return
        self._set_active_patient(pid)
        if self.local_db.get_active_study(pid):
            QMessageBox.information(self, "Study already active", "This participant already has an active study.")
            return
        self.active_study_id = self.local_db.start_study(
            pid,
            duration_hours=48.0,
            protocol={
                "purpose": "two_day_observation",
                "wear_policy": "remove_before_bathing; reconnect_after_bathing",
                "missing_data_policy": "preserve_gap",
                "model_mode": "research_screening_only",
            },
            label="REAL",
        )
        self.patient_status.setText(
            "48-hour study active. Start a wear session; remove before bathing and reconnect afterward."
        )
        self._set_active_patient(pid)

    def _start_wear_session(self) -> None:
        pid = self.active_patient_id
        if not pid:
            QMessageBox.information(self, "No active patient", "Select a patient first.")
            return
        study = self.local_db.get_active_study(pid)
        if not study:
            self._start_48h_study()
            study = self.local_db.get_active_study(pid)
        if not study:
            return
        device_id = self.device_id_edit.text().strip() or "WEARABLE-01"
        self.active_device_id = device_id
        self.local_db.register_wearable(pid, device_id, "ENDO-TWIN prototype wearable", "serial_or_mobile_ble")
        self.local_db.set_wearable_state(pid, device_id, "WORN", "wear session started")
        self.active_session_id = self.local_db.create_session(
            pid,
            source="WEARABLE_SERIAL_OR_MOBILE",
            label="REAL",
            notes="Wear episode. A removal event closes the episode and preserves the gap.",
            study_id=study["study_id"],
        )
        self.wearable_state_label.setText("WORN • active wear episode")
        self.sync_status_label.setText("Session active. Connect the wearable transport and begin acquisition.")
        self._set_active_patient(pid)

    def _remove_for_bathing(self) -> None:
        pid = self.active_patient_id
        if not pid:
            return
        if self.active_session_id:
            self.local_db.close_sensor_session(pid, self.active_session_id, "Wearable removed before bathing.")
            self.local_db.record_wearable_event(
                pid, self.active_session_id, "WEARABLE_REMOVED_BATHING",
                {"gap_is_missing_data": True},
            )
            self.active_session_id = None
        if self.active_device_id:
            self.local_db.set_wearable_state(pid, self.active_device_id, "REMOVED", "removed before bathing")
        self.stop_stream()
        self.wearable_state_label.setText("REMOVED • bathing gap recorded")
        self.sync_status_label.setText("No data will be generated during the removal interval.")

    def _reconnect_wearable(self) -> None:
        pid = self.active_patient_id
        study = self.local_db.get_active_study(pid) if pid else None
        if not pid or not study:
            QMessageBox.information(self, "No active study", "Select a participant and start the 48-hour study first.")
            return
        device_id = self.active_device_id or self.device_id_edit.text().strip() or "WEARABLE-01"
        self.active_device_id = device_id
        self.local_db.register_wearable(pid, device_id, "ENDO-TWIN prototype wearable", "serial_or_mobile_ble")
        self.local_db.set_wearable_state(pid, device_id, "WORN", "reconnected after removal")
        self.active_session_id = self.local_db.create_session(
            pid,
            source="WEARABLE_SERIAL_OR_MOBILE",
            label="REAL",
            notes="Wear episode after explicit removal/reconnection.",
            study_id=study["study_id"],
        )
        self.local_db.record_wearable_event(pid, self.active_session_id, "WEARABLE_RECONNECTED", {"previous_gap": True})
        self.wearable_state_label.setText("RECONNECTED • WORN")
        self.sync_status_label.setText("New wear episode active. Connect the wearable transport now.")

    def _end_study(self) -> None:
        pid = self.active_patient_id
        if not pid:
            return
        if self.active_session_id:
            self.local_db.close_sensor_session(pid, self.active_session_id, "Study ended.")
            self.active_session_id = None
        self.stop_stream()
        if self.active_device_id:
            self.local_db.set_wearable_state(pid, self.active_device_id, "NOT_CONNECTED", "study ended")
        study = self.local_db.get_active_study(pid)
        if study:
            self.local_db.end_study(pid, study["study_id"], "COMPLETED")
        self.active_study_id = None
        self.wearable_state_label.setText("STUDY ENDED")
        self.sync_status_label.setText("Study ended. Export the complete patient package for doctor review.")

    def _export_patient_package(self) -> None:
        pid = self.active_patient_id or self._selected_patient_id()
        if not pid:
            QMessageBox.information(self, "Select a patient", "Select a patient first.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export complete patient package",
            str(DATA_DIR / "exports" / f"endo_twin_{pid[:8]}.json"),
            "JSON files (*.json)"
        )
        if not path:
            return
        try:
            package = self.local_db.export_patient_data(pid)
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            Path(path).write_text(json.dumps(package, indent=2, default=str), encoding="utf-8")
            if hasattr(self, "sync_status_label"):
                self.sync_status_label.setText(f"Complete patient package exported → {path}")
        except Exception as exc:
            QMessageBox.critical(self, "Export failed", str(exc))

    def _import_patient_package(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Import mobile patient package", "", "JSON files (*.json)")
        if not path:
            return
        try:
            package = json.loads(Path(path).read_text(encoding="utf-8"))
            pid = self.local_db.import_patient_data(package)
            self._set_active_patient(pid)
            loaded = self._load_stored_features(pid)
            self._refresh_patient_table()
            self.sync_status_label.setText(
                f"Imported patient {pid}: sessions, raw sensor channels, features, events and research metadata merged. {loaded} feature vector(s) available for analysis."
            )
        except Exception as exc:
            QMessageBox.critical(self, "Import failed", str(exc))

    def _build_patients_tab(self):
        tab = QWidget()
        root = QVBoxLayout(tab)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(14)

        title = QLabel("Patients")
        title.setObjectName("HeroTitle")
        root.addWidget(title)
        sub = QLabel("Real patient-scoped workspaces. A participant's 48-hour study may contain multiple wear episodes and explicit removal gaps.")
        sub.setObjectName("HeroSubtitle")
        sub.setWordWrap(True)
        root.addWidget(sub)

        actions = QHBoxLayout()
        for label, slot, obj in [
            ("Create participant", self._create_patient_dialog, "Primary"),
            ("Open selected", self._open_selected_patient, "Secondary"),
            ("Start 48-hour study", self._start_48h_study, "Primary"),
            ("Export package", self._export_patient_package, "Secondary"),
            ("Import mobile package", self._import_patient_package, "Secondary"),
        ]:
            b = QPushButton(label)
            b.setObjectName(obj)
            b.clicked.connect(slot)
            actions.addWidget(b)
        root.addLayout(actions)

        self.patient_table = QTableWidget(0, 5)
        self.patient_table.setHorizontalHeaderLabels(["Participant", "Display", "Age", "BMI", "Status"])
        self.patient_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.patient_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.patient_table.horizontalHeader().setStretchLastSection(True)
        self.patient_table.horizontalHeader().setSectionResizeMode(0, QTableWidget.ResizeMode.Stretch)
        self.patient_table.itemSelectionChanged.connect(lambda: self._set_active_patient(self._selected_patient_id()))
        root.addWidget(self.patient_table, 1)

        sessions_title = QLabel("Selected patient's wear sessions")
        sessions_title.setObjectName("SectionEyebrow")
        root.addWidget(sessions_title)
        self.session_table = QTableWidget(0, 5)
        self.session_table.setHorizontalHeaderLabels(["Session", "Start", "End", "Samples", "Quality"])
        self.session_table.horizontalHeader().setStretchLastSection(True)
        root.addWidget(self.session_table, 1)

        self.patient_status = QLabel("Loading…")
        self.patient_status.setObjectName("SmallMuted")
        root.addWidget(self.patient_status)
        self._refresh_patient_table()
        return tab

    def _build_wearable_tab(self):
        tab = QWidget()
        root = QVBoxLayout(tab)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(14)

        title = QLabel("Wearable • Mobile • Sync")
        title.setObjectName("HeroTitle")
        root.addWidget(title)
        sub = QLabel("The wearable is a removable device. Wear episodes, bathing removals and reconnections are first-class data events.")
        sub.setObjectName("HeroSubtitle")
        sub.setWordWrap(True)
        root.addWidget(sub)

        self.patient_context_label = QLabel("Active patient: none • study: none")
        self.patient_context_label.setObjectName("BigValue")
        root.addWidget(self.patient_context_label)

        card = QFrame()
        card.setObjectName("ScientificCard")
        grid = QGridLayout(card)
        grid.addWidget(QLabel("Wearable ID"), 0, 0)
        self.device_id_edit = QLineEdit("WEARABLE-01")
        grid.addWidget(self.device_id_edit, 0, 1)
        grid.addWidget(QLabel("Transport"), 1, 0)
        transport = QLabel("USB serial • Android BLE/USB-OTG/Wi-Fi bridge transport boundary • hardware-specific packet configuration remains documented separately")
        transport.setWordWrap(True)
        grid.addWidget(transport, 1, 1)
        grid.addWidget(QLabel("State"), 2, 0)
        self.wearable_state_label = QLabel("NOT_CONNECTED")
        self.wearable_state_label.setObjectName("Warn")
        grid.addWidget(self.wearable_state_label, 2, 1)
        root.addWidget(card)

        actions = QGridLayout()
        for row, specs in enumerate([
            ("Start wear session", self._start_wear_session, "Primary"),
            ("Remove for bathing", self._remove_for_bathing, "Danger"),
            ("Reconnect", self._reconnect_wearable, "Primary"),
            ("End 48-hour study", self._end_study, "Secondary"),
            ("Export to doctor", self._export_patient_package, "Secondary"),
            ("Import from mobile", self._import_patient_package, "Secondary"),
        ]):
            b = QPushButton(specs[0])
            b.setObjectName(specs[2])
            b.clicked.connect(specs[1])
            actions.addWidget(b, row // 2, row % 2)
        root.addLayout(actions)

        self.sync_status_label = QLabel("No active patient/session. Local database is waiting for patient-scoped data.")
        self.sync_status_label.setObjectName("SmallMuted")
        self.sync_status_label.setWordWrap(True)
        root.addWidget(self.sync_status_label)

        protocol = QFrame()
        protocol.setObjectName("WarningCard")
        pl = QVBoxLayout(protocol)
        pl.addWidget(QLabel(
            "48-hour protocol: participant → study → wear episode → acquisition → remove before bathing → "
            "session closes → reconnect → new episode → final export. Missing intervals remain missing."
        ))
        root.addWidget(protocol)
        root.addStretch(1)
        return tab

    def _build_self_learning_tab(self):
        tab = QWidget()
        root = QVBoxLayout(tab)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(14)
        title = QLabel("Self-learning • Personal Twin")
        title.setObjectName("HeroTitle")
        root.addWidget(title)
        sub = QLabel(
            "The automatic layer learns this participant's baseline and short-term drift. "
            "It does not silently rewrite the CHRONO-PCOS model."
        )
        sub.setWordWrap(True)
        sub.setObjectName("HeroSubtitle")
        root.addWidget(sub)
        self.learning_status = QLabel("No personalization run yet.")
        self.learning_status.setObjectName("BigValue")
        root.addWidget(self.learning_status)

        actions = QHBoxLayout()
        b1 = QPushButton("Update personal twin")
        b1.setObjectName("Primary")
        b1.clicked.connect(self._run_personalization)
        b2 = QPushButton("Check disease-model training gate")
        b2.setObjectName("Secondary")
        b2.clicked.connect(self._show_training_gate)
        b3 = QPushButton("Train research candidate")
        b3.setObjectName("Secondary")
        b3.clicked.connect(self._train_candidate)
        actions.addWidget(b1)
        actions.addWidget(b2)
        actions.addWidget(b3)
        root.addLayout(actions)

        self.learning_details = QTextEdit()
        self.learning_details.setReadOnly(True)
        root.addWidget(self.learning_details, 1)

        safety = QFrame()
        safety.setObjectName("WarningCard")
        sl = QVBoxLayout(safety)
        sl.addWidget(QLabel(
            "A 48-hour observation can adapt the personal twin. It cannot by itself establish clinical accuracy for PCOS or another disease."
        ))
        root.addWidget(safety)
        return tab

    def _run_personalization(self):
        if not self.active_patient_id:
            self.learning_status.setText("Select a patient first.")
            return
        try:
            result = self.self_learning.personalize(self.local_db, self.active_patient_id)
            self.learning_status.setText(
                f"{result.status} • {result.observations} observations • {result.features_updated} baseline features updated"
            )
            self.learning_details.setText("\n".join(result.notes))
        except Exception as exc:
            self.learning_status.setText(f"ERROR • {exc}")

    def _train_candidate(self):
        gate = self.self_learning.candidate_training_gate(self.local_db)
        if gate["status"] != "READY_FOR_CANDIDATE_TRAINING":
            self.learning_status.setText(
                f"{gate['status']} • {gate['distinct_participants']} participant(s)"
            )
            self.learning_details.setText(
                gate["note"] + "\n\nAdd explicit research labels from independent participants before candidate training."
            )
            return
        try:
            result = self.self_learning.train_candidate(self.local_db)
            self.learning_status.setText(
                f"{result['status']} • {result.get('usable_participants', result.get('distinct_participants', 0))} participant(s)"
            )
            self.learning_details.setText(
                json.dumps(result, indent=2, default=str)
            )
        except Exception as exc:
            self.learning_status.setText(f"TRAINING ERROR • {exc}")

    def _show_training_gate(self):
        gate = self.self_learning.candidate_training_gate(self.local_db)
        self.learning_status.setText(
            f"{gate['status']} • {gate['distinct_participants']} participant(s) • {gate['label_rows']} label row(s)"
        )
        self.learning_details.setText(
            gate['note'] + "\n\nNo disease-model weights are changed by this gate."
        )

    def _build_care_tab(self):
        tab = QWidget()
        root = QVBoxLayout(tab)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(14)
        title = QLabel("Care discovery & supplies")
        title.setObjectName("HeroTitle")
        root.addWidget(title)
        sub = QLabel("Accessibility/discovery layer separated from the private patient record. Demo providers remain explicitly marked demo.")
        sub.setWordWrap(True)
        sub.setObjectName("HeroSubtitle")
        root.addWidget(sub)

        providers = self.local_db.list_providers()
        group = QGroupBox("Providers")
        layout = QVBoxLayout(group)
        table = QTableWidget(0, 5)
        table.setHorizontalHeaderLabels(["Name", "Type", "Specialty", "Distance", "Verification"])
        table.horizontalHeader().setStretchLastSection(True)
        for p in providers:
            row = table.rowCount()
            table.insertRow(row)
            vals = [p.get("name"), p.get("type"), p.get("specialty"), p.get("distance_km"), p.get("verification_status")]
            for col, value in enumerate(vals):
                table.setItem(row, col, QTableWidgetItem(str(value if value is not None else "—")))
        layout.addWidget(table)
        root.addWidget(group, 1)

        supplies = self.local_db.list_supplies()
        supply_group = QGroupBox("Monitoring supplies")
        sl = QVBoxLayout(supply_group)
        supply_table = QTableWidget(0, 3)
        supply_table.setHorizontalHeaderLabels(["Item", "Category", "Availability"])
        for item in supplies:
            row = supply_table.rowCount()
            supply_table.insertRow(row)
            for col, value in enumerate([item.get("name"), item.get("category"), item.get("availability")]):
                supply_table.setItem(row, col, QTableWidgetItem(str(value if value is not None else "—")))
        sl.addWidget(supply_table)
        root.addWidget(supply_group, 1)
        return tab

    def _build_database_tab(self):
        tab = QWidget()
        root = QVBoxLayout(tab)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(14)
        title = QLabel("Local database")
        title.setObjectName("HeroTitle")
        root.addWidget(title)
        info = QFrame()
        info.setObjectName("ScientificCard")
        il = QVBoxLayout(info)
        patient_count = len(self.local_db.list_patients(include_archived=True))
        il.addWidget(QLabel(f"Database: {self.local_db.db_path}"))
        il.addWidget(QLabel(f"Patients: {patient_count}"))
        il.addWidget(QLabel("Canonical storage: patients → studies → wear sessions → raw channels → feature vectors → baselines → learning runs → reports"))
        il.addWidget(QLabel("Mobile sync: patient-scoped export/import package; DEMO_DATA and REAL labels are preserved."))
        root.addWidget(info)
        return tab

    def _build_audit_tab(self):
        tab = QWidget()
        root = QVBoxLayout(tab)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(14)
        title = QLabel("Audit & provenance")
        title.setObjectName("HeroTitle")
        root.addWidget(title)
        text = QTextEdit()
        text.setReadOnly(True)
        rows = []
        if self.active_patient_id:
            rows = self.local_db.conn.execute(
                "SELECT timestamp, action, details_json FROM audit_records WHERE patient_id=? ORDER BY timestamp DESC LIMIT 200",
                (self.active_patient_id,),
            ).fetchall()
        if rows:
            lines = []
            for row in rows:
                lines.append(
                    f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(row['timestamp']))}  •  {row['action']}  •  {row['details_json'] or ''}"
                )
            text.setText("\n".join(lines))
        else:
            text.setText(
                "Select/open a patient to inspect patient-scoped audit entries.\n\n"
                "Provenance layers: MEASURED • DERIVED • CLINICALLY_ENTERED • IMAGE-DERIVED • MODEL-INFERRED • DEMO_DATA • UNKNOWN"
            )
        root.addWidget(text, 1)
        return tab

    def _build_overview_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(2, 2, 2, 2)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        root = QVBoxLayout(content)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(15)

        hero = QFrame()
        hero.setObjectName("PremiumCard")
        hero_layout = QHBoxLayout(hero)
        hero_layout.setContentsMargins(16, 14, 16, 14)

        hero_copy = QVBoxLayout()
        eyebrow = QLabel("ENDO-TWIN / OVERVIEW")
        eyebrow.setObjectName("SectionEyebrow")
        hero_copy.addWidget(eyebrow)
        hero_title = QLabel("Physiological command center")
        hero_title.setObjectName("HeroTitle")
        hero_copy.addWidget(hero_title)
        hero_sub = QLabel(
            "Observe signals → establish a personal baseline → evaluate persistent change → "
            "apply research modules with provenance and uncertainty."
        )
        hero_sub.setObjectName("HeroSubtitle")
        hero_sub.setWordWrap(True)
        hero_copy.addWidget(hero_sub)
        hero_layout.addLayout(hero_copy, 1)

        scope = QLabel("ENDO-TWIN core\n↳ CHRONO-PCOS\n↳ VoxVasc (experimental)")
        scope.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        scope.setStyleSheet("font-weight: 750; color: #B38CFF;")
        hero_layout.addWidget(scope)
        root.addWidget(hero)

        top = QHBoxLayout()
        top.setSpacing(14)

        gauge_card = QFrame()
        gauge_card.setObjectName("ScientificCard")
        gauge_layout = QVBoxLayout(gauge_card)
        gauge_layout.addWidget(QLabel("RESEARCH INDEX"))
        self.risk_gauge = GaugeWidget("Overall data quality", higher_is_better=True)
        gauge_layout.addWidget(self.risk_gauge, 1)
        top.addWidget(gauge_card, 2)

        status_box = QGroupBox("Live system state")
        status_layout = QVBoxLayout(status_box)
        self.confidence_label = QLabel("Model confidence: —")
        self.quality_label = QLabel("Data quality: —")
        self.coverage_label = QLabel("Fusion coverage: —")
        self.baseline_label = QLabel("Personal baseline: not established")
        self.mode_label = QLabel("NO STREAM")
        self.mode_label.setObjectName("Warn")
        for label in (
            self.confidence_label,
            self.quality_label,
            self.coverage_label,
            self.baseline_label,
            self.mode_label,
        ):
            label.setObjectName("BigValue")
            status_layout.addWidget(label)

        note = QLabel(
            "Numbers appear only after acquisition / validated computation. "
            "Unavailable inputs stay unavailable."
        )
        note.setWordWrap(True)
        note.setObjectName("SmallMuted")
        status_layout.addWidget(note)
        top.addWidget(status_box, 3)
        root.addLayout(top)

        key_box = QGroupBox("Live physiology")
        key_layout = QGridLayout(key_box)
        key_layout.setHorizontalSpacing(12)
        key_layout.setVerticalSpacing(12)
        self.cards = {}

        vital_specs = [
            ("hr", "Heart rate", "bpm"),
            ("hrv", "HRV · RMSSD", "ms"),
            ("temp", "Skin temperature", "°C"),
            ("activity", "Activity index", "%"),
            ("gsr", "GSR", "raw"),
            ("stress", "Stress index", ""),
            ("sleep", "Sleep probability", ""),
            ("quality", "Signal quality", "%"),
            ("recovery", "Recovery score", ""),
        ]
        for i, (key, title, unit) in enumerate(vital_specs):
            card = VitalCard(title, unit)
            card.setMinimumHeight(92)
            self.cards[key] = card
            key_layout.addWidget(card, i // 3, i % 3)

        root.addWidget(key_box)

        rep_box = QGroupBox("Shared physiological representation")
        rep_layout = QVBoxLayout(rep_box)
        rep_head = QHBoxLayout()
        rep_label = QLabel("CORE ENGINE")
        rep_label.setObjectName("SectionEyebrow")
        rep_head.addWidget(rep_label)
        rep_head.addStretch()
        provenance = QLabel("MEASURED → DERIVED → BASELINE → LONGITUDINAL → FUSION")
        provenance.setObjectName("SmallMuted")
        rep_head.addWidget(provenance)
        rep_layout.addLayout(rep_head)

        self.shared_text = QTextEdit()
        self.shared_text.setReadOnly(True)
        self.shared_text.setMinimumHeight(155)
        self.shared_text.setPlaceholderText(
            "No shared feature vector yet. Start a real wearable stream or run a clearly labelled synthetic scenario."
        )
        rep_layout.addWidget(self.shared_text)
        root.addWidget(rep_box)

        signal_box = QGroupBox("Research modules")
        signal_layout = QGridLayout(signal_box)
        signal_layout.setHorizontalSpacing(12)
        signal_layout.setVerticalSpacing(12)
        self.signal_labels = {}
        for i, mod in enumerate(["pcos", "sleep", "cardiometabolic", "autonomic"]):
            card = QFrame()
            card.setObjectName("MetricCard")
            ml = QVBoxLayout(card)
            title = QLabel(mod.replace("_", " ").title())
            title.setObjectName("MetricLabel")
            value = QLabel("Awaiting data")
            value.setObjectName("MetricValue")
            value.setWordWrap(True)
            detail = QLabel("Model state: unavailable until required inputs pass quality gates.")
            detail.setObjectName("MetricDetail")
            detail.setWordWrap(True)
            ml.addWidget(title)
            ml.addWidget(value)
            ml.addWidget(detail)
            self.signal_labels[mod] = value
            signal_layout.addWidget(card, 0, i)

        root.addWidget(signal_box)

        safety = QFrame()
        safety.setObjectName("WarningCard")
        safety_layout = QVBoxLayout(safety)
        safety_layout.addWidget(QLabel(
            "RESEARCH BOUNDARY  •  Observed, derived, image-derived, model-inferred, clinically-entered "
            "and demo data stay explicitly separated. Missing or low-quality data never becomes a fabricated result."
        ))
        root.addWidget(safety)
        root.addStretch(1)

        scroll.setWidget(content)
        layout.addWidget(scroll)
        return tab

    def _build_baseline_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        root = QVBoxLayout(content)

        info = QLabel(
            "Personal Baseline Engine V8.3\n"
            "Learns what is normal for THIS person: mean, median, std, robust MAD, rolling baseline, confidence, "
            "minimum observations, seasonal/circadian context.\n"
            "CURRENT vs PERSONAL BASELINE -> normalized deviation (z-score, % change)"
        )
        info.setWordWrap(True)
        root.addWidget(info)

        self.baseline_status = QLabel("No baseline yet. Collect at least 5 min calm data, then capture.")
        self.baseline_status.setWordWrap(True)
        root.addWidget(self.baseline_status)

        btn_row = QHBoxLayout()
        capture_btn = QPushButton("Capture Baseline (5 min)")
        capture_btn.clicked.connect(self._capture_baseline)
        btn_row.addWidget(capture_btn)
        root.addLayout(btn_row)

        self.baseline_details = QTextEdit()
        self.baseline_details.setReadOnly(True)
        self.baseline_details.setPlaceholderText("Baseline details appear here...")
        root.addWidget(self.baseline_details)

        self.baseline_comparison = QTextEdit()
        self.baseline_comparison.setReadOnly(True)
        self.baseline_comparison.setPlaceholderText("Current vs baseline comparison...")
        root.addWidget(self.baseline_comparison)

        scroll.setWidget(content)
        layout.addWidget(scroll)
        return tab

    def _build_trends_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        info = QLabel(
            "Longitudinal Engine - Heart of V8.3\n"
            "Rolling windows, persistence detection, trend detection, change-point detection, recovery detection, "
            "missing-data handling, confidence scoring.\n"
            "ONE ABNORMAL -> weak signal, REPEATED CHANGE -> stronger, MULTIPLE FEATURES -> multimodal, "
            "PERSISTENT + GOOD QUALITY -> higher confidence"
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        self.trend_plot = TimeSeriesPlot("HR Trend", "bpm", "#f87171")
        layout.addWidget(self.trend_plot)

        self.trend_plot2 = TimeSeriesPlot("HRV Trend", "ms", "#60a5fa")
        layout.addWidget(self.trend_plot2)

        self.longitudinal_text = QTextEdit()
        self.longitudinal_text.setReadOnly(True)
        self.longitudinal_text.setPlaceholderText("Longitudinal analysis appears here...")
        layout.addWidget(self.longitudinal_text)

        return tab

    def _build_health_signals_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        tabs = QTabWidget()

        # PCOS
        pcos_tab = QWidget()
        pcos_layout = QVBoxLayout(pcos_tab)
        pcos_info = QLabel("MODULE A - PCOS / Reproductive-Metabolic Risk\nPCOS-associated physiological and clinical risk signals (not 'wearable detects PCOS')\nDistinguishes: clinical variables, wearable physiology, ultrasound, combined/fused")
        pcos_info.setWordWrap(True)
        pcos_layout.addWidget(pcos_info)
        self.pcos_text = QTextEdit()
        self.pcos_text.setReadOnly(True)
        pcos_layout.addWidget(self.pcos_text)
        tabs.addTab(pcos_tab, "PCOS / Reproductive-Metabolic")

        # Sleep
        sleep_tab = QWidget()
        sleep_layout = QVBoxLayout(sleep_tab)
        sleep_info = QLabel("MODULE B - Sleep / Circadian Health\nUses activity, HR, HRV, temp, sleep duration/timing/regularity, day/night pattern\nOutputs: sleep regularity signal, circadian disruption signal, recovery signal, persistent deviation\nLanguage: 'sleep-related risk signal' or 'circadian disruption pattern' (not diagnosis)")
        sleep_info.setWordWrap(True)
        sleep_layout.addWidget(sleep_info)
        self.sleep_text = QTextEdit()
        self.sleep_text.setReadOnly(True)
        sleep_layout.addWidget(self.sleep_text)
        tabs.addTab(sleep_tab, "Sleep / Circadian")

        # Cardiometabolic
        cardio_tab = QWidget()
        cardio_layout = QVBoxLayout(cardio_tab)
        cardio_info = QLabel("MODULE C - Cardiometabolic Risk (research-oriented)\nFeatures: resting HR, HRV, activity, BMI, age, BP if entered, glucose if entered, sleep, temp, longitudinal\nOutputs: cardiometabolic risk signal, reduced activity trend, elevated RHR trend, metabolic flag\nNever claims diabetes/hypertension/CVD diagnosis")
        cardio_info.setWordWrap(True)
        cardio_layout.addWidget(cardio_info)
        self.cardio_text = QTextEdit()
        self.cardio_text.setReadOnly(True)
        cardio_layout.addWidget(self.cardio_text)
        tabs.addTab(cardio_tab, "Cardiometabolic")

        # Autonomic
        auto_tab = QWidget()
        auto_layout = QVBoxLayout(auto_tab)
        auto_info = QLabel("MODULE D - Autonomic / Stress Regulation\nUses HRV, resting HR, GSR, activity, sleep, temp\nExplainable estimator separating ACUTE SIGNAL from PERSISTENT LONGITUDINAL CHANGE\nNot a mental-health diagnosis")
        auto_info.setWordWrap(True)
        auto_layout.addWidget(auto_info)
        self.autonomic_text = QTextEdit()
        self.autonomic_text.setReadOnly(True)
        auto_layout.addWidget(self.autonomic_text)
        tabs.addTab(auto_tab, "Autonomic / Stress")

        # Future
        future_tab = QWidget()
        future_layout = QVBoxLayout(future_tab)
        future_info = QLabel("Future Modules - Not Implemented\nThese modules require appropriate dataset, validated features, scientifically defensible labels.\nMarked as 'Future research module - not implemented' and not generating fake data.")
        future_info.setWordWrap(True)
        future_layout.addWidget(future_info)
        self.future_text = QTextEdit()
        self.future_text.setReadOnly(True)
        self.future_text.setText("\n".join([f"- {m}: Future research module - not implemented" for m in GLOBAL_REGISTRY.list_future()]))
        future_layout.addWidget(self.future_text)
        tabs.addTab(future_tab, "Future Modules")

        layout.addWidget(tabs)
        return tab

    def _build_data_quality_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        info = QLabel("Sensor Quality - Every reading has quality metadata: value, quality 0..1, source, timestamp, artifact\nDetects: missing data, impossible values, flatline, excessive noise, motion artifacts, packet corruption, stale data\nBad data must not silently become model input.")
        info.setWordWrap(True)
        layout.addWidget(info)

        self.quality_text = QTextEdit()
        self.quality_text.setReadOnly(True)
        layout.addWidget(self.quality_text)

        self.quality_gauge = GaugeWidget("Overall Data Quality")
        layout.addWidget(self.quality_gauge)

        return tab

    def _build_clinical_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        root = QVBoxLayout(content)

        info = QLabel("Clinical Inputs - Manual measurements (USER-ENTERED)\nBMI, BP, glucose, cycle info, age, etc.\nClearly labelled as USER-ENTERED, not MEASURED")
        info.setWordWrap(True)
        root.addWidget(info)

        grid = QGridLayout()
        self.age_spin = QDoubleSpinBox()
        self.age_spin.setRange(10, 80)
        self.age_spin.setValue(22)
        self.bmi_spin = QDoubleSpinBox()
        self.bmi_spin.setRange(10, 60)
        self.bmi_spin.setValue(23.5)
        self.bmi_spin.setDecimals(1)
        self.sys_spin = QDoubleSpinBox()
        self.sys_spin.setRange(0, 250)
        self.sys_spin.setValue(0)
        self.sys_spin.setSpecialValueText("none")
        self.dia_spin = QDoubleSpinBox()
        self.dia_spin.setRange(0, 150)
        self.dia_spin.setValue(0)
        self.dia_spin.setSpecialValueText("none")
        self.glucose_spin = QDoubleSpinBox()
        self.glucose_spin.setRange(0, 500)
        self.glucose_spin.setValue(0)
        self.glucose_spin.setSpecialValueText("none")
        self.cycle_spin = QSpinBox()
        self.cycle_spin.setRange(0, 120)
        self.cycle_spin.setValue(0)
        self.cycle_spin.setSpecialValueText("unknown")
        self.length_spin = QSpinBox()
        self.length_spin.setRange(0, 120)
        self.length_spin.setValue(28)
        self.cycle_irregular_combo = QComboBox()
        self.cycle_irregular_combo.addItems(["unknown", "regular", "irregular"])

        grid.addWidget(QLabel("Age"), 0, 0)
        grid.addWidget(self.age_spin, 0, 1)
        grid.addWidget(QLabel("BMI"), 0, 2)
        grid.addWidget(self.bmi_spin, 0, 3)
        grid.addWidget(QLabel("Systolic BP"), 1, 0)
        grid.addWidget(self.sys_spin, 1, 1)
        grid.addWidget(QLabel("Diastolic BP"), 1, 2)
        grid.addWidget(self.dia_spin, 1, 3)
        grid.addWidget(QLabel("Glucose mg/dL"), 2, 0)
        grid.addWidget(self.glucose_spin, 2, 1)
        grid.addWidget(QLabel("Cycle day"), 2, 2)
        grid.addWidget(self.cycle_spin, 2, 3)
        grid.addWidget(QLabel("Usual length"), 3, 0)
        grid.addWidget(self.length_spin, 3, 1)
        grid.addWidget(QLabel("Irregular"), 3, 2)
        grid.addWidget(self.cycle_irregular_combo, 3, 3)

        for w in [self.age_spin, self.bmi_spin, self.sys_spin, self.dia_spin, self.glucose_spin, self.cycle_spin, self.length_spin]:
            w.valueChanged.connect(self._clinical_changed)
        self.cycle_irregular_combo.currentTextChanged.connect(self._clinical_changed)

        root.addLayout(grid)

        self.clinical_text = QTextEdit()
        self.clinical_text.setReadOnly(True)
        root.addWidget(self.clinical_text)

        scroll.setWidget(content)
        layout.addWidget(scroll)
        return tab

    def _build_ultrasound_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        info = QLabel("Ultrasound - Periodic clinical imaging\nProvenance preserved: source image -> preprocessing -> detected features -> quality -> uncertainty\nIf feature cannot be reliably extracted: return UNKNOWN, never invent.\nFeatures labelled as CLINICALLY-ENTERED or IMAGE-DERIVED")
        info.setWordWrap(True)
        layout.addWidget(info)

        self.ultrasound_text = QTextEdit()
        self.ultrasound_text.setReadOnly(True)
        self.ultrasound_text.setPlaceholderText("Ultrasound features appear here...")
        layout.addWidget(self.ultrasound_text)

        btn_row = QHBoxLayout()
        self.cyst_size_spin = QDoubleSpinBox()
        self.cyst_size_spin.setRange(0, 100)
        self.cyst_size_spin.setValue(0)
        self.cyst_size_spin.setSpecialValueText("none")
        self.cyst_size_spin.setSuffix(" mm")
        btn_row.addWidget(QLabel("Cyst size"))
        btn_row.addWidget(self.cyst_size_spin)
        add_btn = QPushButton("Add Ultrasound (Clinically Entered)")
        add_btn.clicked.connect(self._add_ultrasound)
        btn_row.addWidget(add_btn)
        layout.addLayout(btn_row)

        return tab

    def _build_explanation_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        info = QLabel("Explainability - Every risk signal explains main contributing factors\nDrivers: e.g. resting HR increased from baseline, HRV decreased, sleep regularity decreased, activity decreased\nThen: 'These changes are not specific to one disease and should not be interpreted as a diagnosis.'")
        info.setWordWrap(True)
        layout.addWidget(info)

        self.explanation_text = QTextEdit()
        self.explanation_text.setReadOnly(True)
        layout.addWidget(self.explanation_text)

        return tab

    def _build_report_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        info = QLabel("Report Generation - Research report with limitations and recommendation: 'Discuss relevant findings with qualified healthcare professional.'\nIncludes: subject ID, observation period, sensor data, data quality, personal baseline, longitudinal changes, disease signals, contributing factors, ultrasound if available, clinical inputs, limitations")
        info.setWordWrap(True)
        layout.addWidget(info)

        self.report_text = QTextEdit()
        self.report_text.setReadOnly(True)
        layout.addWidget(self.report_text)

        btn_row = QHBoxLayout()
        gen_btn = QPushButton("Generate Report")
        gen_btn.clicked.connect(self._generate_report)
        btn_row.addWidget(gen_btn)
        save_btn = QPushButton("Save Report")
        save_btn.clicked.connect(self._save_report)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

        return tab

    def _build_validation_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        info = QLabel("Validation - Engineering vs Clinical\nTests: baseline accuracy, trend detection, persistence, recovery, missing sensor handling, noisy data, multimodal fusion, disease module isolation, subject-level validation, reproducibility")
        info.setWordWrap(True)
        layout.addWidget(info)

        self.validation_text = QTextEdit()
        self.validation_text.setReadOnly(True)
        self.validation_text.setText(
            "CHRONO-TWIN NEXUS V8.3 Validation Status\n"
            "========================================\n\n"
            "Engineering Validation:\n"
            "- Personal baseline: mean, median, std, MAD, rolling, confidence, min obs, circadian context - IMPLEMENTED\n"
            "- Longitudinal engine: rolling windows, persistence, trend, change-point, recovery, missing handling, confidence - IMPLEMENTED\n"
            "- Shared representation: heart_rate, resting_hr, hrv, activity, sleep, temp, gsr, circadian, recovery, baseline_dev, trends, quality - IMPLEMENTED\n"
            "- Disease modules: PCOS, Sleep, Cardiometabolic, Autonomic with consistent API - IMPLEMENTED\n"
            "- Sensor quality: missing, impossible, flatline, noise, motion, corruption, stale - IMPLEMENTED\n"
            "- Hardware failure tests: disconnected MAX30102, temp, corrupted packet, duplicate, delayed, missing, noisy PPG, motion, reconnection - IMPLEMENTED\n"
            "- Synthetic longitudinal data with 6 scenarios - IMPLEMENTED\n"
            "- Multimodal fusion with provenance - IMPLEMENTED\n"
            "- Explainability - IMPLEMENTED\n"
            "- Subject-level validation (no leakage) - IMPLEMENTED\n"
            "- Data honesty: REAL, SYNTHETIC, PUBLIC, USER-ENTERED labelled - IMPLEMENTED\n\n"
            "Clinical Validation: NOT ESTABLISHED\n"
            "- All modules are research-only signals\n"
            "- No diagnostic claims\n"
            "- Requires ethics-approved prospective study\n"
            "- Model confidence vs data quality vs clinical validation separated\n\n"
            "Hardware:\n"
            "- Wearable Nano Pod: MAX30102 + MPU6050 + DS18B20 + optional GSR - PRESERVED from V8.1\n"
            "- Mega Hub: expanded experimental sensors - PRESERVED\n"
            "- Software gracefully handles missing sensors - IMPLEMENTED\n"
        )
        layout.addWidget(self.validation_text)

        return tab

    # ------------------------------------------------- logic
    def _refresh_ports(self):
        # Simple refresh - in real app would scan serial ports
        self.port_combo.addItem("/dev/ttyACM0")

    def connect_serial(self, port=None):
        p = port or self.port_combo.currentText()
        try:
            self.arduino_reader = ArduinoReader(port=p, baud=115200)
            self.arduino_reader.start()
            self.mode_label.setText(f"LIVE • wearable serial {p} • patient session required for storage")
            self.mode_label.setStyleSheet("font-weight: bold; color: #4ade80;")
        except Exception as e:
            self.mode_label.setText(f"Mode: SERIAL FAILED {e}")
            self.mode_label.setStyleSheet("font-weight: bold; color: #f87171;")

    def connect_network(self, hostport: str):
        if not hostport:
            return
        try:
            parts = hostport.split(":")
            host = parts[0]
            port = int(parts[1]) if len(parts) > 1 else 7777
            self.network_reader = NetworkReader(host=host, port=port)
            self.network_reader.start()
            self.mode_label.setText(f"LIVE • network bridge {hostport} • patient session required for storage")
            self.mode_label.setStyleSheet("font-weight: bold; color: #4ade80;")
        except Exception as e:
            self.mode_label.setText(f"Mode: NETWORK FAILED {e}")

    def start_demo(self):
        self.demo_stream = DemoSensorStream()
        self.demo_stream.start()
        self.mode_label.setText("DEMO • synthetic display stream • never stored as REAL")
        self.mode_label.setStyleSheet("font-weight: bold; color: #fbbf24;")

    def stop_stream(self):
        if self.arduino_reader:
            self.arduino_reader.stop()
            self.arduino_reader = None
        if self.network_reader:
            self.network_reader.stop()
            self.network_reader = None
        if self.demo_stream:
            self.demo_stream.stop()
            self.demo_stream = None
        self.mode_label.setText("Mode: NO STREAM")
        self.mode_label.setStyleSheet("font-weight: bold; color: #f87171;")

    def _load_scenario_dialog(self):
        # Load one of the 6 scenarios as demo
        from PySide6.QtWidgets import QInputDialog
        scenarios = ["scenario_1_stable", "scenario_2_gradual", "scenario_3_persistent",
                     "scenario_4_temporary", "scenario_5_sensor_failure", "scenario_6_recovery"]
        item, ok = QInputDialog.getItem(self, "Load Scenario", "Scenario:", scenarios, 0, False)
        if ok and item:
            self._load_scenario(item)

    def _load_scenario(self, name: str):
        path = DATA_DIR / "synthetic" / "scenarios" / f"{name}.json"
        if not path.exists():
            self.mode_label.setText(f"Scenario not found: {name}")
            return
        try:
            data = json.loads(path.read_text())
            # Convert to FeatureVectors
            from src.data_models import FeatureVector
            vectors = []
            for row in data["data"][:200]:  # load first 200 for demo
                fv = FeatureVector(
                    timestamp_s=row["timestamp_s"],
                    hr_bpm=row.get("hr_bpm"),
                    rmssd_ms=row.get("rmssd_ms"),
                    skin_temp_c=row.get("skin_temp_c"),
                    activity_level=row.get("activity_level", 0),
                    sleep_regularity=row.get("sleep_regularity", 0),
                    circadian_stability_index=row.get("circadian_stability_index", 50),
                    stress_index=row.get("stress_index", 30),
                    signal_quality=row.get("signal_quality", 0.8),
                )
                vectors.append(fv)
            self.feature_history = vectors
            self.mode_label.setText(f"Mode: SCENARIO {name} - {data['expected_result']}")
            self.mode_label.setStyleSheet("font-weight: bold; color: #60a5fa;")
            self._update_risk()
        except Exception as e:
            self.mode_label.setText(f"Failed to load scenario: {e}")

    def _update_features(self):
        sample = None
        if self.arduino_reader and self.arduino_reader.has_sample():
            sample = self.arduino_reader.get_sample()
        elif self.network_reader and self.network_reader.has_sample():
            sample = self.network_reader.get_sample()
        elif self.demo_stream and self.demo_stream.has_sample():
            sample = self.demo_stream.get_sample()

        if sample:
            # Convert to SensorSample if needed
            if isinstance(sample, dict):
                # demo stream dict
                from src.data_models import SensorSample
                import time
                s = SensorSample(
                    timestamp_s=time.time(),
                    ms=int(sample.get("ms", 0)),
                    ir=int(sample.get("ir", 5000)),
                    red=int(sample.get("red", 5000)),
                    ax_g=float(sample.get("ax", 0)),
                    ay_g=float(sample.get("ay", 0)),
                    az_g=float(sample.get("az", 1)),
                    gx_dps=float(sample.get("gx", 0)),
                    gy_dps=float(sample.get("gy", 0)),
                    gz_dps=float(sample.get("gz", 0)),
                    temp_c=float(sample.get("temp_c", 32.5)),
                    gsr_raw=int(sample.get("gsr", 450)),
                    lux=float(sample.get("lux", 100)),
                    source="demo" if self.demo_stream else "serial"
                )
                sample = s

            self.extractor.add_sample(sample)
            fv = self.extractor.compute()
            self.feature_history.append(fv)
            if len(self.feature_history) > 5000:
                self.feature_history = self.feature_history[-5000:]

            # Persist only real transport data inside an explicitly active wear session.
            # DEMO streams remain presentation-only and cannot contaminate research records.
            if (
                self.active_patient_id
                and self.active_session_id
                and getattr(sample, "source", "serial") not in {"demo", "synthetic"}
            ):
                try:
                    self.local_db.save_sensor_sample(
                        self.active_patient_id,
                        self.active_session_id,
                        sample,
                        feature_vector=fv,
                        label="REAL",
                    )
                    self.local_db.set_wearable_state(
                        self.active_patient_id,
                        self.active_device_id or "WEARABLE-01",
                        "WORN",
                        "live sample received",
                    )
                except Exception as exc:
                    self.sync_status_label.setText(f"Local database write error: {exc}")

            # Update UI vitals
            self._update_vital_cards(fv)

            # Update shared
            try:
                shared = self.shared_extractor.extract(fv, self.feature_history[-50:])
                self.current_shared = shared
                self.shared_history.append(shared)
                if len(self.shared_history) > 500:
                    self.shared_history = self.shared_history[-500:]
                self.shared_text.setText(self.explanation_engine.explain_shared_features(shared))
            except Exception as e:
                pass

    def _update_vital_cards(self, fv: FeatureVector):
        def set_card(key, value, fmt="{:.0f}"):
            if key in self.cards:
                if value is None:
                    self.cards[key].set_value("—")
                else:
                    try:
                        self.cards[key].set_value(fmt.format(value))
                    except:
                        self.cards[key].set_value(str(value))

        set_card("hr", fv.hr_bpm)
        set_card("hrv", fv.rmssd_ms)
        set_card("temp", fv.skin_temp_c, "{:.1f}")
        set_card("activity", fv.activity_level)
        set_card("gsr", fv.gsr_tonic)
        set_card("stress", fv.stress_index)
        set_card("sleep", fv.sleep_probability)
        set_card("quality", fv.signal_quality * 100 if fv.signal_quality else 0)
        set_card("recovery", fv.shared_features.get("recovery_score", 50) if isinstance(fv.shared_features, dict) else 50)

    def _update_risk(self):
        if not self.feature_history:
            return
        if not self.current_shared:
            return

        # Longitudinal
        try:
            longitudinal_report = self.longitudinal_engine.evaluate(self.feature_history[-200:])
            self.longitudinal_text.setText(self.explanation_engine.explain_longitudinal(longitudinal_report))
        except Exception as e:
            longitudinal_report = None
            self.longitudinal_text.setText(f"Longitudinal error: {e}")

        # Clinical data
        clinical = self.clinical_data.copy()
        clinical["profile"] = self.profile

        # Disease modules
        module_results = {}
        for mod_name in GLOBAL_REGISTRY.list_implemented():
            try:
                mod_cls = GLOBAL_REGISTRY.get_module_class(mod_name)
                if not mod_cls:
                    continue
                mod = mod_cls(profile=self.profile)
                result = mod.predict(
                    shared=self.current_shared,
                    clinical=clinical,
                    ultrasound=self.ultrasound_data,
                    history=self.feature_history[-100:]
                )
                module_results[mod_name] = result
            except Exception as e:
                print(f"Module {mod_name} error: {e}")

        self.module_results = module_results

        # Update health signals tab
        for name, result in module_results.items():
            text_widget = None
            if name == "pcos":
                text_widget = self.pcos_text
            elif name == "sleep":
                text_widget = self.sleep_text
            elif name == "cardiometabolic":
                text_widget = self.cardio_text
            elif name == "autonomic":
                text_widget = self.autonomic_text

            if text_widget:
                text_widget.setText(self.explanation_engine.explain_module(result, self.current_shared))

            # Overview signal labels
            if name in self.signal_labels:
                self.signal_labels[name].setText(
                    f"{result.signal}\nLevel: {result.level}\nConf: {result.confidence:.2f}\nQuality: {result.data_quality:.2f}\n{result.explanation[:150]}..."
                )
                # Color by level
                if result.level == "high":
                    self.signal_labels[name].setStyleSheet("color: #f87171; font-weight: bold;")
                elif result.level == "elevated":
                    self.signal_labels[name].setStyleSheet("color: #fb923c;")
                elif result.level == "moderate":
                    self.signal_labels[name].setStyleSheet("color: #fbbf24;")
                else:
                    self.signal_labels[name].setStyleSheet("color: #4ade80;")

        # Fusion
        try:
            context = self.fusion_engine.build(
                profile=self.profile,
                shared=self.current_shared,
                longitudinal_report=longitudinal_report,
                bp={"systolic": self.profile.systolic_bp, "diastolic": self.profile.diastolic_bp} if self.profile.systolic_bp else None,
                glucose={"value": self.profile.glucose_mg_dl} if self.profile.glucose_mg_dl else None,
                ultrasound=self.ultrasound_data,
                wearable_quality=self.current_shared.overall_quality if self.current_shared else 0.0
            )
            fusion_result = self.fusion_engine.fuse(module_results, context)
            self.fusion_result = fusion_result

            # Update overview: the gauge represents measured/computed data quality,
            # not an invented composite disease-risk score.
            overall_quality = float(fusion_result.confidence_breakdown.get("data_quality", 0.0))
            self.risk_gauge.set_value(overall_quality * 100.0)
            self.confidence_label.setText(
                f"Model confidence: {fusion_result.confidence_breakdown.get('model_confidence', 0):.2f}"
            )
            self.quality_label.setText(f"Data quality: {overall_quality:.2f}")
            self.coverage_label.setText(f"Coverage: {fusion_result.confidence_breakdown.get('fusion_coverage', 0):.0%}")
            self.quality_gauge.set_value(fusion_result.confidence_breakdown.get('data_quality', 0) * 100)

            # Baseline status
            if self.baseline_engine.has_baseline:
                self.baseline_label.setText(f"Baseline: YES (conf {self.baseline_engine.baseline.confidence:.2f}, {self.baseline_engine.baseline.days_covered} days)")
                self.baseline_label.setStyleSheet("color: #4ade80;")
            else:
                self.baseline_label.setText("Baseline: NO - need 5 min calm data")
                self.baseline_label.setStyleSheet("color: #fbbf24;")

            # Data quality tab
            self.quality_text.setText(
                context.summary_text() + "\n\n" + self.explanation_engine.explain_fusion(fusion_result)
            )

            # Explanation tab
            self.explanation_text.setText(
                self.explanation_engine.generate_report_explanation(
                    self.current_shared, longitudinal_report, fusion_result
                )
            )

            # Baseline tab details
            self.baseline_details.setText(
                f"Baseline has data: {self.baseline_engine.has_baseline}\n"
                f"Confidence: {self.baseline_engine.baseline.confidence:.2f}\n"
                f"Quality: {self.baseline_engine.baseline.quality:.2f}\n"
                f"Days covered: {self.baseline_engine.baseline.days_covered}\n"
                f"Samples: {self.baseline_engine.baseline.samples}\n"
                f"Metrics: {list(self.baseline_engine.baseline.stats.keys())}\n\n"
                + "\n".join([f"{k}: median {v.median:.1f}, std {v.std:.1f}, conf {v.confidence:.2f}" for k, v in self.baseline_engine.baseline.stats.items()])
            )
            if self.baseline_engine.has_baseline and self.feature_history:
                comp = self.baseline_engine.compare_current_vs_baseline(self.feature_history[-1])
                self.baseline_comparison.setText(
                    "\n".join([f"{k}: current {v.get('current')} vs baseline {v.get('baseline_median')} -> {v.get('deviation_pct')}%, z={v.get('zscore')}, status {v.get('status')}" for k, v in comp.items()])
                )

        except Exception as e:
            print(f"Fusion error: {e}")
            import traceback
            traceback.print_exc()

    def _capture_baseline(self):
        success = self.extractor.capture_baseline()
        if success:
            self.baseline_status.setText(f"Baseline captured! Confidence {self.baseline_engine.baseline.confidence:.2f}, {self.baseline_engine.baseline.days_covered} days, {len(self.baseline_engine.baseline.stats)} metrics")
        else:
            self.baseline_status.setText(f"Baseline failed: {self.extractor.last_capture_error}")

    def _clinical_changed(self):
        # Update profile
        self.profile.age_years = float(self.age_spin.value())
        bmi = float(self.bmi_spin.value())
        self.profile.bmi = bmi if bmi > 0 else None
        sys_bp = float(self.sys_spin.value())
        self.profile.systolic_bp = sys_bp if sys_bp > 0 else None
        dia_bp = float(self.dia_spin.value())
        self.profile.diastolic_bp = dia_bp if dia_bp > 0 else None
        glucose = float(self.glucose_spin.value())
        self.profile.glucose_mg_dl = glucose if glucose > 0 else None
        cycle_day = int(self.cycle_spin.value())
        self.profile.cycle_day = cycle_day if cycle_day > 0 else None
        usual_length = int(self.length_spin.value())
        self.profile.usual_cycle_length_days = usual_length if usual_length > 0 else None
        irr_text = self.cycle_irregular_combo.currentText()
        if irr_text == "regular":
            self.profile.cycle_irregular = False
        elif irr_text == "irregular":
            self.profile.cycle_irregular = True
        else:
            self.profile.cycle_irregular = None

        self.clinical_data = {
            "age_years": self.profile.age_years,
            "bmi": self.profile.bmi,
            "systolic_bp": self.profile.systolic_bp,
            "diastolic_bp": self.profile.diastolic_bp,
            "glucose_mg_dl": self.profile.glucose_mg_dl,
            "cycle_day": self.profile.cycle_day,
            "usual_cycle_length_days": self.profile.usual_cycle_length_days,
            "cycle_irregular": self.profile.cycle_irregular,
            "profile": self.profile,
        }
        self.clinical_text.setText(json.dumps({k: v for k, v in self.clinical_data.items() if k != "profile"}, indent=2))
        self.extractor.set_profile(self.profile)

    def _add_ultrasound(self):
        size = float(self.cyst_size_spin.value())
        if size > 0:
            self.ultrasound_data = {
                "cyst_size_mm": size,
                "source": "CLINICALLY-ENTERED",
                "quality": 0.85,
                "timestamp_s": time.time(),
            }
            self.ultrasound_text.setText(
                f"Ultrasound (CLINICALLY-ENTERED)\n"
                f"Cyst size: {size} mm\n"
                f"Quality: 0.85\n"
                f"Provenance: CLINICALLY-ENTERED\n"
                f"Note: Image-derived features are UNKNOWN by design until validated labelled dataset exists. "
                f"This entry is clinically-entered structured feature.\n"
            )

    def _generate_report(self):
        if not self.fusion_result or not self.current_shared:
            self.report_text.setText("No data yet - collect some data first")
            return

        # Build report
        lines = [
            f"{'='*60}",
            f"CHRONO-TWIN NEXUS V8.3 RESEARCH REPORT",
            f"{'='*60}",
            f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Subject ID: Anonymous (no identifiers stored)",
            f"Observation period: {len(self.feature_history)} samples over {(self.feature_history[-1].timestamp_s - self.feature_history[0].timestamp_s)/3600:.1f}h" if len(self.feature_history) > 1 else "Observation period: insufficient",
            f"",
            f"DISCLAIMER: {DISCLAIMER}",
            f"This is a research estimate, NOT a diagnosis. Clinical evaluation required.",
            f"",
            f"--- Sensor Data Available ---",
            f"Wearable: {'Yes' if self.feature_history else 'No'} ({len(self.feature_history)} samples)",
            f"Data quality: {self.fusion_result.confidence_breakdown.get('data_quality', 0):.2f}",
            f"Coverage: {self.fusion_result.confidence_breakdown.get('fusion_coverage', 0):.0%}",
            f"Present groups: {', '.join(self.fusion_result.context.present_groups())}",
            f"Missing groups: {', '.join(self.fusion_result.context.missing_groups())}",
            f"",
            f"--- Personal Baseline ---",
            f"Has baseline: {self.baseline_engine.has_baseline}",
        ]
        if self.baseline_engine.has_baseline:
            lines.append(f"Baseline confidence: {self.baseline_engine.baseline.confidence:.2f}")
            lines.append(f"Days covered: {self.baseline_engine.baseline.days_covered}")
            lines.append(f"Quality: {self.baseline_engine.baseline.quality:.2f}")
            for k, v in self.baseline_engine.baseline.stats.items():
                lines.append(f"  {k}: median {v.median:.1f} (p05 {v.p05:.1f} - p95 {v.p95:.1f}), std {v.std:.1f}")

        lines.extend([
            f"",
            f"--- Longitudinal Changes ---",
            f"{self.longitudinal_text.toPlainText()[:1000]}",
            f"",
            f"--- Disease Module Signals ---",
        ])
        for name, result in self.module_results.items():
            lines.append(f"\n[{name.upper()}] {result.signal} ({result.level})")
            lines.append(f"  Confidence: {result.confidence:.2f}, Data quality: {result.data_quality:.2f}, Validation: {result.clinical_validation}")
            lines.append(f"  Explanation: {result.explanation}")
            lines.append(f"  Drivers: {', '.join([d.get('description', '') for d in result.drivers[:2]])}")
            lines.append(f"  Limitations: {result.limitations[:200]}...")

        lines.extend([
            f"",
            f"--- Ultrasound ---",
            f"{self.ultrasound_text.toPlainText() if self.ultrasound_data else 'No ultrasound data'}",
            f"",
            f"--- Clinical Inputs ---",
            f"{json.dumps({k:v for k,v in self.clinical_data.items() if k!='profile'}, indent=2)}",
            f"",
            f"--- Fusion Summary ---",
            f"{self.fusion_result.explanation}",
            f"",
            f"--- Recommendations ---",
        ])
        for rec in self.fusion_result.recommendations:
            lines.append(f"- {rec}")

        lines.extend([
            f"",
            f"--- Limitations ---",
            f"- All signals are research-only, not diagnostic",
            f"- Model confidence: {self.fusion_result.confidence_breakdown.get('model_confidence', 0):.2f}",
            f"- Data quality: {self.fusion_result.confidence_breakdown.get('data_quality', 0):.2f}",
            f"- Clinical validation: NOT ESTABLISHED",
            f"- Requires clinical evaluation for any health concern",
            f"- Wearable data alone cannot diagnose any condition",
            f"",
            f"Recommended next step: Discuss relevant findings with qualified healthcare professional if symptomatic.",
            f"",
            f"{'='*60}",
        ])

        report = "\n".join(lines)
        self.report_text.setText(report)

    def _save_report(self):
        from PySide6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getSaveFileName(self, "Save Report", str(DATA_DIR / "reports" / f"report_{int(time.time())}.txt"), "Text Files (*.txt)")
        if path:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            Path(path).write_text(self.report_text.toPlainText(), encoding="utf-8")
            self.status_label.setText(f"Report saved to {path}")
