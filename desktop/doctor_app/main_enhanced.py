#!/usr/bin/env python3
"""ENDO-TWIN Doctor Workstation V8.5."""
from __future__ import annotations
import sys
from pathlib import Path
PROJECT_ROOT=Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:sys.path.insert(0,str(PROJECT_ROOT))
from database.database import LocalDatabase
from desktop.doctor_app.patient_management import PatientManager
from services.bridge.server import EndoTwinBridgeServer
try:
 from PySide6.QtCore import Qt
 from PySide6.QtWidgets import QApplication,QFrame,QGridLayout,QHBoxLayout,QLabel,QLineEdit,QListWidget,QMainWindow,QMessageBox,QPushButton,QStackedWidget,QTableWidget,QTableWidgetItem,QVBoxLayout,QWidget
 PYSIDE_AVAILABLE=True
except ImportError:PYSIDE_AVAILABLE=False
from desktop.workstation_theme import APP_QSS,card
DISCLAIMER="Research / risk-screening output — not a medical diagnosis."
class DoctorWindow(QMainWindow):
 def __init__(self):
  super().__init__();self.db=LocalDatabase();self.patient_mgr=PatientManager(self.db);self.bridge=EndoTwinBridgeServer(PROJECT_ROOT,7777);self.bridge.start();self.current_patient=None;self.setWindowTitle("ENDO-TWIN • Doctor Workstation • V8.5");self.resize(1480,920);self.setMinimumSize(1180,760);self.setStyleSheet(APP_QSS);self._build();self._refresh()
 def closeEvent(self,e):self.bridge.stop();e.accept()
 def _page(self,t,s):
  w=QWidget();o=QVBoxLayout(w);o.setContentsMargins(26,24,26,18);o.setSpacing(16);a=QLabel(t);a.setObjectName("title");o.addWidget(a);b=QLabel(s);b.setObjectName("muted");b.setWordWrap(True);o.addWidget(b);return w,o
 def _build(self):
  root=QWidget();self.setCentralWidget(root);shell=QGridLayout(root);shell.setContentsMargins(0,0,0,0)
  side=QFrame();side.setObjectName("sidebar");side.setFixedWidth(246);sl=QVBoxLayout(side);sl.setContentsMargins(20,24,20,20)
  a=QLabel("ENDO-TWIN");a.setObjectName("brand");sl.addWidget(a);b=QLabel("DOCTOR WORKSTATION");b.setObjectName("eyebrow");sl.addWidget(b);sl.addSpacing(18)
  self.nav={}
  for k,txt in [("dash","⌂  Dashboard"),("patients","◉  Patients"),("signals","∿  Signals"),("analysis","✦  Analysis"),("imaging","▣  Ultrasound"),("reports","▤  Reports"),("mobile","⌁  Mobile Link")]:
   q=QPushButton(txt);q.setObjectName("nav");q.setCheckable(True);q.clicked.connect(lambda checked=False,key=k:self._go(key));self.nav[k]=q;sl.addWidget(q)
  sl.addStretch();bc=QFrame();bc.setObjectName("hero");bl=QVBoxLayout(bc);x=QLabel("LOCAL BRIDGE");x.setObjectName("eyebrow");bl.addWidget(x);self.bridge_addr=QLabel(self.bridge.endpoint);self.bridge_addr.setObjectName("muted");self.bridge_addr.setWordWrap(True);bl.addWidget(self.bridge_addr);sl.addWidget(bc);shell.addWidget(side,0,0)
  right=QWidget();rv=QVBoxLayout(right);rv.setContentsMargins(0,0,0,0);rv.setSpacing(0);top=QFrame();top.setObjectName("topbar");tl=QHBoxLayout(top);tl.setContentsMargins(24,16,24,16);title=QLabel("Doctor review workspace");title.setObjectName("title");tl.addWidget(title);tl.addStretch();self.context=QLabel("No patient selected");self.context.setObjectName("muted");tl.addWidget(self.context);rv.addWidget(top)
  self.stack=QStackedWidget()
  for fn in [self._dashboard,self._patients,self._signals,self._analysis,self._imaging,self._reports,self._mobile]:self.stack.addWidget(fn())
  rv.addWidget(self.stack,1);foot=QLabel(f"{DISCLAIMER}  •  ENDO-TWIN V8.5  •  Local-first workstation");foot.setObjectName("muted");rv.addWidget(foot);shell.addWidget(right,0,1)
 def _dashboard(self):
  w,o=self._page("Today","See what is new, what is incomplete, and which patient workspace is active.");g=QGridLayout();self.stat=card("Patients","0","Visible local records");self.mobile_stat=card("Mobile inbox","0","Deliberately transferred packages");g.addWidget(self.stat,0,0);g.addWidget(card("Pending review","2 demo","Illustrative queue only"),0,1);g.addWidget(card("Signal quality","UNKNOWN","No live channel attached"),0,2);g.addWidget(self.mobile_stat,0,3);o.addLayout(g)
  h=QFrame();h.setObjectName("hero");hl=QVBoxLayout(h);e=QLabel("REVIEW FLOW");e.setObjectName("eyebrow");hl.addWidget(e);t=QLabel("Patient → observations → quality → baseline → longitudinal → research model → provenance → report");t.setWordWrap(True);t.setStyleSheet("font-size:18px;font-weight:750;color:#f2fbff;");hl.addWidget(t);p=QLabel("Observed/derived data, model-inferred outputs and UNKNOWN states remain distinct.");p.setObjectName("muted");p.setWordWrap(True);hl.addWidget(p);o.addWidget(h);self.preview=QListWidget();self.preview.setMaximumHeight(250);o.addWidget(self.preview,1);return w
 def _patients(self):
  w,o=self._page("Patients","Search and open one patient to lock the downstream workspace to that patient.");self.search=QLineEdit();self.search.setPlaceholderText("Search patient ID or alias…");self.search.textChanged.connect(self._refresh);o.addWidget(self.search);self.table=QTableWidget(0,5);self.table.setHorizontalHeaderLabels(["Patient","Age","BMI","Last activity","Status"]);self.table.horizontalHeader().setStretchLastSection(True);self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows);self.table.doubleClicked.connect(self._open_selected);o.addWidget(self.table,1);return w
 def _signals(self):
  w,o=self._page("Signals","Patient-specific measurements and derived features with quality/provenance context.");g=QGridLayout()
  for i,c in enumerate([card("Heart rate","72 bpm","MEASURED • illustrative DEMO_DATA"),card("HRV • RMSSD","48 ms","DERIVED • pulse-derived example"),card("Skin temperature","32.5 °C","MEASURED • illustrative DEMO_DATA"),card("Activity","35 %","DERIVED • illustrative motion index")]):g.addWidget(c,0,i)
  o.addLayout(g);b=QFrame();b.setObjectName("card");bl=QVBoxLayout(b);bl.addWidget(QLabel("PIPELINE"));d=QLabel("SENSOR → QUALITY → FILTERING → ARTIFACTS → FEATURES → STORAGE → BASELINE → LONGITUDINAL → MODEL → EXPLANATION → REPORT");d.setObjectName("muted");d.setWordWrap(True);bl.addWidget(d);o.addWidget(b);o.addStretch();return w
 def _analysis(self):
  w,o=self._page("Research analysis","Keep observations separate from disease-model inference and experimental constructs.");g=QGridLayout()
  for i,(a,b) in enumerate([("Personal baseline","Patient-specific reference from valid observations."),("Longitudinal change","Trend, persistence, recovery and quality context."),("CHRONO-PCOS","Disease-specific research module inside ENDO-TWIN."),("Uncertainty","Missing/low-quality inputs reduce usable evidence.")]):g.addWidget(card(a,"REVIEW",b),i//2,i%2)
  o.addLayout(g);o.addStretch();return w
 def _imaging(self):
  w,o=self._page("Ultrasound","Image-derived research workflow with conservative uncertainty.");box=QFrame();box.setObjectName("card");bl=QVBoxLayout(box)
  for x in ["IMAGE-DERIVED • source image → preprocessing → quality → features → uncertainty","UNKNOWN when no validated evidence supports an anatomical feature.","Missing/inapplicable model → insufficient/UNKNOWN, not a fabricated probability."]:z=QLabel(x);z.setObjectName("muted");z.setWordWrap(True);bl.addWidget(z)
  o.addWidget(box);o.addStretch();return w
 def _reports(self):
  w,o=self._page("Reports","Review-ready reports retain provenance, uncertainty and limitations.");box=QFrame();box.setObjectName("card");bl=QVBoxLayout(box);bl.addWidget(QLabel("Patient context • observations • quality • baseline • longitudinal change • model layer • image provenance • limitations"));q=QPushButton("Generate demo report");q.setObjectName("primary");q.clicked.connect(lambda:QMessageBox.information(self,"ENDO-TWIN",DISCLAIMER));bl.addWidget(q);o.addWidget(box);o.addStretch();return w
 def _mobile(self):
  w,o=self._page("Mobile Link","Pair Patient Android on the same Wi-Fi and receive deliberate local packages.");g=QGridLayout();g.addWidget(card("Address",self.bridge.endpoint,"Enter this in Patient Android → Connect"),0,0);g.addWidget(card("Pairing code",self.bridge.pair_code,"Six digits • regenerated on restart"),0,1);g.addWidget(card("Received",str(self.bridge.received_count),"Saved under data/bridge/inbox"),0,2);o.addLayout(g)
  q=QPushButton("Copy address + code");q.setObjectName("primary");q.clicked.connect(self._copy_pairing);o.addWidget(q);r=QPushButton("Restart bridge");r.setObjectName("secondary");r.clicked.connect(self._restart_bridge);o.addWidget(r);n=QLabel("Trusted-LAN research bridge. Production deployments need TLS, strong authentication/authorization, audit controls and security review.");n.setObjectName("muted");n.setWordWrap(True);o.addWidget(n);o.addStretch();return w
 def _go(self,k):
  self.stack.setCurrentIndex(list(self.nav).index(k))
  for n,b in self.nav.items():b.setChecked(n==k)
  if k=="mobile":self._refresh()
 def _refresh(self):
  try:ps=self.db.list_patients()
  except Exception:ps=[]
  if hasattr(self,"preview"):
   self.preview.clear()
   for p in ps[:8]:self.preview.addItem(f"{p.get('anonymous_id','unknown')}  •  age {p.get('age_years','—')}  •  BMI {p.get('bmi','—')}")
  if hasattr(self,"table"):
   q=self.search.text().lower();self.table.setRowCount(0)
   for p in ps[:100]:
    line=" ".join(str(p.get(k,"")) for k in ("anonymous_id","display_name","age_years","bmi")).lower()
    if q and q not in line:continue
    row=self.table.rowCount();self.table.insertRow(row);item=QTableWidgetItem(str(p.get("anonymous_id","unknown")));item.setData(Qt.ItemDataRole.UserRole,str(p.get("patient_id","")));self.table.setItem(row,0,item)
    for c,v in enumerate([p.get("age_years","—"),p.get("bmi","—"),p.get("updated_at","—"),"LOCAL/DEMO"],1):self.table.setItem(row,c,QTableWidgetItem(str(v)))
 def _open_selected(self):
  if not self.table.selectedItems():return
  pid=self.table.item(self.table.currentRow(),0).data(Qt.ItemDataRole.UserRole)
  if not pid:return
  self.current_patient=self.patient_mgr.open_patient(pid);self.context.setText("Patient context • "+(self.current_patient.get("anonymous_id",pid) if self.current_patient else pid));self._go("signals")
 def _copy_pairing(self):
  QApplication.clipboard().setText(self.bridge.endpoint+"\nPairing code: "+self.bridge.pair_code);QMessageBox.information(self,"Mobile Link","Address and code copied.")
 def _restart_bridge(self):
  self.bridge.stop();self.bridge=EndoTwinBridgeServer(PROJECT_ROOT,7777)
  try:self.bridge.start()
  except OSError as e:QMessageBox.warning(self,"Bridge","Could not restart bridge: "+str(e));return
  self.bridge_addr.setText(self.bridge.endpoint);self._refresh()
def run():
 if not PYSIDE_AVAILABLE:print("PySide6 is required for ENDO-TWIN Doctor Workstation.");return 1
 app=QApplication(sys.argv);app.setStyle("Fusion");w=DoctorWindow();w.show();return app.exec()
if __name__=="__main__":raise SystemExit(run())
