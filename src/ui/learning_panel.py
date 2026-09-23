"""Panel that shows what the wearable model has learned so far.

The panel is a plain read-only view over ``AdaptiveWearableModel.status()``: which
capability tier this wearer has earned, how much wearing time it rests on, what
unlocks next, and the promotion / drift / rollback history. Nothing here invents a
number - if the model cannot support a claim it says so in words (``WITHHELD``,
``COLLECTING``), not just in colour.

Accessibility notes
-------------------
* Colours are passed in by the host app (``palette``), so the panel uses the same
  audited tokens as the rest of the surface - no new hard-coded hex values.
* Status is always spelled out in text; colour is decoration, never the only signal.
* No inline font sizes: the host stylesheet's type floor applies unchanged.
* Interactive controls (the optional label buttons) carry accessible names.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

# The panel deliberately ships no colours of its own. Every colour is supplied by the
# host app from a contrast-audited palette, so no untested hex value can slip in here.
REQUIRED_COLOURS = ("text", "muted", "accent", "good", "warn", "bad")


class LearningStatusPanel(QGroupBox):
    """Read-only status panel for one wearer's continually-learning model."""

    def __init__(
        self,
        *,
        palette: Dict[str, str],
        title: str = "Wearable learning",
        allow_labels: bool = False,
        on_label: Optional[Callable[[bool], None]] = None,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(title, parent)
        missing = [name for name in REQUIRED_COLOURS if name not in palette]
        if missing:
            raise ValueError(f"palette missing {missing} - pass the host app's audited tokens")
        self.palette = dict(palette)
        self.setAccessibleName(title)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)

        root = QVBoxLayout(self)

        self.headline = QLabel("No model yet.")
        self.headline.setWordWrap(True)
        self.headline.setAccessibleName("Current learning tier")
        root.addWidget(self.headline)

        self.detail = QLabel("")
        self.detail.setWordWrap(True)
        self.detail.setAccessibleName("Wearing time and what unlocks next")
        root.addWidget(self.detail)

        self.history = QPlainTextEdit()
        self.history.setReadOnly(True)
        self.history.setPlaceholderText("Promotions, absorbed shifts and rollbacks appear here.")
        self.history.setAccessibleName("Learning history")
        self.history.setMinimumHeight(96)
        self.history.setMaximumHeight(150)
        root.addWidget(self.history)

        self.feedback = QLabel("")
        self.feedback.setWordWrap(True)
        self.feedback.setAccessibleName("Label feedback")
        root.addWidget(self.feedback)

        self._buttons: Dict[str, QPushButton] = {}
        if allow_labels:
            row = QHBoxLayout()
            symptom = QPushButton("Log a symptom episode")
            symptom.setObjectName("primary")
            symptom.setAccessibleName("Log a symptom episode for the wearable model")
            symptom.clicked.connect(lambda: self._emit_label(True))
            normal = QPushButton("Log a normal day")
            normal.setAccessibleName("Log a normal day for the wearable model")
            normal.clicked.connect(lambda: self._emit_label(False))
            row.addWidget(symptom)
            row.addWidget(normal)
            row.addStretch()
            root.addLayout(row)
            self._buttons = {"symptom": symptom, "normal": normal}
            self.feedback.setText(
                "These labels are the only way the supervised personalization head can "
                "learn; they never leave this device."
            )
        self._on_label = on_label
        self._set_colour(self.headline, self.palette["muted"])

    # ------------------------------------------------------------------
    def _emit_label(self, symptom: bool) -> None:
        if self._on_label is not None:
            self._on_label(bool(symptom))

    def _set_colour(self, widget: QWidget, colour: str) -> None:
        widget.setStyleSheet(f"color: {colour};")

    def set_message(self, text: str, level: str = "muted") -> None:
        """Show a plain message when no model is available."""
        self.headline.setText(text)
        self._set_colour(self.headline, self.palette.get(level, self.palette["muted"]))
        self.detail.setText("")
        self.history.setPlainText("")

    # ------------------------------------------------------------------
    def update_from(self, status: Dict[str, Any]) -> None:
        """Refresh from ``AdaptiveWearableModel.status()``."""
        if not status:
            self.set_message("No model yet.")
            return
        tier = str(status.get("tier", "population")).upper()
        version = status.get("model_version", "-")
        worn = float(status.get("worn_hours", 0.0))
        observations = int(status.get("observations", 0))
        confidence = float(status.get("confidence", 0.0))

        level = "muted"
        if status.get("tier") == "adaptive":
            level = "good"
        elif status.get("tier") == "circadian":
            level = "accent"
        elif status.get("tier") == "personalized":
            level = "accent"
        self.headline.setText(
            f"TIER {tier}  •  model v{version}  •  {status.get('upgrades', 0)} upgrade(s)"
        )
        self._set_colour(self.headline, self.palette[level])

        lines = [
            str(status.get("tier_headline", "")),
            f"Learned from {worn:.1f} h of wearing time, {observations} samples, "
            f"{status.get('days_covered', 0)} day(s).",
            f"Data confidence {confidence:.2f} - {status.get('confidence_note', '')}",
        ]
        next_tier = status.get("next_tier")
        if next_tier:
            remaining = [
                f"{req['label']}: {req['current']:.0f}/{req['target']:.0f}"
                for req in status.get("requirements", []) if not req.get("met")
            ]
            if remaining:
                lines.append(f"Next upgrade ({next_tier}) needs - " + "; ".join(remaining))
            else:
                lines.append(f"Next upgrade ({next_tier}) is ready.")
        else:
            lines.append("Every capability this model defines is already unlocked.")

        disclaimer = str(status.get("disclaimer") or "")
        if disclaimer:
            lines.append(disclaimer)

        head = status.get("head") or {}
        head_status = str(head.get("status", "collecting")).upper()
        lines.append(f"Supervised personalization: {head_status} - {head.get('reason', '')}")
        self.detail.setText("\n".join(line for line in lines if line))

        entries = []
        for event in reversed(status.get("events", [])[-8:]):
            stamp = event.get("iso") or ""
            kind = str(event.get("kind", "")).upper()
            suffix = f" [{event['metric']}]" if event.get("metric") else ""
            entries.append(f"{stamp}  {kind}{suffix}  {event.get('detail', '')}")
        self.history.setPlainText("\n".join(entries) if entries else
                                  "No promotions, absorbed shifts or rollbacks yet.")
        self.feedback.setEnabled(self._buttons.get("symptom") is not None)

    def set_label_feedback(self, text: str, level: str = "muted") -> None:
        self.feedback.setText(text)
        self._set_colour(self.feedback, self.palette.get(level, self.palette["muted"]))


def build_learning_panel(*args: Any, **kwargs: Any) -> LearningStatusPanel:
    """Convenience factory used by the desktop apps."""
    return LearningStatusPanel(*args, **kwargs)


__all__ = ["LearningStatusPanel", "build_learning_panel", "REQUIRED_COLOURS"]

# Qt API surface is checked by scripts/diagnostics/qt_api_check.py against the
# PySide6 stubs, because this environment has no libGL and cannot render a widget.
