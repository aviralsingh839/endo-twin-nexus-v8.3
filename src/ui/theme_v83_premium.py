"""
CHRONO-PCOS V8.3+ / CHRONO-TWIN NEXUS V8.3 - Premium Scientific Medical Theme

Serious modern scientific clean typography diagrams accessible colors responsive mobile strong identity
Avoid excessive animations/fake claims/stock AI doctor imagery/exaggerated promises/100% accurate/fake hospital branding
Use clean typography/scientific diagrams/clear sections/accessible colors/responsive/mobile/strong identity

Design principles:
- Scientific: clean typography, data-driven, no fake claims, honest limitations, provenance first-class
- Medical: clinical, professional, trustworthy, disclaimer Research risk-screening not diagnosis
- Premium: polished, coherent, strong identity, consistent typography/icons/terminology/logo/nav

Patient app: simple friendly, large readable, accessibility-friendly, low complexity, clear explanations
Doctor app: professional dense, complete technical interface
Website: scientific accessible, clean typography, scientific diagrams, clear sections

Colors: accessible, WCAG AA compliant, scientific not stock AI doctor
"""

from __future__ import annotations
from PySide6.QtGui import QFont

# Font stack - clean, modern, scientific, readable
FONT_FAMILY = '"Inter", "Segoe UI", "Helvetica Neue", "Helvetica", "Arial", sans-serif'
FONT_FAMILY_MONO = '"JetBrains Mono", "Fira Code", "Consolas", "Monaco", monospace'
PAINTER_FONT = "Inter"
PAINTER_FONT_BOLD = "Inter"

# Scientific Medical Premium Palette - Dark Mode (default)
# Based on midnight ocean but refined for scientific credibility
DARK = {
    "bg": "#070d1a",
    "bg_top": "#0a1322",
    "panel": "#0d1626",
    "panel_alt": "#122035",
    "panel_hover": "#182842",
    "track": "#0a1322",
    "plot_bg": "#0b1424",
    "border": "#1e2d4a",
    "border_light": "#2c3e63",
    "text": "#e8eef7",
    "text_muted": "#94a6c2",
    "text_secondary": "#7a8db0",
    "accent": "#8ecbff",
    "accent_strong": "#3aa7f0",
    "accent_deep": "#2f6fd6",
    "indigo": "#7b8cff",
    "violet": "#a78bfa",
    "pink": "#f472b6",
    "green": "#34d399",
    "green_bright": "#4ade80",
    "yellow": "#fbbf24",
    "orange": "#fb923c",
    "red": "#f87171",
    "scientific_blue": "#3b82f6",
    "medical_teal": "#14b8a6",
    "premium_gold": "#f59e0b",
}

# Light mode - for accessibility, scientific papers, reports
LIGHT = {
    "bg": "#f8fafc",
    "bg_top": "#ffffff",
    "panel": "#ffffff",
    "panel_alt": "#f1f5f9",
    "panel_hover": "#e2e8f0",
    "track": "#f1f5f9",
    "plot_bg": "#ffffff",
    "border": "#e2e8f0",
    "border_light": "#cbd5e1",
    "text": "#0f172a",
    "text_muted": "#64748b",
    "text_secondary": "#94a3b8",
    "accent": "#0ea5e9",
    "accent_strong": "#0284c7",
    "accent_deep": "#0369a1",
    "indigo": "#6366f1",
    "violet": "#8b5cf6",
    "pink": "#ec4899",
    "green": "#10b981",
    "green_bright": "#059669",
    "yellow": "#f59e0b",
    "orange": "#f97316",
    "red": "#ef4444",
    "scientific_blue": "#2563eb",
    "medical_teal": "#0d9488",
    "premium_gold": "#d97706",
}

# Use dark as default for medical-tech premium feel
PALETTE = DARK

def painter_font(size: int, bold: bool = False, mono: bool = False) -> QFont:
    family = FONT_FAMILY_MONO if mono else PAINTER_FONT
    font = QFont(family, size)
    font.setBold(bold)
    # Improve readability
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
        "gray": p["text_muted"],
        "pink": p["pink"],
        "violet": p["violet"],
        "indigo": p["indigo"],
        "teal": p["medical_teal"],
        "scientific": p["scientific_blue"],
        "premium": p["premium_gold"],
    }.get(state, p["text_muted"])

