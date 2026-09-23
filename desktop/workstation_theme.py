"""Shared ENDO-TWIN V8.6 reference-inspired workstation visual language."""
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QHBoxLayout

APP_QSS = """
QMainWindow,QWidget{
    background:#050d18;color:#eef7ff;
    font-family:"Inter","Noto Sans","Segoe UI",sans-serif;font-size:12px;
}
QFrame#sidebar{
    background:#071321;border-right:1px solid #1c3852;
}
QFrame#topbar{
    background:#09182a;border-bottom:1px solid #244663;
}
QFrame#patientHeader{
    background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #10253a,stop:1 #0b1b2c);
    border:1px solid #244663;border-radius:14px;
}
QFrame#card{
    background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #10243a,stop:1 #0b1b2d);
    border:1px solid #244663;border-radius:14px;
}
QFrame#soft{
    background:#0c1d30;border:1px solid #203f5b;border-radius:11px;
}
QFrame#hero{
    background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #0d3044,stop:1 #0b1d31);
    border:1px solid #245a76;border-radius:12px;
}
QLabel#brand{color:#f6fbff;font-size:20px;font-weight:850;}
QLabel#eyebrow{color:#48d9ff;font-size:9px;font-weight:850;letter-spacing:1.2px;}
QLabel#title{color:#f4f9ff;font-size:29px;font-weight:850;}
QLabel#subtitle{color:#91abc5;font-size:12px;font-weight:650;}
QLabel#muted{color:#87a1bb;font-size:10px;}
QLabel#metricValue{color:#f4fbff;font-size:25px;font-weight:850;}
QLabel#bigValue{color:#f4fbff;font-size:37px;font-weight:850;}
QLabel#sectionTitle{color:#eaf6ff;font-size:14px;font-weight:850;}
QLabel#smallCaps{color:#7f9bb5;font-size:8px;font-weight:850;letter-spacing:0.9px;}
QLabel#dashboardWelcome{color:#f7fbff;font-size:23px;font-weight:850;}
QLabel#dashboardDate{color:#8da9c3;font-size:9px;}
QLabel#dashboardClock{color:#9edfff;font-size:16px;font-weight:850;}
QLabel#brandAccent{color:#35d8ff;font-size:18px;font-weight:900;}
QLabel#liveSignal{color:#46e5b3;font-weight:850;font-size:10px;}
QLabel#signalName{color:#cde2f2;font-weight:750;font-size:10px;}
QLabel#signalValue{color:#f3fbff;font-weight:850;font-size:11px;}
QPushButton#nav{
    text-align:left;background:transparent;border:1px solid transparent;border-radius:9px;
    padding:10px 11px;color:#8fa9c2;font-size:11px;font-weight:750;
}
QPushButton#nav:hover{background:#102a42;color:#ffffff;border-color:#214d6b;}
QPushButton#nav:checked{
    background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #0d5b88,stop:1 #153e76);
    color:#ffffff;border-color:#1b88c0;
}
QPushButton#nav:disabled{color:#536b80;}
QPushButton#primary{
    background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #24c8ee,stop:1 #587fff);color:white;border:0;border-radius:9px;
    padding:9px 14px;font-weight:850;
}
QPushButton#primary:hover{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #3ed7f5,stop:1 #7092ff);}
QPushButton#secondary{
    background:#102b43;color:#bfeaff;border:1px solid #2b5b7a;
    border-radius:8px;padding:8px 12px;font-weight:750;
}
QPushButton#danger{
    background:#3b1c29;color:#ff9eaa;border:1px solid #743143;
    border-radius:8px;padding:8px 12px;font-weight:800;
}
QPushButton#tab{
    background:transparent;border:0;border-bottom:2px solid transparent;
    border-radius:0;padding:10px;color:#7e99b2;font-weight:650;
}
QPushButton#tab:hover{color:#dff5ff;}
QPushButton#tab:checked{color:#45d9ff;border-bottom-color:#45d9ff;}
QLineEdit,QTextEdit,QListWidget,QTableWidget,QComboBox{
    background:#0b1b2d;border:1px solid #284963;border-radius:8px;
    padding:8px;color:#eef7ff;selection-background-color:#164b6b;
}
QLineEdit:focus,QComboBox:focus{border-color:#37bfe9;}
QTableWidget{gridline-color:#1c3850;}
QHeaderView::section{
    background:#0d2135;color:#8fa8c0;padding:9px;border:0;
    border-bottom:1px solid #244663;font-weight:800;
}
QTableWidget::item{padding:8px;}
QTableWidget::item:selected{background:#123b57;color:#ffffff;}
QScrollBar:vertical{background:#071321;width:9px;}
QScrollBar::handle:vertical{background:#294b65;border-radius:5px;min-height:30px;}
QProgressBar{
    background:#081522;border:1px solid #25445e;border-radius:6px;
    text-align:center;color:#9ab1c7;height:10px;
}
QProgressBar::chunk{background:#22c7ec;border-radius:6px;}
QTabBar::tab{background:transparent;color:#7d97b0;padding:10px 12px;border:0;border-bottom:2px solid transparent;}
QTabBar::tab:hover{color:#dff5ff;}
QTabBar::tab:selected{color:#45d9ff;border-bottom:2px solid #45d9ff;font-weight:800;}
QToolTip{background:#071321;color:#ffffff;border:1px solid #315875;padding:6px;}
QLabel#warning{background:#3b2910;color:#ffd47a;border:1px solid #71521d;border-radius:8px;padding:8px;}
QSplitter::handle{background:#15334b;}
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

def pill(text, bg="#E8F3F4", fg="#0B6670", parent=None):
    x = QLabel(text, parent)
    x.setStyleSheet(
        f"background:{bg};color:{fg};border:1px solid {bg};"
        "border-radius:9px;padding:5px 8px;font-weight:800;font-size:10px;"
    )
    return x

def status_badge(text, kind="neutral", parent=None):
    palette = {
        "good": ("#E8F4EE", "#237A57", "#B8D8C8"),
        "fair": ("#FFF6E2", "#A66A00", "#E8D39A"),
        "poor": ("#FBEDEC", "#B33A3A", "#E2B9B6"),
        "info": ("#EAF0F7", "#315B84", "#C7D6E5"),
        "neutral": ("#F1F4F7", "#667483", "#D8E0E8"),
        "measured": ("#E8F3F4", "#0B6670", "#BBDADD"),
        "derived": ("#EEF0F7", "#6D628A", "#D2CEE1"),
        "demo": ("#FFF6E2", "#A66A00", "#E8D39A"),
        "model": ("#EEF0F7", "#6D628A", "#D2CEE1"),
        "unavailable": ("#F1F4F7", "#667483", "#D8E0E8"),
    }
    bg, fg, border = palette.get(kind, palette["neutral"])
    x = QLabel(text, parent)
    x.setStyleSheet(
        f"background:{bg};color:{fg};border:1px solid {border};"
        "border-radius:9px;padding:5px 8px;font-weight:800;font-size:10px;"
    )
    return x
