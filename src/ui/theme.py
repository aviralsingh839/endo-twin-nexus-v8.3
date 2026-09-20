"""Shared visual theme for the CHRONO-PCOS dashboard - Scientific Medical Premium V8.3+

CHRONO-PCOS V8.3+ / CHRONO-TWIN NEXUS V8.3 - Premium Scientific Medical Theme
Serious modern scientific clean typography diagrams accessible colors responsive mobile strong identity
Avoid excessive animations/fake claims/stock AI doctor imagery/exaggerated promises/100% accurate/fake hospital branding
Use clean typography/scientific diagrams/clear sections/accessible colors/responsive/mobile/strong identity

Centralizes the font stack, the color palette and the dark stylesheet so every
tab and custom painted widget uses the same look. The palette is a "midnight
ocean" medical-tech scheme: deep navy backgrounds, layered panels and a
cyan → indigo → pink accent family (the pink nods to the women's-health
domain without sacrificing a clinical feel). Enhanced for V8.3+ scientific medical premium.

Design principles:
- Scientific: clean typography, data-driven, no fake claims, honest limitations, provenance first-class
- Medical: clinical, professional, trustworthy, disclaimer Research risk-screening not diagnosis
- Premium: polished, coherent, strong identity, consistent typography/icons/terminology/logo/nav

Chosen font stack (Segoe UI → Inter → Helvetica Neue → Arial) renders well on
Windows, Linux and macOS. Inter preferred for scientific readability.

See also: theme_v83_premium.py for enhanced scientific medical premium theme with light/dark modes,
accessible colors WCAG AA, scientific/medical/premium cards, data quality, provenance labels.
"""
from __future__ import annotations

from PySide6.QtGui import QFont

# Qt stylesheet font-family stack.
FONT_FAMILY = '"Segoe UI", "Inter", "Helvetica Neue", "Helvetica", "Arial", sans-serif'
# QFont() family for custom-painted widgets (gauges, clocks, radars, twin flow).
PAINTER_FONT = "Segoe UI"

# ----------------------------------------------------------------- palette --
# Backgrounds (deep navy, slightly layered).
BG = "#070d1a"
BG_TOP = "#0a1322"
PANEL = "#0d1626"
PANEL_ALT = "#122035"
PANEL_HOVER = "#182842"
TRACK = "#0a1322"
PLOT_BG = "#0b1424"

# Borders.
BORDER = "#1e2d4a"
BORDER_LIGHT = "#2c3e63"

# Text.
TEXT = "#e8eef7"
TEXT_MUTED = "#94a6c2"

# Accent family (cyan → blue → indigo → violet → pink).
ACCENT = "#8ecbff"          # bright ice-blue, used for titles / accent text
ACCENT_STRONG = "#3aa7f0"   # cyan highlight
ACCENT_DEEP = "#2f6fd6"     # button base blue
INDIGO = "#7b8cff"
VIOLET = "#a78bfa"
PINK = "#f472b6"

# Semantics.
GREEN = "#34d399"
GREEN_BRIGHT = "#4ade80"
YELLOW = "#fbbf24"
ORANGE = "#fb923c"
RED = "#f87171"


def painter_font(size: int, bold: bool = False) -> QFont:
    font = QFont(PAINTER_FONT, size)
    font.setBold(bold)
    return font


def status_color(state: str) -> str:
    """Map a semantic state name to its hex color."""
    return {
        "green": GREEN,
        "yellow": YELLOW,
        "orange": ORANGE,
        "red": RED,
        "blue": ACCENT_STRONG,
        "gray": TEXT_MUTED,
        "pink": PINK,
        "violet": VIOLET,
        "indigo": INDIGO,
    }.get(state, TEXT_MUTED)


