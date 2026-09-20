# 21 - Deployment - V8.3+

## Requirements
- Python 3.9+
- PySide6, pyqtgraph, numpy, pandas, sklearn, pyserial, joblib, pytest (requirements.txt)
- For Android: Kivy, Buildozer, Android SDK/NDK
- For website: static hosting (GitHub Pages, Netlify, etc.)
- Ordinary hardware, avoid heavy cloud/expensive APIs/proprietary paid/unnecessary frameworks

## Local Setup
```bash
git clone <repo>
cd chrono-pcos-v8.1
pip install -r requirements.txt
python -m src.app  # V8.3 existing app
python -m desktop.doctor_app.main_enhanced  # Enhanced doctor PC console demo
python -m database.database  # Test DB
python -m provider_network.care_discovery  # Test care discovery
python -m core.chrono_metabolic  # Test fingerprint
python android/patient_app/main.py  # Patient Android console demo (Kivy if available)
python android/doctor_app/main.py  # Doctor Android console demo
```

## Database
- Location DATA_DIR/chrono_twin_nexus_v8_3_plus.db
- 18 tables, seeded 4 demo providers 5 supplies
- Backup: LocalDatabase.backup_database(path)

## Desktop Doctor App
- PySide6 GUI: preserves src/ui/main_window.py
- Enhanced: desktop/doctor_app/main_enhanced.py
- Run: python -m desktop.doctor_app.main_enhanced --gui or src.app

## Android Apps
- Patient: android/patient_app/main.py Kivy TabbedPanel Dashboard/Profile/Measurements/Symptoms/Cycle/Results/Find Care
- Doctor: android/doctor_app/main.py Kivy patient list/search/profiles/recent measurements/trends/screening results/ultrasound/reports/notes/follow-up
- Build APK: Buildozer spec, offline SQLite, local-first
- buildozer android debug

## Provider Network
- CareDiscoveryEngine, SupplyDiscoveryEngine
- Seeded demo providers, OSM directions no API key

## Website
- website/index.html, style.css, script.js
- Static hosting, no private records, no backend required
- Serious modern scientific design

## Demo Mode
Demo patient, simulated sensor, signal processing, AI, chrono-metabolic, ultrasound, risk-screening, doctor dashboard, report, every simulated labeled DEMO/SIMULATED

## Testing
- pytest tests/ -k not hardware -q
- Manual tests via python -m modules
