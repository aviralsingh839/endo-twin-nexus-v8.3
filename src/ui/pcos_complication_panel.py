"""Reusable PCOS complication-context panel for desktop surfaces."""
from __future__ import annotations

from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, QPushButton
from types import SimpleNamespace

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
