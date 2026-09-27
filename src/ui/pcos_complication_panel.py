"""Reusable PCOS complication-context panel for desktop surfaces."""
from __future__ import annotations

from PySide6.QtWidgets import QComboBox, QFrame, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, QPushButton
from PySide6.QtCore import Signal
from types import SimpleNamespace

from src.config import UserProfile
from src.core.longitudinal_engine import LongitudinalEngine
from src.data_models import FeatureVector
from src.personal_twin.baseline_store import baseline_engine
from desktop.workstation_theme import section_header

from src.disease_modules.pcos_complications import PCOSComplicationContextEngine


class PCOSComplicationPanel(QWidget):
    """Read-only context panel shared by unified/doctor/patient workstations."""

    def __init__(self, title="PCOS / Complications", parent=None):
        super().__init__(parent)
        self.engine = PCOSComplicationContextEngine()
        self._clinical = {}
        self._feature = None
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(10)

        header = QFrame()
        header.setObjectName("card")
        h = QHBoxLayout(header)
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size:18px;font-weight:900;")
        h.addWidget(title_label)
        h.addStretch()
        self.state = QLabel("No context loaded")
        self.state.setStyleSheet("font-weight:800;")
        h.addWidget(self.state)
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh)
        h.addWidget(self.refresh_btn)
        outer.addWidget(header)

        note = QLabel(
            "Context/surveillance view only. Wearable physiology is not a standalone "
            "diagnostic criterion; items requiring clinical, laboratory or validated "
            "assessment remain explicitly marked."
        )
        note.setWordWrap(True)
        note.setStyleSheet("padding:8px;")
        outer.addWidget(note)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Domain", "Status", "Current context", "Assessment / data needed"])
        self.table.setWordWrap(True)
        self.table.setAlternatingRowColors(True)
        outer.addWidget(self.table, 1)

    def set_context(self, clinical: dict | None = None, feature=None) -> None:
        self._clinical = dict(clinical or {})
        self._feature = feature
        self.refresh()

    def refresh(self) -> None:
        feature = self._feature
        if isinstance(feature, dict):
            feature = SimpleNamespace(**feature)
        rows = self.engine.evaluate(self._clinical, feature, [])
        self.table.setRowCount(len(rows))
        for r, item in enumerate(rows):
            for c, key in enumerate(("domain", "status", "finding", "data_needed")):
                self.table.setItem(r, c, QTableWidgetItem(str(item.get(key, "—"))))
        self.table.resizeColumnsToContents()
        has_feature = self._feature is not None
        self.state.setText("Live wearable context" if has_feature else "Clinical/profile context")



