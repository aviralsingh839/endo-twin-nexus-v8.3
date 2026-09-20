#!/usr/bin/env python3
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
print('Signal Processing - Filtering, Baseline, Artifact, Quality, Features')
try:
    from src.core.feature_extraction import RealtimeFeatureExtractor
    extractor = RealtimeFeatureExtractor()
    print(f'Extractor OK: {extractor}')
    from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QTextEdit
    app = QApplication(sys.argv)
    win = QMainWindow()
    win.setWindowTitle('Signal Processing')
    win.resize(1000, 700)
    central = QWidget()
    layout = QVBoxLayout()
    layout.addWidget(QLabel('Signal Processing - Filtering, Baseline, Artifact, Quality'))
    text = QTextEdit()
    text.setText('Filtering bandpass 0.5-4Hz, baseline removal, artifact detection, quality control, feature extraction')
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
