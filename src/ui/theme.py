"""ENDO-TWIN NEXUS professional visual system.

Single semantic token layer for Qt desktop surfaces. No gradients are used in
the core component system; state is communicated by text, iconography and
semantic color rather than color alone.
"""
from __future__ import annotations

from PySide6.QtGui import QFont

FONT_FAMILY = '"Inter", "Segoe UI", "Helvetica Neue", "Arial", sans-serif'
PAINTER_FONT = "Inter"

# Neutral foundation
BG = "#050C16"
BG_TOP = "#091625"
PANEL = "#0B1828"
PANEL_ALT = "#0F2237"
PANEL_HOVER = "#142B44"
TRACK = "#17304A"
PLOT_BG = "#07121F"

# Structure
BORDER = "#203852"
BORDER_LIGHT = "#31516E"

# Text
TEXT = "#EAF4FF"
TEXT_MUTED = "#8EA4B8"

# Brand: restrained scientific teal/blue
ACCENT = "#18C7E8"
ACCENT_STRONG = "#24D6F2"
ACCENT_DEEP = "#0B6F89"
INDIGO = "#7185FF"
VIOLET = "#A27BFF"
PINK = "#F06FAE"

# Semantic
GREEN = "#32D6A0"
GREEN_BRIGHT = "#45E5B3"
YELLOW = "#F4C95D"
ORANGE = "#FF9F5B"
RED = "#FF647C"

# Layout tokens — keep screens aligned to the same 4px rhythm.
SPACE_1, SPACE_2, SPACE_3, SPACE_4 = 4, 8, 12, 16
SPACE_5, SPACE_6, SPACE_8 = 20, 24, 32
RADIUS_SM, RADIUS_MD, RADIUS_LG = 6, 8, 10

# Semantic provenance tokens. Never use these to imply clinical validity.
PROVENANCE = {
    "LIVE": ACCENT_STRONG,
    "DEMO": YELLOW,
    "MEASURED": ACCENT,
    "DERIVED": INDIGO,
    "MODEL": VIOLET,
    "UNAVAILABLE": TEXT_MUTED,
    "ERROR": RED,
}

def provenance_color(label: str) -> str:
    """Return the semantic UI color for a provenance/state label."""
    return PROVENANCE.get(str(label).upper(), TEXT_MUTED)

def painter_font(size: int, bold: bool = False) -> QFont:
    font = QFont(PAINTER_FONT, size)
    font.setBold(bold)
    return font

def status_color(state: str) -> str:
    return {
        "green": GREEN, "yellow": YELLOW, "orange": ORANGE, "red": RED,
        "blue": ACCENT_STRONG, "gray": TEXT_MUTED, "pink": PINK,
        "violet": VIOLET, "indigo": INDIGO,
    }.get(state, TEXT_MUTED)

def progress_state_qss(value: float) -> str:
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
        f"border-radius: 5px; text-align: center; font-size: 9.5pt; color: {TEXT_MUTED}; }}"
        f"QProgressBar::chunk {{ background: {color}; border-radius: 5px; }}"
    )

def style_plot(plot, y_label: str = "", x_label: str = "") -> None:
    import pyqtgraph as pg
    plot.setBackground(PLOT_BG)
    plot.showGrid(x=True, y=True, alpha=0.10)
    plot.setMouseEnabled(x=True, y=False)
    for axis_name, label in (("left", y_label), ("bottom", x_label)):
        axis = plot.getAxis(axis_name)
        axis.setPen(pg.mkPen(BORDER))
        axis.setTextPen(pg.mkPen(TEXT_MUTED))
        axis.setTickFont(painter_font(9))
        axis.setLabel(label if label else "")
    plot.getViewBox().setDefaultPadding(0.02)

