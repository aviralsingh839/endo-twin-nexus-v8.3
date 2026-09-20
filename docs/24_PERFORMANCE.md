# 24 - Performance - V8.3+

## Ordinary Hardware
Avoid heavy cloud, expensive APIs, proprietary paid, unnecessary frameworks. Prefer free/open-source: Python, PySide6, PyQtGraph, NumPy, Pandas, PySerial, sklearn, Kivy. Do NOT introduce Dash/Plotly/Flask/Electron/browser dashboard unless architectural reason not replacing existing.

## Local Database
- SQLite file DATA_DIR/chrono_twin_nexus_v8_3_plus.db
- 18 tables, indexes on patient_id, session_id, anonymous_id
- Seeded 4 demo providers 5 supplies small
- Queries: list_patients, search_patients, get_nearby_providers distance filter simple not haversine for demo performance
- Backup via conn.backup

## Signal Processing
- Filtering: NumPy, low computational cost
- Feature extraction: real-time 20Hz feasible on ordinary hardware
- Quality control: per sample quality 0-1, artifact flags

## AI/ML
- sklearn models, small datasets 541 rows, 10 subjects 30 days
- Training: seconds on ordinary hardware
- Inference: milliseconds
- No heavy cloud, no expensive APIs

## Ultrasound
- Image loading: PIL/OpenCV if available, else placeholder
- Preprocessing: resize normalize denoise
- Quality checks: blur exposure anatomy visibility
- No heavy GPU required for prototype, CPU inference if model available
- Do not invent accuracy, state if insufficient

## Desktop Doctor App
- PySide6, PyQtGraph time-series visualization
- Preserves src/ui/main_window.py V8.3
- Enhanced main_enhanced.py fallback console demo if PySide6 not available
- 1400x900 window, tabs, QListWidget, QTextEdit

## Android Apps
- Kivy, offline SQLite, local-first
- TabbedPanel, BoxLayout, GridLayout, ScrollView
- Console demo fallback if Kivy not available
- APK via Buildozer, ordinary Android device

## Website
- Static HTML/CSS/JS, no backend, no heavy frameworks
- Responsive, mobile support, serious modern scientific
- No excessive animations
- Clean typography, accessible colors

## Care Discovery
- Local providers list, OSM directions URL no API key
- No heavy map SDK, list view offline, map tiles optional

## Why Performance Matters?
Class 11 project accessible, offline-first, no expensive APIs, reproducible, science/clarity/reproducibility/explainability/honest limitations over enterprise architecture keep offline.
