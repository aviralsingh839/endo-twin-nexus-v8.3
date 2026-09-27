"""Patient/person selector shared by desktop workstations."""
from __future__ import annotations

import sys
from PySide6.QtWidgets import QApplication, QDialog, QDialogButtonBox, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QMessageBox, QPushButton, QVBoxLayout

from src.personal_twin.profile_store import list_profiles, select_participant


class ParticipantSelector(QDialog):
    def __init__(self, title="Select Patient", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumSize(700, 480)
        self.selected_id = None
        outer = QVBoxLayout(self)
        h = QLabel("Which patient is using this workstation?")
        h.setStyleSheet("font-size:24px;font-weight:900;")
        outer.addWidget(h)
        note = QLabel("Choose the local participant whose Personal Twin, clinical inputs and longitudinal observations should be opened. Each person remains isolated.")
        note.setWordWrap(True)
        outer.addWidget(note)
        self.list = QListWidget()
        outer.addWidget(self.list, 1)
        row = QHBoxLayout()
        add = QPushButton("＋ Add / Manage People")
        add.clicked.connect(self._manage)
        row.addWidget(add)
        row.addStretch()
        outer.addLayout(row)
        box = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Open)
        box.accepted.connect(self.accept_selected)
        box.rejected.connect(self.reject)
        outer.addWidget(box)
        self._refresh()

    def _refresh(self):
        self.list.clear()
        for p in list_profiles():
            pid = str(p.get("participant_id"))
            alias = str(p.get("alias") or pid)
            line = f"{alias}  •  {pid}"
            if p.get("_active"):
                line += "  •  ACTIVE"
            item = QListWidgetItem(line)
            item.setData(256, pid)
            self.list.addItem(item)
        if self.list.count():
            self.list.setCurrentRow(0)

    def _manage(self):
        from src.personal_twin.onboarding import PeopleManagerDialog
        dlg = PeopleManagerDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._refresh()

    def accept_selected(self):
        item = self.list.currentItem()
        if item is None:
            QMessageBox.warning(self, "Select Patient", "Add a person first, then select the patient.")
            return
        self.selected_id = str(item.data(256))
        select_participant(self.selected_id)
        self.accept()


def choose_participant(title="Select Patient") -> str | None:
    app = QApplication.instance() or QApplication(sys.argv)
    dlg = ParticipantSelector(title)
    return dlg.selected_id if dlg.exec() == QDialog.DialogCode.Accepted else None