def get_scientific_qss(palette=None, mode="dark") -> str:
    """Scientific Medical Premium QSS - clean, accessible, no fake claims"""
    p = palette or (DARK if mode == "dark" else LIGHT)
    
    return f"""
/* CHRONO-PCOS V8.3+ Scientific Medical Premium Theme */
/* Serious modern scientific clean typography accessible colors strong identity */

QWidget {{ 
    background: {p['bg']}; 
    color: {p['text']}; 
    font-family: {FONT_FAMILY}; 
    font-size: 11pt; 
    line-height: 1.5;
}}
QMainWindow, QDialog {{ background: {p['bg']}; }}

QScrollArea {{ background: transparent; border: none; }}
QScrollArea > QWidget > QWidget {{ background: transparent; }}

/* Header - scientific, not fake hospital branding */
QFrame#AppHeader {{ 
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {p['bg_top']}, stop:1 {p['panel_alt']});
    border: 1px solid {p['border']}; 
    border-radius: 14px; 
}}
QFrame#HeaderDivider {{ 
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {p['accent_strong']}, stop:0.5 {p['indigo']}, stop:1 {p['scientific_blue']});
    border: none; 
    border-radius: 2px; 
    height: 3px;
}}
QLabel#AppTitle {{ 
    font-size: 22pt; 
    font-weight: 700; 
    color: {p['accent']}; 
    letter-spacing: -0.02em;
    font-family: {FONT_FAMILY};
}}
QLabel#AppSubtitle {{ 
    font-size: 10.5pt; 
    color: {p['text_muted']}; 
    font-weight: 400;
}}
QLabel#Tagline {{
    font-size: 11pt;
    color: {p['text_secondary']};
    font-style: italic;
}}
QLabel#StatusPill {{ 
    font-size: 10pt; 
    font-weight: 600; 
    padding: 6px 14px; 
    border-radius: 20px;
    background: {p['panel_alt']}; 
    border: 1px solid {p['border_light']}; 
    color: {p['text_muted']}; 
}}

/* Panels - clean, scientific, clear sections */
QGroupBox {{ 
    background: {p['panel']};
    border: 1px solid {p['border_light']}; 
    border-radius: 12px; 
    margin-top: 12px; 
    padding: 12px;
    font-weight: 600;
}}
QGroupBox::title {{ 
    subcontrol-origin: margin; 
    left: 14px; 
    padding: 0 8px; 
    color: {p['accent']};
    font-weight: 700; 
    font-size: 10.5pt; 
    background: {p['panel']};
    border: 1px solid {p['border_light']}; 
    border-bottom: none; 
    border-top-left-radius: 6px;
    border-top-right-radius: 6px; 
}}

/* Vital Cards - medical, premium, data quality Good not raw unless advanced */
QFrame#VitalCard, QFrame#HormoneCard {{
    background: {p['panel_alt']};
    border: 1px solid {p['border_light']}; 
    border-radius: 12px;
}}
QFrame#VitalCard:hover, QFrame#HormoneCard:hover {{ 
    border-color: {p['accent_strong']}; 
    background: {p['panel_hover']};
}}
QFrame#VitalCard[state="green"]   {{ border-left: 4px solid {p['green']}; }}
QFrame#VitalCard[state="yellow"]  {{ border-left: 4px solid {p['yellow']}; }}
QFrame#VitalCard[state="orange"]  {{ border-left: 4px solid {p['orange']}; }}
QFrame#VitalCard[state="red"]     {{ border-left: 4px solid {p['red']}; }}
QFrame#VitalCard[state="blue"]    {{ border-left: 4px solid {p['accent_strong']}; }}
QFrame#VitalCard[state="gray"]    {{ border-left: 4px solid {p['border_light']}; }}

QLabel#VitalValue {{ 
    font-size: 20pt; 
    font-weight: 700; 
    color: {p['text']};
    font-family: {FONT_FAMILY};
}}
QLabel#VitalLabel {{
    font-size: 9pt;
    font-weight: 600;
    color: {p['text_muted']};
    text-transform: uppercase;
    letter-spacing: 0.05em;
}}
QLabel#HormoneValue {{ 
    font-size: 11pt; 
    font-weight: 600; 
    color: {p['text']}; 
}}
QLabel#HormoneTitle {{ 
    color: {p['accent']}; 
    font-weight: 700; 
    font-size: 10pt; 
}}
QLabel#SmallMuted {{ 
    color: {p['text_muted']}; 
    font-size: 9pt; 
}}
QLabel#DataQuality {{
    font-size: 9pt;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 10px;
    background: {p['panel']};
    border: 1px solid {p['border']};
}}
QLabel#Provenance {{
    font-size: 8pt;
    font-family: {FONT_FAMILY_MONO};
    color: {p['text_secondary']};
    background: {p['track']};
    padding: 2px 6px;
    border-radius: 4px;
}}
QLabel#WarningText {{ 
    color: {p['yellow']}; 
    font-weight: 600; 
    font-size: 10pt; 
}}
QLabel#Disclaimer {{
    font-size: 9pt;
    color: {p['text_secondary']};
    font-style: italic;
    background: {p['track']};
    padding: 8px;
    border-radius: 6px;
    border-left: 3px solid {p['yellow']};
}}

/* Buttons - premium, accessible, clear */
QPushButton {{
    background: {p['accent_deep']};
    border: 1px solid {p['accent_strong']}; 
    border-radius: 8px; 
    padding: 8px 16px; 
    font-weight: 600;
    font-size: 10.5pt;
    color: white;
}}
QPushButton:hover {{ 
    background: {p['accent_strong']};
    border-color: {p['accent']}; 
}}
QPushButton:pressed {{ 
    background: {p['accent_deep']}; 
}}
QPushButton:focus {{ 
    border: 2px solid {p['accent_strong']}; 
    outline: none;
}}
QPushButton:disabled {{ 
    background: {p['panel_alt']}; 
    border-color: {p['border']}; 
    color: {p['text_secondary']}; 
}}
QPushButton#Primary {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {p['accent_strong']}, stop:1 {p['accent_deep']});
    font-weight: 700;
}}
QPushButton#Secondary {{
    background: transparent;
    border: 1px solid {p['border_light']};
    color: {p['text']};
}}
QPushButton#Secondary:hover {{
    background: {p['panel_alt']};
    border-color: {p['accent_strong']};
}}

/* Inputs - accessible, large readable for patient app */
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTimeEdit {{
    background: {p['panel_alt']}; 
    border: 1px solid {p['border_light']}; 
    border-radius: 8px;
    padding: 8px 12px; 
    font-size: 11pt;
    min-height: 20px;
}}
QLineEdit:hover, QComboBox:hover, QSpinBox:hover, QDoubleSpinBox:hover, QTimeEdit:hover {{ 
    border-color: {p['accent_strong']}; 
}}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QTimeEdit:focus {{
    border-color: {p['accent_strong']}; 
    background: {p['panel']};
    border-width: 2px;
}}
QLineEdit:disabled {{
    background: {p['track']};
    color: {p['text_secondary']};
}}

/* Progress - scientific, data quality Good */
QProgressBar {{ 
    background: {p['track']}; 
    border: 1px solid {p['border']}; 
    border-radius: 8px;
    text-align: center; 
    font-size: 9pt; 
    color: {p['text_muted']}; 
    height: 8px;
}}
QProgressBar::chunk {{ 
    background: {p['accent_strong']}; 
    border-radius: 8px; 
}}

/* Tabs - consistent navigation, strong identity */
QTabWidget::pane {{ 
    border: 1px solid {p['border_light']}; 
    border-radius: 12px; 
    top: -1px;
    background: {p['panel']}; 
}}
QTabBar::tab {{
    background: {p['panel']}; 
    border: 1px solid {p['border']}; 
    border-top-left-radius: 10px;
    border-top-right-radius: 10px; 
    padding: 10px 16px; 
    margin: 2px 2px 0 2px;
    font-size: 10pt; 
    font-weight: 500;
    color: {p['text_muted']};
}}
QTabBar::tab:selected {{
    background: {p['accent_deep']};
    color: white; 
    font-weight: 600; 
    border-color: {p['accent_deep']};
}}
QTabBar::tab:hover:!selected {{ 
    background: {p['panel_hover']}; 
    color: {p['text']}; 
}}

/* Text - clean typography, understandable language */
QTextEdit {{
    background: {p['panel_alt']}; 
    border: 1px solid {p['border']}; 
    border-radius: 10px; 
    padding: 12px;
    font-size: 10.5pt; 
    line-height: 1.6;
    selection-background-color: {p['accent_deep']};
}}
QTextEdit:focus {{ 
    border-color: {p['accent_strong']}; 
}}

/* Tables - professional dense for doctor PC */
QTableWidget {{
    background: {p['panel_alt']}; 
    border: 1px solid {p['border']}; 
    border-radius: 8px;
    font-size: 10pt; 
    gridline-color: {p['border']}; 
    selection-background-color: {p['accent_deep']};
    alternate-background-color: {p['track']};
}}
QTableWidget::item {{ padding: 6px 8px; }}
QTableWidget::item:selected {{ background: {p['accent_deep']}; color: white; }}
QHeaderView::section {{ 
    background: {p['panel']}; 
    color: {p['accent']}; 
    font-weight: 700; 
    padding: 8px;
    border: none; 
    border-bottom: 2px solid {p['border_light']}; 
    font-size: 9.5pt;
    text-transform: uppercase;
    letter-spacing: 0.03em;
}}

QListWidget {{ 
    background: {p['panel_alt']}; 
    border: 1px solid {p['border']}; 
    border-radius: 10px;
    padding: 8px; 
    outline: 0; 
    font-size: 10.5pt; 
}}
QListWidget::item {{ 
    border: none; 
    margin: 3px; 
    padding: 8px;
    border-radius: 8px;
    background: transparent; 
}}
QListWidget::item:hover {{ 
    background: {p['panel_hover']}; 
}}
QListWidget::item:selected {{ 
    background: {p['accent_deep']}; 
    color: white;
}}

/* Scrollbars - minimal, not excessive animations */
QScrollBar:vertical {{ background: transparent; width: 8px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: {p['border_light']}; border-radius: 4px; min-height: 30px; }}
QScrollBar::handle:vertical:hover {{ background: {p['text_muted']}; }}
QScrollBar:horizontal {{ background: transparent; height: 8px; margin: 2px; }}
QScrollBar::handle:horizontal {{ background: {p['border_light']}; border-radius: 4px; min-width: 30px; }}
QScrollBar::handle:horizontal:hover {{ background: {p['text_muted']}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}

/* Scientific specific */
QFrame#ScientificCard {{
    background: {p['panel']};
    border: 1px solid {p['border_light']};
    border-radius: 12px;
    border-left: 4px solid {p['scientific_blue']};
}}
QFrame#MedicalCard {{
    background: {p['panel']};
    border: 1px solid {p['border_light']};
    border-radius: 12px;
    border-left: 4px solid {p['medical_teal']};
}}
QFrame#PremiumCard {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {p['panel']}, stop:1 {p['panel_alt']});
    border: 1px solid {p['border_light']};
    border-radius: 12px;
    border-top: 3px solid {p['premium_gold']};
}}
QLabel#ScientificTitle {{
    font-size: 12pt;
    font-weight: 700;
    color: {p['scientific_blue']};
    letter-spacing: -0.01em;
}}
QLabel#MedicalTitle {{
    font-size: 12pt;
    font-weight: 700;
    color: {p['medical_teal']};
}}
"""

