"""Modern VoxVasc experimental UI for the active ENDO-TWIN desktop."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.models.voice_vasc_model import VoiceVascEstimator, wav_features


class VoiceVascTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.estimator = VoiceVascEstimator()
        self._build()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(16)

        hero = QFrame()
        hero.setObjectName("PremiumCard")
        hero_layout = QVBoxLayout(hero)
        title = QLabel("VoxVasc")
        title.setObjectName("HeroTitle")
        subtitle = QLabel(
            "Experimental voice-physiology modality • optional CHRONO-PCOS input"
        )
        subtitle.setObjectName("HeroSubtitle")
        hero_layout.addWidget(title)
        hero_layout.addWidget(subtitle)
        root.addWidget(hero)

        notice = QFrame()
        notice.setObjectName("WarningCard")
        notice_layout = QVBoxLayout(notice)
        notice_layout.addWidget(QLabel(
            "Research-only feature. Acoustic voice features do not measure "
            "testosterone or diagnose PCOS. They must never override measured "
            "physiology, clinical inputs, or validated imaging."
        ))
        root.addWidget(notice)

        metrics = QGridLayout()
        metrics.setHorizontalSpacing(14)
        metrics.setVerticalSpacing(14)
        for col in range(3):
            metrics.setColumnStretch(col, 1)

        self.pitch_value = QLabel("—")
        self.pitch_value.setObjectName("MetricValue")
        self.score_value = QLabel("Unavailable")
        self.score_value.setObjectName("MetricValue")
        self.quality_value = QLabel("Not assessed")
        self.quality_value.setObjectName("MetricValue")

        metrics.addWidget(self._metric_card("Sustained pitch", self.pitch_value, "Hz"), 0, 0)
        metrics.addWidget(self._metric_card("Experimental index", self.score_value, "not a probability"), 0, 1)
        metrics.addWidget(self._metric_card("Audio quality", self.quality_value, "WAV/acquisition"), 0, 2)
        root.addLayout(metrics)

        actions = QGroupBox("Voice acquisition")
        action_layout = QVBoxLayout(actions)
        protocol = QLabel(
            "Recommended research protocol: record a sustained “aaa” for ~3 seconds "
            "in a quiet room, with the same microphone position across repeated "
            "measurements. Store the original audio and feature provenance."
        )
        protocol.setWordWrap(True)
        action_layout.addWidget(protocol)

        button = QPushButton("Load WAV for analysis")
        button.setObjectName("Primary")
        button.clicked.connect(self.load_wav)
        action_layout.addWidget(button)

        self.result = QLabel(
            "No audio loaded. VoxVasc remains unavailable until a valid recording is provided."
        )
        self.result.setWordWrap(True)
        self.result.setObjectName("MutedPanelText")
        action_layout.addWidget(self.result)
        root.addWidget(actions)

        limits = QGroupBox("Interpretation boundary")
        limits_layout = QVBoxLayout(limits)
        limits_layout.addWidget(QLabel(
            "• Experimental acoustic feature only\n"
            "• No androgen or vascular measurement\n"
            "• No standalone PCOS inference\n"
            "• No clinical validation claim\n"
            "• If audio quality or pitch extraction fails: UNKNOWN / UNAVAILABLE"
        ))
        root.addWidget(limits)
        root.addStretch(1)

    @staticmethod
    def _metric_card(title: str, value: QLabel, detail: str) -> QFrame:
        card = QFrame()
        card.setObjectName("MetricCard")
        layout = QVBoxLayout(card)
        label = QLabel(title)
        label.setObjectName("MetricLabel")
        detail_label = QLabel(detail)
        detail_label.setObjectName("MetricDetail")
        layout.addWidget(label)
        layout.addWidget(value)
        layout.addWidget(detail_label)
        return card

    def load_wav(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Choose sustained-vowel WAV", "", "WAV files (*.wav)"
        )
        if not path:
            return

        try:
            features = wav_features(path)
            pitch = features.get("pitch_hz")
            rms = features.get("rms")
            score, note = self.estimator.score(pitch, rms)

            self.pitch_value.setText(
                "—" if pitch is None else f"{pitch:.1f}"
            )
            self.score_value.setText(
                "Unavailable" if score is None else f"{score:.0f} / 100"
            )
            self.quality_value.setText(
                "Insufficient" if rms is None else f"RMS {rms:.1f}"
            )
            self.result.setText(
                f"File: {path}\n\n{note}\n\n"
                "Provenance: IMAGE/VOICE-DERIVED ACOUSTIC FEATURE. "
                "Do not interpret this as hormone measurement or diagnosis."
            )
        except Exception as exc:
            self.pitch_value.setText("—")
            self.score_value.setText("Unavailable")
            self.quality_value.setText("Error")
            self.result.setText(f"Audio analysis failed: {exc}")
