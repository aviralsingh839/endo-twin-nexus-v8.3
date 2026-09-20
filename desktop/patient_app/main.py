#!/usr/bin/env python3
"""ENDO-TWIN V8.6 Patient Workstation."""
from __future__ import annotations
import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication,QFrame,QGridLayout,QHBoxLayout,QLabel,QMainWindow,QMessageBox,QPushButton,QStackedWidget,QVBoxLayout,QWidget
ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from desktop.demo_data import DEMO_CASES
from desktop.workstation_runtime import LiveSession,ModeConfig,Sparkline,choose_mode
from desktop.workstation_theme import APP_QSS,card,section_header
from services.bridge.server import EndoTwinBridgeServer
DISCLAIMER="Research / risk-screening output — not a medical diagnosis."

class PatientWindow(QMainWindow):
    def __init__(self,mode:ModeConfig):
        super().__init__(); self.mode=mode; self.case=DEMO_CASES[0]; self.metric_labels={}
        self.bridge=EndoTwinBridgeServer(ROOT,7778); self.bridge.start()
        self.session=LiveSession(mode,self); self.session.features_updated.connect(self._on_features); self.session.state_changed.connect(self._on_state); self.session.error_received.connect(self._on_error); self.session.start()
        self.setWindowTitle("ENDO-TWIN • Patient Workstation • V8.6"); self.resize(1400,900); self.setMinimumSize(1080,720); self.setStyleSheet(APP_QSS); self._build()
    def closeEvent(self,e): self.session.stop(); self.bridge.stop(); e.accept()
    def _page(self,title,sub):
        w=QWidget(); o=QVBoxLayout(w); o.setContentsMargins(28,24,28,18); o.setSpacing(14); a=QLabel(title); a.setObjectName("title"); o.addWidget(a); b=QLabel(sub); b.setObjectName("muted"); b.setWordWrap(True); o.addWidget(b); return w,o
    def _build(self):
        root=QWidget(); self.setCentralWidget(root); shell=QGridLayout(root); shell.setContentsMargins(0,0,0,0)
        side=QFrame(); side.setObjectName("sidebar"); side.setFixedWidth(238); sl=QVBoxLayout(side); sl.setContentsMargins(20,22,20,20); sl.setSpacing(5); brand=QLabel("ENDO-TWIN"); brand.setObjectName("brand"); sl.addWidget(brand); tag=QLabel("PATIENT WORKSTATION • V8.6"); tag.setObjectName("eyebrow"); sl.addWidget(tag); sl.addSpacing(14)
        self.nav={}
        for key,text in [("home","◈  Overview"),("health","♥  My Health"),("measure","∿  Measurements"),("timeline","◷  Timeline"),("connect","⌁  Connect"),("reports","▤  Reports")]:
            b=QPushButton(text); b.setObjectName("nav"); b.setCheckable(True); b.clicked.connect(lambda _=False,k=key:self._go(k)); self.nav[key]=b; sl.addWidget(b)
        sl.addStretch(); box=QFrame(); box.setObjectName("hero"); bl=QVBoxLayout(box); bl.setContentsMargins(13,12,13,12); x=QLabel("SESSION"); x.setObjectName("eyebrow"); bl.addWidget(x); self.mode_label=QLabel(); self.mode_label.setObjectName("subtitle"); bl.addWidget(self.mode_label); self.state_label=QLabel(); self.state_label.setObjectName("muted"); self.state_label.setWordWrap(True); bl.addWidget(self.state_label); sl.addWidget(box); shell.addWidget(side,0,0)
        right=QWidget(); rv=QVBoxLayout(right); rv.setContentsMargins(0,0,0,0); top=QFrame(); top.setObjectName("topbar"); tl=QHBoxLayout(top); tl.setContentsMargins(24,13,24,13); t=QLabel("Your physiological workspace"); t.setObjectName("subtitle"); t.setStyleSheet("font-size:16px;font-weight:850;"); tl.addWidget(t); tl.addStretch(); self.mode_badge=QLabel(); tl.addWidget(self.mode_badge); rv.addWidget(top)
        self.stack=QStackedWidget(); self.pages=[self._home(),self._health(),self._measure(),self._timeline(),self._connect(),self._reports()]; [self.stack.addWidget(x) for x in self.pages]; rv.addWidget(self.stack,1); foot=QLabel(f"{DISCLAIMER}  •  Patient-scoped  •  Local-first  •  Startup mode is fixed for this run"); foot.setObjectName("muted"); rv.addWidget(foot); shell.addWidget(right,0,1); self._go("home"); self._refresh_mode()
    def _refresh_mode(self):
        live=self.mode.mode=="live"; self.mode_label.setText("LIVE SENSOR" if live else "DEMO DATA"); self.state_label.setText(self.mode.port if live else "Synthetic showcase stream"); self.mode_badge.setText("LIVE • USB" if live else "DEMO • SYNTHETIC"); self.mode_badge.setStyleSheet("background:#123e36;color:#7ce5c2;border:1px solid #1e6c5b;border-radius:10px;padding:7px 11px;font-weight:850;" if live else "background:#162f4a;color:#86d8ff;border:1px solid #245878;border-radius:10px;padding:7px 11px;font-weight:850;")
    def _go(self,key):
        keys=list(self.nav); self.stack.setCurrentIndex(keys.index(key)); [b.setChecked(k==key) for k in self.nav.values()]
    def _home(self):
        w,o=self._page("Overview","One patient, one stream, one timeline. Measurements and model layers stay visibly separate."); g=QGridLayout()
        for a,b,c in [("Heart rate","—","processed from PPG"),("HRV RMSSD","—","cleaned beat-to-beat intervals"),("SpO₂","—","research estimate; quality-gated"),("Signal quality","—","channel-aware quality gate")]: f=card(a,b,c); g.addWidget(f,0,g.count()); self.metric_labels[a]=f.findChildren(QLabel)[1]
        o.addLayout(g); self.home_chart=Sparkline("Heart rate","bpm","#54d8f5"); o.addWidget(self.home_chart); o.addWidget(section_header("How to read this","A measured sensor channel is different from a derived feature and different again from a disease-model output. Missing or low-quality data remain missing.")); o.addWidget(card("Disease-model layer","CHRONO-PCOS" if self.mode.mode=="demo" else "NOT RUN","Disease-specific research module inside ENDO-TWIN • not a diagnosis")); return w
    def _health(self):
        w,o=self._page("My Health","Longitudinal context grows from repeated observations instead of one isolated reading."); g=QGridLayout()
        for a,b,c in [("Personal baseline","Building","Needs repeated observations"),("Recovery","—","Not inferred on this screen"),("Activity","—","IMU-derived activity index"),("Skin temperature","—","Validity-gated temperature")]: f=card(a,b,c); g.addWidget(f,0,g.count()); self.metric_labels[a]=f.findChildren(QLabel)[1]
        o.addLayout(g); o.addWidget(section_header("Provenance","MEASURED • DERIVED • PATIENT-REPORTED • IMAGE-DERIVED • MODEL-INFERRED • DEMO_DATA • UNKNOWN")); o.addStretch(); return w
    def _measure(self):
        w,o=self._page("Measurements","The same packet and processing path is used for demo and live sessions. Only the source changes."); g=QGridLayout()
        for i,(a,b,c) in enumerate([("PPG","20 Hz packet stream","IR + red"),("IMU","20 Hz packet stream","accelerometer + gyro"),("GSR","10 Hz source","raw conductance proxy"),("Temperature","1 Hz source","validity-gated")]): g.addWidget(card(a,b,c),0,i)
        o.addLayout(g); self.live_chart=Sparkline("Motion / activity","%","#f4b85b"); o.addWidget(self.live_chart); self.measure_status=QLabel("Waiting…"); self.measure_status.setObjectName("muted"); o.addWidget(self.measure_status); o.addStretch(); return w
    def _timeline(self):
        w,o=self._page("Timeline","Chronological events and sessions remain patient-scoped.")
        for a,b in [("Current session","LIVE SENSOR" if self.mode.mode=="live" else "DEMO_DATA"),("Sensor pipeline","raw packet → CRC → filtering → features → quality"),("Disease model","CHRONO-PCOS is available as a research module"),("Ultrasound","UNKNOWN until a validated image pipeline supports an output")]: o.addWidget(card(a,"ACTIVE",b))
        o.addStretch(); return w
    def _connect(self):
        w,o=self._page("Connect","Pair this Patient Workstation with a Doctor Workstation on the same trusted LAN."); g=QGridLayout(); g.addWidget(card("This workstation",self.bridge.endpoint,"Patient bridge • port 7778"),0,0); g.addWidget(card("Doctor bridge","Port 7777","Use Doctor → Mobile Link for address and code"),0,1); g.addWidget(card("Packages received",str(self.bridge.received_count),"Bridge inbox"),0,2); o.addLayout(g); b=QPushButton("Copy patient endpoint"); b.setObjectName("primary"); b.clicked.connect(lambda:(QApplication.clipboard().setText(self.bridge.endpoint),QMessageBox.information(self,"Connect","Endpoint copied."))); o.addWidget(b); note=QLabel("Transport is research LAN infrastructure. Production health systems require encrypted transport, strong authentication, authorization and audit logging."); note.setObjectName("muted"); note.setWordWrap(True); o.addWidget(note); o.addStretch(); return w
    def _reports(self):
        w,o=self._page("Reports","Reports preserve source, quality, uncertainty and the non-clinical validation status of this prototype."); o.addWidget(card("Report layers","OBSERVATIONS → QUALITY → BASELINE → LONGITUDINAL → MODEL → LIMITATIONS","A report should never convert an estimate into a measurement.")); b=QPushButton("Generate demo report"); b.setObjectName("primary"); b.clicked.connect(lambda:QMessageBox.information(self,"ENDO-TWIN","Demo report created. Synthetic values remain marked DEMO_DATA.")); o.addWidget(b); o.addStretch(); return w
    def _on_state(self,state):
        self.state_label.setText(state.upper().replace("_"," ")) if hasattr(self,"state_label") else None
    def _on_error(self,msg):
        self.state_label.setText("ERROR • "+msg) if hasattr(self,"state_label") else None
    def _on_features(self,row):
        if not hasattr(self,"measure_status"): return
        def fmt(v,suf="",d=1): return "—" if v is None else f"{float(v):.{d}f}{suf}"
        vals={"Heart rate":fmt(row.get("hr_bpm")," bpm",0),"HRV RMSSD":fmt(row.get("rmssd_ms")," ms"),"SpO₂":fmt(row.get("spo2_pct")," %"),"Signal quality":f"{float(row.get('signal_quality') or 0)*100:.0f}%","Activity":f"{float(row.get('activity_level') or 0):.0f}%","Skin temperature":fmt(row.get("skin_temp_c")," °C")}
        for k,v in vals.items():
            if k in self.metric_labels: self.metric_labels[k].setText(v)
        self.home_chart.set_value(row.get("hr_bpm")); self.live_chart.set_value(row.get("activity_level")); self.measure_status.setText(f"{row.get('gating','QUALITY_GATE')} • {row.get('provenance','UNKNOWN')} • {len(row.get('status_flags',[]))} status flag(s)")
def run():
    app=QApplication(sys.argv); app.setStyle("Fusion"); mode=choose_mode("ENDO-TWIN • Patient Workstation")
    if mode is None: return 0
    w=PatientWindow(mode); w.show(); return app.exec()
if __name__=="__main__": raise SystemExit(run())
