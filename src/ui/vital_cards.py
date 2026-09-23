"""Reusable vital sign card widgets.

Accessibility contract:
  * A card's severity is never carried by its border colour alone. Whenever
    ``set_color_state`` is used, the state word ("Normal", "Watch", ...) is
    written into the card's status line as well.
  * Type sizes here are the smallest in the workstation, so they have a floor:
    nothing renders below 8.5pt, and the primary value is always the largest
    element on the card.
  * Each card exposes an accessible name and description built from its own
    title, value and state, so a screen reader announces one meaningful
    sentence instead of three disconnected labels.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout

from src.ui.theme import ACCENT, TEXT, TEXT_MUTED

# Words for every state the shared stylesheet can render. Keeping them here —
# next to the widget that applies the colour — is what guarantees the two never
# drift apart.
STATE_LABELS = {
    "green": "Normal",
    "yellow": "Watch",
    "orange": "Elevated",
    "red": "High",
    "blue": "Info",
    "gray": "No data",
}

VALID_STATES = tuple(STATE_LABELS)


class VitalCard(QFrame):
    def __init__(self, title: str, unit: str = "", compact: bool = False, parent=None):
        super().__init__(parent)
        self.title = title
        self.unit = unit
        self.compact = compact
        self._state = "gray"
        self._status = ""
        self.setObjectName("VitalCard")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setProperty("state", "gray")
        self.setMinimumHeight(46 if compact else 74)
        layout = QVBoxLayout(self)
        if compact:
            layout.setContentsMargins(6, 2, 6, 2)
            layout.setSpacing(0)
        else:
            layout.setContentsMargins(10, 5, 10, 5)
            layout.setSpacing(1)
        # Minimum legible sizes: 9pt for a card title, 8.5pt for its footnote.
        title_pt = "9pt" if compact else "10.5pt"
        status_pt = "8.5pt" if compact else "9.5pt"
        self.title_label = QLabel(title)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setWordWrap(True)
        self.title_label.setStyleSheet(
            f"font-weight: bold; color: {ACCENT}; font-size: {title_pt};")
        self.value_label = QLabel("--")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.value_label.setObjectName("VitalValue")
        self._value_pt = 13 if compact else 18
        self.value_label.setStyleSheet(
            f"font-size: {self._value_pt}pt; font-weight: bold; color: {TEXT_MUTED};")
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setWordWrap(True)
        self.status_label.setMinimumHeight(13 if compact else 18)
        self.status_label.setObjectName("SmallMuted")
        self.status_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: {status_pt};")
        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        layout.addWidget(self.status_label)
        self._sync_accessible_text()

    # ------------------------------------------------------------ internals
    def _sync_accessible_text(self) -> None:
        """Keep the screen-reader view of the card in step with its pixels."""
        self.setAccessibleName(f"{self.title}: {self.value_label.text()}")
        parts = [p for p in (self._status, STATE_LABELS.get(self._state, "")) if p]
        self.setAccessibleDescription("; ".join(parts) or "No status reported")

    def _status_line(self) -> str:
        """Status text plus the state word, so state is never colour-only."""
        state_word = STATE_LABELS.get(self._state, "")
        parts = [p for p in (self._status, state_word) if p]
        return " — ".join(parts)

    # --------------------------------------------------------------- public
    def set_value(self, value, status: str = "", decimals: int = 1):
        if value is None:
            text = "--"
            if not status:
                status = "awaiting data"
        elif isinstance(value, str):
            text = value
        else:
            text = f"{float(value):.{decimals}f} {self.unit}".strip()
        self.value_label.setText(text)
        self._status = status
        self.status_label.setText(self._status_line())
        # Missing data renders muted so "--" reads as intentional, not broken.
        color = TEXT_MUTED if value is None else TEXT
        self.value_label.setStyleSheet(
            f"font-size: {self._value_pt}pt; font-weight: bold; color: {color};")
        self._sync_accessible_text()

    def set_color_state(self, state: str):
        """Set the semantic state; the shared theme stylesheet renders it.

        The matching word from STATE_LABELS is written into the status line as
        well, so the severity survives greyscale printing and colour-vision
        deficiency.
        """
        if state not in VALID_STATES:
            state = "gray"
        if self._state == state:
            return
        self._state = state
        self.setProperty("state", state)
        self.status_label.setText(self._status_line())
        self.style().unpolish(self)
        self.style().polish(self)
        self._sync_accessible_text()

    def state_label(self) -> str:
        """The word a sighted user sees for the current state."""
        return STATE_LABELS.get(self._state, "")
