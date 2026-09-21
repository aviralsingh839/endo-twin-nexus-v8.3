"""ENDO-TWIN visual system — modern scientific/medical desktop UI.

The visual language is intentionally vivid but restrained:
deep ink surfaces, cyan/teal/indigo/pink accents, strong hierarchy,
large readable metrics, explicit state colors, and generous spacing.

No visual element implies clinical validity. Data provenance and unavailable
states remain visible by design.
"""
from __future__ import annotations

from PySide6.QtGui import QFont

FONT_FAMILY = '"Inter", "Segoe UI", "Noto Sans", "Helvetica Neue", "Arial", sans-serif'
FONT_FAMILY_MONO = '"JetBrains Mono", "Fira Code", "Consolas", monospace'
PAINTER_FONT = "Inter"
PAINTER_FONT_BOLD = "Inter"

DARK = {
    "bg": "#070B14",
    "bg_top": "#0A1020",
    "sidebar": "#0B1221",
    "panel": "#101A2D",
    "panel_alt": "#14223A",
    "panel_hover": "#1A2C49",
    "track": "#09111F",
    "plot_bg": "#0D1728",
    "border": "#213452",
    "border_light": "#2C456A",
    "text": "#F4F7FB",
    "text_muted": "#9BAAC2",
    "text_secondary": "#71839F",
    "accent": "#62E6FF",
    "accent_strong": "#29B6F6",
    "accent_deep": "#1176D2",
    "indigo": "#8B7CFF",
    "violet": "#B38CFF",
    "pink": "#FF6FB5",
    "teal": "#20D5B2",
    "green": "#45E09C",
    "yellow": "#FFD166",
    "orange": "#FF9E5E",
    "red": "#FF667C",
    "scientific_blue": "#4EA8FF",
    "medical_teal": "#20C7B0",
    "premium_gold": "#FFC857",
}

LIGHT = {
    "bg": "#F5F8FC",
    "bg_top": "#FFFFFF",
    "sidebar": "#FFFFFF",
    "panel": "#FFFFFF",
    "panel_alt": "#F0F5FB",
    "panel_hover": "#E7EEF8",
    "track": "#E8EEF6",
    "plot_bg": "#FFFFFF",
    "border": "#D8E2EE",
    "border_light": "#C4D2E3",
    "text": "#122033",
    "text_muted": "#5E7088",
    "text_secondary": "#8291A5",
    "accent": "#0AA9D8",
    "accent_strong": "#087FB7",
    "accent_deep": "#0B5EA8",
    "indigo": "#645CE6",
    "violet": "#8059D9",
    "pink": "#D94E91",
    "teal": "#079D89",
    "green": "#0C9E67",
    "yellow": "#C88A00",
    "orange": "#D86B16",
    "red": "#C53751",
    "scientific_blue": "#2E7CD6",
    "medical_teal": "#078B79",
    "premium_gold": "#B97C00",
}

PALETTE = DARK


def painter_font(size: int, bold: bool = False, mono: bool = False) -> QFont:
    font = QFont(FONT_FAMILY_MONO if mono else PAINTER_FONT, size)
    font.setBold(bold)
    font.setStyleStrategy(QFont.PreferAntialias)
    return font


def status_color(state: str, palette=None) -> str:
    p = palette or PALETTE
    return {
        "green": p["green"],
        "yellow": p["yellow"],
        "orange": p["orange"],
        "red": p["red"],
        "blue": p["accent_strong"],
        "teal": p["teal"],
        "pink": p["pink"],
        "violet": p["violet"],
        "indigo": p["indigo"],
        "gray": p["text_muted"],
    }.get(str(state).lower(), p["text_muted"])


