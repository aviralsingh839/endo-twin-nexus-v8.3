#!/usr/bin/env python3
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
from database.database import LocalDatabase
import tempfile
db_path = Path(tempfile.gettempdir()) / 'chrono_test_db_ui.db'
db = LocalDatabase(db_path=db_path)
print('Database: Local-first SQLite 18 Tables')
print(f'Path: {db_path}')
print(f'Providers: {len(db.list_providers())} demo')
print(f'Supplies: {len(db.list_supplies())}')
pid = db.create_patient(display_name='DB Demo Patient', age_years=22, bmi=23.5)
print(f'Created demo patient: {pid}')
try:
    from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QTextEdit, QPushButton
    import subprocess
    app = QApplication(sys.argv)
    win = QMainWindow()
    win.setWindowTitle('CHRONO-PCOS Database - Local-first 18 Tables')
    win.resize(1100, 800)
    central = QWidget()
    layout = QVBoxLayout()
    layout.addWidget(QLabel(f'Local Database - SQLite 18 Tables - Path: {db_path}'))
    text = QTextEdit()
    text.setText(f'Tables: users, patients, profiles, symptoms, cycles, sensor_sessions, ppg, hrv, gsr, motion, temp, quality, ultrasound, model_results, analysis, reports, doctor_notes, providers, supplies, audit, access\nDemo patient: {pid}\nProviders: {len(db.list_providers())} demo\nSupplies: {len(db.list_supplies())}')
    layout.addWidget(text)
    central.setLayout(layout)
    win.setCentralWidget(central)
    win.show()
    sys.exit(app.exec())
except Exception as e:
    print(f'GUI failed: {e}')
    try:
        input("Press Enter to exit...")
    except (EOFError, KeyboardInterrupt):
        print("\nExiting...")