def progress_state_qss(value: float) -> str:
    """Stylesheet for a QProgressBar whose chunk color tracks the value.

    Low values render green, mid amber, high orange/red. The track keeps the
    shared dark look.
    """
    if value < 35:
        color = GREEN
    elif value < 65:
        color = YELLOW
    elif value < 80:
        color = ORANGE
    else:
        color = RED
    return (
        f"QProgressBar {{ background: {TRACK}; border: 1px solid {BORDER}; "
        f"border-radius: 7px; text-align: center; font-size: 9.5pt; color: {TEXT_MUTED}; }}"
        f"QProgressBar::chunk {{ background: {color}; border-radius: 7px; }}"
    )


def style_plot(plot, y_label: str = "", x_label: str = "") -> None:
    """Apply the shared dark look to a pyqtgraph PlotWidget."""
    import pyqtgraph as pg

    plot.setBackground(PLOT_BG)
    plot.showGrid(x=True, y=True, alpha=0.16)
    for axis_name, label in (("left", y_label), ("bottom", x_label)):
        axis = plot.getAxis(axis_name)
        axis.setPen(pg.mkPen(BORDER_LIGHT))
        axis.setTextPen(pg.mkPen(TEXT_MUTED))
        axis.setTickFont(painter_font(9))
        if label:
            axis.setLabel(label)
        else:
            axis.setLabel("")
    plot.getViewBox().setDefaultPadding(0.02)


