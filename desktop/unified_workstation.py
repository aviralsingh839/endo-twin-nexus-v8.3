#!/usr/bin/env python3
"""ENDO-TWIN NEXUS V8.7 unified Patient + Doctor + Prototype Lab workstation."""
from __future__ import annotations
import math, sys, time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDialog, QDialogButtonBox,
    QDoubleSpinBox, QFileDialog, QFormLayout, QFrame, QGridLayout,
    QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMessageBox,
    QPushButton, QSpinBox, QStackedWidget, QTableWidget, QTableWidgetItem,
    QTextEdit, QVBoxLayout, QWidget,
)

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from database.database import LocalDatabase
from src.core.feature_extraction import RealtimeFeatureExtractor
from src.disease_modules.pcos import PCOSModule
from src.serial_io.arduino_reader import ArduinoReader
from src.utils.demo_stream import DemoSensorStream
from desktop.unified_engine import DISCLAIMER, context_ready, compute_research_index
from desktop.model_lab import ModelLabWidget

APP_QSS = """
QWidget{background:#07111f;color:#edf5f9;font-family:"Noto Sans","DejaVu Sans",sans-serif;}
QFrame#sidebar{background:#0b1725;border-right:1px solid #173149;}
QFrame#topbar{background:#8e93bc;border-bottom:1px solid #a9abd0;}
QFrame#card{background:#0c1c2b;border:1px solid #1c3850;border-radius:14px;}
QFrame#hero{background:#10283a;border:1px solid #285875;border-radius:16px;}
QLabel#brand{font-size:19px;font-weight:900;color:#f8fbff;}
QLabel#eyebrow{font-size:10px;font-weight:850;letter-spacing:1px;color:#7dbcd5;}
QLabel#muted{color:#98aaba;font-size:11px;}
QLabel#title{font-size:25px;font-weight:900;color:#f5f9fc;}
QLabel#value{font-size:23px;font-weight:900;color:#f7fbff;}
QLabel#risk{font-size:42px;font-weight:950;color:#73e0cf;}
QLabel#warning{background:#392b18;color:#f1c46d;border:1px solid #684f27;border-radius:10px;padding:9px;}
QPushButton#nav{background:transparent;border:0;border-radius:9px;padding:10px 12px;text-align:left;color:#bdcddb;font-weight:750;}
QPushButton#nav:hover{background:#11283a;color:#fff;}
QPushButton#nav:checked{background:#17384e;color:#72d7e7;border-left:3px solid #46cadf;}
QPushButton#primary{background:#28b5d4;color:#04131c;border:0;border-radius:10px;padding:10px 14px;font-weight:900;}
QPushButton#secondary{background:#0f2435;color:#d6e6ee;border:1px solid #294a61;border-radius:10px;padding:9px 13px;font-weight:750;}
QLineEdit,QComboBox,QSpinBox,QDoubleSpinBox,QTextEdit{background:#091725;color:#ecf4f8;border:1px solid #244158;border-radius:9px;padding:8px;}
QTableWidget{background:#091725;border:1px solid #1a364d;gridline-color:#173149;selection-background-color:#173e55;}
QHeaderView::section{background:#102638;color:#9eb7c4;border:0;padding:7px;font-weight:800;}
"""

@dataclass
class LiveConfig:
    mode: str
    source: str
    port: str = ""
    host: str = ""
    tcp_port: int = 7777
    baud: int = 115200

class StartupDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ENDO-TWIN NEXUS V8.7 — choose data mode")
        self.setMinimumWidth(720); self.setStyleSheet(APP_QSS); self.config = None
        v=QVBoxLayout(self)
        h=QLabel("Choose the data source before the workstation opens"); h.setObjectName("title"); v.addWidget(h)
        n=QLabel("DEMO uses synthetic labelled data. LIVE uses the same processing chain from an ESP32-S3 wearable or Arduino Mega USB stream. The choice is fixed for the run.")
        n.setObjectName("muted"); n.setWordWrap(True); v.addWidget(n)
        row=QHBoxLayout()
        demo=QPushButton("Open DEMO MODE"); demo.setObjectName("primary"); demo.clicked.connect(self._demo); row.addWidget(demo)
        live=QPushButton("Configure LIVE SENSOR MODE"); live.setObjectName("primary"); live.clicked.connect(self._live); row.addWidget(live)
        v.addLayout(row)
        self.live_box=QFrame(); self.live_box.setObjectName("card"); f=QFormLayout(self.live_box)
        self.port=QLineEdit(); self.port.setPlaceholderText("Auto-detect /dev/ttyACM0, /dev/ttyUSB0 or COM3")
        self.detect=QPushButton("Auto-detect USB"); self.detect.setObjectName("primary"); self.detect.clicked.connect(self.auto_detect_port)
        self.refresh=QPushButton("Refresh"); self.refresh.setObjectName("secondary"); self.refresh.clicked.connect(self.auto_detect_port)
        port_row=QHBoxLayout(); port_row.addWidget(self.port,1); port_row.addWidget(self.detect); port_row.addWidget(self.refresh)
        f.addRow("USB port",port_row)
        self.status=QLabel("Scanning for ESP32-S3 / Arduino Mega..."); self.status.setObjectName("muted"); self.status.setWordWrap(True)
        f.addRow("Detection",self.status)
        self.baud=QSpinBox(); self.baud.setRange(1200,1000000); self.baud.setValue(115200)
        f.addRow("Baud",self.baud)
        ok=QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Ok)
        ok.accepted.connect(self._accept_live); ok.rejected.connect(self.reject); f.addRow(ok); v.addWidget(self.live_box)
        self.auto_detect_port()
    def auto_detect_port(self):
        ports=ArduinoReader.available_ports()
        if not ports:
            self.port.clear()
            self.status.setText("No USB serial device detected. Connect the ESP32-S3 wearable or Arduino Mega and click Auto-detect USB.")
            return
        preferred=[p for p in ports if "/ttyACM" in p or "/ttyUSB" in p or p.upper().startswith("COM")]
        selected=preferred[0] if preferred else ports[0]
        self.port.setText(selected)
        self.status.setText(f"Auto-detected USB serial device: {selected}")
    def _demo(self):
        self.config=LiveConfig("demo","demo"); self.accept()
    def _live(self):
        self.live_box.setFocus()
    def _accept_live(self):
        if not self.port.text().strip():
            self.auto_detect_port()
        if not self.port.text().strip():
            QMessageBox.warning(self,"LIVE mode","No USB serial device detected. Connect the ESP32-S3 or Arduino Mega and try Auto-detect USB."); return
        self.config=LiveConfig("live","usb",port=self.port.text().strip(),baud=self.baud.value())
        self.accept()

class Session(QObject):
    sample_ready=Signal(object); feature_ready=Signal(object); state_ready=Signal(str); error_ready=Signal(str)
    def __init__(self,cfg,parent=None):
        super().__init__(parent); self.cfg=cfg; self.reader=None; self.extractor=RealtimeFeatureExtractor()
        self.samples=0; self.packet_errors=0; self._last_feature=0.0; self.started=time.monotonic()
    def start(self):
        self.stop(); self.extractor=RealtimeFeatureExtractor(); self.samples=0; self.packet_errors=0; self._last_feature=0.0; self.started=time.monotonic()
        if self.cfg.mode=="demo": self.reader=DemoSensorStream(fs_hz=20.0,parent=self)
        else: self.reader=ArduinoReader(self.cfg.port,self.cfg.baud,require_crc=True,parent=self)
        self.reader.sample_received.connect(self._on_sample); self.reader.state_changed.connect(self.state_ready); self.reader.error_received.connect(self._on_error); self.reader.start()
    def stop(self):
        if self.reader:
            try: self.reader.stop()
            except Exception: pass
        self.reader=None
    def command(self,c):
        if self.reader and hasattr(self.reader,"write_command"): self.reader.write_command(c)
    def _on_sample(self,s):
        self.samples+=1; self.extractor.add_sample(s); self.sample_ready.emit(s)
        now=time.monotonic()
        if now-self._last_feature>=0.5:
            self._last_feature=now
            try:
                f=self.extractor.compute(); setattr(f,"_source",getattr(s,"source",None)); self.feature_ready.emit(f)
            except Exception as e: self._on_error(f"Feature computation failed: {type(e).__name__}: {e}")
    def _on_error(self,msg):
        if "Packet parse error" in msg or "crc" in msg.lower(): self.packet_errors+=1
        self.error_ready.emit(msg)