DARK_QSS = f"""
QWidget {{
    background: {BG};
    color: {TEXT};
    font-family: {FONT_FAMILY};
    font-size: 10.5pt;
}}
QMainWindow, QDialog {{ background: {BG}; }}
QScrollArea {{ background: transparent; border: none; }}
QScrollArea > QWidget > QWidget {{ background: transparent; }}

QFrame#AppHeader {{
    background: {BG_TOP};
    border: 1px solid {BORDER};
    border-radius: 8px;
}}
QFrame#HeaderDivider {{
    background: {ACCENT_STRONG};
    border: none;
    border-radius: 1px;
}}
QLabel#AppTitle {{
    font-size: 20pt;
    font-weight: 700;
    color: {TEXT};
    letter-spacing: 0.2px;
}}
QLabel#AppSubtitle {{ font-size: 10.5pt; color: {TEXT_MUTED}; }}
QLabel#StatusPill {{
    font-size: 9.5pt;
    font-weight: 600;
    padding: 4px 10px;
    border-radius: 10px;
    background: {PANEL_ALT};
    border: 1px solid {BORDER};
    color: {TEXT_MUTED};
}}

QGroupBox {{
    background: {PANEL};
    border: 1px solid {BORDER};
    border-radius: 8px;
    margin-top: 12px;
    padding: 10px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
    color: {TEXT};
    font-weight: 650;
    font-size: 10pt;
    background: {BG};
}}

QFrame#VitalCard, QFrame#HormoneCard {{
    background: {PANEL};
    border: 1px solid {BORDER};
    border-radius: 8px;
}}
QFrame#VitalCard:hover, QFrame#HormoneCard:hover {{ border-color: {BORDER_LIGHT}; }}
QFrame#VitalCard[state="green"] {{ border-left: 3px solid {GREEN}; }}
QFrame#VitalCard[state="yellow"] {{ border-left: 3px solid {YELLOW}; }}
QFrame#VitalCard[state="orange"] {{ border-left: 3px solid {ORANGE}; }}
QFrame#VitalCard[state="red"] {{ border-left: 3px solid {RED}; }}
QFrame#VitalCard[state="blue"] {{ border-left: 3px solid {ACCENT_STRONG}; }}
QFrame#VitalCard[state="gray"] {{ border-left: 3px solid {BORDER}; }}

QLabel#VitalValue {{ font-size: 19pt; font-weight: 700; color: {TEXT}; }}
QLabel#HormoneValue {{ font-size: 11.5pt; font-weight: 700; color: {TEXT}; }}
QLabel#HormoneTitle {{ color: {ACCENT}; font-weight: 650; font-size: 10pt; }}
QLabel#SmallMuted {{ color: {TEXT_MUTED}; font-size: 9pt; }}
QLabel#WarningText {{ color: {YELLOW}; font-weight: 650; font-size: 10pt; }}

QPushButton {{
    background: {ACCENT_DEEP};
    border: 1px solid {ACCENT_DEEP};
    color: white;
    border-radius: 6px;
    padding: 7px 12px;
    font-weight: 600;
}}
QPushButton:hover {{ background: {ACCENT}; border-color: {ACCENT}; }}
QPushButton:pressed {{ background: #084B53; }}
QPushButton:focus {{ border: 2px solid {ACCENT_STRONG}; }}
QPushButton:disabled {{ background: {TRACK}; border-color: {BORDER}; color: {TEXT_MUTED}; }}

QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTimeEdit {{
    background: {PANEL};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 6px 8px;
    font-size: 10pt;
    selection-background-color: {ACCENT};
}}
QLineEdit:hover, QComboBox:hover, QSpinBox:hover, QDoubleSpinBox:hover, QTimeEdit:hover {{ border-color: {BORDER_LIGHT}; }}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QTimeEdit:focus {{
    border-color: {ACCENT_STRONG};
}}
QComboBox::drop-down {{ border: none; width: 22px; }}
QComboBox::down-arrow {{
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid {TEXT_MUTED};
    margin-right: 7px;
}}
QComboBox QAbstractItemView {{
    background: {PANEL};
    color: {TEXT};
    border: 1px solid {BORDER};
    selection-background-color: {PANEL_HOVER};
    selection-color: {TEXT};
    outline: 0;
}}

QProgressBar {{
    background: {TRACK};
    border: 1px solid {BORDER};
    border-radius: 5px;
    text-align: center;
    font-size: 9pt;
    color: {TEXT_MUTED};
}}
QProgressBar::chunk {{ background: {ACCENT_STRONG}; border-radius: 5px; }}

QTabWidget::pane {{
    border: 1px solid {BORDER};
    border-radius: 8px;
    background: {PANEL};
}}
QTabBar::tab {{
    background: transparent;
    border: none;
    border-left: 3px solid transparent;
    padding: 8px 10px;
    margin: 2px 3px 0 0;
    font-size: 9.5pt;
    color: {TEXT_MUTED};
}}
QTabBar::tab:selected {{
    color: {TEXT};
    font-weight: 650;
    border-left: 3px solid {ACCENT_STRONG};\n    background: #E8F3F4;
}}
QTabBar::tab:hover:!selected {{ color: {TEXT}; background: {PANEL_HOVER}; }}

QTextEdit {{
    background: {PANEL};
    border: 1px solid {BORDER};
    border-radius: 7px;
    padding: 8px;
    font-size: 10pt;
    selection-background-color: {ACCENT};
}}
QTextEdit:focus {{ border-color: {ACCENT_STRONG}; }}

QTableWidget {{
    background: {PANEL};
    border: 1px solid {BORDER};
    border-radius: 7px;
    font-size: 9.5pt;
    gridline-color: {TRACK};
    selection-background-color: #E8F3F4;
    selection-color: {TEXT};
    alternate-background-color: {PANEL_ALT};
}}
QTableWidget::item {{ padding: 5px 6px; }}
QHeaderView::section {{
    background: {PANEL_ALT};
    color: {TEXT_MUTED};
    font-weight: 650;
    padding: 7px;
    border: none;
    border-bottom: 1px solid {BORDER};
}}

QListWidget {{
    background: {PANEL};
    border: 1px solid {BORDER};
    border-radius: 7px;
    padding: 5px;
    outline: 0;
    font-size: 10pt;
}}
QListWidget::item {{ border: none; margin: 1px; padding: 4px 6px; }}
QListWidget::item:hover {{ background: {PANEL_HOVER}; }}
QListWidget::item:selected {{ background: #E8F3F4; color: {TEXT}; }}

QSlider::groove:horizontal {{ height: 5px; background: {TRACK}; border-radius: 2px; }}
QSlider::handle:horizontal {{
    background: {PANEL};
    width: 16px;
    margin: -5px 0;
    border-radius: 8px;
    border: 2px solid {ACCENT_STRONG};
}}

QScrollBar:vertical {{ background: transparent; width: 9px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: {BORDER_LIGHT}; border-radius: 4px; min-height: 28px; }}
QScrollBar:horizontal {{ background: transparent; height: 9px; margin: 2px; }}
QScrollBar::handle:horizontal {{ background: {BORDER_LIGHT}; border-radius: 4px; min-width: 28px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}

QMenu {{
    background: {PANEL};
    border: 1px solid {BORDER};
    border-radius: 7px;
    padding: 4px;
}}
QMenu::item {{ padding: 7px 18px; border-radius: 4px; }}
QMenu::item:selected {{ background: {PANEL_HOVER}; color: {TEXT}; }}

QCheckBox {{ spacing: 7px; }}
QCheckBox::indicator {{
    width: 16px; height: 16px; border-radius: 4px;
    border: 1px solid {BORDER_LIGHT}; background: {PANEL};
}}
QCheckBox::indicator:checked {{ background: {ACCENT_STRONG}; border-color: {ACCENT_STRONG}; }}

QToolTip {{
    background: {TEXT};
    color: #FFFFFF;
    border: none;
    padding: 6px 8px;
    border-radius: 4px;
    font-size: 9pt;
}}
"""
