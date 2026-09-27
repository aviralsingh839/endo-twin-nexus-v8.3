"""Guided Personal Twin onboarding launched by START.sh."""
from __future__ import annotations

import math
import sys
import time
import uuid
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDialog, QDialogButtonBox,
    QDoubleSpinBox, QFormLayout, QGroupBox, QLabel, QMessageBox,
    QPlainTextEdit, QScrollArea, QVBoxLayout, QWidget
)

from src.config import DATA_DIR
from src.personal_twin.profile_store import save_profile, load_state, profile_summary, append_event


class PersonalTwinOnboarding(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ENDO-TWIN • Personal Twin Setup & Learning")
        self.setMinimumSize(760, 700)
        self.setModal(True)
        outer = QVBoxLayout(self)

        title = QLabel("Build your Personal Twin")
        title.setStyleSheet("font-size:28px;font-weight:900;")
        outer.addWidget(title)
        intro = QLabel(
            "Enter the local profile used to personalize longitudinal baselines. "
            "The workstation will keep raw sensor observations locally and update "
            "the personal model as quality-gated measurements arrive."
        )
        intro.setWordWrap(True)
        intro.setStyleSheet("color:#718096;")
        outer.addWidget(intro)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        form = QFormLayout(content)
        form.setSpacing(10)

        self.alias = QDoubleSpinBox()  # replaced below with a simple text field via alias_name
        from PySide6.QtWidgets import QLineEdit
        self.alias_name = QLineEdit()
        self.alias_name.setPlaceholderText("Optional local alias")
        self.sex = QComboBox()
        self.sex.addItems(["Unknown", "Female", "Male", "Intersex / other", "Prefer not to say"])

        self.age = QDoubleSpinBox(); self.age.setRange(10, 100); self.age.setValue(17); self.age.setDecimals(1)
        self.height = QDoubleSpinBox(); self.height.setRange(100, 230); self.height.setValue(165); self.height.setDecimals(1)
        self.weight = QDoubleSpinBox(); self.weight.setRange(25, 250); self.weight.setValue(60); self.weight.setDecimals(1)
        self.waist = QDoubleSpinBox(); self.waist.setRange(0, 200); self.waist.setValue(0); self.waist.setSpecialValueText("Unknown")
        self.sbp = QDoubleSpinBox(); self.sbp.setRange(0, 250); self.sbp.setValue(0); self.sbp.setSpecialValueText("Unknown")
        self.dbp = QDoubleSpinBox(); self.dbp.setRange(0, 150); self.dbp.setValue(0); self.dbp.setSpecialValueText("Unknown")
        self.glucose = QDoubleSpinBox(); self.glucose.setRange(0, 600); self.glucose.setValue(0); self.glucose.setSpecialValueText("Unknown")
        self.cycle_len = QDoubleSpinBox(); self.cycle_len.setRange(0, 120); self.cycle_len.setValue(28); self.cycle_len.setSpecialValueText("Unknown")
        self.days_since = QDoubleSpinBox(); self.days_since.setRange(0, 365); self.days_since.setValue(0); self.days_since.setSpecialValueText("Unknown")
        self.ypm = QDoubleSpinBox(); self.ypm.setRange(0, 80); self.ypm.setValue(0); self.ypm.setSpecialValueText("Unknown")
        self.cycle = QComboBox(); self.cycle.addItems(["Unknown", "Regular", "Irregular"])

        checks = []
        for label, widget in [
            ("Local alias", self.alias_name), ("Sex", self.sex), ("Age (years)", self.age),
            ("Height (cm)", self.height), ("Weight (kg)", self.weight), ("Waist (cm)", self.waist),
            ("Systolic BP", self.sbp), ("Diastolic BP", self.dbp), ("Glucose mg/dL", self.glucose),
            ("Cycle status", self.cycle), ("Usual cycle length (days)", self.cycle_len),
            ("Days since last period", self.days_since), ("Years post-menarche", self.ypm)
        ]:
            form.addRow(label, widget)

        consent = QLabel(
            "Stored locally only. This setup is a profile/personalization record, "
            "not a clinical diagnosis. You can edit it later from the workstation."
        )
        consent.setWordWrap(True)
        consent.setStyleSheet("color:#a05a00;")
        form.addRow("Storage", consent)

        scroll.setWidget(content); outer.addWidget(scroll, 1)

        self.state = QLabel()
        self.state.setWordWrap(True)
        self.state.setText(profile_summary(load_state().get("profile", {})))
        outer.addWidget(self.state)

        box = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Save)
        box.accepted.connect(self.save)
        box.rejected.connect(self.reject)
        outer.addWidget(box)

        self._load_existing()

    def _load_existing(self):
        p = load_state().get("profile", {})
        self.alias_name.setText(str(p.get("alias", "")))
        sex = str(p.get("sex", "Unknown"))
        idx = max(0, self.sex.findText(sex))
        self.sex.setCurrentIndex(idx)
        for widget, key in [
            (self.age, "age_years"), (self.height, "height_cm"), (self.weight, "weight_kg"),
            (self.waist, "waist_cm"), (self.sbp, "systolic_bp"), (self.dbp, "diastolic_bp"),
            (self.glucose, "glucose_mg_dl"), (self.cycle_len, "usual_cycle_length_days"),
            (self.days_since, "days_since_last_period"), (self.ypm, "years_post_menarche"),
        ]:
            value = p.get(key)
            if value is not None:
                try: widget.setValue(float(value))
                except Exception: pass
        cyc = p.get("cycle_irregular")
        if cyc is True: self.cycle.setCurrentText("Irregular")
        elif cyc is False: self.cycle.setCurrentText("Regular")

    def save(self):
        height = float(self.height.value())
        weight = float(self.weight.value())
        bmi = weight / ((height / 100.0) ** 2) if height > 0 else None
        cyc = self.cycle.currentText()
        existing = load_state().get("profile", {})
        if not isinstance(existing, dict):
            existing = {}
        profile = {
            "participant_id": str(existing.get("participant_id") or ("PT-" + uuid.uuid4().hex[:10].upper())),
            "alias": self.alias_name.text().strip(),
            "sex": self.sex.currentText(),
            "age_years": float(self.age.value()),
            "height_cm": height,
            "weight_kg": weight,
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
        save_profile(profile)
        append_event({"kind": "profile_saved", "profile_keys": sorted(profile.keys())})
        self.state.setText("Saved locally • " + profile_summary(profile))
        QMessageBox.information(self, "Personal Twin", "Profile saved. New wearable observations will now update the local adaptive model.")
        self.accept()


def main() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    d = PersonalTwinOnboarding()
    d.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
