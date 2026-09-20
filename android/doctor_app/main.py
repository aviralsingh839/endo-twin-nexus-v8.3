"""
Doctor Android Application - CHRONO-PCOS V8.3+

Mobile doctor companion, review and monitoring, not duplicate every PC feature.

PC = full workstation
Android = mobile review and monitoring interface

Provides:
- patient list
- patient search
- patient profiles
- recent measurements
- trends
- screening results
- ultrasound results
- reports
- notes
- follow-up information

Technology: Kivy (Python) offline-first, local SQLite, authorized patients only.
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

import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from database.database import LocalDatabase
from provider_network.care_discovery import CareDiscoveryEngine


class PatientListTab(BoxLayout):
    def __init__(self, db, doctor_id=None, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.db = db
        self.doctor_id = doctor_id

        self.add_widget(Label(text='Patient List - Authorized Only', size_hint_y=None, height=dp(40), font_size='18sp', bold=True))
        self.add_widget(Label(text='Search patient, open patient, patient history - only authorized patients', size_hint_y=None, height=dp(50)))

        # Search
        search_box = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10), padding=dp(10))
        search_box.add_widget(Label(text='Search:'))
        search_box.add_widget(Button(text='Search Patient', size_hint_x=0.5))
        self.add_widget(search_box)

        # Patient list
        scroll = ScrollView()
        grid = GridLayout(cols=1, spacing=dp(10), padding=dp(10), size_hint_y=None)
        grid.bind(minimum_height=grid.setter('height'))

        patients = self.db.list_patients(doctor_id=doctor_id)
        if not patients:
            # Demo patients
            grid.add_widget(Label(text='No authorized patients yet - demo data:', size_hint_y=None, height=dp(30)))
            for i in range(3):
                card = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(80), padding=dp(5))
                card.add_widget(Label(text=f'Patient P{i:05d} (Demo) - Age 22, BMI 23.5', bold=True, size_hint_y=None, height=dp(25)))
                card.add_widget(Label(text='Last assessment: 2 days ago, Data quality: Good', size_hint_y=None, height=dp(20)))
                card.add_widget(Button(text='Open Patient', size_hint_y=None, height=dp(30)))
                grid.add_widget(card)
        else:
            for p in patients[:10]:
                card = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(80), padding=dp(5))
                card.add_widget(Label(text=f'{p["anonymous_id"]} - {p.get("display_name","")}', bold=True, size_hint_y=None, height=dp(25)))
                card.add_widget(Label(text=f'Age {p.get("age_years","")} BMI {p.get("bmi","")}', size_hint_y=None, height=dp(20)))
                card.add_widget(Button(text='Open Patient', size_hint_y=None, height=dp(30)))
                grid.add_widget(card)

        scroll.add_widget(grid)
        self.add_widget(scroll)


class PatientProfileTab(BoxLayout):
    def __init__(self, db, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.add_widget(Label(text='Patient Profile', size_hint_y=None, height=dp(40), font_size='18sp', bold=True))
        self.add_widget(Label(text='Patient profiles - basic info, questionnaire, cycle, symptoms - minimal data', size_hint_y=None, height=dp(50)))

        grid = GridLayout(cols=2, spacing=dp(10), padding=dp(10))
        grid.add_widget(Label(text='Anonymous ID:'))
        grid.add_widget(Label(text='P12345'))
        grid.add_widget(Label(text='Age:'))
        grid.add_widget(Label(text='22 (USER-ENTERED)'))
        grid.add_widget(Label(text='BMI:'))
        grid.add_widget(Label(text='23.5 (USER-ENTERED)'))
        grid.add_widget(Label(text='Cycle Length:'))
        grid.add_widget(Label(text='28 days (USER-ENTERED)'))

        self.add_widget(grid)


class MeasurementsTab(BoxLayout):
    def __init__(self, db, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.add_widget(Label(text='Recent Measurements', size_hint_y=None, height=dp(40), font_size='18sp', bold=True))
        self.add_widget(Label(text='Recent measurements, trends, screening results, ultrasound results - technical', size_hint_y=None, height=dp(50)))

        scroll = ScrollView()
        grid = GridLayout(cols=1, spacing=dp(10), padding=dp(10), size_hint_y=None)
        grid.bind(minimum_height=grid.setter('height'))

        grid.add_widget(Label(text='HR: 72 bpm (MEASURED, quality 0.91)', size_hint_y=None, height=dp(30)))
        grid.add_widget(Label(text='HRV RMSSD: 48 ms (MEASURED, quality 0.85)', size_hint_y=None, height=dp(30)))
        grid.add_widget(Label(text='Skin Temp: 32.5°C (MEASURED, quality 0.88)', size_hint_y=None, height=dp(30)))
        grid.add_widget(Label(text='Activity: 35% (MEASURED)', size_hint_y=None, height=dp(30)))
        grid.add_widget(Label(text='Sleep Regularity: 75% (MODEL-INFERRED)', size_hint_y=None, height=dp(30)))

        scroll.add_widget(grid)
        self.add_widget(scroll)


class ScreeningResultsTab(BoxLayout):
    def __init__(self, db, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.add_widget(Label(text='Screening Results - Research Only', size_hint_y=None, height=dp(40), font_size='18sp', bold=True))
        self.add_widget(Label(text='Research / risk-screening output — not a medical diagnosis. Model name/version, input data, quality, confidence, features, limitations', size_hint_y=None, height=dp(60)))

        scroll = ScrollView()
        grid = GridLayout(cols=1, spacing=dp(10), padding=dp(10), size_hint_y=None)
        grid.bind(minimum_height=grid.setter('height'))

        grid.add_widget(Label(text='PCOS Module v8.3.0: pcos_associated_risk (low), confidence 0.75, data quality 0.85, clinical validation NOT ESTABLISHED', size_hint_y=None, height=dp(60)))
        grid.add_widget(Label(text='Sleep Module v8.3.0: circadian_disruption_pattern (moderate), confidence 0.68', size_hint_y=None, height=dp(60)))
        grid.add_widget(Label(text='Cardiometabolic v8.3.0: cardiometabolic_risk_signal (moderate)', size_hint_y=None, height=dp(60)))
        grid.add_widget(Label(text='Autonomic v8.3.0: autonomic_regulation_signal (moderate)', size_hint_y=None, height=dp(60)))

        scroll.add_widget(grid)
        self.add_widget(scroll)


class ReportsTab(BoxLayout):
    def __init__(self, db, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.add_widget(Label(text='Reports & Notes', size_hint_y=None, height=dp(40), font_size='18sp', bold=True))
        self.add_widget(Label(text='Reports, notes, follow-up information - professional research/clinical-review style', size_hint_y=None, height=dp(50)))

        self.add_widget(Button(text='Generate Report', size_hint_y=None, height=dp(50)))
        self.add_widget(Button(text='Add Doctor Note', size_hint_y=None, height=dp(50)))
        self.add_widget(Label(text='Previous reports would list here'))


class DoctorApp(App):
    def build(self):
        self.title = 'CHRONO-PCOS Doctor V8.3+'
        Window.clearcolor = (0.9, 0.9, 0.95, 1)

        self.db = LocalDatabase()

        root = BoxLayout(orientation='vertical')
        root.add_widget(Label(text='CHRONO-PCOS Doctor V8.3+ - Mobile Review - Sense • Model • Predict • Personalize • Connect', size_hint_y=None, height=dp(30), bold=True))
        root.add_widget(Label(text='Research / risk-screening output — not a medical diagnosis', size_hint_y=None, height=dp(25), color=(1, 0.6, 0, 1)))

        tabs = TabbedPanel(do_default_tab=False)

        # Patient list
        list_tab = TabbedPanelItem(text='Patients')
        list_tab.add_widget(PatientListTab(self.db))
        tabs.add_widget(list_tab)

        # Profile
        profile_tab = TabbedPanelItem(text='Profile')
        profile_tab.add_widget(PatientProfileTab(self.db))
        tabs.add_widget(profile_tab)

        # Measurements
        meas_tab = TabbedPanelItem(text='Measurements')
        meas_tab.add_widget(MeasurementsTab(self.db))
        tabs.add_widget(meas_tab)

        # Screening
        screen_tab = TabbedPanelItem(text='Screening')
        screen_tab.add_widget(ScreeningResultsTab(self.db))
        tabs.add_widget(screen_tab)

        # Reports
        reports_tab = TabbedPanelItem(text='Reports')
        reports_tab.add_widget(ReportsTab(self.db))
        tabs.add_widget(reports_tab)

        root.add_widget(tabs)
        return root


if __name__ == '__main__':
    try:
        DoctorApp().run()
    except Exception as e:
        print(f"Kivy not available or error: {e}")
        print("Running console demo of Doctor Android App")
        print("="*60)
        print("CHRONO-PCOS Doctor Android App V8.3+ - Console Demo")
        print("Patient list: patient list, search, only authorized patients")
        print("Patient profiles: basic info, questionnaire, cycle, symptoms")
        print("Recent measurements: HR, HRV, GSR, motion, temp, quality, artifacts")
        print("Trends: longitudinal changes")
        print("Screening results: PCOS, Sleep, Cardiometabolic, Autonomic modules, research-only, not diagnosis, model name/version, quality, confidence, features, limitations")
        print("Ultrasound results: image, quality, features, provenance")
        print("Reports: professional research/clinical-review style, not medical diagnosis")
        print("Notes: doctor notes, follow-up")
        print("PC = full workstation, Android = mobile review")
        print("="*60)
