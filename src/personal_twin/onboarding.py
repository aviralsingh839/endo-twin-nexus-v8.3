"""Personal Twin people/profile manager and onboarding wizard."""
from __future__ import annotations

import math
import sys
import time
import uuid

from PySide6.QtWidgets import (
    QApplication, QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox,
    QFormLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QMessageBox, QPushButton, QScrollArea, QTabWidget, QVBoxLayout, QWidget,
)
from PySide6.QtCore import Qt

from src.personal_twin.profile_store import (
    append_event,
    get_learning,
    get_profile,
    list_profiles,
    load_state,
    remove_profile,
    save_profile,
    select_participant,
    profile_summary,
)
from src.personal_twin.adaptive_model import PersonalAdaptiveModel
from src.ui.pcos_complication_panel import PCOSComplicationPanel


MULTI_PERSON_DISCLAIMER = (
    "Multiple people are supported, but each participant has a separate local profile, "
    "learning history and event stream. Only enter or review another person's data with "
    "their permission and according to your project's authorized workflow. Do not mix "
    "participants or treat another person's Personal Twin as your own."
)


class PersonalTwinOnboarding(QDialog):
    def __init__(self, participant_id: str | None = None, parent=None):
        super().__init__(parent)
        self.participant_id = participant_id
        self.setWindowTitle("ENDO-TWIN • Personal Twin Profile")
        self.setModal(True)
        self.setMinimumSize(760, 720)
        outer = QVBoxLayout(self)

        title = QLabel("Build / edit a Personal Twin")
        title.setStyleSheet("font-size:26px;font-weight:900;")
        outer.addWidget(title)
        intro = QLabel(
            "Profile data is stored locally and becomes the context shared by the "
            "Personal Twin, Unified Workstation, Doctor Workstation, Patient Workstation and ENDO-TWIN."
        )
        intro.setWordWrap(True)
        outer.addWidget(intro)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        form = QFormLayout(content)
        form.setSpacing(9)

        self.patient_name = QLineEdit()
        self.patient_name.setPlaceholderText("Patient name / local record name")
        self.alias = QLineEdit()
        self.alias.setPlaceholderText("Optional short alias")
        self.sex = QComboBox()
        self.sex.addItems(["Unknown", "Female", "Male", "Intersex / other", "Prefer not to say"])
        self.age = self._spin(10, 100, 17, 1)
        self.height = self._spin(100, 230, 165, 1)
        self.weight = self._spin(25, 250, 60, 1)
        self.waist = self._spin(0, 200, 0, 1, "Unknown")
        self.sbp = self._spin(0, 250, 0, 1, "Unknown")
        self.dbp = self._spin(0, 150, 0, 1, "Unknown")
        self.glucose = self._spin(0, 600, 0, 1, "Unknown")
        self.cycle = QComboBox()
        self.cycle.addItems(["Unknown", "Regular", "Irregular"])
        self.cycle_len = self._spin(0, 120, 28, 0, "Unknown")
        self.days_since = self._spin(0, 365, 0, 0, "Unknown")
        self.ypm = self._spin(0, 80, 0, 1, "Unknown")

        for label, widget in [
            ("Patient name", self.patient_name), ("Local alias", self.alias), ("Sex", self.sex), ("Age (years)", self.age),
            ("Height (cm)", self.height), ("Weight (kg)", self.weight), ("Waist (cm)", self.waist),
            ("Systolic BP", self.sbp), ("Diastolic BP", self.dbp),
            ("Glucose mg/dL", self.glucose), ("Cycle status", self.cycle),
            ("Usual cycle length (days)", self.cycle_len),
            ("Days since last period", self.days_since), ("Years post-menarche", self.ypm),
        ]:
            form.addRow(label, widget)

        local = QLabel("LOCAL-FIRST • USER-ENTERED • patient-specific state")
        local.setStyleSheet("font-weight:800;")
        form.addRow("Provenance", local)
        scroll.setWidget(content)
        outer.addWidget(scroll, 1)

        self.summary = QLabel()
        self.summary.setWordWrap(True)
        self.summary.setStyleSheet("color:#718096;")
        outer.addWidget(self.summary)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Save)
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        outer.addWidget(buttons)

        self._load()

    def _spin(self, lo, hi, value, decimals, unknown=None):
        w = QDoubleSpinBox()
        w.setRange(lo, hi)
        w.setValue(value)
        w.setDecimals(decimals)
        if unknown is not None:
            w.setSpecialValueText(unknown)
        return w

    def _load(self):
        p = get_profile(self.participant_id) if self.participant_id else {}
        self.patient_name.setText(str(p.get("patient_name", p.get("alias", ""))))
        self.alias.setText(str(p.get("alias", "")))
        self.sex.setCurrentText(str(p.get("sex", "Unknown")))
        for widget, key in [
            (self.age, "age_years"), (self.height, "height_cm"), (self.weight, "weight_kg"),
            (self.waist, "waist_cm"), (self.sbp, "systolic_bp"), (self.dbp, "diastolic_bp"),
            (self.glucose, "glucose_mg_dl"), (self.cycle_len, "usual_cycle_length_days"),
            (self.days_since, "days_since_last_period"), (self.ypm, "years_post_menarche"),
        ]:
            value = p.get(key)
            if value is not None:
                try:
                    widget.setValue(float(value))
                except Exception:
                    pass
        cyc = p.get("cycle_irregular")
        self.cycle.setCurrentText("Irregular" if cyc is True else "Regular" if cyc is False else "Unknown")
        self.summary.setText(profile_summary(p) if p else "New participant — enter the profile below.")

    def save(self):
        patient_name = self.patient_name.text().strip()
        if not patient_name:
            QMessageBox.warning(self, "Patient name required", "Enter the patient's name before saving this Personal Twin.")
            self.patient_name.setFocus()
            return
        pid = self.participant_id or ("PT-" + uuid.uuid4().hex[:10].upper())
        h = float(self.height.value())
        w = float(self.weight.value())
        bmi = w / ((h / 100.0) ** 2) if h > 0 else None
        cyc = self.cycle.currentText()
        profile = {
            "participant_id": pid,
            "patient_name": self.patient_name.text().strip() or self.alias.text().strip() or pid,
            "alias": self.alias.text().strip(),
            "sex": self.sex.currentText(),
            "age_years": float(self.age.value()),
            "height_cm": h,
            "weight_kg": w,
            "bmi": round(bmi, 2) if bmi and math.isfinite(bmi) else None,
            "waist_cm": float(self.waist.value()) or None,
            "systolic_bp": float(self.sbp.value()) or None,
            "diastolic_bp": float(self.dbp.value()) or None,
            "glucose_mg_dl": float(self.glucose.value()) or None,
            "cycle_irregular": True if cyc == "Irregular" else False if cyc == "Regular" else None,
            "usual_cycle_length_days": int(self.cycle_len.value()) or None,
            "days_since_last_period": int(self.days_since.value()) or None,
            "years_post_menarche": float(self.ypm.value()) or None,
            "provenance": "USER-ENTERED",
            "updated_at": time.time(),
        }
        save_profile(profile, set_active=True)
        append_event({"kind": "profile_saved", "participant_id": pid})
        self.participant_id = pid
        self.summary.setText("Saved locally • " + profile_summary(profile))
        self.accept()


