"""Shared ENDO-TWIN V8.6 reference-inspired workstation visual language."""
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QHBoxLayout

APP_QSS = """
QMainWindow,QWidget{
    background:#f5f7fa;color:#17212b;
    font-family:"Inter","Noto Sans",sans-serif;font-size:12px;
}
QFrame#sidebar{background:#142b3a;border-right:1px solid #203e4d;}
QFrame#topbar{background:#ffffff;border:0;border-bottom:1px solid #d9e2e8;}
QFrame#patientHeader{background:#ffffff;border:1px solid #d8e0e8;border-radius:10px;}
QFrame#card{background:#ffffff;border:1px solid #d8e0e8;border-radius:10px;}
QFrame#soft{background:#f8fafc;border:1px solid #d8e0e8;border-radius:9px;}
QFrame#hero{background:#eef5f6;border:1px solid #c9dfe2;border-radius:10px;}
QLabel#brand{color:#ffffff;font-size:20px;font-weight:850;}
QLabel#eyebrow{color:#71808d;font-size:10px;font-weight:800;letter-spacing:1px;}
QLabel#title{color:#17212b;font-size:27px;font-weight:850;}
QLabel#subtitle{color:#50616e;font-size:13px;font-weight:650;}
QLabel#muted{color:#71808d;font-size:11px;}
QLabel#metricValue{color:#17212b;font-size:27px;font-weight:850;}
QLabel#bigValue{color:#17212b;font-size:37px;font-weight:850;}
QLabel#sectionTitle{color:#253746;font-size:14px;font-weight:850;}
QLabel#smallCaps{color:#71808d;font-size:9px;font-weight:800;letter-spacing:0.8px;}
QPushButton#nav{
    text-align:left;background:transparent;border:0;border-radius:7px;
    padding:10px 11px;color:#b9c7d2;font-size:12px;font-weight:750;
}
QPushButton#nav:hover{background:#1e3c4c;color:#ffffff;}
QPushButton#nav:checked{background:#0b6670;color:#ffffff;}
QPushButton#nav:disabled{color:#667783;}
QPushButton#primary{
    background:#0b6670;color:white;border:0;border-radius:7px;
    padding:9px 14px;font-weight:850;
}
QPushButton#primary:hover{background:#167d88;}
QPushButton#secondary{
    background:#ffffff;color:#29404e;border:1px solid #cbd6dd;
    border-radius:7px;padding:8px 12px;font-weight:750;
}
QPushButton#danger{
    background:#fff3f2;color:#a83b38;border:1px solid #e4b8b5;
    border-radius:7px;padding:8px 12px;font-weight:800;
}
QPushButton#tab{
    background:transparent;border:0;border-bottom:2px solid transparent;
    border-radius:0;padding:10px 10px;color:#71808d;font-weight:650;
}
QPushButton#tab:hover{color:#29404e;}
QPushButton#tab:checked{color:#0b6670;border-bottom-color:#0b6670;}
QLineEdit,QTextEdit,QListWidget,QTableWidget,QComboBox{
    background:#ffffff;border:1px solid #cbd6dd;border-radius:7px;
    padding:8px;color:#17212b;selection-background-color:#d9eff0;
}
QTableWidget{gridline-color:#e1e7eb;}
QHeaderView::section{
    background:#f2f5f7;color:#61717d;padding:9px;border:0;
    border-bottom:1px solid #d8e0e8;font-weight:800;
}
QTableWidget::item{padding:8px;}
QTableWidget::item:selected{background:#e5f1f2;color:#17212b;}
QScrollBar:vertical{background:#f5f7fa;width:10px;}
QScrollBar::handle:vertical{background:#c3cfd6;border-radius:5px;min-height:30px;}
QProgressBar{
    background:#edf1f3;border:1px solid #d3dde2;border-radius:6px;
    text-align:center;color:#334955;height:10px;
}
QProgressBar::chunk{background:#0b6670;border-radius:6px;}
QTabBar::tab{
    background:transparent;color:#71808d;padding:10px 12px;
    border:0;border-bottom:2px solid transparent;
}
QTabBar::tab:hover{color:#29404e;}
QTabBar::tab:selected{color:#0b6670;border-bottom:2px solid #0b6670;font-weight:800;}
QToolTip{background:#17212b;color:#ffffff;border:1px solid #52636f;padding:5px;}
QLabel#warning{background:#fff8e8;color:#7a5700;border:1px solid #ead39a;border-radius:7px;padding:8px;}
"""

def card(title, value, detail, parent=None, accent=None):
    frame = QFrame(parent)
    frame.setObjectName("card")
    lay = QVBoxLayout(frame)
    lay.setContentsMargins(15, 13, 15, 13)
    lay.setSpacing(5)
    a = QLabel(title.upper())
    a.setObjectName("eyebrow")
    lay.addWidget(a)
    b = QLabel(value)
    b.setObjectName("metricValue")
    b.setWordWrap(True)
    if accent:
        b.setStyleSheet(f"color:{accent};")
    lay.addWidget(b)
    c = QLabel(detail)
    c.setObjectName("muted")
    c.setWordWrap(True)
    lay.addWidget(c)
    return frame

def section_header(title, detail=""):
    box = QFrame()
    box.setObjectName("soft")
    row = QHBoxLayout(box)
    row.setContentsMargins(13, 10, 13, 10)
    col = QVBoxLayout()
    col.setSpacing(2)
    a = QLabel(title)
    a.setObjectName("sectionTitle")
    col.addWidget(a)
    if detail:
        b = QLabel(detail)
        b.setObjectName("muted")
        b.setWordWrap(True)
        col.addWidget(b)
    row.addLayout(col)
    row.addStretch()
    return box

def pill(text, bg="#2a2548", fg="#b6a8ff", parent=None):
    x = QLabel(text, parent)
    x.setStyleSheet(
        f"background:{bg};color:{fg};border:1px solid {bg};"
        "border-radius:9px;padding:5px 8px;font-weight:800;font-size:10px;"
    )
    return x

def status_badge(text, kind="neutral", parent=None):
    palette = {
        "good": ("#183d35", "#69d5b3", "#28604f"),
        "fair": ("#4a391e", "#e9ae45", "#6b5429"),
        "poor": ("#4d2b25", "#ee8c79", "#714139"),
        "info": ("#24284a", "#b3a6ff", "#46456b"),
        "neutral": ("#2a2f3b", "#b4bdcc", "#41495a"),
        "measured": ("#173b38", "#79dac0", "#376f63"),
        "derived": ("#2d2949", "#b2a6ef", "#56507e"),
    }
    bg, fg, border = palette.get(kind, palette["neutral"])
    x = QLabel(text, parent)
    x.setStyleSheet(
        f"background:{bg};color:{fg};border:1px solid {border};"
        "border-radius:9px;padding:5px 8px;font-weight:800;font-size:10px;"
    )
    return x