class PCODProgressPanel(QWidget):
    """Patient-facing PCOD progress and gated complication presentation.

    Presentation/orchestration only; reuses existing baseline, longitudinal and
    complication engines without creating a second disease model.
    """

    pcod_status_changed = Signal(object)

    def __init__(self, title="PCOD Healing & Complications", parent=None):
        super().__init__(parent)
        self.participant_id = None
        self.profile = {}
        self.feature_history = []
        self.latest_feature = None
        self._setting_status = False

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(10)
        root.addWidget(section_header(
            title,
            "Personal-baseline and longitudinal context from the existing research engines."
        ))

        state = QFrame()
        state.setObjectName("hero")
        sv = QHBoxLayout(state)
        left = QVBoxLayout()
        ey = QLabel("PCOD / PCOS STATUS")
        ey.setObjectName("eyebrow")
        left.addWidget(ey)
        self.status_text = QLabel("UNKNOWN — not reported")
        self.status_text.setStyleSheet("font-size:20px;font-weight:900;")
        left.addWidget(self.status_text)
        self.status_note = QLabel(
            "Status is patient-reported. PCOD-specific complication context stays off until Yes."
        )
        self.status_note.setWordWrap(True)
        self.status_note.setObjectName("muted")
        left.addWidget(self.status_note)
        sv.addLayout(left, 1)
        self.status_combo = QComboBox()
        self.status_combo.addItems([
            "Unknown",
            "Yes — has PCOD/PCOS",
            "No — does not report PCOD/PCOS",
        ])
        self.status_combo.currentTextChanged.connect(self._status_changed)
        sv.addWidget(self.status_combo)
        root.addWidget(state)

        overall = QFrame()
        overall.setObjectName("card")
        ov = QHBoxLayout(overall)
        self.overall_value = QLabel("PCOD progress not active")
        self.overall_value.setStyleSheet("font-size:21px;font-weight:900;")
        ov.addWidget(self.overall_value)
        self.overall_detail = QLabel()
        self.overall_detail.setWordWrap(True)
        self.overall_detail.setObjectName("muted")
        ov.addWidget(self.overall_detail, 1)
        root.addWidget(overall)

        root.addWidget(section_header(
            "PCOD Healing / Longitudinal Progress",
            "Uses the existing LongitudinalEngine recovery/trend classifications."
        ))
        self.progress_table = QTableWidget(0, 7)
        self.progress_table.setHorizontalHeaderLabels([
            "Metric", "Baseline", "Current", "Change", "Trend", "Existing State", "Recovery"
        ])
        self.progress_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.progress_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        root.addWidget(self.progress_table, 1)

        root.addWidget(section_header(
            "PCOD Complication Context",
            "Existing PCOSComplicationContextEngine output; evaluated only when PCOD = Yes."
        ))
        self.complication_table = QTableWidget(0, 4)
        self.complication_table.setHorizontalHeaderLabels([
            "Domain", "Status", "Finding", "Data needed"
        ])
        self.complication_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.complication_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        root.addWidget(self.complication_table, 1)

        footer = QLabel(
            "Research prototype. Longitudinal movement toward a personal baseline is not proof of PCOD/PCOS healing or resolution. Complication rows are context prompts, not diagnoses."
        )
        footer.setWordWrap(True)
        footer.setObjectName("warning")
        root.addWidget(footer)

    @staticmethod
    def _status_value(profile):
        value = profile.get("has_pcod", profile.get("has_pcos"))
        return "yes" if value is True else "no" if value is False else None

    @staticmethod
    def _to_feature(value):
        if isinstance(value, FeatureVector):
            return value
        if not isinstance(value, dict):
            return None
        def n(key, default=None):
            value = value.get(key, default)
            try:
                return float(value) if value is not None else default
            except (TypeError, ValueError):
                return default
        return FeatureVector(
            timestamp_s=n("timestamp", n("timestamp_s", 0.0)),
            hr_bpm=n("hr_bpm"),
            resting_hr_bpm=n("resting_hr_bpm"),
            rmssd_ms=n("rmssd_ms"),
            skin_temp_c=n("skin_temp_c"),
            gsr_tonic=n("gsr_tonic"),
            activity_level=n("activity_level", 0.0),
            sleep_duration_h=n("sleep_duration_h"),
            sleep_regularity=n("sleep_regularity", 0.0),
            circadian_stability_index=n("circadian_stability_index", 50.0),
            stress_index=n("stress_index", 0.0),
            signal_quality=n("signal_quality", 0.0),
        )

    def _status_changed(self, text):
        if self._setting_status:
            return
        key = "yes" if text.startswith("Yes") else "no" if text.startswith("No") else None
        self.profile["has_pcod"] = True if key == "yes" else False if key == "no" else None
        self._apply_status(key)
        self.pcod_status_changed.emit(key)

    def _apply_status(self, key):
        self.status_text.setText(
            "YES — PCOD/PCOS reported" if key == "yes"
            else "NO — PCOD/PCOS not reported" if key == "no"
            else "UNKNOWN — not reported"
        )
        self.status_note.setText(
            "PCOD/PCOS is recorded for this patient. Longitudinal recovery and complication context are enabled."
            if key == "yes"
            else "PCOD/PCOS is not reported. PCOD-specific complication context is disabled."
            if key == "no"
            else "Ask the patient and confirm status in Self-Learning Model before using PCOD-specific complication context."
        )
        self._render_progress()
        self._render_complications()

    def set_context(self, profile=None, feature_history=None, latest=None):
        if isinstance(profile, UserProfile):
            self.profile = {k: getattr(profile, k) for k in vars(profile)}
        else:
            self.profile = dict(profile or {})
        self.participant_id = str(
            self.profile.get("participant_id")
            or self.profile.get("anonymous_id")
            or ""
        ) or None
        self.feature_history = [
            f for f in (self._to_feature(x) for x in (feature_history or []))
            if f is not None
        ]
        self.latest_feature = self._to_feature(latest)
        key = self._status_value(self.profile)
        self._setting_status = True
        self.status_combo.setCurrentIndex(1 if key == "yes" else 2 if key == "no" else 0)
        self._setting_status = False
        self._apply_status(key)

    def _render_progress(self):
        self.progress_table.setRowCount(0)
        key = self._status_value(self.profile)
        if key != "yes":
            msg = (
                "Ask / confirm PCOD status first."
                if key is None else
                "PCOD marked No — healing assessment is not applicable."
            )
            self.progress_table.insertRow(0)
            self.progress_table.setItem(0, 0, QTableWidgetItem("PCOD status"))
            self.progress_table.setItem(0, 5, QTableWidgetItem(msg))
            self.progress_table.setItem(0, 6, QTableWidgetItem("DISABLED"))
            self.overall_value.setText("PCOD progress not active")
            self.overall_detail.setText(msg)
            return

        if not self.participant_id:
            self.overall_value.setText("Patient record required")
            self.overall_detail.setText("Create/select this patient in Self-Learning so a person-specific baseline exists.")
            return

        try:
            report = LongitudinalEngine(
                baseline=baseline_engine(self.participant_id)
            ).evaluate(self.feature_history)
        except Exception as exc:
            self.overall_value.setText("LONGITUDINAL VIEW UNAVAILABLE")
            self.overall_detail.setText(str(exc))
            return

        engine = LongitudinalEngine(baseline=baseline_engine(self.participant_id))
        if report.n_windows < engine.min_points:
            self.overall_value.setText("INSUFFICIENT LONGITUDINAL DATA")
            self.overall_detail.setText(
                f"{report.n_windows} windows available; existing engine requires at least {engine.min_points}."
            )
            return

        recovering = [m for m in report.per_metric.values() if m.is_recovering]
        if recovering or report.recovery_detected:
            self.overall_value.setText("IMPROVING TOWARD PERSONAL BASELINE")
            self.overall_detail.setText(
                f"Existing recovery classifications: {len(recovering)} metric(s)."
            )
        elif report.overall_kind == "normal":
            self.overall_value.setText("STABLE WITHIN PERSONAL BASELINE")
            self.overall_detail.setText("No persistent change detected by the existing longitudinal engine.")
        else:
            self.overall_value.setText("NO RECOVERY CONFIRMED YET")
            self.overall_detail.setText(report.summary)

        for metric, label, unit in (
            ("hr_bpm", "Heart rate", "bpm"),
            ("rmssd_ms", "HRV / RMSSD", "ms"),
            ("skin_temp_c", "Skin temperature", "°C"),
            ("gsr_tonic", "GSR / EDA", "rel."),
            ("activity_level", "Activity", "index"),
            ("sleep_duration_h", "Sleep duration", "h"),
        ):
            item = report.per_metric.get(metric)
            if item is None or item.n_points < engine.min_points:
                continue
            row = self.progress_table.rowCount()
            self.progress_table.insertRow(row)
            vals = [
                label,
                f"{item.baseline_median:.2f} {unit}",
                f"{item.latest_value:.2f} {unit}",
                f"{item.pct_change:+.1f}%",
                item.trend_direction,
                item.kind,
                f"{item.recovery_progress * 100:.0f}% recovered" if item.is_recovering else "—",
            ]
            for col, value in enumerate(vals):
                self.progress_table.setItem(row, col, QTableWidgetItem(str(value)))
        self.progress_table.resizeColumnsToContents()

    def _render_complications(self):
        self.complication_table.setRowCount(0)
        key = self._status_value(self.profile)
        if key != "yes":
            msg = (
                "Disabled until patient reports PCOD/PCOS = Yes."
                if key is None else
                "PCOD/PCOS marked No — complication context disabled."
            )
            self.complication_table.insertRow(0)
            for col, value in enumerate([
                "PCOD gate", "OFF", msg, "Patient status confirmation"
            ]):
                self.complication_table.setItem(0, col, QTableWidgetItem(value))
            return

        clinical = {
            k: self.profile.get(k) for k in (
                "age_years", "bmi", "systolic_bp", "diastolic_bp",
                "glucose_mg_dl", "cycle_irregular", "usual_cycle_length_days",
                "days_since_last_period", "years_post_menarche",
            )
        }
        rows = self.engine.evaluate(
            clinical,
            self.latest_feature,
            self.feature_history,
        )
        for item in rows:
            row = self.complication_table.rowCount()
            self.complication_table.insertRow(row)
            for col, key in enumerate(("domain", "status", "finding", "data_needed")):
                self.complication_table.setItem(row, col, QTableWidgetItem(str(item.get(key, "—"))))
        self.complication_table.resizeColumnsToContents()