class PeopleManagerDialog(QDialog):
    """Top-level Self-Learning Model window with multi-person management."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ENDO-TWIN • Self-Learning Personal Twin")
        self.setModal(True)
        self.setMinimumSize(1000, 720)
        self.selected_id: str | None = None

        outer = QVBoxLayout(self)
        title = QLabel("Self-Learning Personal Twin")
        title.setStyleSheet("font-size:28px;font-weight:900;")
        outer.addWidget(title)
        desc = QLabel(
            "One local source of truth for patient profile + quality-gated longitudinal learning. "
            "The selected participant is synchronized to the desktop workstations."
        )
        desc.setWordWrap(True)
        outer.addWidget(desc)

        self.tabs = QTabWidget()
        outer.addWidget(self.tabs, 1)

        self.people_tab = QWidget()
        pbox = QVBoxLayout(self.people_tab)
        self.people_list = QListWidget()
        self.people_list.currentItemChanged.connect(self._selection_changed)
        pbox.addWidget(self.people_list, 1)

        buttons = QHBoxLayout()
        for text, handler in [
            ("＋ Add Person", self._add),
            ("✎ Edit Selected", self._edit),
            ("✓ Set Active", self._set_active),
            ("Remove", self._remove),
        ]:
            b = QPushButton(text)
            b.clicked.connect(handler)
            buttons.addWidget(b)
        buttons.addStretch()
        pbox.addLayout(buttons)

        disclaimer = QLabel(MULTI_PERSON_DISCLAIMER)
        disclaimer.setWordWrap(True)
        disclaimer.setObjectName("warning")
        pbox.addWidget(disclaimer)
        self.tabs.addTab(self.people_tab, "Multiple People / Profiles")

        self.learning_tab = QWidget()
        lbox = QVBoxLayout(self.learning_tab)
        self.learning_text = QLabel("Select a participant.")
        self.learning_text.setWordWrap(True)
        lbox.addWidget(self.learning_text, 1)
        refresh = QPushButton("Refresh learned data")
        refresh.clicked.connect(self._refresh_learning)
        lbox.addWidget(refresh)
        self.tabs.addTab(self.learning_tab, "Self-Learning Data")

        self.comp_tab = PCOSComplicationPanel("PCOS / Complication Context • Selected Person")
        self.tabs.addTab(self.comp_tab, "PCOS Complications")

        footer = QLabel(
            "All participant records are local-first and patient-scoped. "
            "The Personal Twin is a personalization layer, not a disease diagnosis."
        )
        footer.setWordWrap(True)
        outer.addWidget(footer)

        action = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok)
        action.button(QDialogButtonBox.StandardButton.Ok).setText("Continue to Unified Workstation")
        action.accepted.connect(self._continue)
        action.rejected.connect(self.reject)
        outer.addWidget(action)

        self._refresh_people()

    def _refresh_people(self):
        self.people_list.clear()
        profiles = list_profiles()
        for p in profiles:
            pid = str(p.get("participant_id"))
            alias = str(p.get("alias") or "Unnamed")
            text = f"{alias}  •  {pid}"
            if p.get("_active"):
                text += "  • ACTIVE"
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, pid)
            self.people_list.addItem(item)
        if self.people_list.count():
            self.people_list.setCurrentRow(0)
        self._refresh_learning()

    def _current_pid(self):
        item = self.people_list.currentItem()
        return str(item.data(Qt.ItemDataRole.UserRole)) if item else None

    def _selection_changed(self, *_):
        self.selected_id = self._current_pid()
        self._refresh_learning()

    def _add(self):
        d = PersonalTwinOnboarding(parent=self)
        if d.exec() == QDialog.DialogCode.Accepted:
            self._refresh_people()

    def _edit(self):
        pid = self._current_pid()
        if not pid:
            QMessageBox.information(self, "People", "Select a person first.")
            return
        d = PersonalTwinOnboarding(pid, self)
        if d.exec() == QDialog.DialogCode.Accepted:
            self._refresh_people()

    def _set_active(self):
        pid = self._current_pid()
        if not pid:
            return
        select_participant(pid)
        self._refresh_people()

    def _remove(self):
        pid = self._current_pid()
        if not pid:
            return
        if len(list_profiles()) <= 1:
            QMessageBox.warning(self, "People", "Keep at least one local participant.")
            return
        p = get_profile(pid)
        answer = QMessageBox.question(self, "Remove person", f"Remove local profile {p.get('alias') or pid}? Learning data for this participant will also be removed.")
        if answer == QMessageBox.StandardButton.Yes:
            remove_profile(pid)
            self._refresh_people()

    def _refresh_learning(self):
        pid = self._current_pid()
        if not pid:
            self.learning_text.setText("No people configured. Add a participant.")
            self.comp_tab.set_context({}, None)
            return
        p = get_profile(pid)
        model = PersonalAdaptiveModel(pid)
        snap = model.snapshot()
        lines = [
            f"Participant: {pid}",
            f"Profile: {profile_summary(p)}",
            f"Learning samples: {snap['samples']:,}",
            f"Quality-weighted samples: {snap['quality_weighted_samples']:.2f}",
            "",
            "Learned reference:",
        ]
        for name, item in snap.get("metrics", {}).items():
            lines.append(f"{name}: mean={item['mean']:.3f} • std={item['std']:.3f} • samples={item['samples']:.1f} • latest={item['last']}")
        self.learning_text.setText("\n".join(lines))
        self.comp_tab.set_context({
            k: p.get(k) for k in (
                "age_years","bmi","systolic_bp","diastolic_bp",
                "glucose_mg_dl","cycle_irregular","usual_cycle_length_days",
                "days_since_last_period","years_post_menarche",
            )
        }, None)

    def _continue(self):
        pid = self._current_pid()
        if not pid:
            QMessageBox.warning(self, "Personal Twin", "Add a participant before continuing.")
            return
        select_participant(pid)
        self.selected_id = pid
        self.accept()


def main() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyle("Fusion")
    dlg = PeopleManagerDialog()
    result = dlg.exec()
    return 0 if result == QDialog.DialogCode.Accepted else 1


if __name__ == "__main__":
    raise SystemExit(main())