DARK_QSS = f"""
QWidget {{ background: {BG}; color: {TEXT}; font-family: {FONT_FAMILY}; font-size: 11pt; }}
QMainWindow, QDialog {{ background: {BG}; }}
QScrollArea {{ background: transparent; border: none; }}
QScrollArea > QWidget > QWidget {{ background: transparent; }}
QWidget#OverviewScrollContent {{ background: transparent; }}
QWidget#CentralRoot {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {BG}, stop:1 #081020); }}

/* ---------------------------------------------------------------- header */
QFrame#AppHeader {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0a1424, stop:1 #0c1a30);
                    border: 1px solid {BORDER}; border-radius: 14px; }}
QFrame#HeaderDivider {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {ACCENT_STRONG}, stop:0.5 {INDIGO}, stop:1 {PINK});
                        border: none; border-radius: 2px; }}
QLabel#AppTitle {{ font-size: 23pt; font-weight: bold; color: {ACCENT}; letter-spacing: 1px; }}
QLabel#AppSubtitle {{ font-size: 11pt; color: {TEXT_MUTED}; }}
QLabel#StatusPill {{ font-size: 10.5pt; font-weight: bold; padding: 5px 14px; border-radius: 12px;
                     background: #16233a; border: 1px solid {BORDER_LIGHT}; color: {TEXT_MUTED}; }}

/* ------------------------------------------------------------- panels */
QGroupBox {{ background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {PANEL_ALT}, stop:1 {PANEL});
             border: 1px solid {BORDER_LIGHT}; border-radius: 13px; margin-top: 10px; padding: 9px; }}
QGroupBox::title {{ subcontrol-origin: margin; left: 13px; padding: 0 7px; color: {ACCENT};
                    font-weight: bold; font-size: 10.5pt; background: {PANEL};
                    border: 1px solid {BORDER_LIGHT}; border-bottom: none; border-top-left-radius: 6px;
                    border-top-right-radius: 6px; }}

QFrame#VitalCard, QFrame#HormoneCard {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #15243c, stop:1 #0f1b30);
    border: 1px solid {BORDER_LIGHT}; border-radius: 13px;
}}
QFrame#VitalCard:hover, QFrame#HormoneCard:hover {{ border-color: #3d5c95; }}
QFrame#VitalCard[state="green"]   {{ border-left: 4px solid {GREEN}; }}
QFrame#VitalCard[state="yellow"]  {{ border-left: 4px solid {YELLOW}; }}
QFrame#VitalCard[state="orange"]  {{ border-left: 4px solid {ORANGE}; }}
QFrame#VitalCard[state="red"]     {{ border-left: 4px solid {RED}; }}
QFrame#VitalCard[state="blue"]    {{ border-left: 4px solid {ACCENT_STRONG}; }}
QFrame#VitalCard[state="gray"]    {{ border-left: 4px solid {BORDER_LIGHT}; }}

QLabel#VitalValue {{ font-size: 20pt; font-weight: bold; color: #ffffff; }}
QLabel#HormoneValue {{ font-size: 11.5pt; font-weight: bold; color: #ffffff; }}
QLabel#HormoneTitle {{ color: {ACCENT}; font-weight: bold; font-size: 10.5pt; }}
QLabel#SmallMuted {{ color: {TEXT_MUTED}; font-size: 9.5pt; }}
QLabel#WarningText {{ color: {YELLOW}; font-weight: bold; font-size: 10.5pt; }}

/* ------------------------------------------------------------- buttons */
QPushButton {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2f7fd6, stop:1 #1e5aa8);
    border: 1px solid #4a9be0; border-radius: 8px; padding: 7px 12px; font-weight: 600;
}}
QPushButton:hover {{ background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #3d93e8, stop:1 #2766bd);
                    border-color: #63b4f2; }}
QPushButton:pressed {{ background: #174a86; border-color: #2f7fd6; }}
QPushButton:focus {{ border: 2px solid {ACCENT_STRONG}; }}
QPushButton:disabled {{ background: #1c2840; border-color: #2a3a55; color: #6b7a90; }}

/* -------------------------------------------------------------- inputs */
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTimeEdit {{
    background: {PANEL_ALT}; border: 1px solid {BORDER_LIGHT}; border-radius: 8px;
    padding: 6px 8px; font-size: 10.5pt; selection-background-color: {ACCENT_DEEP};
}}
QLineEdit:hover, QComboBox:hover, QSpinBox:hover, QDoubleSpinBox:hover, QTimeEdit:hover {{ border-color: #3d5c95; }}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QTimeEdit:focus {{
    border-color: {ACCENT_STRONG}; background: #15243c;
}}
QComboBox::drop-down {{ border: none; width: 24px; }}
QComboBox::down-arrow {{ image: none; border-left: 5px solid transparent; border-right: 5px solid transparent;
                         border-top: 6px solid {TEXT_MUTED}; margin-right: 8px; }}
QComboBox QAbstractItemView {{ background: {PANEL_ALT}; color: {TEXT}; border: 1px solid {BORDER_LIGHT};
                               border-radius: 8px; selection-background-color: {ACCENT_DEEP};
                               selection-color: white; outline: 0; padding: 4px; }}
QSpinBox::up-button, QDoubleSpinBox::up-button, QTimeEdit::up-button, QSpinBox::down-button,
QDoubleSpinBox::down-button, QTimeEdit::down-button {{
    background: transparent; border: none; width: 18px;
}}
QSpinBox::up-arrow, QDoubleSpinBox::up-arrow, QTimeEdit::up-arrow {{
    image: none; border-left: 4px solid transparent; border-right: 4px solid transparent;
    border-bottom: 5px solid {TEXT_MUTED}; margin: 2px;
}}
QSpinBox::down-arrow, QDoubleSpinBox::down-arrow, QTimeEdit::down-arrow {{
    image: none; border-left: 4px solid transparent; border-right: 4px solid transparent;
    border-top: 5px solid {TEXT_MUTED}; margin: 2px;
}}

/* ---------------------------------------------------------- progress */
QProgressBar {{ background: {TRACK}; border: 1px solid {BORDER}; border-radius: 7px;
                text-align: center; font-size: 9.5pt; color: {TEXT_MUTED}; }}
QProgressBar::chunk {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                       stop:0 {ACCENT_STRONG}, stop:1 {GREEN}); border-radius: 7px; }}

/* ---------------------------------------------------------------- tabs */
QTabWidget::pane {{ border: 1px solid {BORDER_LIGHT}; border-radius: 12px; top: -1px;
                    background: {PANEL}; }}
QTabBar::tab {{
    background: {PANEL}; border: 1px solid {BORDER}; border-top-left-radius: 9px;
    border-top-right-radius: 9px; padding: 9px 13px; margin: 2px 2px 0 2px;
    font-size: 10pt; color: {TEXT_MUTED};
}}
QTabBar::tab:selected {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {ACCENT_DEEP}, stop:1 {INDIGO});
    color: white; font-weight: bold; border-color: {ACCENT_DEEP};
}}
QTabBar::tab:hover:!selected {{ background: {PANEL_HOVER}; color: {TEXT}; }}
QTabBar::tab:disabled {{ color: #5a6b85; }}

/* ------------------------------------------------------------- text */
QTextEdit {{
    background: {PANEL_ALT}; border: 1px solid {BORDER}; border-radius: 10px; padding: 8px;
    font-size: 10.5pt; selection-background-color: {ACCENT_DEEP};
}}
QTextEdit:focus {{ border-color: {ACCENT_STRONG}; }}

/* ------------------------------------------------------------- tables */
QTableWidget {{
    background: {PANEL_ALT}; border: 1px solid {BORDER}; border-radius: 9px;
    font-size: 10pt; gridline-color: #1b2a45; selection-background-color: {ACCENT_DEEP};
    alternate-background-color: #0f1a2e;
}}
QTableWidget::item {{ padding: 4px 6px; }}
QTableWidget::item:selected {{ background: {ACCENT_DEEP}; color: white; }}
QHeaderView::section {{ background: {PANEL}; color: {ACCENT}; font-weight: bold; padding: 7px;
                        border: none; border-bottom: 2px solid {BORDER_LIGHT}; }}

QListWidget {{ background: {PANEL_ALT}; border: 1px solid {BORDER}; border-radius: 11px;
               padding: 6px; outline: 0; font-size: 10.5pt; }}
QListWidget::item {{ border: none; margin: 2px; background: transparent; }}
QListWidget::item:hover {{ background: {PANEL_HOVER}; border-radius: 8px; }}
QListWidget::item:selected {{ background: transparent; }}

/* ------------------------------------------------------------- sliders */
QSlider::groove:horizontal {{ height: 6px; background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                            stop:0 {ACCENT_DEEP}, stop:1 {ACCENT_STRONG}); border-radius: 3px; }}
QSlider::handle:horizontal {{ background: #ffffff; width: 18px; margin: -6px 0; border-radius: 9px;
                              border: 2px solid {ACCENT_STRONG}; }}
QSlider::handle:horizontal:hover {{ background: {ACCENT}; }}

/* ---------------------------------------------------------- scrollbars */
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: #2c3e63; border-radius: 5px; min-height: 28px; }}
QScrollBar::handle:vertical:hover {{ background: #3d5c95; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 2px; }}
QScrollBar::handle:horizontal {{ background: #2c3e63; border-radius: 5px; min-width: 28px; }}
QScrollBar::handle:horizontal:hover {{ background: #3d5c95; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}

/* --------------------------------------------------------------- menus */
QMenu {{ background: #0f1b30; border: 1px solid {BORDER_LIGHT}; border-radius: 10px; padding: 5px; }}
QMenu::item {{ padding: 7px 22px; border-radius: 6px; }}
QMenu::item:selected {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                       stop:0 {ACCENT_DEEP}, stop:1 {INDIGO}); color: white; }}
QMenu::separator {{ height: 1px; background: {BORDER}; margin: 5px 10px; }}

QCheckBox {{ spacing: 8px; }}
QCheckBox::indicator {{ width: 17px; height: 17px; border-radius: 5px;
                        border: 1px solid {BORDER_LIGHT}; background: {PANEL_ALT}; }}
QCheckBox::indicator:hover {{ border-color: {ACCENT_STRONG}; }}
QCheckBox::indicator:checked {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                               stop:0 {ACCENT_STRONG}, stop:1 {INDIGO}); border-color: {ACCENT_STRONG}; }}

QToolTip {{ background: {PANEL_ALT}; color: {TEXT}; border: 1px solid {BORDER_LIGHT};
            padding: 7px; border-radius: 7px; font-size: 10pt; }}
"""
