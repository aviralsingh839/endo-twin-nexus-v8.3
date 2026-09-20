"""Shared ENDO-TWIN workstation visual language."""
from PySide6.QtWidgets import QFrame,QLabel,QVBoxLayout
APP_QSS="""
QMainWindow,QWidget{background:#07111f;color:#e6edf5;font-family:"Inter","Noto Sans",sans-serif;}
QFrame#sidebar{background:#091827;border-right:1px solid #183047;}
QFrame#topbar{background:#0a1626;border-bottom:1px solid #183047;}
QFrame#card{background:#0d1d2f;border:1px solid #1b3650;border-radius:16px;}
QFrame#hero{background:#0f2637;border:1px solid #24536f;border-radius:18px;}
QLabel#brand{color:#eff8ff;font-size:22px;font-weight:800;} QLabel#eyebrow{color:#6ca9c8;font-size:10px;font-weight:700;}
QLabel#title{color:#f5f9fd;font-size:26px;font-weight:750;} QLabel#muted{color:#8ca3b7;font-size:12px;}
QLabel#metricValue{color:#f5fbff;font-size:24px;font-weight:800;}
QPushButton#nav{text-align:left;background:transparent;border:0;border-radius:10px;padding:12px 14px;color:#9fb2c4;font-size:13px;font-weight:650;}
QPushButton#nav:hover{background:#10283c;color:#eaf6ff;} QPushButton#nav:checked{background:#12354c;color:#74d5ff;}
QPushButton#primary{background:#1ca6cf;color:#04131f;border:0;border-radius:10px;padding:10px 16px;font-weight:800;}
QPushButton#secondary{background:#10283b;color:#cfe8f5;border:1px solid #22465f;border-radius:10px;padding:9px 14px;font-weight:700;}
QLineEdit,QTextEdit,QListWidget,QTableWidget,QComboBox{background:#091929;border:1px solid #1b3650;border-radius:10px;padding:8px;color:#e6edf5;selection-background-color:#15506f;}
QHeaderView::section{background:#0f2235;color:#91a9bd;padding:8px;border:0;}
QScrollBar:vertical{background:#081522;width:10px;} QScrollBar::handle:vertical{background:#193c56;border-radius:5px;min-height:30px;}
"""
def card(title,value,detail,parent=None):
    frame=QFrame(parent);frame.setObjectName("card");lay=QVBoxLayout(frame);lay.setContentsMargins(16,14,16,14);lay.setSpacing(5)
    a=QLabel(title.upper());a.setObjectName("eyebrow");lay.addWidget(a);b=QLabel(value);b.setObjectName("metricValue");b.setWordWrap(True);lay.addWidget(b);c=QLabel(detail);c.setObjectName("muted");c.setWordWrap(True);lay.addWidget(c);return frame
