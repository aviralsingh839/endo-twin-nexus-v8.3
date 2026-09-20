#!/usr/bin/env python3
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
print('CHRONO-PCOS AI/ML Modules - Research not diagnosis')
try:
    from src.disease_modules.pcos import PCOSModule
    print('PCOSModule OK')
    from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QTextEdit
    app = QApplication(sys.argv)
    win = QMainWindow()
    win.setWindowTitle('AI/ML Modules')
    win.resize(1000, 700)
    central = QWidget()
    layout = QVBoxLayout()
    layout.addWidget(QLabel('AI/ML - Research / risk-screening not diagnosis'))
    text = QTextEdit()
    text.setText('PCOSModule v8.3.0 pcos_associated_risk low confidence 0.75 data quality 0.85 clinical validation NOT ESTABLISHED - EXAMPLE DATA - real path uses real_pcos_model_adapter.py calibrated probability, not hard-coded 0.75')
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