def get_scientific_qss(p=None, mode: str = "dark") -> str:
    p = p or PALETTE
    return f"""
* {{
    font-family: {FONT_FAMILY};
    color: {p["text"]};
}}

QWidget {{
    background: {p["bg"]};
}}

QMainWindow {{
    background: {p["bg"]};
}}

QStatusBar {{
    background: {p["sidebar"]};
    border-top: 1px solid {p["border"]};
    color: {p["text_secondary"]};
    padding: 5px 10px;
}}

QFrame#AppHeader {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {p["panel"]}, stop:0.55 {p["panel_alt"]}, stop:1 #14263D);
    border: 1px solid {p["border_light"]};
    border-radius: 18px;
}}

QFrame#BrandMark {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 {p["accent_strong"]}, stop:0.5 {p["indigo"]}, stop:1 {p["pink"]});
    border-radius: 14px;
}}

QLabel#BrandTitle {{
    font-size: 18pt;
    font-weight: 800;
    letter-spacing: 0.02em;
}}

QLabel#BrandSubtitle {{
    color: {p["text_muted"]};
    font-size: 9.5pt;
}}

QLabel#SectionEyebrow {{
    color: {p["accent"]};
    font-size: 8.5pt;
    font-weight: 800;
    letter-spacing: 0.08em;
}}

QLabel#HeroTitle {{
    font-size: 18pt;
    font-weight: 800;
}}

QLabel#HeroSubtitle {{
    color: {p["text_muted"]};
    font-size: 10pt;
}}

QLabel#MetricLabel {{
    color: {p["text_muted"]};
    font-size: 9pt;
    font-weight: 700;
}}

QLabel#MetricValue {{
    font-size: 19pt;
    font-weight: 800;
    color: {p["text"]};
}}

QLabel#MetricDetail {{
    color: {p["text_secondary"]};
    font-size: 8.5pt;
}}

QLabel#BigValue {{
    color: {p["text"]};
    font-size: 10.5pt;
    font-weight: 750;
    background: {p["track"]};
    border: 1px solid {p["border"]};
    border-radius: 9px;
    padding: 8px 10px;
}}

QLabel#SmallMuted, QLabel#MutedPanelText {{
    color: {p["text_muted"]};
}}

QLabel#WarningText {{
    color: {p["yellow"]};
    font-weight: 700;
}}

QFrame#Sidebar {{
    background: {p["sidebar"]};
    border: 1px solid {p["border"]};
    border-radius: 18px;
}}

QPushButton#NavButton {{
    text-align: left;
    background: transparent;
    border: 1px solid transparent;
    border-radius: 11px;
    padding: 10px 13px;
    min-height: 24px;
    color: {p["text_muted"]};
    font-size: 10pt;
    font-weight: 650;
}}

QPushButton#NavButton:hover {{
    background: {p["panel_hover"]};
    color: {p["text"]};
    border-color: {p["border"]};
}}

QPushButton#NavButton:checked {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {p["accent_deep"]}, stop:1 {p["indigo"]});
    color: white;
    border-color: rgba(255,255,255,0.16);
}}

QPushButton#Primary {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {p["accent_strong"]}, stop:1 {p["indigo"]});
    border: none;
    border-radius: 10px;
    padding: 9px 15px;
    font-weight: 750;
    color: white;
}}

QPushButton#Primary:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #3FC8FF, stop:1 #A08DFF);
}}

QPushButton#Secondary {{
    background: {p["panel_alt"]};
    border: 1px solid {p["border_light"]};
    border-radius: 10px;
    padding: 9px 14px;
    font-weight: 650;
}}

QPushButton#Secondary:hover {{
    background: {p["panel_hover"]};
    border-color: {p["accent_strong"]};
}}

QPushButton#Danger {{
    background: rgba(255,102,124,0.12);
    border: 1px solid rgba(255,102,124,0.38);
    color: {p["red"]};
    border-radius: 10px;
    padding: 9px 14px;
    font-weight: 700;
}}

QPushButton:disabled {{
    background: {p["track"]};
    border: 1px solid {p["border"]};
    color: {p["text_secondary"]};
}}

QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTimeEdit {{
    background: {p["panel_alt"]};
    border: 1px solid {p["border_light"]};
    border-radius: 10px;
    padding: 8px 10px;
    min-height: 22px;
}}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QTimeEdit:focus {{
    border: 2px solid {p["accent_strong"]};
    background: {p["panel"]};
}}

QGroupBox {{
    background: {p["panel"]};
    border: 1px solid {p["border"]};
    border-radius: 16px;
    margin-top: 12px;
    padding: 18px 14px 14px 14px;
    font-weight: 750;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 14px;
    padding: 2px 8px;
    background: {p["panel"]};
    color: {p["accent"]};
}}

QFrame#MetricCard, QFrame#ScientificCard, QFrame#MedicalCard, QFrame#PremiumCard {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 {p["panel"]}, stop:1 {p["panel_alt"]});
    border: 1px solid {p["border"]};
    border-radius: 16px;
}}

QFrame#MetricCard:hover, QFrame#ScientificCard:hover,
QFrame#MedicalCard:hover, QFrame#PremiumCard:hover {{
    border-color: {p["accent_strong"]};
}}

QFrame#PremiumCard {{
    border-top: 3px solid {p["pink"]};
}}

QFrame#WarningCard {{
    background: rgba(255,209,102,0.08);
    border: 1px solid rgba(255,209,102,0.28);
    border-radius: 14px;
}}

QFrame#StatusPill {{
    background: {p["track"]};
    border: 1px solid {p["border_light"]};
    border-radius: 12px;
}}

QTabWidget::pane {{
    border: none;
    background: transparent;
}}

QTabBar {{
    qproperty-drawBase: 0;
}}

QTabBar::tab {{
    background: {p["panel_alt"]};
    border: 1px solid {p["border"]};
    border-radius: 10px;
    padding: 9px 14px;
    margin: 2px;
    color: {p["text_muted"]};
    font-weight: 650;
}}

QTabBar::tab:hover {{
    background: {p["panel_hover"]};
    color: {p["text"]};
}}

QTabBar::tab:selected {{
    background: {p["accent_deep"]};
    border-color: {p["accent_strong"]};
    color: white;
}}

QTextEdit, QPlainTextEdit {{
    background: {p["panel_alt"]};
    border: 1px solid {p["border"]};
    border-radius: 12px;
    padding: 10px;
    selection-background-color: {p["accent_deep"]};
}}

QListWidget, QTableWidget {{
    background: {p["panel_alt"]};
    border: 1px solid {p["border"]};
    border-radius: 12px;
    alternate-background-color: {p["track"]};
}}

QListWidget::item {{
    border-radius: 9px;
    padding: 8px;
    margin: 2px;
}}

QListWidget::item:hover {{
    background: {p["panel_hover"]};
}}

QListWidget::item:selected {{
    background: {p["accent_deep"]};
    color: white;
}}

QHeaderView::section {{
    background: {p["panel"]};
    border: none;
    border-bottom: 1px solid {p["border"]};
    color: {p["text_muted"]};
    font-weight: 750;
    padding: 8px;
}}

QProgressBar {{
    background: {p["track"]};
    border: 1px solid {p["border"]};
    border-radius: 7px;
    text-align: center;
    min-height: 10px;
}}

QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {p["accent_strong"]}, stop:1 {p["teal"]});
    border-radius: 7px;
}}

QScrollBar:vertical {{
    background: transparent;
    width: 8px;
}}
QScrollBar::handle:vertical {{
    background: {p["border_light"]};
    border-radius: 4px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: {p["accent_strong"]};
}}
QScrollBar::add-line, QScrollBar::sub-line {{
    width: 0;
    height: 0;
}}
QScrollBar:horizontal {{
    background: transparent;
    height: 8px;
}}
QScrollBar::handle:horizontal {{
    background: {p["border_light"]};
    border-radius: 4px;
}}

QFrame#FooterBar {{
    background: {p["sidebar"]};
    border-top: 1px solid {p["border"]};
}}

QLabel#FooterText {{
    color: {p["text_secondary"]};
    font-size: 8.5pt;
}}

QLabel#Good {{
    color: {p["green"]};
    font-weight: 800;
}}
QLabel#Warn {{
    color: {p["yellow"]};
    font-weight: 800;
}}
QLabel#Error {{
    color: {p["red"]};
    font-weight: 800;
}}
"""


