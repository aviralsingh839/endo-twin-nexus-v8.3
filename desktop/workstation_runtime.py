"""Shared V8.7 workstation startup, live sensor processing and plotting widgets."""
from __future__ import annotations
from dataclasses import dataclass
from collections import deque
import math

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QComboBox, QDialog, QFrame, QHBoxLayout, QLabel, QMessageBox, QPushButton, QVBoxLayout, QWidget

from src.serial_io.arduino_reader import ArduinoReader
from src.serial_io.packet_parser import decode_status_flags
from src.signal_processing.gsr import GSRProcessor
from src.signal_processing.imu import IMUProcessor
from src.signal_processing.ppg import PPGProcessor
from src.signal_processing.temperature import TemperatureProcessor
from src.utils.demo_stream import DemoSensorStream

@dataclass
class ModeConfig:
    mode: str = "demo"
    port: str = ""
    baud: int = 115200

class ModeDialog(QDialog):
    """Startup-only mode chooser; the selected data source is fixed for the run."""
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(720)
        self.choice = None
        root=QVBoxLayout(self); root.setContentsMargins(30,28,30,28); root.setSpacing(16)
        h=QLabel("Choose data mode"); h.setObjectName("modeTitle"); root.addWidget(h)
        s=QLabel("Choose the source before the workstation opens. Demo and live data are kept on separate session paths."); s.setObjectName("muted"); s.setWordWrap(True); root.addWidget(s)
        row=QHBoxLayout(); row.setSpacing(14)
        row.addWidget(self._card("DEMO MODE","Synthetic physiological stream","Hardware-free exhibition mode. Every sample is labelled DEMO_DATA.","Open Demo",lambda:self._accept("demo")))
        row.addWidget(self._card("LIVE SENSOR MODE","ESP32 wearable / Mega lab USB","CRC-checked $CP/$CP2 packets feed the real processing chain.","Open Live",lambda:self._accept("live")))
        root.addLayout(row)
        box=QFrame(); box.setObjectName("card"); lv=QVBoxLayout(box); lv.setContentsMargins(16,14,16,14); lv.setSpacing(8)
        e=QLabel("LIVE INPUT"); e.setObjectName("eyebrow"); lv.addWidget(e)
        line=QHBoxLayout(); self.port=QComboBox(); self.port.setEditable(True); self.port.setPlaceholderText("USB serial port will be detected automatically")
        detect=QPushButton("Auto-detect USB"); detect.setObjectName("primary"); detect.clicked.connect(self.auto_detect_port)
        b=QPushButton("Refresh"); b.setObjectName("secondary"); b.clicked.connect(self.refresh_ports)
        line.addWidget(self.port,1); line.addWidget(detect); line.addWidget(b); lv.addLayout(line)
        self.port_status=QLabel("Detecting USB serial devices…"); self.port_status.setObjectName("muted"); self.port_status.setWordWrap(True); lv.addWidget(self.port_status)
        n=QLabel("Active hardware: ESP32 primary wearable or Arduino Mega bench/lab controller. Both emit the canonical ~20 packets/s CP2 stream; sensor validity still depends on placement, calibration and hardware."); n.setObjectName("muted"); n.setWordWrap(True); lv.addWidget(n)
        root.addWidget(box)
        self.refresh_ports()
        self.auto_detect_port()

    def _card(self,title,value,detail,action,callback):
        f=QFrame(); f.setObjectName("hero"); l=QVBoxLayout(f); l.setContentsMargins(18,16,18,16); l.setSpacing(7)
        for txt,obj in [(title,"eyebrow"),(value,"metricValue")]:
            x=QLabel(txt); x.setObjectName(obj); x.setWordWrap(True); l.addWidget(x)
        c=QLabel(detail); c.setObjectName("muted"); c.setWordWrap(True); l.addWidget(c)
        p=QPushButton(action); p.setObjectName("primary"); p.clicked.connect(callback); l.addWidget(p)
        return f

    def refresh_ports(self):
        cur=self.port.currentText().strip()
        ports=ArduinoReader.available_ports()
        self.port.clear(); self.port.addItems(ports)
        if cur and cur in ports: self.port.setCurrentText(cur)
        self.port_status.setText(f"USB serial devices found: {len(ports)}" if ports else "No USB serial device detected. Connect the ESP32 or Mega and click Auto-detect USB.")

    def auto_detect_port(self):
        ports=ArduinoReader.available_ports()
        self.port.clear(); self.port.addItems(ports)
        if not ports:
            self.port_status.setText("No USB serial device detected. Connect the ESP32 or Mega and click Auto-detect USB.")
            return
        # Prefer the normal Linux/macOS USB-serial names, then Windows COM ports.
        preferred=[p for p in ports if "/ttyACM" in p or "/ttyUSB" in p or p.upper().startswith("COM")]
        selected=preferred[0] if preferred else ports[0]
        self.port.setCurrentText(selected)
        self.port_status.setText(f"Auto-detected USB serial device: {selected}")

    def _accept(self,mode):
        if mode=="live" and not self.port.currentText().strip():
            self.auto_detect_port()
        if mode=="live" and not self.port.currentText().strip():
            QMessageBox.warning(self,"Live mode","No USB serial device detected. Connect the ESP32 or Mega and try Auto-detect USB."); return
        self.choice=ModeConfig(mode=mode,port=self.port.currentText().strip()); self.accept()

