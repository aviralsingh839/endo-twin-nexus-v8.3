"""
Patient Android Application - CHRONO-PCOS V8.3+

Kivy-based, offline-first, local SQLite, accessibility-friendly.

Sections:
- Dashboard: data collection status, sensor status, recent measurements, quality, cycle, previous sessions, notifications
- Patient Profile: basic profile, questionnaire, cycle, symptom (minimal data)
- Measurements: sensor connection, guided measurement, PPG, HR, HRV, motion, temp, quality
- Symptoms: structured symptom logging
- Cycle Tracking: dates, length, irregularity, symptoms, notes (not diagnosis)
- Results: understandable language "Data quality: Good" not raw technical unless advanced
- Reports: view appropriate reports
- Doctor Sharing: controlled sharing/export of selected info, local-first
- Find Care: nearby doctors/clinics/labs/supplies

Technology: Kivy (Python) can build to APK with Buildozer, offline-first, local SQLite.
"""
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.metrics import dp
from kivy.core.window import Window

# For demo without Kivy installed, fallback to simple console
try:
    KIVY_AVAILABLE = True
except:
    KIVY_AVAILABLE = False

# Local database - reuse V8.3+ database
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from database.database import LocalDatabase
from provider_network.care_discovery import CareDiscoveryEngine, SupplyDiscoveryEngine


class PatientDashboard(BoxLayout):
    def __init__(self, db, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.db = db

        # Status
        self.add_widget(Label(text='CHRONO-PCOS Patient Dashboard', size_hint_y=None, height=dp(40), font_size='20sp', bold=True))
        self.add_widget(Label(text='Research / Risk-Screening - Not a Medical Diagnosis', size_hint_y=None, height=dp(30), color=(1, 0.8, 0.2, 1)))

        # Data collection status
        status_box = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(150), padding=dp(10))
        status_box.add_widget(Label(text='Data Collection Status: Ready', font_size='16sp'))
        status_box.add_widget(Label(text='Sensor Status: No sensor connected (Demo mode available)', font_size='14sp'))
        status_box.add_widget(Label(text='Recent Measurements: No recent data', font_size='14sp'))
        status_box.add_widget(Label(text='Data Quality: No data yet', font_size='14sp'))
        self.add_widget(status_box)

        # Buttons
        btn_box = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10), padding=dp(10))
        btn_box.add_widget(Button(text='Start Measurement', on_press=self.start_measurement))
        btn_box.add_widget(Button(text='View Results', on_press=self.view_results))
        btn_box.add_widget(Button(text='Find Care', on_press=self.find_care))
        self.add_widget(btn_box)

        # Recent sessions
        self.add_widget(Label(text='Previous Screening Sessions: None yet', size_hint_y=None, height=dp(30)))

    def start_measurement(self, instance):
        print("Starting guided measurement - PPG, HR, HRV, motion, temp")

    def view_results(self, instance):
        print("Viewing results in understandable language - Data quality: Good")

    def find_care(self, instance):
        print("Opening Find Care - nearby providers")