class AddPatientDialog(QDialog):
    def __init__(self,parent=None):
        super().__init__(parent); self.setWindowTitle("Add Patient"); self.setMinimumWidth(460); self.setStyleSheet(APP_QSS); f=QFormLayout(self)
        self.alias=QLineEdit(); self.anon=QLineEdit(); self.age=QDoubleSpinBox(); self.age.setRange(1,120); self.age.setValue(23)
        self.bmi=QDoubleSpinBox(); self.bmi.setRange(0,80); self.bmi.setDecimals(1); self.bmi.setValue(24)
        self.cycle=QComboBox(); self.cycle.addItems(["Unknown","Regular","Irregular"]); self.clen=QSpinBox(); self.clen.setRange(0,120); self.clen.setSpecialValueText("Unknown"); self.clen.setValue(28)
        self.ypm=QDoubleSpinBox(); self.ypm.setRange(0,80); self.ypm.setDecimals(1); self.ypm.setSpecialValueText("Unknown")
        self.hyper=QCheckBox("Hyperandrogenism evidence"); self.pcom=QCheckBox("PCOM / equivalent clinical evidence"); self.excl=QCheckBox("Relevant exclusions completed")
        self.glucose=QDoubleSpinBox(); self.glucose.setRange(0,600); self.glucose.setDecimals(1); self.glucose.setSpecialValueText("Unknown")
        for label,w in [("Alias",self.alias),("Anonymous ID",self.anon),("Age",self.age),("BMI",self.bmi),("Cycle",self.cycle),("Typical cycle length",self.clen),("Years post-menarche",self.ypm),("",self.hyper),("",self.pcom),("",self.excl),("Glucose mg/dL",self.glucose)]: f.addRow(label,w)
        b=QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Ok); b.accepted.connect(self.accept); b.rejected.connect(self.reject); f.addRow(b)
    def values(self):
        c=self.cycle.currentText()
        return {"display_name":self.alias.text().strip() or None,"anonymous_id":self.anon.text().strip() or None,"age_years":self.age.value(),"bmi":self.bmi.value() or None,"cycle_irregular":True if c=="Irregular" else False if c=="Regular" else None,"cycle_length":self.clen.value() or None,"years_post_menarche":self.ypm.value() or None,"hyperandrogenism":self.hyper.isChecked(),"pcom_present":self.pcom.isChecked(),"exclusions_completed":self.excl.isChecked(),"glucose_mg_dl":self.glucose.value() or None}