def choose_mode(title: str) -> ModeConfig | None:
    dlg=ModeDialog(title); dlg.setStyleSheet(STARTUP_QSS)
    return dlg.choice if dlg.exec()==QDialog.DialogCode.Accepted else None

STARTUP_QSS="""
QDialog,QWidget{background:#07111f;color:#eaf2f7;font-family:"Inter","Noto Sans",sans-serif;}
QLabel#modeTitle{font-size:28px;font-weight:800;color:#f7fbff;} QLabel#eyebrow{font-size:10px;font-weight:800;color:#72b7d7;} QLabel#muted{font-size:12px;color:#91a7b7;}
QLabel#metricValue{font-size:21px;font-weight:800;color:#f7fbff;} QFrame#card{background:#0d1c2b;border:1px solid #1b3952;border-radius:16px;} QFrame#hero{background:#0d2536;border:1px solid #24536c;border-radius:18px;}
QComboBox{background:#091827;border:1px solid #1c3a52;border-radius:10px;padding:9px;color:#eaf2f7;} QPushButton#primary{background:#1ca8d1;color:#04131c;border:0;border-radius:10px;padding:10px 14px;font-weight:800;} QPushButton#secondary{background:#0f2435;color:#cfe4ee;border:1px solid #22485f;border-radius:10px;padding:8px 12px;font-weight:700;}
"""

class StreamingFeatureProcessor:
    """Decode-ready feature layer with sensor-specific sampling and quality gates."""
    def __init__(self):
        self.ppg=PPGProcessor(history_s=180,fs_hz=20.0)
        self.imu=IMUProcessor(history_s=180,fs_hz=20.0)
        self.gsr=GSRProcessor(history_s=600,fs_hz=10.0)
        self.temp=TemperatureProcessor(history_s=3600)
        self.samples=0
        self.last_emit=0.0
        self.last_gsr_ts=0.0
        self.last_temp_ts=0.0
        self.times=deque(maxlen=60)

    def reset(self):
        self.__init__()

    def process(self,sample):
        self.samples+=1
        ts=float(sample.timestamp_s)
        self.times.append(ts)

        # PPG and IMU follow the received workstation packet stream (~20 Hz).
        self.ppg.add_sample(ts,sample.ir,sample.red)
        self.imu.add_sample(ts,sample.ax_g,sample.ay_g,sample.az_g,sample.gx_dps,sample.gy_dps,sample.gz_dps)

        # Do not oversample slower channels merely because the transport packet is faster.
        if self.last_gsr_ts<=0.0 or ts-self.last_gsr_ts>=0.10:
            self.gsr.add_sample(ts,sample.gsr_raw)
            self.last_gsr_ts=ts
        if self.last_temp_ts<=0.0 or ts-self.last_temp_ts>=1.0:
            self.temp.add_sample(ts,sample.temp_c)
            self.last_temp_ts=ts

        if ts-self.last_emit<0.5:
            return None
        self.last_emit=ts

        motion=self.imu.features(10.0)
        ppg=self.ppg.features(motion_index=motion["motion_index"])
        gsr=self.gsr.features(60.0)
        temp=self.temp.features(300.0)

        ppg_q=float(ppg.get("ppg_quality") or 0.0)
        flags=decode_status_flags(int(sample.status))
        ppg_absent=any("PPG finger absent" in x for x in flags)
        ppg_sat=any("PPG saturated" in x for x in flags)
        gsr_bad=any("GSR saturated" in x for x in flags)
        temp_bad=any("DS18B20 error" in x for x in flags)

        if ppg_absent: ppg_q*=0.35
        if ppg_sat: ppg_q*=0.50

        gsr_q=0.0 if gsr_bad or sample.gsr_raw<5 or sample.gsr_raw>1018 else 1.0
        temp_q=0.0 if temp_bad else (1.0 if temp.get("skin_temp_c") is not None else 0.0)
        motion_q=max(0.0,min(1.0,1.0-float(motion["motion_index"])/0.45))

        quality=max(0.0,min(1.0,0.65*ppg_q+0.12*gsr_q+0.10*temp_q+0.13*motion_q))
        usable=quality>=0.45 and not ppg_absent and not ppg_sat

        hr=ppg.get("hr_bpm") if usable else None
        rmssd=ppg.get("rmssd_ms") if usable else None
        sdnn=ppg.get("sdnn_ms") if usable else None
        spo2=ppg.get("spo2_pct") if quality>=0.55 and not ppg_absent and not ppg_sat else None

        rate=None
        if len(self.times)>=5:
            vals=list(self.times)[-10:]
            dt=[b-a for a,b in zip(vals[:-1],vals[1:]) if 0.005<(b-a)<1.0]
            if dt: rate=1.0/(sum(dt)/len(dt))

        return {
            "timestamp":ts,
            "hr_bpm":hr,
            "rmssd_ms":rmssd,
            "sdnn_ms":sdnn,
            "spo2_pct":spo2,
            "skin_temp_c":temp.get("skin_temp_c"),
            "temp_slope_c_per_min":temp.get("temp_slope_c_per_min",0.0),
            "gsr_tonic":gsr.get("gsr_tonic"),
            "gsr_phasic_per_min":gsr.get("gsr_phasic_per_min",0.0),
            "motion_index":motion.get("motion_index",0.0),
            "activity_level":motion.get("activity_level",0.0),
            "signal_quality":quality,
            "ppg_quality":ppg_q,
            "sample_rate_hz":rate,
            "raw_ir":sample.ir,
            "raw_red":sample.red,
            "gsr_raw":sample.gsr_raw,
            "status_flags":flags,
            "source":sample.source,
            "status":int(sample.status),
            "ecg_raw":sample.ecg_raw,
            "room_temp_c":sample.room_temp_c,
            "humidity_pct":sample.humidity_pct,
            "pressure_hpa":sample.pressure_hpa,
            "provenance":"DEMO_DATA" if sample.source=="demo" else "MEASURED",
            "gating":"USABLE" if usable else "QUALITY_GATE",
            "derived_provenance":"DERIVED"
        }

