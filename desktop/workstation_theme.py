"""Shared ENDO-TWIN V8.6 reference-inspired workstation visual language."""
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QHBoxLayout

APP_QSS = """
QMainWindow,QWidget{
    background:#151821;color:#e8ebf4;
    font-family:"Inter","Noto Sans",sans-serif;font-size:12px;
}
QFrame#sidebar{background:#1c202b;border-right:1px solid #303748;}
QFrame#topbar{background:#101824;border:0;border-bottom:1px solid #273448;}
QFrame#patientHeader{background:#1e232f;border:1px solid #364055;border-radius:15px;}
QFrame#card{background:#1b222e;border:1px solid #303b50;border-radius:14px;}
QFrame#soft{background:#1a1f2a;border:1px solid #30394c;border-radius:12px;}
QFrame#hero{background:#182333;border:1px solid #2e4561;border-radius:14px;}
QLabel#brand{color:#f8fbff;font-size:21px;font-weight:850;}
QLabel#eyebrow{color:#8b96ac;font-size:10px;font-weight:800;letter-spacing:1px;}
QLabel#title{color:#f3f6fb;font-size:27px;font-weight:850;}
QLabel#subtitle{color:#bec6d7;font-size:13px;font-weight:650;}
QLabel#muted{color:#8e98ad;font-size:11px;}
QLabel#metricValue{color:#f5f7fb;font-size:27px;font-weight:850;}
QLabel#bigValue{color:#f7f9fc;font-size:37px;font-weight:850;}
QLabel#sectionTitle{color:#dfe4ee;font-size:14px;font-weight:850;}
QLabel#smallCaps{color:#9099ae;font-size:9px;font-weight:800;letter-spacing:0.8px;}
QPushButton#nav{
    text-align:left;background:transparent;border:0;border-radius:8px;
    padding:11px 12px;color:#9fa8bb;font-size:12px;font-weight:750;
}
QPushButton#nav:hover{background:#252b39;color:#ebf1fb;}
QPushButton#nav:checked{background:#153b3a;color:#5fe0c2;}
QPushButton#nav:disabled{color:#5c6473;}
QPushButton#primary{
    background:#2f6af6;color:white;border:0;border-radius:9px;
    padding:9px 14px;font-weight:850;
}
QPushButton#secondary{
    background:#1b2230;color:#dce3ef;border:1px solid #3a465c;
    border-radius:9px;padding:8px 12px;font-weight:750;
}
QPushButton#danger{
    background:#4a2630;color:#ffb9c5;border:1px solid #7b3d4c;
    border-radius:9px;padding:8px 12px;font-weight:800;
}
QPushButton#tab{
    background:transparent;border:0;border-bottom:2px solid transparent;
    border-radius:0;padding:10px 10px;color:#7e879b;font-weight:650;
}
QPushButton#tab:hover{color:#bec8df;}
QPushButton#tab:checked{color:#9fb2ff;border-bottom-color:#9fb2ff;}
QLineEdit,QTextEdit,QListWidget,QTableWidget,QComboBox{
    background:#181d27;border:1px solid #354057;border-radius:8px;
    padding:8px;color:#edf1f7;selection-background-color:#284c78;
}
QTableWidget{gridline-color:#2a3345;}
QHeaderView::section{
    background:#1e2430;color:#909bb1;padding:9px;border:0;
    border-bottom:1px solid #303a4d;font-weight:800;
}
QTableWidget::item{padding:8px;}
QTableWidget::item:selected{background:#23384e;color:#f6f9fd;}
QScrollBar:vertical{background:#141821;width:10px;}
QScrollBar::handle:vertical{background:#343e53;border-radius:5px;min-height:30px;}
QProgressBar{
    background:#171d27;border:1px solid #303a4b;border-radius:7px;
    text-align:center;color:#eaf0f7;height:10px;
}
QProgressBar::chunk{background:#45c8a4;border-radius:6px;}
QTabBar::tab{
    background:transparent;color:#7f889a;padding:10px 12px;
    border:0;border-bottom:2px solid transparent;
}
QTabBar::tab:hover{color:#bbc4d8;}
QTabBar::tab:selected{color:#a9baff;border-bottom:2px solid #a9baff;font-weight:800;}
QToolTip{background:#202633;color:#f3f6fb;border:1px solid #455168;padding:5px;}
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