# Default QSS
DARK_QSS = get_scientific_qss(DARK, "dark")
LIGHT_QSS = get_scientific_qss(LIGHT, "light")

# For backward compatibility, export same names as old theme.py
BG = DARK["bg"]
BG_TOP = DARK["bg_top"]
PANEL = DARK["panel"]
PANEL_ALT = DARK["panel_alt"]
PANEL_HOVER = DARK["panel_hover"]
TRACK = DARK["track"]
PLOT_BG = DARK["plot_bg"]
BORDER = DARK["border"]
BORDER_LIGHT = DARK["border_light"]
TEXT = DARK["text"]
TEXT_MUTED = DARK["text_muted"]
ACCENT = DARK["accent"]
ACCENT_STRONG = DARK["accent_strong"]
ACCENT_DEEP = DARK["accent_deep"]
INDIGO = DARK["indigo"]
VIOLET = DARK["violet"]
PINK = DARK["pink"]
GREEN = DARK["green"]
GREEN_BRIGHT = DARK["green_bright"]
YELLOW = DARK["yellow"]
ORANGE = DARK["orange"]
RED = DARK["red"]

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
        f"border-radius: 7px; text-align: center; font-size: 9.5pt; color: {p['text_muted']}; }}"
        f"QProgressBar::chunk {{ background: {color}; border-radius: 7px; }}"
    )

def style_plot(plot, y_label: str = "", x_label: str = "", palette=None) -> None:
    import pyqtgraph as pg
    p = palette or DARK
    plot.setBackground(p["plot_bg"])
    plot.showGrid(x=True, y=True, alpha=0.16)
    for axis_name, label in (("left", y_label), ("bottom", x_label)):
        axis = plot.getAxis(axis_name)
        axis.setPen(pg.mkPen(p["border_light"]))
        axis.setTextPen(pg.mkPen(p["text_muted"]))
        axis.setTickFont(painter_font(9))
        if label:
            axis.setLabel(label)
        else:
            axis.setLabel("")
    plot.getViewBox().setDefaultPadding(0.02)
