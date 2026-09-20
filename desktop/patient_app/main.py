#!/usr/bin/env python3
"""ENDO-TWIN Patient Workstation V8.5."""
from __future__ import annotations
import sys
from pathlib import Path
PROJECT_ROOT=Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:sys.path.insert(0,str(PROJECT_ROOT))
from services.bridge.server import EndoTwinBridgeServer
from desktop.workstation_theme import APP_QSS,card
try:
 from PySide6.QtWidgets import QApplication,QFrame,QGridLayout,QHBoxLayout,QLabel,QMainWindow,QMessageBox,QPushButton,QStackedWidget,QVBoxLayout,QWidget
 PYSIDE_AVAILABLE=True
except ImportError:PYSIDE_AVAILABLE=False
DISCLAIMER="Research / risk-screening output — not a medical diagnosis."
class PatientWindow(QMainWindow):
 def __init__(self):
  super().__init__();self.bridge=EndoTwinBridgeServer(PROJECT_ROOT,7778);self.bridge.start();self.setWindowTitle("ENDO-TWIN • Patient Workstation • V8.5");self.resize(1380,860);self.setStyleSheet(APP_QSS);self._build()
 def closeEvent(self,e):self.bridge.stop();e.accept()
 def _page(self,t,s):
  w=QWidget();o=QVBoxLayout(w);o.setContentsMargins(26,24,26,18);o.setSpacing(16);a=QLabel(t);a.setObjectName("title");o.addWidget(a);b=QLabel(s);b.setObjectName("muted");b.setWordWrap(True);o.addWidget(b);return w,o
 def _build(self):
  root=QWidget();self.setCentralWidget(root);shell=QGridLayout(root);shell.setContentsMargins(0,0,0,0)
  side=QFrame();side.setObjectName("sidebar");side.setFixedWidth(236);sl=QVBoxLayout(side);sl.setContentsMargins(20,24,20,20);a=QLabel("ENDO-TWIN");a.setObjectName("brand");sl.addWidget(a);b=QLabel("PATIENT WORKSTATION");b.setObjectName("eyebrow");sl.addWidget(b);sl.addSpacing(16)
  self.nav={}
  for k,txt in [("home","⌂  Home"),("health","♥  My Health"),("measure","∿  Measurements"),("timeline","◷  Timeline"),("connect","⌁  Connect"),("reports","▤  Reports")]:
   q=QPushButton(txt);q.setObjectName("nav");q.setCheckable(True);q.clicked.connect(lambda checked=False,key=k:self._go(key));self.nav[k]=q;sl.addWidget(q)
  sl.addStretch();c=QFrame();c.setObjectName("hero");cl=QVBoxLayout(c);a=QLabel("LOCAL WORKSTATION");a.setObjectName("eyebrow");cl.addWidget(a);self.bridge_label=QLabel(self.bridge.endpoint);self.bridge_label.setObjectName("muted");self.bridge_label.setWordWrap(True);cl.addWidget(self.bridge_label);sl.addWidget(c);shell.addWidget(side,0,0)
  right=QWidget();rv=QVBoxLayout(right);rv.setContentsMargins(0,0,0,0);top=QFrame();top.setObjectName("topbar");tl=QHBoxLayout(top);t=QLabel("Your physiological workspace");t.setObjectName("title");tl.addWidget(t);tl.addStretch();d=QLabel("DEMO • DEMO-001");d.setStyleSheet("background:#13364d;color:#9edfff;padding:7px 10px;border-radius:12px;font-weight:800;font-size:10px;");tl.addWidget(d);rv.addWidget(top)
  self.stack=QStackedWidget()
  for fn in [self._home,self._health,self._measure,self._timeline,self._connect,self._reports]:self.stack.addWidget(fn())
  rv.addWidget(self.stack,1);foot=QLabel(f"{DISCLAIMER}  •  Local-first  •  DEMO_DATA only");foot.setObjectName("muted");rv.addWidget(foot);shell.addWidget(right,0,1)
 def _home(self):
  w,o=self._page("Good to see you","A simple patient surface focused on your own physiological history.");g=QGridLayout()
  for i,c in enumerate([card("Baseline","72%","Illustrative completeness • DEMO_DATA"),card("Heart rate","72 bpm","MEASURED • illustrative"),card("HRV","48 ms","DERIVED • illustrative pulse-derived"),card("Data quality","0.91","DEMO_DATA • illustrative")]):g.addWidget(c,0,i)
  o.addLayout(g);h=QFrame();h.setObjectName("hero");hl=QVBoxLayout(h);e=QLabel("HOW ENDO-TWIN THINKS");e.setObjectName("eyebrow");hl.addWidget(e);q=QLabel("Personal baseline → time series → change → persistence → recovery → context");q.setWordWrap(True);q.setStyleSheet("font-size:18px;font-weight:750;color:#f2fbff;");hl.addWidget(q);o.addWidget(h);o.addStretch();return w
 def _health(self):
  w,o=self._page("My Health","Measured, derived and model-inferred layers are displayed separately.");g=QGridLayout()
  for i,c in enumerate([card("Heart rate","72 bpm","MEASURED • illustrative"),card("Skin temperature","32.5 °C","MEASURED • illustrative"),card("Activity","35 %","DERIVED • illustrative motion"),card("CHRONO-PCOS","Research module","MODEL-INFERRED • validation NOT ESTABLISHED")]):g.addWidget(c,0,i)
  o.addLayout(g);o.addStretch();return w
 def _measure(self):
  w,o=self._page("Measurements","Sensor status stays adjacent to every reading.");g=QGridLayout()
  for i,c in enumerate([card("PPG","20 Hz","Illustrative MAX30102"),card("GSR","Tonic + phasic","Illustrative electrodermal"),card("Motion","6-axis IMU","Illustrative MPU6050"),card("Temperature","Skin trend","Illustrative DS18B20")]):g.addWidget(c,0,i)
  o.addLayout(g);o.addWidget(QLabel("NO LIVE SENSOR ATTACHED • USB serial/TCP remain supported by the scientific core."));o.addStretch();return w
 def _timeline(self):
  w,o=self._page("Timeline","Chronological patient-scoped history.")
  for a,b in [("19 Sep 2026","Sensor session • DEMO_DATA"),("18 Sep 2026","Symptom entry • CLINICALLY-ENTERED"),("Study","Ultrasound • IMAGE-DERIVED • unsupported features UNKNOWN"),("Model run","CHRONO-PCOS • MODEL-INFERRED")]:o.addWidget(card(a,"EVENT",b))
  o.addStretch();return w
 def _connect(self):
  w,o=self._page("Connect","Pair your phone with this Patient Workstation on the same Wi-Fi.");g=QGridLayout();g.addWidget(card("Address",self.bridge.endpoint,"Use in Patient Android → Connect"),0,0);g.addWidget(card("Port","7778","Separate from Doctor Workstation"),0,1);g.addWidget(card("Received",str(self.bridge.received_count),"data/bridge/inbox"),0,2);o.addLayout(g)
  b=QPushButton("Copy connection details");b.setObjectName("primary");b.clicked.connect(lambda:(QApplication.clipboard().setText(self.bridge.endpoint+"\nPort: 7778"),QMessageBox.information(self,"Connect","Copied.")));o.addWidget(b);o.addStretch();return w
 def _reports(self):
  w,o=self._page("Reports","Patient-scoped reports retain provenance and limitations.");o.addWidget(card("Report layers","READY","Observation period • quality • baseline • longitudinal change • model layer • image provenance"));o.addStretch();return w
 def _go(self,k):
  self.stack.setCurrentIndex(list(self.nav).index(k))
  for n,b in self.nav.items():b.setChecked(n==k)
def run():
 if not PYSIDE_AVAILABLE:print("PySide6 is required for the ENDO-TWIN Patient Workstation.");return 1
 app=QApplication(sys.argv);app.setStyle("Fusion");w=PatientWindow();w.show();return app.exec()
if __name__=="__main__":raise SystemExit(run())
