#!/usr/bin/env python3
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
print('CHRONO-PCOS Ultrasound - Research not diagnosis, no invented accuracy')
try:
    from desktop.doctor_app.patient_management import UltrasoundViewer
    from database.database import LocalDatabase
    db = LocalDatabase(db_path=Path('/tmp/ultrasound_demo.db'))
    viewer = UltrasoundViewer(db)
    img = viewer.load_image('ultrasound_demo.png (DEMO)')
    qc = viewer.quality_check(img)
    print(f'Quality check: {qc}')
    from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QTextEdit
    app = QApplication(sys.argv)
    win = QMainWindow()
    win.setWindowTitle('Ultrasound Research')
    win.resize(1000, 700)
    central = QWidget()
    layout = QVBoxLayout()
    layout.addWidget(QLabel('Ultrasound - Quality gate UNKNOWN by design'))
    text = QTextEdit()
    text.setText(str(qc))
    layout.addWidget(text)
    central.setLayout(layout)
    win.setCentralWidget(central)
    win.show()
    sys.exit(app.exec())
except Exception as e:
    print(f'Error: {e}')
    try:
        input("Press Enter...")
    except:
        pass
