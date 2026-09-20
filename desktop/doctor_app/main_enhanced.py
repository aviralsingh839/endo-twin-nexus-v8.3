#!/usr/bin/env python3
"""ENDO-TWIN V8.6 Doctor Workstation."""
from __future__ import annotations
import sys
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication,QComboBox,QFrame,QGridLayout,QHBoxLayout,QLabel,QLineEdit,QMainWindow,QMessageBox,QPushButton,QSplitter,QStackedWidget,QTableWidget,QTableWidgetItem,QVBoxLayout,QWidget
ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from database.database import LocalDatabase
from desktop.doctor_app.patient_management import PatientManager
from desktop.demo_data import DemoCase,condition_list,sorted_cases
from desktop.workstation_runtime import LiveSession,ModeConfig,Sparkline,choose_mode
from desktop.workstation_theme import APP_QSS,card,section_header
from services.bridge.server import EndoTwinBridgeServer
DISCLAIMER="Research / risk-screening output — not a medical diagnosis."
ORDER={"High":4,"Elevated":3,"Moderate":2,"Low":1,"Unknown":0}

class DoctorWindow(QMainWindow):
    def __init__(self,mode:ModeConfig):
        super().__init__(); self.mode=mode; self.db=LocalDatabase(); self.patient_mgr=PatientManager(self.db); self.current_case=None; self.live_patient=None; self.page_keys=["dashboard","patients","signals","pcos","imaging","reports","mobile"]; self.metric_labels={}; self.kpi_labels={}; self.packet_count=0
        self.bridge=EndoTwinBridgeServer(ROOT,7777); self.bridge.start()
        self.session=LiveSession(mode,self); self.session.features_updated.connect(self._on_features); self.session.sample_received.connect(self._on_sample); self.session.state_changed.connect(self._on_state); self.session.error_received.connect(self._on_error); self.session.start()
        self.setWindowTitle("ENDO-TWIN • Doctor Workstation • V8.6"); self.resize(1500,940); self.setMinimumSize(1180,760); self.setStyleSheet(APP_QSS); self._build(); self._refresh()
    def closeEvent(self,e): self.session.stop(); self.bridge.stop(); self.db.close(); e.accept()
    def _page(self,title,sub):
        w=QWidget(); o=QVBoxLayout(w); o.setContentsMargins(28,24,28,18); o.setSpacing(14); a=QLabel(title); a.setObjectName("title"); o.addWidget(a); b=QLabel(sub); b.setObjectName("muted"); b.setWordWrap(True); o.addWidget(b); return w,o
    def _build(self):
        root=QWidget(); self.setCentralWidget(root); shell=QGridLayout(root); shell.setContentsMargins(0,0,0,0)
        side=QFrame(); side.setObjectName("sidebar"); side.setFixedWidth(246); sl=QVBoxLayout(side); sl.setContentsMargins(20,22,20,20); sl.setSpacing(5); brand=QLabel("ENDO-TWIN"); brand.setObjectName("brand"); sl.addWidget(brand); tag=QLabel("DOCTOR WORKSTATION • V8.6"); tag.setObjectName("eyebrow"); sl.addWidget(tag); sl.addSpacing(14)
        self.nav={}
        for key,text in [("dashboard","◈  Command Center"),("patients","◉  Patient Registry"),("signals","∿  Live Signals"),("pcos","✦  CHRONO-PCOS"),("imaging","▣  Ultrasound"),("reports","▤  Reports"),("mobile","⌁  Mobile Link")]:
            b=QPushButton(text); b.setObjectName("nav"); b.setCheckable(True); b.clicked.connect(lambda _=False,k=key:self._go(k)); self.nav[key]=b; sl.addWidget(b)
        sl.addStretch(); box=QFrame(); box.setObjectName("hero"); bl=QVBoxLayout(box); bl.setContentsMargins(13,12,13,12); x=QLabel("SESSION MODE"); x.setObjectName("eyebrow"); bl.addWidget(x); self.side_mode=QLabel(); self.side_mode.setObjectName("subtitle"); bl.addWidget(self.side_mode); self.side_state=QLabel(); self.side_state.setObjectName("muted"); self.side_state.setWordWrap(True); bl.addWidget(self.side_state); sl.addWidget(box); shell.addWidget(side,0,0)
        right=QWidget(); rv=QVBoxLayout(right); rv.setContentsMargins(0,0,0,0); top=QFrame(); top.setObjectName("topbar"); tl=QHBoxLayout(top); tl.setContentsMargins(24,13,24,13); title=QLabel("Clinical review workspace"); title.setObjectName("subtitle"); title.setStyleSheet("font-size:16px;font-weight:850;"); tl.addWidget(title); tl.addStretch(); self.context=QLabel("No patient dossier selected"); self.context.setObjectName("muted"); tl.addWidget(self.context); tl.addSpacing(12); self.mode_badge=QLabel(); tl.addWidget(self.mode_badge); rv.addWidget(top)
        self.stack=QStackedWidget()
        for fn in [self._dashboard,self._patients,self._signals,self._pcos,self._imaging,self._reports,self._mobile]: self.stack.addWidget(fn())
        rv.addWidget(self.stack,1); foot=QLabel(f"{DISCLAIMER}  •  V8.6  •  Local-first  •  Startup mode is fixed for this run"); foot.setObjectName("muted"); rv.addWidget(foot); shell.addWidget(right,0,1); self._go("dashboard")
    def _mode_text(self): return ("DEMO MODE","Synthetic signals • DEMO_DATA") if self.mode.mode=="demo" else ("LIVE SENSOR MODE",f"USB serial • {self.mode.port}")
    def _set_mode_badges(self):
        title,detail=self._mode_text(); live=self.mode.mode=="live"; self.side_mode.setText(title); self.side_state.setText(detail); self.mode_badge.setText(title); self.mode_badge.setStyleSheet("background:#123e36;color:#7ce5c2;border:1px solid #1e6c5b;border-radius:10px;padding:7px 11px;font-weight:850;" if live else "background:#162f4a;color:#86d8ff;border:1px solid #245878;border-radius:10px;padding:7px 11px;font-weight:850;")
    def _go(self,key):
        self.stack.setCurrentIndex(self.page_keys.index(key)) if key in self.page_keys else None
        for k,b in self.nav.items(): b.setChecked(k==key)
        self._set_mode_badges()
        if key in ("dashboard","patients","pcos"): self._refresh()
    def _dashboard(self):
        w,o=self._page("Command center","Priority cases, current sensor quality and the evidence boundary around every model output.")
        g=QGridLayout(); g.setSpacing(12)
        for i,(a,b,c) in enumerate([("Patients in queue","—","Updates for this session"),("High signal tier","—","Synthetic demo tier only"),("CHRONO-PCOS cases","—","First disease-specific module"),("Live signal quality","—","Updates from processed stream")]):
            f=card(a,b,c); g.addWidget(f,0,i); self.kpi_labels[a]=f.findChildren(QLabel)[1]
        split=QSplitter(Qt.Orientation.Horizontal); left=QFrame(); left.setObjectName("card"); lv=QVBoxLayout(left); lv.addWidget(section_header("Priority review","Sorted by signal tier → research risk → condition")); self.queue=QTableWidget(0,5); self.queue.setHorizontalHeaderLabels(["Patient","Condition / module","Tier","Research risk","Quality"]); self._fit_table(self.queue); lv.addWidget(self.queue)
        right=QFrame(); right.setObjectName("card"); rv=QVBoxLayout(right); rv.addWidget(section_header("Processed sensor feed","PPG + IMU + GSR + temperature")); self.live_big=QLabel("Waiting for signal…"); self.live_big.setObjectName("bigValue"); rv.addWidget(self.live_big)
        for label,key in [("Heart rate","hr_bpm"),("HRV RMSSD","rmssd_ms"),("Skin temperature","skin_temp_c"),("Signal quality","signal_quality")]: q=QLabel(f"{label}  —"); q.setObjectName("muted"); rv.addWidget(q); self.metric_labels["dash_"+key]=q
        self.gate=QLabel("QUALITY GATE • waiting"); self.gate.setObjectName("warning"); rv.addWidget(self.gate); rv.addStretch(); split.addWidget(left); split.addWidget(right); split.setSizes([820,430]); o.addLayout(g); o.addWidget(split,1); return w
    def _fit_table(self,t): t.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows); t.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers); t.horizontalHeader().setStretchLastSection(True); t.verticalHeader().setVisible(False)
    def _patients(self):
        w,o=self._page("Patient registry","Demo mode shows synthetic cases with condition/module, severity tier, research risk and quality. Live mode shows only local database records."); bar=QHBoxLayout(); self.search=QLineEdit(); self.search.setPlaceholderText("Search patient / alias / module…"); self.search.textChanged.connect(self._refresh); bar.addWidget(self.search,1)
        self.cond=QComboBox(); self.cond.addItems(condition_list()); self.cond.currentTextChanged.connect(self._refresh); bar.addWidget(self.cond); self.sorter=QComboBox(); self.sorter.addItems(["Priority","Risk","Condition"]); self.sorter.currentTextChanged.connect(self._refresh); bar.addWidget(self.sorter); o.addLayout(bar)
        note=QLabel("Tier and risk in DEMO MODE are synthetic UI examples only. They are not patient diagnoses, clinical severity scores or validated model performance."); note.setObjectName("warning"); note.setWordWrap(True); o.addWidget(note)
        split=QSplitter(Qt.Orientation.Horizontal); table_box=QFrame(); table_box.setObjectName("card"); tb=QVBoxLayout(table_box); self.table=QTableWidget(0,7); self.table.setHorizontalHeaderLabels(["Patient","Alias","Condition / module","Severity tier*","Research risk*","Quality","Last update"]); self._fit_table(self.table); self.table.cellClicked.connect(self._select_row); tb.addWidget(self.table)
        detail=QFrame(); detail.setObjectName("card"); dv=QVBoxLayout(detail); dv.addWidget(section_header("Patient dossier","Open a case without losing the review queue.")); self.dossier=QVBoxLayout(); dv.addLayout(self.dossier); dv.addStretch(); split.addWidget(table_box); split.addWidget(detail); split.setSizes([900,420]); o.addWidget(split,1); return w
    def _clear_layout(self,lay):
        while lay.count():
            item=lay.takeAt(0); x=item.widget(); x.deleteLater() if x else None
    def _select_row(self,row,_col):
        if hasattr(self,"table") and row>=0: self._open_case(self.table.item(row,0).data(Qt.ItemDataRole.UserRole))
    def _open_case(self,pid):
        self.current_case=next((x for x in sorted_cases() if x.patient==pid),None) if self.mode.mode=="demo" else None
        if self.current_case: self.context.setText(f"{self.current_case.patient} • {self.current_case.condition}"); self._render_dossier(); return
        try: self.live_patient=self.db.get_patient(pid)
        except Exception: self.live_patient=None
        if self.live_patient: self.context.setText(f"{self.live_patient.get('anonymous_id',pid)} • local patient"); self._render_dossier()
    def _render_dossier(self):
        if not hasattr(self,"dossier"): return
        self._clear_layout(self.dossier); c=self.current_case
        if not c:
            p=self.live_patient
            if not p: self.dossier.addWidget(QLabel("No patient selected.")); return
            self.dossier.addWidget(QLabel(str(p.get("display_name") or p.get("anonymous_id") or "Local patient")))
            for t,v,d in [("Patient ID",p.get("anonymous_id","—"),"Local database"),("Age",p.get("age_years","—"),"Patient-entered/local record"),("BMI",p.get("bmi","—"),"Patient-entered/local record"),("Disease model","UNKNOWN","No model run attached"),("Research risk","UNKNOWN","No fabricated risk")]: self.dossier.addWidget(card(t,str(v),d))
            return
        self.dossier.addWidget(QLabel(c.alias+"  •  "+c.patient))
        for t,v,d in [("Condition / module",c.condition,"Disease-model surface, not diagnosis"),("Severity tier",c.tier,"Synthetic research UI tier"),("Research risk",f"{c.risk:.0f}%","Synthetic demo value"),("Data quality",f"{c.quality*100:.0f}%","Synthetic completeness"),("Drivers"," • ".join(c.drivers),"Illustrative explanation only")]: self.dossier.addWidget(card(t,str(v),d))
        b=QPushButton("Open live signal workspace"); b.setObjectName("primary"); b.clicked.connect(lambda:self._go("signals")); self.dossier.addWidget(b)
    def _signals(self):
        w,o=self._page("Live signals","Raw packets are CRC-checked before existing PPG, HRV, IMU, GSR and temperature processors run. Derived values remain quality-gated.")
        top=QGridLayout(); top.setSpacing(12); self.sig_values={}; specs=[("Heart rate","—","bpm"),("HRV RMSSD","—","ms"),("SpO₂","—","%"),("Skin temperature","—","°C"),("GSR","—","raw proxy"),("Activity","—","%"),("PPG quality","—","%"),("Packet rate","—","Hz")]
        for i,(a,v,u) in enumerate(specs): f=card(a,v,u); top.addWidget(f,i//4,i%4); self.sig_values[a]=f.findChildren(QLabel)[1]
        o.addLayout(top); charts=QGridLayout(); self.charts={}
        for i,(key,title,unit,line) in enumerate([("hr_bpm","Heart rate","bpm","#54d8f5"),("rmssd_ms","HRV RMSSD","ms","#9d8cff"),("skin_temp_c","Skin temperature","°C","#66d1a4"),("activity_level","Motion / activity","%","#f4b85b")]): s=Sparkline(title,unit,line); charts.addWidget(s,i//2,i%2); self.charts[key]=s
        o.addLayout(charts,1); bottom=QHBoxLayout(); self.signal_state=QLabel("CONNECTING…"); self.signal_state.setObjectName("muted"); bottom.addWidget(self.signal_state); bottom.addStretch(); self.signal_gate=QLabel("QUALITY GATE"); self.signal_gate.setObjectName("warning"); bottom.addWidget(self.signal_gate); stop=QPushButton("Stop stream"); stop.setObjectName("danger"); stop.clicked.connect(self._stop_stream); bottom.addWidget(stop); restart=QPushButton("Restart stream"); restart.setObjectName("secondary"); restart.clicked.connect(self._restart_stream); bottom.addWidget(restart); o.addLayout(bottom); return w
    def _stop_stream(self): self.session.stop()
    def _restart_stream(self): self.session.stop(); self.session.start()
    def _pcos(self):
        w,o=self._page("CHRONO-PCOS","The first disease-specific module inside ENDO-TWIN. Risk and tier examples below are synthetic demo UI values, not diagnoses or validation results.")
        hero=QFrame(); hero.setObjectName("hero"); h=QVBoxLayout(hero); h.addWidget(QLabel("CHRONO-PCOS • disease-model module")); h.addWidget(QLabel("Wearable physiology, clinical inputs, longitudinal history and ultrasound evidence are separate layers. Missing evidence stays UNKNOWN.")); self.pcos_status=QLabel("DEMO QUEUE • synthetic examples"); self.pcos_status.setObjectName("muted"); h.addWidget(self.pcos_status); o.addWidget(hero)
        g=QGridLayout();
        for i,(a,b,c) in enumerate([("Cases","3","CHRONO-PCOS synthetic cases"),("Evidence layers","Wearable + clinical + longitudinal","Provenance retained"),("Ultrasound","UNKNOWN by default","No invented anatomy"),("Validation","NOT ESTABLISHED","Research prototype")]): g.addWidget(card(a,b,c),0,i)
        o.addLayout(g); self.pcos_table=QTableWidget(0,6); self.pcos_table.setHorizontalHeaderLabels(["Patient","Signal tier","Risk*","Key drivers","Quality","Provenance"]); self._fit_table(self.pcos_table); o.addWidget(self.pcos_table,1); return w
    def _imaging(self):
        w,o=self._page("Ultrasound evidence","Image-derived features require validated, patient-grouped evidence. The absence of support is shown as UNKNOWN."); g=QGridLayout(); box=QFrame(); box.setObjectName("card"); gg=QGridLayout(box)
        for i,(a,b,c) in enumerate([("Image status","UNKNOWN","No validated image attached"),("Follicle count","UNKNOWN","Not estimated by this workstation"),("Ovarian morphology","UNKNOWN","No unsupported anatomical inference"),("Source","IMAGE-DERIVED","Only when a real source image is supplied")]): gg.addWidget(card(a,b,c),0,i)
        o.addWidget(box); warn=QLabel("No synthetic ultrasound result is promoted into a patient record. A future validated imaging model must retain source, cohort split, uncertainty and provenance."); warn.setObjectName("warning"); warn.setWordWrap(True); o.addWidget(warn); o.addStretch(); return w
    def _reports(self):
        w,o=self._page("Reports","Traceable report assembly keeps observations, quality, baseline, longitudinal context, disease-model output and limitations separate."); o.addWidget(section_header("Report structure","Patient → acquisition → quality → features → baseline → longitudinal → disease model → uncertainty → limitations")); f=QFrame(); f.setObjectName("card"); v=QVBoxLayout(f); v.addWidget(QLabel("Report readiness")); b=QPushButton("Generate demo report"); b.setObjectName("primary"); b.clicked.connect(lambda:QMessageBox.information(self,"ENDO-TWIN","Demo report generated. Synthetic values remain labeled DEMO_DATA.")); v.addWidget(b); o.addWidget(f); o.addStretch(); return w
    def _mobile(self):
        w,o=self._page("Mobile Link","Pair Patient Android on the same trusted LAN. This bridge is research/demo infrastructure, not production clinical security."); info=QGridLayout(); self.mobile_endpoint=card("Workstation endpoint",self.bridge.endpoint,"Use in Patient Android → Connect"); self.mobile_code=card("Pairing code",self.bridge.pair_code,"Regenerated at bridge restart"); self.mobile_received=card("Received packages",str(self.bridge.received_count),"data/bridge/inbox"); self.mobile_security=card("Security","Trusted LAN","Production needs TLS + strong authentication + audit"); 
        for i,f in enumerate([self.mobile_endpoint,self.mobile_code,self.mobile_received,self.mobile_security]): info.addWidget(f,0,i)
        o.addLayout(info); c=QPushButton("Copy pairing instructions"); c.setObjectName("primary"); c.clicked.connect(self._copy_mobile); o.addWidget(c); r=QPushButton("Restart bridge"); r.setObjectName("secondary"); r.clicked.connect(self._restart_bridge); o.addWidget(r); self.mobile_hint=QLabel("Patient Android transport is deliberate and patient-scoped. Its current payload path remains DEMO_DATA."); self.mobile_hint.setObjectName("muted"); self.mobile_hint.setWordWrap(True); o.addWidget(self.mobile_hint); o.addStretch(); return w
    def _copy_mobile(self): QApplication.clipboard().setText(f"ENDO-TWIN Doctor Workstation\nAddress: {self.bridge.endpoint}\nPairing code: {self.bridge.pair_code}\nUse Patient Android → Connect."); QMessageBox.information(self,"Mobile Link","Pairing instructions copied.")
    def _restart_bridge(self):
        self.bridge.stop(); self.bridge=EndoTwinBridgeServer(ROOT,7777)
        try: self.bridge.start()
        except OSError as e: QMessageBox.warning(self,"Mobile Link",str(e)); return
        self.mobile_endpoint.findChildren(QLabel)[1].setText(self.bridge.endpoint); self.mobile_code.findChildren(QLabel)[1].setText(self.bridge.pair_code)
    def _refresh(self):
        demo=self.mode.mode=="demo"
        if hasattr(self,"table"):
            self.table.setRowCount(0)
            if demo:
                cond=self.cond.currentText(); sk=self.sorter.currentText().lower(); q=self.search.text().lower(); rows=sorted_cases(cond,"risk" if sk=="risk" else "condition" if sk=="condition" else "priority")
                for c in rows:
                    if q and q not in f"{c.patient} {c.alias} {c.condition}".lower(): continue
                    r=self.table.rowCount(); self.table.insertRow(r); vals=[c.patient,c.alias,c.condition,c.tier,f"{c.risk:.0f}%",f"{c.quality*100:.0f}%",c.last_seen]
                    for col,val in enumerate(vals): it=QTableWidgetItem(str(val)); it.setData(Qt.ItemDataRole.UserRole,c.patient if col==0 else (c.risk if col==4 else ORDER[c.tier] if col==3 else None)); self.table.setItem(r,col,it)
            else:
                self.cond.blockSignals(True); self.cond.clear(); self.cond.addItem("Local patients"); self.cond.blockSignals(False); local=[]
                try: local=self.db.list_patients()
                except Exception: local=[]
                q=self.search.text().lower()
                for p in local:
                    pid=str(p.get("patient_id","")); alias=str(p.get("display_name") or p.get("anonymous_id") or pid)
                    if q and q not in f"{pid} {alias}".lower(): continue
                    r=self.table.rowCount(); self.table.insertRow(r); vals=[p.get("anonymous_id",pid),alias,"No model run","Unknown","—","—",p.get("updated_at","—")]
                    for col,val in enumerate(vals):
                        it=QTableWidgetItem(str(val)); 
                        if col==0: it.setData(Qt.ItemDataRole.UserRole,pid)
                        self.table.setItem(r,col,it)
        if hasattr(self,"queue"):
            self.queue.setRowCount(0)
            for c in sorted_cases()[:6] if demo else []:
                r=self.queue.rowCount(); self.queue.insertRow(r)
                for col,val in enumerate([c.patient,c.condition,c.tier,f"{c.risk:.0f}%",f"{c.quality*100:.0f}%"]): self.queue.setItem(r,col,QTableWidgetItem(str(val)))
        if hasattr(self,"pcos_table"):
            self.pcos_table.setRowCount(0)
            for c in sorted_cases("CHRONO-PCOS") if demo else []:
                r=self.pcos_table.rowCount(); self.pcos_table.insertRow(r); vals=[c.patient,c.tier,f"{c.risk:.0f}%"," • ".join(c.drivers),f"{c.quality*100:.0f}%","SYNTHETIC / DEMO_DATA"]
                for col,val in enumerate(vals): self.pcos_table.setItem(r,col,QTableWidgetItem(str(val)))
        self._render_dossier()
    def _on_sample(self,_): self.packet_count+=1
    def _on_state(self,state):
        if hasattr(self,"signal_state"): self.signal_state.setText(state.upper().replace("_"," "))
        if hasattr(self,"side_state"): self.side_state.setText(("LIVE" if state.startswith("connected") else "DEMO" if state.startswith("demo") else state))
    def _on_error(self,msg):
        if hasattr(self,"signal_state"): self.signal_state.setText("ERROR • "+msg)
    def _on_features(self,row):
        if not hasattr(self,"live_big"): return
        hr=row.get("hr_bpm"); rmssd=row.get("rmssd_ms"); spo2=row.get("spo2_pct"); temp=row.get("skin_temp_c"); gsr=row.get("gsr_tonic"); act=row.get("activity_level"); q=row.get("signal_quality"); rate=row.get("sample_rate_hz")
        def fmt(v,suf="",digits=1): return "—" if v is None else f"{float(v):.{digits}f}{suf}"
        self.live_big.setText(fmt(hr," bpm",0))
        for k,v in [("hr_bpm",hr),("rmssd_ms",rmssd),("skin_temp_c",temp)]: self.metric_labels["dash_"+k].setText({"hr_bpm":"Heart rate","rmssd_ms":"HRV RMSSD","skin_temp_c":"Skin temperature"}[k]+"  "+fmt(v,{"hr_bpm":" bpm","rmssd_ms":" ms","skin_temp_c":" °C"}[k]))
        self.metric_labels["dash_signal_quality"].setText(f"Signal quality  {float(q or 0)*100:.0f}%"); self.gate.setText(f"{row.get('gating','QUALITY_GATE')} • {len(row.get('status_flags',[]))} status flag(s)")
        for key,val in [("Heart rate",hr),("HRV RMSSD",rmssd),("SpO₂",spo2),("Skin temperature",temp),("GSR",gsr),("Activity",act)]: self.sig_values.get(key) and self.sig_values[key].setText(fmt(val,"",1))
        self.sig_values.get("PPG quality") and self.sig_values["PPG quality"].setText(f"{float(row.get('ppg_quality') or 0)*100:.0f}%"); self.sig_values.get("Packet rate") and self.sig_values["Packet rate"].setText(fmt(rate,"",1))
        for key,val in [("hr_bpm",hr),("rmssd_ms",rmssd),("skin_temp_c",temp),("activity_level",act)]: self.charts[key].set_value(val)
        self.signal_gate.setText(f"{row.get('gating','QUALITY_GATE')} • {row.get('provenance','UNKNOWN')} • {len(row.get('status_flags',[]))} flags")

def run():
    app=QApplication(sys.argv); app.setStyle("Fusion"); mode=choose_mode("ENDO-TWIN • Doctor Workstation")
    if mode is None: return 0
    w=DoctorWindow(mode); w.show(); return app.exec()
if __name__=="__main__": raise SystemExit(run())
