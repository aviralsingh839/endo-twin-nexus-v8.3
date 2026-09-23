"""Shared ENDO-TWIN V8.6 reference-inspired workstation visual language.

Used by the Doctor PC and Patient PC workstations (both set ``APP_QSS`` at
startup).

Accessibility rules for anything added here:
  * No text below 11px. The original sheet used 8px/9px footnotes, which is
    roughly 6pt on a 96-dpi screen.
  * White button labels sit on the dark stops of the gradient. White on the
    previous ``#24c8ee`` stop measured 1.99:1 — the label was unreadable.
  * Every interactive control gets a ``:focus`` rule, so keyboard focus is
    always visible.
  * Badge colours are contrast-checked against their own tinted background.
    Run ``python scripts/diagnostics/a11y_contrast_audit.py`` after editing.
"""
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QHBoxLayout

# Focus ring colour: clears 3:1 against every surface, card and input below.
FOCUS = "#8FE3FF"

APP_QSS = f"""
QMainWindow,QWidget{{
    background:#050d18;color:#eef7ff;
    font-family:"Inter","Noto Sans","Segoe UI",sans-serif;font-size:12px;
}}
QFrame#sidebar{{
    background:#071321;border-right:1px solid #1c3852;
}}
QFrame#topbar{{
    background:#09182a;border-bottom:1px solid #244663;
}}
QFrame#patientHeader{{
    background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #10253a,stop:1 #0b1b2c);
    border:1px solid #244663;border-radius:14px;
}}
QFrame#card{{
    background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #10243a,stop:1 #0b1b2d);
    border:1px solid #244663;border-radius:14px;
}}
QFrame#soft{{
    background:#0c1d30;border:1px solid #203f5b;border-radius:11px;
}}
QFrame#hero{{
    background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #0d3044,stop:1 #0b1d31);
    border:1px solid #245a76;border-radius:12px;
}}
QLabel#brand{{color:#f6fbff;font-size:20px;font-weight:850;}}
QLabel#eyebrow{{color:#5fddff;font-size:11px;font-weight:850;letter-spacing:1.2px;}}
QLabel#title{{color:#f4f9ff;font-size:29px;font-weight:850;}}
QLabel#subtitle{{color:#a4bcd3;font-size:13px;font-weight:650;}}
QLabel#muted{{color:#9db4cb;font-size:12px;}}
QLabel#metricValue{{color:#f4fbff;font-size:25px;font-weight:850;}}
QLabel#bigValue{{color:#f4fbff;font-size:37px;font-weight:850;}}
QLabel#sectionTitle{{color:#eaf6ff;font-size:15px;font-weight:850;}}
QLabel#smallCaps{{color:#9db4cb;font-size:11px;font-weight:850;letter-spacing:0.9px;}}
QLabel#dashboardWelcome{{color:#f7fbff;font-size:23px;font-weight:850;}}
QLabel#dashboardDate{{color:#a2bad2;font-size:12px;}}
QLabel#dashboardClock{{color:#a8e6ff;font-size:16px;font-weight:850;}}
QLabel#brandAccent{{color:#4ddcff;font-size:18px;font-weight:900;}}
QLabel#liveSignal{{color:#5ce9be;font-weight:850;font-size:12px;}}
QLabel#signalName{{color:#cde2f2;font-weight:750;font-size:12px;}}
QLabel#signalValue{{color:#f3fbff;font-weight:850;font-size:12px;}}
QPushButton#nav{{
    text-align:left;background:transparent;border:1px solid transparent;border-radius:9px;
    padding:10px 11px;color:#a3bcd2;font-size:12px;font-weight:750;min-height:20px;
}}
QPushButton#nav:hover{{background:#102a42;color:#ffffff;border-color:#2d6288;}}
QPushButton#nav:checked{{
    background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #0d5b88,stop:1 #153e76);
    color:#ffffff;border-color:#2b9fd4;
}}
QPushButton#nav:focus{{border:2px solid {FOCUS};}}
QPushButton#nav:disabled{{color:#6b8299;}}
QPushButton#primary{{
    background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #0B6F89,stop:1 #3A56C4);
    color:#ffffff;border:2px solid transparent;border-radius:9px;
    padding:9px 14px;font-weight:850;min-height:22px;
}}
QPushButton#primary:hover{{
    background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #127FA0,stop:1 #4A66D4);
}}
QPushButton#primary:focus{{border:2px solid {FOCUS};}}
QPushButton#secondary{{
    background:#102b43;color:#bfeaff;border:1px solid #38708f;
    border-radius:8px;padding:8px 12px;font-weight:750;min-height:20px;
}}
QPushButton#secondary:hover{{background:#16395a;border-color:#4a89ab;}}
QPushButton#secondary:focus{{border:2px solid {FOCUS};}}
QPushButton#danger{{
    background:#3b1c29;color:#ffb3bd;border:1px solid #8a3d51;
    border-radius:8px;padding:8px 12px;font-weight:800;min-height:20px;
}}
QPushButton#danger:hover{{background:#4a2334;border-color:#a94a61;}}
QPushButton#danger:focus{{border:2px solid {FOCUS};}}
QPushButton#tab{{
    background:transparent;border:0;border-bottom:2px solid transparent;
    border-radius:0;padding:10px;color:#96b0c7;font-weight:650;
}}
QPushButton#tab:hover{{color:#e8f8ff;}}
QPushButton#tab:checked{{color:#5fddff;border-bottom-color:#5fddff;}}
QPushButton#tab:focus{{border:2px solid {FOCUS};border-radius:6px;}}
QLineEdit,QTextEdit,QPlainTextEdit,QListWidget,QTableWidget,QComboBox{{
    background:#0b1b2d;border:1px solid #2d5470;border-radius:8px;
    padding:8px;color:#eef7ff;selection-background-color:#17567c;selection-color:#ffffff;
}}
QLineEdit:focus,QTextEdit:focus,QPlainTextEdit:focus,QListWidget:focus,
QTableWidget:focus,QComboBox:focus{{border:2px solid {FOCUS};}}
QLineEdit:disabled,QComboBox:disabled{{color:#7b90a4;background:#0a1626;}}
QTableWidget{{gridline-color:#1c3850;}}
QHeaderView::section{{
    background:#0d2135;color:#a3bcd2;padding:9px;border:0;
    border-bottom:1px solid #244663;font-weight:800;
}}
QTableWidget::item{{padding:8px;}}
QTableWidget::item:selected{{background:#17567c;color:#ffffff;}}
QListWidget::item:selected{{background:#17567c;color:#ffffff;}}
QListWidget::item:hover,QTableWidget::item:hover{{background:#14304a;}}
QScrollBar:vertical{{background:#071321;width:12px;margin:2px;}}
QScrollBar::handle:vertical{{background:#3a617f;border-radius:6px;min-height:30px;}}
QScrollBar::handle:vertical:hover{{background:#4d7a9c;}}
QScrollBar:horizontal{{background:#071321;height:12px;margin:2px;}}
QScrollBar::handle:horizontal{{background:#3a617f;border-radius:6px;min-width:30px;}}
QScrollBar::handle:horizontal:hover{{background:#4d7a9c;}}
QScrollBar::add-line,QScrollBar::sub-line{{width:0;height:0;}}
QScrollBar::add-page,QScrollBar::sub-page{{background:transparent;}}
QProgressBar{{
    background:#081522;border:1px solid #2d5470;border-radius:6px;
    text-align:center;color:#c3d5e5;height:14px;font-size:11px;
}}
QProgressBar::chunk{{background:#35cdf2;border-radius:6px;}}
QTabBar::tab{{
    background:transparent;color:#96b0c7;padding:10px 12px;border:0;
    border-bottom:2px solid transparent;
}}
QTabBar::tab:hover{{color:#e8f8ff;}}
QTabBar::tab:selected{{color:#5fddff;border-bottom:2px solid #5fddff;font-weight:800;}}
QTabBar::tab:focus{{border:2px solid {FOCUS};}}
QToolTip{{background:#071321;color:#ffffff;border:1px solid {FOCUS};padding:6px;font-size:12px;}}
QLabel#warning{{background:#3b2910;color:#ffdf9e;border:1px solid #8a6626;border-radius:8px;padding:8px;}}
QSplitter::handle{{background:#15334b;}}
QCheckBox,QRadioButton{{spacing:7px;min-height:22px;}}
QCheckBox:focus,QRadioButton:focus{{border:2px solid {FOCUS};border-radius:5px;}}
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
    # The triple reads as one unit to assistive tech: "title: value, detail".
    frame.setAccessibleName(f"{title}: {value}")
    frame.setAccessibleDescription(detail)
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
    """Small tinted label. Default colours measure 5.89:1."""
    x = QLabel(text, parent)
    x.setStyleSheet(
        f"background:{bg};color:{fg};border:1px solid {fg};"
        "border-radius:9px;padding:5px 8px;font-weight:800;font-size:11px;"
    )
    return x


# Every foreground has been contrast-checked against its own background.
# `fair`/`demo` and `neutral`/`unavailable` were 4.17:1 and 4.33:1 before.
STATUS_PALETTE = {
    "good": ("#E8F4EE", "#1F6D4D", "#B8D8C8"),
    "fair": ("#FFF6E2", "#9C6200", "#E8D39A"),
    "poor": ("#FBEDEC", "#A53232", "#E2B9B6"),
    "info": ("#EAF0F7", "#315B84", "#C7D6E5"),
    "neutral": ("#F1F4F7", "#5A6875", "#C6D0D9"),
    "measured": ("#E8F3F4", "#0B6670", "#BBDADD"),
    "derived": ("#EEF0F7", "#6D628A", "#D2CEE1"),
    "demo": ("#FFF6E2", "#9C6200", "#E8D39A"),
    "model": ("#EEF0F7", "#6D628A", "#D2CEE1"),
    "unavailable": ("#F1F4F7", "#5A6875", "#C6D0D9"),
}


def status_badge(text, kind="neutral", parent=None):
    """Tinted provenance/status chip.

    The word in ``text`` is the signal; the colour only reinforces it, so the
    badge still reads correctly in greyscale.
    """
    bg, fg, border = STATUS_PALETTE.get(kind, STATUS_PALETTE["neutral"])
    x = QLabel(text, parent)
    x.setStyleSheet(
        f"background:{bg};color:{fg};border:1px solid {border};"
        "border-radius:9px;padding:5px 8px;font-weight:800;font-size:11px;"
    )
    x.setAccessibleName(f"{kind}: {text}")
    return x