DARK_QSS = get_scientific_qss(DARK, "dark")
LIGHT_QSS = get_scientific_qss(LIGHT, "light")

BG = DARK["bg"]
BG_TOP = DARK["bg_top"]
SIDEBAR = DARK["sidebar"]
PANEL = DARK["panel"]
PANEL_ALT = DARK["panel_alt"]
PANEL_HOVER = DARK["panel_hover"]
TRACK = DARK["track"]
PLOT_BG = DARK["plot_bg"]
BORDER = DARK["border"]
BORDER_LIGHT = DARK["border_light"]
TEXT = DARK["text"]
TEXT_MUTED = DARK["text_muted"]
TEXT_SECONDARY = DARK["text_secondary"]
ACCENT = DARK["accent"]
ACCENT_STRONG = DARK["accent_strong"]
ACCENT_DEEP = DARK["accent_deep"]
INDIGO = DARK["indigo"]
VIOLET = DARK["violet"]
PINK = DARK["pink"]
TEAL = DARK["teal"]
GREEN = DARK["green"]
GREEN_BRIGHT = DARK["green"]
YELLOW = DARK["yellow"]
ORANGE = DARK["orange"]
RED = DARK["red"]
SCIENTIFIC_BLUE = DARK["scientific_blue"]
MEDICAL_TEAL = DARK["medical_teal"]
PREMIUM_GOLD = DARK["premium_gold"]


def progress_state_qss(value: float, palette=None) -> str:
    p = palette or DARK
    if value < 35:
        color = p["green"]
    elif value < 65:
        color = p["yellow"]
    elif value < 80:
        color = p["orange"]
    else:
        color = p["red"]
    return (
        f"QProgressBar {{ background: {p['track']}; border: 1px solid {p['border']}; "
        f"border-radius: 7px; text-align: center; color: {p['text_muted']}; }}"
        f"QProgressBar::chunk {{ background: {color}; border-radius: 7px; }}"
    )


def style_plot(plot, y_label: str = "", x_label: str = "", palette=None) -> None:
    import pyqtgraph as pg
    p = palette or DARK
    plot.setBackground(p["plot_bg"])
    plot.showGrid(x=True, y=True, alpha=0.18)
    for axis_name, label in (("left", y_label), ("bottom", x_label)):
        axis = plot.getAxis(axis_name)
        axis.setPen(pg.mkPen(p["border_light"]))
        axis.setTextPen(pg.mkPen(p["text_muted"]))
        axis.setTickFont(painter_font(9))
        axis.setLabel(label or "")
    plot.getViewBox().setDefaultPadding(0.02)
