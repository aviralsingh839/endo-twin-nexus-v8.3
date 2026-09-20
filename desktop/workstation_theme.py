"""Shared ENDO-TWIN V8.6 workstation visual language."""
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QHBoxLayout
APP_QSS = """
QMainWindow,QWidget{background:#06101b;color:#e9f2f7;font-family:"Inter","Noto Sans",sans-serif;font-size:12px;}
QFrame#sidebar{background:#081725;border-right:1px solid #17344b;} QFrame#topbar{background:#081421;border-bottom:1px solid #17344b;}
QFrame#card{background:#0b1b2a;border:1px solid #19364d;border-radius:14px;} QFrame#hero{background:#0d2435;border:1px solid #25536a;border-radius:16px;} QFrame#soft{background:#0a1825;border:1px solid #163248;border-radius:12px;}
QLabel#brand{color:#f5fbff;font-size:22px;font-weight:850;} QLabel#eyebrow{color:#73b9d8;font-size:10px;font-weight:800;letter-spacing:1px;}
QLabel#title{color:#f4f9fc;font-size:24px;font-weight:800;} QLabel#subtitle{color:#a6b9c7;font-size:13px;font-weight:500;} QLabel#muted{color:#8299aa;font-size:11px;} QLabel#metricValue{color:#f8fcff;font-size:23px;font-weight:850;} QLabel#bigValue{color:#f8fcff;font-size:34px;font-weight:850;}
QPushButton#nav{text-align:left;background:transparent;border:0;border-radius:10px;padding:12px 13px;color:#9db1bf;font-size:12px;font-weight:700;} QPushButton#nav:hover{background:#0e2638;color:#e9f7fd;} QPushButton#nav:checked{background:#12344a;color:#73d5fb;}
QPushButton#primary{background:#1ba5cf;color:#03111a;border:0;border-radius:10px;padding:10px 15px;font-weight:850;} QPushButton#secondary{background:#0d2233;color:#d4e8f1;border:1px solid #24485d;border-radius:10px;padding:9px 13px;font-weight:750;} QPushButton#danger{background:#422329;color:#ffbec4;border:1px solid #7b3742;border-radius:10px;padding:9px 13px;font-weight:800;}
QLineEdit,QTextEdit,QListWidget,QTableWidget,QComboBox{background:#081725;border:1px solid #19364d;border-radius:9px;padding:8px;color:#e9f2f7;selection-background-color:#124864;} QTableWidget{gridline-color:#122c3e;} QHeaderView::section{background:#0d2030;color:#94acbb;padding:9px;border:0;border-bottom:1px solid #17364b;font-weight:800;}
QScrollBar:vertical{background:#06111b;width:10px;} QScrollBar::handle:vertical{background:#17384e;border-radius:5px;min-height:30px;} QProgressBar{background:#091827;border:1px solid #183348;border-radius:7px;text-align:center;color:#eaf3f8;height:12px;} QProgressBar::chunk{background:#1ba5cf;border-radius:6px;}
"""
def card(title,value,detail,parent=None,accent=None):
    frame=QFrame(parent); frame.setObjectName("card"); lay=QVBoxLayout(frame); lay.setContentsMargins(15,13,15,13); lay.setSpacing(5)
    a=QLabel(title.upper()); a.setObjectName("eyebrow"); lay.addWidget(a); b=QLabel(value); b.setObjectName("metricValue"); b.setWordWrap(True); 
    if accent: b.setStyleSheet(f"color:{accent};")
    lay.addWidget(b); c=QLabel(detail); c.setObjectName("muted"); c.setWordWrap(True); lay.addWidget(c); return frame
def section_header(title,detail=""):
    box=QFrame(); box.setObjectName("soft"); row=QHBoxLayout(box); row.setContentsMargins(14,10,14,10); col=QVBoxLayout(); col.setSpacing(2)
    a=QLabel(title); a.setObjectName("subtitle"); a.setStyleSheet("font-size:14px;font-weight:800;color:#e8f3f8;"); col.addWidget(a)
    if detail: b=QLabel(detail); b.setObjectName("muted"); b.setWordWrap(True); col.addWidget(b)
    row.addLayout(col); row.addStretch(); return box
def pill(text,bg="#123149",fg="#8bdcff",parent=None):
    x=QLabel(text,parent); x.setStyleSheet(f"background:{bg};color:{fg};border:1px solid {bg};border-radius:9px;padding:5px 8px;font-weight:800;font-size:10px;"); return x