class UnifiedWorkstation(QMainWindow):
    def __init__(self,cfg):
        super().__init__(); self.cfg=cfg; self.db=LocalDatabase(); self.pcos=PCOSModule(); self.current=None; self.latest=None; self.test_active=False; self.test_rows=[]; self.test_features=[]; self.test_start=0.0
        self.setWindowTitle("ENDO-TWIN NEXUS — V8.7 Unified Workstation"); self.resize(1580,940); self.setMinimumSize(1180,760); self.setStyleSheet(APP_QSS)
        self.session=Session(cfg,self); self.session.sample_ready.connect(self._on_sample); self.session.feature_ready.connect(self._on_feature); self.session.state_ready.connect(self._on_state); self.session.error_ready.connect(self._on_error)
        self._build(); self._seed_demo(); self._refresh_roster(); self.session.start(); self._timer=QTimer(self); self._timer.timeout.connect(self._tick); self._timer.start(250)
    def closeEvent(self,e): self.session.stop(); self.db.close(); e.accept()
    def _build(self):
        root=QWidget(); shell=QGridLayout(root); shell.setContentsMargins(0,0,0,0); shell.setSpacing(0); self.setCentralWidget(root)
        side=QFrame(); side.setObjectName("sidebar"); side.setFixedWidth(215); sv=QVBoxLayout(side); sv.setContentsMargins(14,18,10,16)
        b=QLabel("Endo-Twin Nexus"); b.setObjectName("brand"); sv.addWidget(b); x=QLabel("UNIFIED WORKSTATION"); x.setObjectName("eyebrow"); sv.addWidget(x); d=QLabel("Patient + Doctor + Prototype Lab"); d.setObjectName("muted"); sv.addWidget(d); sv.addSpacing(15)
        self.nav={}; 
        for k,t in [("patient","◉  Patient"),("doctor","♙  Doctor"),("lab","⌁  Prototype Lab"),("model","⌁  Model Lab"),("settings","⚙  Settings")]:
            q=QPushButton(t); q.setObjectName("nav"); q.setCheckable(True); q.clicked.connect(lambda _,kk=k:self._go(kk)); self.nav[k]=q; sv.addWidget(q)
        sv.addStretch(); m=QFrame(); m.setObjectName("hero"); mv=QVBoxLayout(m); e=QLabel("SESSION"); e.setObjectName("eyebrow"); mv.addWidget(e); self.mode_lbl=QLabel(); self.mode_lbl.setObjectName("value"); mv.addWidget(self.mode_lbl); self.state_lbl=QLabel("starting"); self.state_lbl.setObjectName("muted"); mv.addWidget(self.state_lbl); sv.addWidget(m); shell.addWidget(side,0,0)
        right=QWidget(); rv=QVBoxLayout(right); rv.setContentsMargins(0,0,0,0); rv.setSpacing(0)
        top=QFrame(); top.setObjectName("topbar"); tv=QHBoxLayout(top); tv.setContentsMargins(16,7,16,7); brand=QLabel("ENDO-TWIN"); brand.setStyleSheet("font-size:16px;font-weight:900;color:#fff;"); tv.addWidget(brand); sub=QLabel("Personalized Physiological Modelling Platform"); sub.setStyleSheet("color:#e8eaff;font-size:10px;font-weight:700;"); tv.addWidget(sub); tv.addStretch(); self.patient_lbl=QLabel("No patient"); self.patient_lbl.setStyleSheet("color:#fff;font-weight:850;"); tv.addWidget(self.patient_lbl); self.quality=QLabel("Quality —"); self.quality.setStyleSheet("color:#fff;"); tv.addWidget(self.quality); rv.addWidget(top)
        self.stack=QStackedWidget(); rv.addWidget(self.stack,1); shell.addWidget(right,0,1)
        self.stack.addWidget(self._patient_page()); self.stack.addWidget(self._doctor_page()); self.stack.addWidget(self._lab_page()); self.stack.addWidget(ModelLabWidget(ROOT)); self.stack.addWidget(self._settings_page()); self._go("patient")
    def _card(self,t,val="—",detail=""):
        f=QFrame(); f.setObjectName("card"); v=QVBoxLayout(f); v.addWidget(QLabel(t)); q=v.itemAt(0).widget(); q.setObjectName("eyebrow"); z=QLabel(str(val)); z.setObjectName("value"); v.addWidget(z); m=QLabel(detail); m.setObjectName("muted"); m.setWordWrap(True); v.addWidget(m); return f
    def _patient_page(self):
        p=QWidget(); v=QVBoxLayout(p); v.setContentsMargins(18,16,18,16); t=QLabel("Patient Workspace"); t.setObjectName("title"); v.addWidget(t)
        w=QLabel(DISCLAIMER); w.setObjectName("warning"); w.setWordWrap(True); v.addWidget(w)
        self.risk=QLabel("UNKNOWN"); self.risk.setObjectName("risk"); self.reason=QLabel("Select a patient and satisfy the evidence gate."); self.reason.setObjectName("muted"); self.reason.setWordWrap(True)
        hero=QFrame(); hero.setObjectName("hero"); hv=QVBoxLayout(hero); hv.addWidget(QLabel("CHRONO-PCOS RESEARCH INDEX")); hv.addWidget(self.risk); hv.addWidget(self.reason); v.addWidget(hero)
        grid=QGridLayout(); self.metrics={}
        for i,(k,t,d) in enumerate([("hr_bpm","Heart rate","PPG/ECG derived when valid"),("rmssd_ms","HRV RMSSD","PPG-derived; not ECG-equivalent"),("skin_temp_c","Skin temperature","Measured channel"),("activity_level","Activity","IMU derived"),("signal_quality","Signal quality","0–1 engineering quality")]):
            self.metrics[k]=self._card(t); grid.addWidget(self.metrics[k],i//3,i%3)
        v.addLayout(grid); c=QFrame(); c.setObjectName("card"); cv=QVBoxLayout(c); h=QHBoxLayout(); h.addWidget(QLabel("Patient context")); h.addStretch(); e=QPushButton("Edit / enter clinical context"); e.setObjectName("secondary"); e.clicked.connect(self._edit_current); h.addWidget(e); cv.addLayout(h); self.context=QLabel("—"); self.context.setObjectName("muted"); self.context.setWordWrap(True); cv.addWidget(self.context); v.addWidget(c); self.timeline=QTextEdit(); self.timeline.setReadOnly(True); self.timeline.setMaximumHeight(135); v.addWidget(self.timeline); return p
    def _doctor_page(self):
        p=QWidget(); v=QVBoxLayout(p); v.setContentsMargins(18,16,18,16); h=QHBoxLayout(); t=QLabel("Doctor Workspace"); t.setObjectName("title"); h.addWidget(t); h.addStretch(); a=QPushButton("+ Add Patient"); a.setObjectName("primary"); a.clicked.connect(self._add_patient); h.addWidget(a); v.addLayout(h); n=QLabel("Shared local registry. Selecting a row changes the Patient workspace and research context."); n.setObjectName("muted"); n.setWordWrap(True); v.addWidget(n)
        self.roster=QTableWidget(0,7); self.roster.setHorizontalHeaderLabels(["ID","Alias","Age","BMI","Cycle","Gate","Updated"]); self.roster.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows); self.roster.cellClicked.connect(lambda r,_:self._select(r)); v.addWidget(self.roster,1); self.doctor_summary=QTextEdit(); self.doctor_summary.setReadOnly(True); self.doctor_summary.setMaximumHeight(170); v.addWidget(self.doctor_summary); return p
    def _lab_page(self):
        p=QWidget(); v=QVBoxLayout(p); v.setContentsMargins(18,16,18,16); t=QLabel("Prototype Lab"); t.setObjectName("title"); v.addWidget(t); n=QLabel("Bench engineering only. PASS = software received/processed a plausible channel. It does not prove calibration or medical validity."); n.setObjectName("warning"); n.setWordWrap(True); v.addWidget(n)
        r=QHBoxLayout(); self.lab_packets=self._card("Packets","0","Current session"); self.lab_rate=self._card("Rate","—","Observed packet input"); self.lab_q=self._card("Quality","—","Realtime feature quality"); [r.addWidget(x,1) for x in (self.lab_packets,self.lab_rate,self.lab_q)]; v.addLayout(r)
        c=QHBoxLayout()
        for label,cmd in [("PING","PING"),("LED green","LED,G"),("BEEP","BEEP")]:
            b=QPushButton(label); b.setObjectName("secondary"); b.clicked.connect(lambda _,cc=cmd:self.session.command(cc)); c.addWidget(b)
        c.addStretch(); self.test_btn=QPushButton("Run 15 s acceptance test"); self.test_btn.setObjectName("primary"); self.test_btn.clicked.connect(self._start_test); c.addWidget(self.test_btn); ex=QPushButton("Export report"); ex.setObjectName("secondary"); ex.clicked.connect(self._export_test); c.addWidget(ex); v.addLayout(c)
        self.modules=QTableWidget(8,4); self.modules.setHorizontalHeaderLabels(["Module","Signal","State","Meaning"]); names=[("MAX30102 PPG","—","NOT TESTED","IR/RED waveform"),("MPU6050 IMU","—","NOT TESTED","accel/gyro"),("DS18B20","—","NOT TESTED","temperature"),("AD8232 ECG","—","OPTIONAL","raw ECG / lead-off"),("FSR","—","OPTIONAL","contact context"),("MAX4466","—","OPTIONAL","RMS/pitch"),("BH1750/BME280","—","OPTIONAL","environment")]
        for r0,row in enumerate(names):
            for c0,val in enumerate(row): self.modules.setItem(r0,c0,QTableWidgetItem(val))
        v.addWidget(self.modules,1); self.lab_log=QTextEdit(); self.lab_log.setReadOnly(True); self.lab_log.setMaximumHeight(155); v.addWidget(self.lab_log); return p
    def _settings_page(self):
        p=QWidget(); v=QVBoxLayout(p); v.setContentsMargins(18,16,18,16); t=QLabel("Settings"); t.setObjectName("title"); v.addWidget(t); q=QLabel("Restart to change DEMO/LIVE or the live transport. Research bridge is LAN-only."); q.setObjectName("muted"); q.setWordWrap(True); v.addWidget(q); box=QFrame(); box.setObjectName("card"); bv=QVBoxLayout(box); bv.addWidget(QLabel(f"Mode: {self.cfg.mode.upper()}")); bv.addWidget(QLabel(f"Source: {self.cfg.source}")); bv.addWidget(QLabel(f"Baud: {self.cfg.baud}")); bv.addWidget(QLabel("Active live hardware: ESP32-S3 wearable or Arduino Mega lab controller over USB. ESP32-S3 is legacy only.")); v.addWidget(box); v.addStretch(); return p
    def _go(self,k): self.stack.setCurrentIndex(["patient","doctor","lab","model","settings"].index(k)); [b.setChecked(kk==k) for kk,b in self.nav.items()]
    def _seed_demo(self):
        if self.cfg.mode=="demo": self.current={"patient_id":"DEMO-021","anonymous_id":"DEMO-021","display_name":"Mira","age_years":23.0,"bmi":24.7,"cycle_irregular":True,"cycle_length":42,"years_post_menarche":10,"hyperandrogenism":True,"pcom_present":False,"exclusions_completed":True,"glucose_mg_dl":98.0,"demo":True}
    def _enrich(self,p):
        out=dict(p); pid=out.get("patient_id")
        if pid:
            try:
                row=self.db.conn.execute("SELECT data_json FROM profiles WHERE patient_id=? ORDER BY updated_at DESC LIMIT 1",(pid,)).fetchone()
                if row and row[0]:
                    import json; data=json.loads(row[0]); out.update(data if isinstance(data,dict) else {})
            except Exception: pass
        return out
    def _refresh_roster(self):
        if not hasattr(self,"roster"): return
        rows=[]; 
        if self.current and self.current.get("demo"): rows.append(self.current)
        try: rows += [self._enrich(p) for p in self.db.list_patients()]
        except Exception: pass
        self._rows=rows; self.roster.setRowCount(len(rows))
        for r,p in enumerate(rows):
            ok,_=context_ready(p); cyc="Irregular" if p.get("cycle_irregular") is True else "Regular" if p.get("cycle_irregular") is False else "Unknown"
            vals=[p.get("anonymous_id","—"),p.get("display_name") or "—",p.get("age_years","—"),p.get("bmi","—"),cyc,"READY" if ok else "INCOMPLETE",datetime.fromtimestamp(p.get("updated_at",time.time())).strftime("%Y-%m-%d %H:%M")]
            for c,x in enumerate(vals): self.roster.setItem(r,c,QTableWidgetItem(str(x)))
        self.roster.resizeColumnsToContents()
    def _select(self,row): self.current=self._enrich(self._rows[row]); self._refresh_current(); self._go("patient")
    def _add_patient(self):
        d=AddPatientDialog(self)
        if d.exec()!=QDialog.DialogCode.Accepted:return
        val=d.values()
        try:
            pid=self.db.create_patient(display_name=val["display_name"],age_years=val["age_years"],bmi=val["bmi"],anonymous_id=val["anonymous_id"])
            import json; now=time.time(); self.db.conn.execute("INSERT INTO profiles(profile_id,patient_id,data_json,label,created_at,updated_at) VALUES(?,?,?,?,?,?)",(f"profile-{pid}",pid,json.dumps(val),"CLINICALLY-ENTERED",now,now)); self.db.conn.commit()
            self.current=self._enrich(self.db.get_patient(pid)); self.current.update(val); self._refresh_roster(); self._refresh_current(); self._go("patient")
        except Exception as e: QMessageBox.critical(self,"Add patient",str(e))
    def _edit_current(self):
        if not self.current or self.current.get("demo"): QMessageBox.information(self,"Demo patient","The demo context is fixed and labelled DEMO_DATA."); return
        d=AddPatientDialog(self); p=self.current; d.alias.setText(p.get("display_name") or ""); d.anon.setText(p.get("anonymous_id") or ""); d.age.setValue(float(p.get("age_years") or 23)); d.bmi.setValue(float(p.get("bmi") or 24)); d.clen.setValue(int(p.get("cycle_length") or 0)); d.ypm.setValue(float(p.get("years_post_menarche") or 0)); d.hyper.setChecked(bool(p.get("hyperandrogenism"))); d.pcom.setChecked(bool(p.get("pcom_present"))); d.excl.setChecked(bool(p.get("exclusions_completed")))
        if p.get("cycle_irregular") is True:d.cycle.setCurrentText("Irregular")
        elif p.get("cycle_irregular") is False:d.cycle.setCurrentText("Regular")
        if d.exec()!=QDialog.DialogCode.Accepted:return
        val=d.values(); self.current.update(val)
        try:
            import json; now=time.time(); pid=self.current["patient_id"]; self.db.conn.execute("UPDATE patients SET display_name=?,age_years=?,bmi=?,updated_at=? WHERE patient_id=?",(val["display_name"],val["age_years"],val["bmi"],now,pid)); self.db.conn.execute("INSERT OR REPLACE INTO profiles(profile_id,patient_id,data_json,label,created_at,updated_at) VALUES(?,?,?,?,?,?)",(f"profile-{pid}",pid,json.dumps(val),"CLINICALLY-ENTERED",now,now)); self.db.conn.commit()
        except Exception: pass
        self._refresh_roster(); self._refresh_current()
    def _refresh_current(self):
        if not self.current:return
        self.patient_lbl.setText(f"Patient: {self.current.get('anonymous_id','—')}"); ok,msg=context_ready(self.current); self.context.setText(f"ID {self.current.get('anonymous_id')} • age {self.current.get('age_years','—')} • BMI {self.current.get('bmi','—')} • evidence gate: {'READY' if ok else 'INCOMPLETE'} — {msg}"); self._compute_risk(); self.doctor_summary.setPlainText(f"{self.current.get('anonymous_id')}\n\n{DISCLAIMER}\n\n{msg}")
    def _on_sample(self,s):
        if self.test_active:self.test_rows.append(s)
    def _on_feature(self,f):
        self.latest=f
        for k,val in [("hr_bpm",f.hr_bpm),("rmssd_ms",f.rmssd_ms),("skin_temp_c",f.skin_temp_c),("activity_level",f.activity_level),("signal_quality",f.signal_quality)]:
            if k in self.metrics:self._set_metric(k,val)
        self.quality.setText(f"Quality {float(f.signal_quality)*100:.0f}%"); self.lab_packets.findChildren(QLabel)[1].setText(str(self.session.samples)); self.lab_q.findChildren(QLabel)[1].setText(f"{float(f.signal_quality)*100:.0f}%")
        self.timeline.append(f"{datetime.now().strftime('%H:%M:%S')} • HR {f.hr_bpm if f.hr_bpm is not None else 'UNKNOWN'} • quality {f.signal_quality:.2f}") if hasattr(self,"timeline") else None
        if self.test_active:self.test_features.append(f)
        self._compute_risk()
    def _set_metric(self,k,val):
        label=self.metrics[k].findChildren(QLabel)[1]
        if val is None or (isinstance(val,float) and not math.isfinite(val)): label.setText("UNKNOWN")
        elif k=="signal_quality": label.setText(f"{float(val)*100:.0f}%")
        elif k=="skin_temp_c": label.setText(f"{float(val):.2f} °C")
        elif k=="rmssd_ms": label.setText(f"{float(val):.0f} ms")
        elif k=="hr_bpm": label.setText(f"{float(val):.0f} bpm")
        else: label.setText(f"{float(val):.1f}")
    def _compute_risk(self):
        if not self.current or not self.latest:self.risk.setText("UNKNOWN"); self.reason.setText("Waiting for patient context and feature data."); return
        ok,msg=context_ready(self.current)
        if not ok:self.risk.setText("UNKNOWN"); self.reason.setText(msg); return
        try:
            idx,res,why=compute_research_index(self.current,self.latest,self.pcos,self.cfg.mode=="demo" and "demo" or "serial")
            if idx is None:self.risk.setText("UNKNOWN"); self.reason.setText(res.explanation if res else why)
            else:self.risk.setText(f"{float(idx):.1f}%"); self.reason.setText(f"{why}\n\nConfidence: {getattr(res,'confidence',0):.0%} • data quality: {getattr(res,'data_quality',0):.0%}\n{DISCLAIMER}")
        except Exception as e:self.risk.setText("ERROR"); self.reason.setText(f"Risk computation failed: {e}")
    def _on_state(self,s): self.state_lbl.setText(s.upper().replace("_"," ")); self.lab_log.append(f"{datetime.now().strftime('%H:%M:%S')} STATE {s}") if hasattr(self,"lab_log") else None
    def _on_error(self,msg): self.lab_log.append(f"{datetime.now().strftime('%H:%M:%S')} ERROR {msg}") if hasattr(self,"lab_log") else None
    def _start_test(self):
        if self.test_active:return
        self.test_active=True; self.test_start=time.monotonic(); self.test_rows=[]; self.test_features=[]; self.test_btn.setEnabled(False); self.test_btn.setText("Testing…")
    def _tick(self):
        elapsed=time.monotonic()-self.session.started; self.lab_rate.findChildren(QLabel)[1].setText(f"{self.session.samples/max(elapsed,0.001):.1f} Hz") if self.session.samples else None
        if self.test_active:
            left=max(0,15-int(time.monotonic()-self.test_start)); self.test_btn.setText(f"Testing… {left}s")
            if time.monotonic()-self.test_start>=15:self.test_active=False; self.test_btn.setEnabled(True); self.test_btn.setText("Run 15 s acceptance test"); self._finish_test()
    def _finish_test(self):
        rows=self.test_rows; fs=self.test_features; q=[float(f.signal_quality) for f in fs if f.signal_quality is not None]; avg=sum(q)/len(q) if q else None
        def finite_attr(name): return any(getattr(r,name,None) is not None for r in rows)
        checks=[("PPG raw",finite_attr("ir") or finite_attr("red")),("IMU",finite_attr("az_g")),("TEMP",any(math.isfinite(float(getattr(r,"temp_c",float("nan")))) for r in rows)),("ECG",finite_attr("ecg_raw")),("FSR",finite_attr("fsr_raw")),("MIC",finite_attr("mic_raw")),("ENV",finite_attr("lux") or finite_attr("room_temp_c"))]
        self.lab_log.append(f"TEST COMPLETE • {len(rows)} samples • avg quality {avg*100:.0f}%" if avg is not None else f"TEST COMPLETE • {len(rows)} samples")
        for i,(name,seen) in enumerate(checks): self.modules.setItem(i,1,QTableWidgetItem("SIGNAL" if seen else "UNKNOWN")); self.modules.setItem(i,2,QTableWidgetItem("PASS" if seen else "CHECK"))
        self.lab_log.append(" • ".join(f"{n}={'PASS' if s else 'UNKNOWN'}" for n,s in checks)); self.lab_log.append("PASS means software receipt/processing only; it does not prove calibration or clinical validity.")
    def _export_test(self):
        p,_=QFileDialog.getSaveFileName(self,"Export prototype test",str(ROOT/"data"/"prototype_tests"/f"unified_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"),"Text files (*.txt)")
        if not p:return
        Path(p).parent.mkdir(parents=True,exist_ok=True); Path(p).write_text("ENDO-TWIN NEXUS V8.7 PROTOTYPE TEST REPORT\n"+"="*58+"\n"+f"Mode: {self.cfg.mode}\nSource: {self.cfg.source}\n\n"+self.lab_log.toPlainText(),encoding="utf-8"); QMessageBox.information(self,"Prototype Lab",f"Saved: {p}")

def main():
    app=QApplication(sys.argv); app.setApplicationName("ENDO-TWIN NEXUS V8.7"); d=StartupDialog()
    if d.exec()!=QDialog.DialogCode.Accepted or d.config is None:return 0
    w=UnifiedWorkstation(d.config); w.show(); return app.exec()
if __name__=="__main__": raise SystemExit(main())
