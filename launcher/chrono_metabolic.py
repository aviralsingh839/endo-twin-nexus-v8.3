#!/usr/bin/env python3
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
from core.chrono_metabolic import ChronoMetabolicFingerprint
print('='*70)
print('CHRONO-PCOS - Chrono-Metabolic Fingerprinting')
print('Research / experimental - not a medical diagnosis')
print('='*70)
engine = ChronoMetabolicFingerprint()
fp = engine.build_from_features(
    features={'hrv_rmssd': 48, 'activity_level': 35, 'skin_temperature': 32.5, 'sleep_regularity': 0.75},
    quality_scores={'ppg': 0.91, 'motion': 0.8, 'temperature': 0.88}
)
print(f"Version: {fp['version']} Components: {len(fp['components'])}")
for c in fp['components']:
    print(f"  - {c['name']}: {c['category']} q={c['quality']}")
print(f"Disclaimer: {fp['disclaimer']}")
try:
    from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QTextEdit
    app = QApplication(sys.argv)
    win = QMainWindow()
    win.setWindowTitle('Chrono-Metabolic Fingerprinting')
    win.resize(1100, 800)
    central = QWidget()
    layout = QVBoxLayout()
    layout.addWidget(QLabel('Chrono-Metabolic Fingerprinting - Research not diagnosis'))
    text = QTextEdit()
    text.setText(str(fp))
    layout.addWidget(text)
    central.setLayout(layout)
    win.setCentralWidget(central)
    win.show()
    sys.exit(app.exec())
except Exception as e:
    print(f'GUI failed: {e}')
    try:
        input("Press Enter...")
    except:
        pass
