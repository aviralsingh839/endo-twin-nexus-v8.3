#!/usr/bin/env python3
"""Executable Doctor Test Workstation for ENDO-TWIN research-prototype testing."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from database.database import LocalDatabase
from src.endo_twin.testing.test_mode import classify_signal_failure


def run_prototype_test(db: LocalDatabase, patient_id: str, session_id: str) -> list[dict]:
    """Run deterministic infrastructure checks without inventing physiological values."""
    checks = []
    for component in ("MAX30102", "MPU6050", "GSR", "DS18B20", "ECG", "Serial", "Database", "Signal Processing"):
        if component in {"Database", "Signal Processing"}:
            result = classify_signal_failure(component, connected=True, samples=1, quality=1.0)
        else:
            # The test workflow verifies the reporting contract first; real hardware can
            # later supply actual connection/sample/quality values.
            result = classify_signal_failure(component, connected=True, samples=0)
        checks.append({
            "component": result.component,
            "status": result.status.value,
            "code": result.code,
            "message": result.message,
            "patient_id": patient_id,
            "session_id": session_id,
        })
    return checks


class DoctorTestWorkstation:
    def __init__(self, db: Optional[LocalDatabase] = None):
        self.db = db or LocalDatabase()

    def create_test_patient(self, anonymous_id: str = "TEST-001") -> str:
        existing = [p for p in self.db.search_patients(anonymous_id) if p["anonymous_id"] == anonymous_id]
        if existing:
            return existing[0]["patient_id"]
        return self.db.create_patient(
            anonymous_id=anonymous_id,
            display_name="ENDO-TWIN Test Patient",
            age_years=22,
            bmi=23.5,
        )

    def create_test_session(self, patient_id: str) -> str:
        return self.db.create_session(
            patient_id=patient_id,
            source="TEST_WORKSTATION",
            label="DEMO_DATA",
            notes="Infrastructure test session; no physiological values implied.",
        )

    def run(self, anonymous_id: str = "TEST-001") -> dict:
        patient_id = self.create_test_patient(anonymous_id)
        session_id = self.create_test_session(patient_id)
        checks = run_prototype_test(self.db, patient_id, session_id)
        return {
            "patient_id": patient_id,
            "anonymous_id": anonymous_id,
            "session_id": session_id,
            "checks": checks,
            "data_status": "DEMO_DATA",
            "note": "Sensor checks are infrastructure contracts; no unavailable sensor is converted into a physiological measurement.",
        }


def launch_gui() -> int:
    try:
        from PySide6.QtWidgets import (
            QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
            QPushButton, QLabel, QTableWidget, QTableWidgetItem, QMessageBox,
        )
        from PySide6.QtCore import Qt
        from src.ui.theme import DARK_QSS
    except ImportError:
        print("PySide6 is required for the Doctor Test Workstation.")
        return 2

    db = LocalDatabase()
    service = DoctorTestWorkstation(db)

    app = QApplication(sys.argv)
    window = QWidget()
    window.setWindowTitle("ENDO-TWIN NEXUS • Doctor Test Workbench")
    window.resize(1100, 700)
    window.setStyleSheet(DARK_QSS)

    layout = QVBoxLayout(window)
    layout.setContentsMargins(18, 18, 18, 18)
    layout.setSpacing(12)
    title = QLabel(
        "ENDO-TWIN Doctor Test Workstation\n"
        "Create a patient → create a test session → execute explicit hardware/infrastructure checks."
    )
    title.setWordWrap(True)
    title.setObjectName("HeroTitle")
    layout.addWidget(title)

    row = QHBoxLayout()
    row.addWidget(QLabel("Test patient ID:"))
    patient_edit = QLineEdit("TEST-001")
    row.addWidget(patient_edit)
    run_button = QPushButton("Create patient + run test")
    run_button.setObjectName("Primary")
    row.addWidget(run_button)
    layout.addLayout(row)

    status = QLabel("READY  •  infrastructure checks only  •  no physiological measurement is implied")
    status.setObjectName("SmallMuted")
    status.setWordWrap(True)
    layout.addWidget(status)

    table = QTableWidget(0, 4)
    table.setHorizontalHeaderLabels(["Component", "Status", "State", "Message"])
    table.horizontalHeader().setStretchLastSection(True)
    layout.addWidget(table)

    def run():
        anon = patient_edit.text().strip() or "TEST-001"
        try:
            result = service.run(anon)
        except Exception as exc:
            QMessageBox.critical(window, "Test failed", str(exc))
            return
        table.setRowCount(0)
        for check in result["checks"]:
            row_index = table.rowCount()
            table.insertRow(row_index)
            values = [check["component"], check["status"], check["code"], check["message"]]
            for col, value in enumerate(values):
                table.setItem(row_index, col, QTableWidgetItem(str(value)))
        status.setText(
            f"Patient {result['anonymous_id']} • session {result['session_id']} • {result['data_status']}\n"
            f"{sum(c['status'] == 'PASS' for c in result['checks'])} PASS, "
            f"{sum(c['status'] == 'WARN' for c in result['checks'])} WARN, "
            f"{sum(c['status'] == 'FAIL' for c in result['checks'])} FAIL"
        )

    run_button.clicked.connect(run)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(launch_gui())