class LiveSession(QObject):
    features_updated=Signal(object)
    sample_received=Signal(object)
    state_changed=Signal(str)
    error_received=Signal(str)

    def __init__(self,mode:ModeConfig,parent=None):
        super().__init__(parent)
        self.mode=mode; self.processor=StreamingFeatureProcessor(); self.reader=None; self.latest=None

    def start(self):
        self.processor.reset()
        self.reader=DemoSensorStream(fs_hz=20.0,parent=self) if self.mode.mode=="demo" else ArduinoReader(self.mode.port,self.mode.baud,require_crc=True,parent=self)
        self.reader.sample_received.connect(self._on_sample)
        self.reader.state_changed.connect(self.state_changed)
        self.reader.error_received.connect(self.error_received)
        self.reader.start()
        self.state_changed.emit("demo-running" if self.mode.mode=="demo" else f"connecting:{self.mode.port}")

    def stop(self):
        if self.reader is not None: self.reader.stop()
        self.reader=None; self.state_changed.emit("stopped")

    def write_command(self,command:str):
        if self.reader is not None and hasattr(self.reader,"write_command"):
            self.reader.write_command(command)

    def _on_sample(self,sample):
        self.sample_received.emit(sample)
        row=self.processor.process(sample)
        if row is not None:
            self.latest=row
            self.features_updated.emit(row)

class Sparkline(QWidget):
    def __init__(self,label,unit="",line="#5fd6f7",parent=None):
        super().__init__(parent); self.label=label; self.unit=unit; self.line=line; self.values=deque(maxlen=120); self.setMinimumHeight(150)

    def set_value(self,value):
        if isinstance(value,(int,float)) and math.isfinite(float(value)): self.values.append(float(value))
        self.update()

    def set_values(self,values):
        self.values=deque([float(v) for v in values if isinstance(v,(int,float)) and math.isfinite(float(v))],maxlen=120)
        self.update()

    def paintEvent(self,_):
        p=QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing); r=self.rect().adjusted(10,10,-10,-10)
        p.fillRect(r,QColor("#091827")); p.setPen(QPen(QColor("#173148"),1))
        for frac in (0.25,0.5,0.75):
            p.drawLine(r.left(),r.top()+int(r.height()*frac),r.right(),r.top()+int(r.height()*frac))
        if not self.values:
            p.setPen(QColor("#7890a0")); p.drawText(r,Qt.AlignmentFlag.AlignCenter,"Waiting for signal…"); return
        vals=list(self.values); lo=min(vals); hi=max(vals); span=max(hi-lo,1e-6); path=QPainterPath()
        for i,v in enumerate(vals):
            x=r.left()+r.width()*i/max(1,len(vals)-1); y=r.bottom()-r.height()*(v-lo)/span
            path.moveTo(x,y) if i==0 else path.lineTo(x,y)
        p.setPen(QPen(QColor(self.line),2)); p.drawPath(path)
        p.setPen(QColor("#eaf2f7")); p.drawText(r.left()+8,r.top()+18,f"{self.label}  {self.unit}")
        p.setPen(QColor("#91a7b7")); p.drawText(r.right()-110,r.top()+18,f"{vals[-1]:.1f}")
