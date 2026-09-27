"""Qt front-end for PCOD longitudinal progress and complication context.

This module intentionally contains presentation/orchestration only. It reuses:
- PersonalBaselineEngine for the stored patient baseline
- LongitudinalEngine for trend/recovery classifications
- PCOSComplicationContextEngine for complication-context rows

It does not introduce a new disease score or diagnostic rule.
"""
from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox, QFrame, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget,
)

from src.config import UserProfile
from src.core.longitudinal_engine import LongitudinalEngine
from src.data_models import FeatureVector
from src.disease_modules.pcos_complications import PCOSComplicationContextEngine
from src.personal_twin.baseline_store import baseline_engine
from desktop.workstation_theme import section_header, status_badge


METRICS = (
    ("hr_bpm", "Heart rate", "bpm"),
    ("rmssd_ms", "HRV / RMSSD", "ms"),
    ("skin_temp_c", "Skin temperature", "°C"),
    ("gsr_tonic", "GSR / EDA", "rel."),
    ("activity_level", "Activity", "index"),
    ("sleep_duration_h", "Sleep duration", "h"),
)


class PCODProgressPanel(QWidget):
    """Combined PCOD status, longitudinal progress and gated complications view."""

    pcod_status_changed = Signal(object)

    def __init__(self, title: str = "PCOD Healing & Complications", parent=None):
        super().__init__(parent)
        self.participant_id: str | None = None
        self.profile: dict[str, Any] = {}
        self.feature_history: list[FeatureVector] = []
        self.latest_feature: FeatureVector | None = None
        self._setting_status = False

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(10)

        root.addWidget(section_header(
            title,
            "Personal-baseline and longitudinal context. Existing model classifications are shown without creating a new diagnostic score.",
        ))

        state = QFrame()
        state.setObjectName("hero")
        sv = QHBoxLayout(state)
        sv.setContentsMargins(14, 12, 14, 12)
        left = QVBoxLayout()
        eyebrow = QLabel("PCOD / PCOS STATUS")
        eyebrow.setObjectName("eyebrow")
        left.addWidget(eyebrow)
        self.status_text = QLabel("Unknown")
        self.status_text.setStyleSheet("font-size:20px;font-weight:900;")
        left.addWidget(self.status_text)
        self.status_note = QLabel("Set this from the patient's own reported/known status. Complication context stays off until status is Yes.")
        self.status_note.setWordWrap(True)
        self.status_note.setObjectName("muted")
        left.addWidget(self.status_note)
        sv.addLayout(left, 1)

        self.status_combo = QComboBox()
        self.status_combo.addItems(["Unknown", "Yes — has PCOD/PCOS", "No — does not report PCOD/PCOS"])
        self.status_combo.currentTextChanged.connect(self._status_changed)
        self.status_combo.setMinimumWidth(280)
        sv.addWidget(self.status_combo, 0, Qt.AlignmentFlag.AlignVCenter)
        root.addWidget(state)

        self.overall_card = QFrame()
        self.overall_card.setObjectName("card")
        ov = QHBoxLayout(self.overall_card)
        ov.setContentsMargins(14, 11, 14, 11)
        self.overall_value = QLabel("Awaiting patient status")
        self.overall_value.setStyleSheet("font-size:22px;font-weight:900;")
        ov.addWidget(self.overall_value)
        self.overall_detail = QLabel()
        self.overall_detail.setWordWrap(True)
        self.overall_detail.setObjectName("muted")
        ov.addWidget(self.overall_detail, 1)
        root.addWidget(self.overall_card)

        root.addWidget(section_header(
            "PCOD Healing / Longitudinal Progress",
            "The table reuses the existing baseline + LongitudinalEngine recovery classifications.",
        ))
        self.progress_table = QTableWidget(0, 7)
        self.progress_table.setHorizontalHeaderLabels(
            ["Metric", "Baseline", "Current", "Change", "Trend", "Existing State", "Recovery"]
        )
        self.progress_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.progress_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.progress_table.setMinimumHeight(250)
        root.addWidget(self.progress_table, 1)

        root.addWidget(section_header(
            "PCOD Complication Context",
            "Existing PCOSComplicationContextEngine output. Displayed only when PCOD/PCOS is marked Yes.",
        ))
        self.complication_table = QTableWidget(0, 4)
        self.complication_table.setHorizontalHeaderLabels(["Domain", "Status", "Finding", "Data needed"])
        self.complication_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.complication_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        root.addWidget(self.complication_table, 1)

        self.footer = QLabel(
            "Research prototype. “Healing” here means longitudinal movement toward a personal baseline in the existing research logic; it is not proof that PCOD/PCOS has resolved. Complication rows are context prompts, not diagnoses."
        )
        self.footer.setWordWrap(True)
        self.footer.setObjectName("warning")
        root.addWidget(self.footer)

    @staticmethod
    def _status_value(profile: dict[str, Any]) -> str | None:
        value = profile.get("has_pcod", profile.get("has_pcos"))
        if value is True:
            return "yes"
        if value is False:
            return "no"
        return None

    @staticmethod
    def _to_feature(value: Any) -> FeatureVector | None:
        if isinstance(value, FeatureVector):
            return value
        if not isinstance(value, dict):
            return None

        def n(key: str, default=None):
            v = value.get(key, default)
            try:
                return float(v) if v is not None else default
            except (TypeError, ValueError):
                return default

        f = FeatureVector(
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
        return f

    def _status_changed(self, text: str):
        if self._setting_status:
            return
        key = "yes" if text.startswith("Yes") else "no" if text.startswith("No") else None
        self._apply_status(key)
        self.pcod_status_changed.emit(key)

    def _apply_status(self, key: str | None):
        self.status_text.setText(
            "YES — PCOD/PCOS reported" if key == "yes"
            else "NO — PCOD/PCOS not reported" if key == "no"
            else "UNKNOWN — not reported"
        )
        if key == "yes":
            self.status_note.setText("PCOD/PCOS is recorded for this patient. Existing longitudinal recovery context and complication-context rows are enabled.")
        elif key == "no":
            self.status_note.setText("PCOD/PCOS is not reported. PCOD complication context remains disabled.")
        else:
            self.status_note.setText("PCOD/PCOS status is unknown. Ask the patient before enabling the PCOD-specific complication view.")
        self._refresh_tables()

    def set_context(
        self,
        profile: dict[str, Any] | UserProfile | None,
        feature_history: list[Any] | None = None,
        latest: Any | None = None,
    ):
        if isinstance(profile, UserProfile):
            p = {k: getattr(profile, k) for k in vars(profile)}
        else:
            p = dict(profile or {})
        self.profile = p
        self.participant_id = str(p.get("participant_id") or p.get("anonymous_id") or "") or None
        self.feature_history = [
            f for f in (self._to_feature(x) for x in (feature_history or [])) if f is not None
        ]
        self.latest_feature = self._to_feature(latest)
        key = self._status_value(p)
        self._setting_status = True
        self.status_combo.setCurrentIndex(1 if key == "yes" else 2 if key == "no" else 0)
        self._setting_status = False
        self._apply_status(key)

    def set_history(self, feature_history: list[Any] | None, latest: Any | None = None):
        self.feature_history = [
            f for f in (self._to_feature(x) for x in (feature_history or [])) if f is not None
        ]
        self.latest_feature = self._to_feature(latest)
        self._refresh_tables()

    def _refresh_tables(self):
        self._render_progress()
        self._render_complications()

    def _render_progress(self):
        self.progress_table.setRowCount(0)
        key = self._status_value(self.profile)
        if key != "yes":
            msg = "Ask / confirm PCOD status first." if key is None else "PCOD marked No — healing assessment is not applicable."
            self.progress_table.insertRow(0)
            self.progress_table.setItem(0, 0, QTableWidgetItem("PCOD status"))
            self.progress_table.setItem(0, 1, QTableWidgetItem("—"))
            self.progress_table.setItem(0, 2, QTableWidgetItem("—"))
            self.progress_table.setItem(0, 3, QTableWidgetItem("—"))
            self.progress_table.setItem(0, 4, QTableWidgetItem("—"))
            self.progress_table.setItem(0, 5, QTableWidgetItem(msg))
            self.progress_table.setItem(0, 6, QTableWidgetItem("DISABLED"))
            self.overall_value.setText("PCOD progress not active")
            self.overall_detail.setText(msg)
            return

        if not self.participant_id:
            self.overall_value.setText("Patient record required")
            self.overall_detail.setText("Create/select the patient in Self-Learning so the baseline and longitudinal record have a stable participant ID.")
            return

        try:
            engine = LongitudinalEngine(baseline=baseline_engine(self.participant_id))
            report = engine.evaluate(self.feature_history)
        except Exception as exc:
            self.overall_value.setText("Unable to calculate longitudinal view")
            self.overall_detail.setText(str(exc))
            return

        if not self.feature_history or report.n_windows < engine.min_points:
            self.overall_value.setText("INSUFFICIENT LONGITUDINAL DATA")
            self.overall_detail.setText(
                f"Need at least {engine.min_points} quality-aware feature windows for the existing recovery/trend engine."
            )
            self.progress_table.insertRow(0)
            self.progress_table.setItem(0, 0, QTableWidgetItem("Longitudinal window"))
            self.progress_table.setItem(0, 5, QTableWidgetItem(f"{report.n_windows} windows available"))
            self.progress_table.setItem(0, 6, QTableWidgetItem("INSUFFICIENT"))
            return

        recovering = [m for m in report.per_metric.values() if m.is_recovering]
        if recovering or report.recovery_detected:
            self.overall_value.setText("IMPROVING TOWARD PERSONAL BASELINE")
            self.overall_detail.setText(
                f"Existing recovery classifications are present in {len(recovering)} metric(s)."
            )
        elif report.overall_kind == "normal":
            self.overall_value.setText("STABLE WITHIN PERSONAL BASELINE")
            self.overall_detail.setText("The existing longitudinal engine currently reports no persistent deviation.")
        elif report.overall_kind in {"deviation", "insufficient_quality"}:
            self.overall_value.setText("NO RECOVERY CONFIRMED YET")
            self.overall_detail.setText("The existing engine reports persistent/deviating or insufficient-quality observations.")
        else:
            self.overall_value.setText(report.overall_kind.upper())
            self.overall_detail.setText(report.summary)

        for name, label, unit in METRICS:
            item = report.per_metric.get(name)
            if item is None or item.n_points < engine.min_points:
                continue
            row = self.progress_table.rowCount()
            self.progress_table.insertRow(row)
            self.progress_table.setItem(row, 0, QTableWidgetItem(label))
            self.progress_table.setItem(row, 1, QTableWidgetItem(f"{item.baseline_median:.2f} {unit}"))
            self.progress_table.setItem(row, 2, QTableWidgetItem(f"{item.latest_value:.2f} {unit}"))
            self.progress_table.setItem(row, 3, QTableWidgetItem(f"{item.pct_change:+.1f}%"))
            self.progress_table.setItem(row, 4, QTableWidgetItem(item.trend_direction))
            self.progress_table.setItem(row, 5, QTableWidgetItem(item.kind))
            recovery = f"{item.recovery_progress*100:.0f}% recovered" if item.is_recovering else "—"
            self.progress_table.setItem(row, 6, QTableWidgetItem(recovery))
            if item.kind == "recovery":
                self.progress_table.item(row, 5).setText("recovery")

    def _render_complications(self):
        self.complication_table.setRowCount(0)
        key = self._status_value(self.profile)
        if key != "yes":
            msg = (
                "Disabled until patient reports PCOD/PCOS = Yes."
                if key is None else
                "PCOD/PCOS marked No — complication-context table is disabled."
            )
            self.complication_table.insertRow(0)
            self.complication_table.setItem(0, 0, QTableWidgetItem("PCOD gate"))
            self.complication_table.setItem(0, 1, QTableWidgetItem("OFF"))
            self.complication_table.setItem(0, 2, QTableWidgetItem(msg))
            self.complication_table.setItem(0, 3, QTableWidgetItem("Patient status confirmation"))
            return

        clinical = {
            k: self.profile.get(k) for k in (
                "age_years", "bmi", "systolic_bp", "diastolic_bp",
                "glucose_mg_dl", "cycle_irregular", "usual_cycle_length_days",
                "days_since_last_period", "years_post_menarche",
            )
        }
        try:
            rows = PCOSComplicationContextEngine().evaluate(
                clinical,
                self.latest_feature,
                self.feature_history,
            )
        except Exception as exc:
            self.complication_table.insertRow(0)
            self.complication_table.setItem(0, 0, QTableWidgetItem("Engine"))
            self.complication_table.setItem(0, 1, QTableWidgetItem("ERROR"))
            self.complication_table.setItem(0, 2, QTableWidgetItem(str(exc)))
            return

        for item in rows:
            row = self.complication_table.rowCount()
            self.complication_table.insertRow(row)
            self.complication_table.setItem(row, 0, QTableWidgetItem(str(item.get("domain", "—"))))
            self.complication_table.setItem(row, 1, QTableWidgetItem(str(item.get("status", "—"))))
            self.complication_table.setItem(row, 2, QTableWidgetItem(str(item.get("finding", "—"))))
            self.complication_table.setItem(row, 3, QTableWidgetItem(str(item.get("data_needed", "—"))))

        self.complication_table.resizeColumnsToContents()
        self.progress_table.resizeColumnsToContents()