class PatientProfileTab(BoxLayout):
    def __init__(self, db, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.db = db
        self.add_widget(Label(text='Patient Profile (Local Only)', size_hint_y=None, height=dp(40), font_size='18sp', bold=True))
        self.add_widget(Label(text='Basic profile, questionnaire, cycle, symptoms - minimal data collection, no unnecessary personal info', size_hint_y=None, height=dp(60)))

        # Example fields - in real app would be text inputs
        grid = GridLayout(cols=2, spacing=dp(10), padding=dp(10), size_hint_y=None)
        grid.bind(minimum_height=grid.setter('height'))
        grid.add_widget(Label(text='Age:'))
        grid.add_widget(Label(text='22 (USER-ENTERED)'))
        grid.add_widget(Label(text='BMI:'))
        grid.add_widget(Label(text='23.5 (USER-ENTERED)'))
        grid.add_widget(Label(text='Cycle Length:'))
        grid.add_widget(Label(text='28 days (USER-ENTERED)'))
        grid.add_widget(Label(text='Irregularity:'))
        grid.add_widget(Label(text='Unknown (USER-ENTERED)'))

        scroll = ScrollView()
        scroll.add_widget(grid)
        self.add_widget(scroll)


class MeasurementsTab(BoxLayout):
    def __init__(self, db, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.add_widget(Label(text='Measurements - Guided', size_hint_y=None, height=dp(40), font_size='18sp', bold=True))
        self.add_widget(Label(text='Sensor connection, guided measurement, PPG, HR, HRV, motion, temp, quality - graceful handling if sensor unavailable/disconnected/noisy', size_hint_y=None, height=dp(60)))

        btn_box = BoxLayout(size_hint_y=None, height=dp(100), spacing=dp(10), padding=dp(10))
        btn_box.add_widget(Button(text='Connect Sensor (USB/BLE)'))
        btn_box.add_widget(Button(text='Demo Mode (Simulated)'))
        self.add_widget(btn_box)

        self.add_widget(Label(text='Live PPG waveform would appear here'))


class SymptomsTab(BoxLayout):
    def __init__(self, db, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.add_widget(Label(text='Symptoms - Structured Logging', size_hint_y=None, height=dp(40), font_size='18sp', bold=True))
        self.add_widget(Label(text='Allow structured symptom logging - minimal, not diagnosis'))

        grid = GridLayout(cols=2, spacing=dp(10), padding=dp(10))
        grid.add_widget(Label(text='Symptom Type:'))
        grid.add_widget(Label(text='e.g. Irregular Cycle'))
        grid.add_widget(Label(text='Severity:'))
        grid.add_widget(Label(text='0-10 scale'))
        grid.add_widget(Label(text='Notes:'))
        grid.add_widget(Label(text='Free text'))

        self.add_widget(grid)
        self.add_widget(Button(text='Log Symptom', size_hint_y=None, height=dp(50)))


class CycleTrackingTab(BoxLayout):
    def __init__(self, db, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.add_widget(Label(text='Cycle Tracking', size_hint_y=None, height=dp(40), font_size='18sp', bold=True))
        self.add_widget(Label(text='Cycle dates, length, irregularity, symptoms, notes - do not interpret as diagnosis', size_hint_y=None, height=dp(60)))

        grid = GridLayout(cols=2, spacing=dp(10), padding=dp(10))
        grid.add_widget(Label(text='Start Date:'))
        grid.add_widget(Label(text='2024-01-15'))
        grid.add_widget(Label(text='Length:'))
        grid.add_widget(Label(text='28 days'))
        grid.add_widget(Label(text='Irregularity:'))
        grid.add_widget(Label(text='Regular'))

        self.add_widget(grid)
        self.add_widget(Button(text='Log Cycle', size_hint_y=None, height=dp(50)))


class ResultsTab(BoxLayout):
    def __init__(self, db, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.add_widget(Label(text='Results - Understandable Language', size_hint_y=None, height=dp(40), font_size='18sp', bold=True))
        self.add_widget(Label(text='Present results in understandable language, not complicated technical variables by default', size_hint_y=None, height=dp(60)))

        self.add_widget(Label(text='Data Quality: Good (example, not raw technical)', font_size='16sp'))
        self.add_widget(Label(text='Screening Result: Research analysis complete - discuss with clinician if symptomatic', font_size='14sp'))
        self.add_widget(Label(text='This is a research / risk-screening output — not a medical diagnosis.', font_size='12sp', color=(1, 0.8, 0.2, 1)))

        self.add_widget(Button(text='View Detailed Report', size_hint_y=None, height=dp(50)))
        self.add_widget(Button(text='Share with Doctor (Controlled)', size_hint_y=None, height=dp(50)))


class FindCareTab(BoxLayout):
    def __init__(self, db, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.db = db
        self.care_engine = CareDiscoveryEngine(db)

        self.add_widget(Label(text='FIND CARE - Nearby Providers', size_hint_y=None, height=dp(40), font_size='18sp', bold=True))
        self.add_widget(Label(text='Discover nearby participating doctors, clinics, labs, supplies - map/list, distance, specialty, address, hours, contact, verification', size_hint_y=None, height=dp(80)))

        # List view
        scroll = ScrollView()
        grid = GridLayout(cols=1, spacing=dp(10), padding=dp(10), size_hint_y=None)
        grid.bind(minimum_height=grid.setter('height'))

        providers = self.care_engine.find_nearby()
        for p in providers[:5]:
            card = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(120), padding=dp(5))
            card.add_widget(Label(text=f'{p.name} - {p.distance_km:.1f} km', bold=True, size_hint_y=None, height=dp(25)))
            card.add_widget(Label(text=f'{p.specialty} - {p.verification_status}', size_hint_y=None, height=dp(20)))
            card.add_widget(Label(text=p.address, size_hint_y=None, height=dp(20)))
            btn_box = BoxLayout(size_hint_y=None, height=dp(30), spacing=dp(5))
            btn_box.add_widget(Button(text='View', size_hint_x=0.3))
            btn_box.add_widget(Button(text='Directions', size_hint_x=0.4))
            btn_box.add_widget(Button(text='Contact', size_hint_x=0.3))
            card.add_widget(btn_box)
            grid.add_widget(card)

        scroll.add_widget(grid)
        self.add_widget(scroll)


class PatientApp(App):
    def build(self):
        self.title = 'CHRONO-PCOS Patient V8.3+'
        Window.clearcolor = (0.95, 0.95, 0.95, 1)

        self.db = LocalDatabase()

        root = BoxLayout(orientation='vertical')
        root.add_widget(Label(text='CHRONO-PCOS V8.3+ Patient - Sense • Model • Predict • Personalize • Connect', size_hint_y=None, height=dp(30), bold=True))

        tabs = TabbedPanel(do_default_tab=False)

        # Dashboard
        dashboard_tab = TabbedPanelItem(text='Dashboard')
        dashboard_tab.add_widget(PatientDashboard(self.db))
        tabs.add_widget(dashboard_tab)

        # Profile
        profile_tab = TabbedPanelItem(text='Profile')
        profile_tab.add_widget(PatientProfileTab(self.db))
        tabs.add_widget(profile_tab)

        # Measurements
        meas_tab = TabbedPanelItem(text='Measurements')
        meas_tab.add_widget(MeasurementsTab(self.db))
        tabs.add_widget(meas_tab)

        # Symptoms
        symp_tab = TabbedPanelItem(text='Symptoms')
        symp_tab.add_widget(SymptomsTab(self.db))
        tabs.add_widget(symp_tab)

        # Cycle
        cycle_tab = TabbedPanelItem(text='Cycle')
        cycle_tab.add_widget(CycleTrackingTab(self.db))
        tabs.add_widget(cycle_tab)

        # Results
        results_tab = TabbedPanelItem(text='Results')
        results_tab.add_widget(ResultsTab(self.db))
        tabs.add_widget(results_tab)

        # Find Care
        care_tab = TabbedPanelItem(text='Find Care')
        care_tab.add_widget(FindCareTab(self.db))
        tabs.add_widget(care_tab)

        root.add_widget(tabs)
        return root


if __name__ == '__main__':
    # For environments without Kivy, run console demo
    try:
        PatientApp().run()
    except Exception as e:
        print(f"Kivy not available or error: {e}")
        print("Running console demo of Patient App")
        print("="*60)
        print("CHRONO-PCOS Patient App V8.3+ - Console Demo")
        print("Dashboard: data collection status, sensor status, recent measurements, quality, cycle, previous sessions")
        print("Profile: basic info, questionnaire, cycle, symptoms - minimal data")
        print("Measurements: sensor connection, guided measurement, PPG, HR, HRV, motion, temp, quality")
        print("Symptoms: structured logging")
        print("Cycle Tracking: dates, length, irregularity, symptoms, notes - not diagnosis")
        print("Results: understandable language, Data quality: Good, not raw technical unless advanced")
        print("Reports: view appropriate reports")
        print("Doctor Sharing: controlled sharing/export, local-first")
        print("Find Care: nearby doctors/clinics/labs/supplies with map/list, distance, specialty, address, hours, contact, verification")
        print("="*60)
        print("This is a research / risk-screening output — not a medical diagnosis.")
        print("Local-first, offline, privacy-focused")
