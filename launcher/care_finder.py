#!/usr/bin/env python3
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
from database.database import LocalDatabase
from provider_network.care_discovery import CareDiscoveryEngine, SupplyDiscoveryEngine
db = LocalDatabase(db_path=Path('/tmp/care_finder_demo.db'))
care = CareDiscoveryEngine(db)
supply = SupplyDiscoveryEngine(db)
nearby = care.find_nearby()
print(f'Nearby providers: {len(nearby)}')
for p in nearby:
    print(p.as_card_text())
supplies = supply.list_supplies()
print(f'\nSupplies: {len(supplies)}')
try:
    from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QListWidget, QTabWidget
    app = QApplication(sys.argv)
    win = QMainWindow()
    win.setWindowTitle('CHRONO-PCOS Care Finder - FIND CARE')
    win.resize(1100, 800)
    tabs = QTabWidget()
    prov_widget = QWidget()
    prov_layout = QVBoxLayout()
    prov_layout.addWidget(QLabel('FIND CARE - Nearby Doctors, Clinics, Labs, Supplies'))
    list_widget = QListWidget()
    for p in nearby:
        list_widget.addItem(f"{p.name} - {p.distance_km:.1f}km - {p.specialty} - {p.verification_status}")
    prov_layout.addWidget(list_widget)
    prov_widget.setLayout(prov_layout)
    tabs.addTab(prov_widget, 'Providers')
    win.setCentralWidget(tabs)
    win.show()
    sys.exit(app.exec())
except Exception as e:
    print(f'GUI failed: {e}')
    try:
        input("Press Enter...")
    except:
        pass
