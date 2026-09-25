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
# Hover fill for ACCENT_DEEP buttons. Deliberately *darker* than ACCENT:
# white on ACCENT is only 2.0:1, so hovering used to erase the label.
ACCENT_HOVER = "#0E7F9C"
INDIGO = "#7185FF"
VIOLET = "#A27BFF"
PINK = "#F06FAE"

# Interaction states. Selection must stay dark — the previous #E8F3F4 fill put
# near-white body text on a near-white row (1.02:1) and made selections invisible.
SEL_BG = "#144C63"
SEL_TEXT = "#FFFFFF"
# Focus ring. White clears 3:1 against every dark surface in this theme and
# against the deepest brand fill, so it never disappears on focus.
FOCUS = "#FFFFFF"

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
    border: 2px solid {ACCENT_DEEP};
    color: white;
    border-radius: 6px;
    padding: 7px 12px;
    font-weight: 600;
    min-height: 26px;
}}
QPushButton:hover {{ background: {ACCENT_HOVER}; border-color: {ACCENT_HOVER}; }}
QPushButton:pressed {{ background: #084B53; border-color: #084B53; }}
QPushButton:focus {{ border: 2px solid {FOCUS}; }}
QPushButton:disabled {{ background: {TRACK}; border-color: {BORDER}; color: {TEXT_MUTED}; }}
QPushButton:default {{ border-color: {ACCENT_STRONG}; }}

QToolButton {{
    background: transparent;
    border: 1px solid {BORDER};
    border-radius: 6px;
    color: {TEXT};
    padding: 4px 8px;
}}
QToolButton:hover {{ border-color: {BORDER_LIGHT}; background: {PANEL_HOVER}; }}
QToolButton:focus {{ border: 2px solid {FOCUS}; }}

QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTimeEdit {{
    background: {PANEL};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 6px 8px;
    font-size: 10pt;
    color: {TEXT};
    selection-background-color: {SEL_BG};
    selection-color: {SEL_TEXT};
}}
QLineEdit:hover, QComboBox:hover, QSpinBox:hover, QDoubleSpinBox:hover, QTimeEdit:hover {{ border-color: {BORDER_LIGHT}; }}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QTimeEdit:focus {{
    border: 2px solid {FOCUS};
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
    selection-background-color: {SEL_BG};
    selection-color: {SEL_TEXT};
    outline: 0;
}}

QProgressBar {{
    background: {TRACK};
    border: 1px solid {BORDER};
    border-radius: 5px;
    text-align: center;
    font-size: 9.5pt;
    color: {TEXT};
    min-height: 18px;
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
    font-size: 10pt;
    color: {TEXT_MUTED};
    min-height: 22px;
}}
/* NOTE: this rule previously carried an escaped newline inside the f-string,
   which silently swallowed the border-left declaration and left a near-white
   #E8F3F4 tab on a dark theme. Keep every declaration on its own line. */
QTabBar::tab:selected {{
    color: {TEXT};
    font-weight: 650;
    border-left: 3px solid {ACCENT_STRONG};
    background: {PANEL_HOVER};
}}
QTabBar::tab:hover:!selected {{ color: {TEXT}; background: {PANEL_HOVER}; }}
QTabBar::tab:focus {{ border: 2px solid {FOCUS}; }}

QTextEdit, QPlainTextEdit {{
    background: {PANEL};
    border: 1px solid {BORDER};
    border-radius: 7px;
    padding: 8px;
    font-size: 10pt;
    color: {TEXT};
    selection-background-color: {SEL_BG};
    selection-color: {SEL_TEXT};
}}
QTextEdit:focus, QPlainTextEdit:focus {{ border: 2px solid {FOCUS}; }}

QTableWidget {{
    background: {PANEL};
    border: 1px solid {BORDER};
    border-radius: 7px;
    font-size: 10pt;
    color: {TEXT};
    gridline-color: {TRACK};
    selection-background-color: {SEL_BG};
    selection-color: {SEL_TEXT};
    alternate-background-color: {PANEL_ALT};
}}
QTableWidget::item {{ padding: 5px 6px; }}
QTableWidget:focus {{ border: 2px solid {FOCUS}; }}
QHeaderView::section {{
    background: {PANEL_ALT};
    color: {TEXT};
    font-weight: 650;
    padding: 7px;
    border: none;
    border-bottom: 1px solid {BORDER};
}}

QListWidget, QListView, QTreeWidget, QTreeView {{
    background: {PANEL};
    border: 1px solid {BORDER};
    border-radius: 7px;
    padding: 5px;
    outline: 0;
    font-size: 10pt;
    color: {TEXT};
    selection-background-color: {SEL_BG};
    selection-color: {SEL_TEXT};
}}
QListWidget::item, QListView::item, QTreeWidget::item, QTreeView::item {{
    border: none;
    margin: 1px;
    padding: 4px 6px;
    min-height: 20px;
}}
QListWidget::item:hover, QListView::item:hover,
QTreeWidget::item:hover, QTreeView::item:hover {{ background: {PANEL_HOVER}; }}
QListWidget::item:selected, QListView::item:selected,
QTreeWidget::item:selected, QTreeView::item:selected {{
    background: {SEL_BG};
    color: {SEL_TEXT};
}}
QListWidget:focus, QListView:focus, QTreeWidget:focus, QTreeView:focus {{
    border: 2px solid {FOCUS};
}}

QSlider::groove:horizontal {{ height: 6px; background: {TRACK}; border-radius: 3px; }}
QSlider::handle:horizontal {{
    background: {PANEL};
    width: 16px;
    margin: -6px 0;
    border-radius: 8px;
    border: 2px solid {ACCENT_STRONG};
}}
QSlider::handle:horizontal:hover {{ border-color: {FOCUS}; }}
QSlider:focus {{ border: 2px solid {FOCUS}; border-radius: 6px; }}

QScrollBar:vertical {{ background: transparent; width: 12px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: {BORDER_LIGHT}; border-radius: 5px; min-height: 28px; }}
QScrollBar::handle:vertical:hover {{ background: {TEXT_MUTED}; }}
QScrollBar:horizontal {{ background: transparent; height: 12px; margin: 2px; }}
QScrollBar::handle:horizontal {{ background: {BORDER_LIGHT}; border-radius: 5px; min-width: 28px; }}
QScrollBar::handle:horizontal:hover {{ background: {TEXT_MUTED}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}

QMenu {{
    background: {PANEL};
    border: 1px solid {BORDER};
    border-radius: 7px;
    padding: 4px;
}}
QMenu::item {{ padding: 7px 18px; border-radius: 4px; }}
QMenu::item:selected {{ background: {SEL_BG}; color: {SEL_TEXT}; }}

QCheckBox, QRadioButton {{ spacing: 7px; padding: 3px 0; min-height: 22px; }}
QCheckBox::indicator {{
    width: 17px; height: 17px; border-radius: 4px;
    border: 2px solid {BORDER_LIGHT}; background: {PANEL};
}}
QCheckBox::indicator:hover {{ border-color: {TEXT_MUTED}; }}
/* Checked state changes fill *and* border weight, so it is legible without
   relying on hue alone. */
QCheckBox::indicator:checked {{
    background: {ACCENT_STRONG};
    border: 3px solid {TEXT};
}}
QCheckBox::indicator:disabled {{ border-color: {BORDER}; background: {TRACK}; }}
QCheckBox:focus {{ border: 2px solid {FOCUS}; border-radius: 5px; }}
QRadioButton::indicator {{
    width: 17px; height: 17px; border-radius: 9px;
    border: 2px solid {BORDER_LIGHT}; background: {PANEL};
}}
QRadioButton::indicator:checked {{
    background: {ACCENT_STRONG};
    border: 3px solid {TEXT};
}}
QRadioButton:focus {{ border: 2px solid {FOCUS}; border-radius: 5px; }}

QToolTip {{
    background: {PANEL_ALT};
    color: {TEXT};
    border: 1px solid {FOCUS};
    padding: 6px 8px;
    border-radius: 4px;
    font-size: 9.5pt;
}}
"""
