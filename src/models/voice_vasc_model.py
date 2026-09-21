"""VoxVasc experimental voice-physiology feature module.

VoxVasc is an optional, low-weight research modality for ENDO-TWIN /
CHRONO-PCOS. It extracts acoustic features from a sustained-vowel WAV
recording. It does NOT measure hormones, diagnose PCOS, or establish a
clinical vascular/androgen state.
"""
from __future__ import annotations

import wave
from pathlib import Path

import numpy as np

from src.utils.math_utils import clamp, sigmoid


def estimate_pitch_autocorr(
    signal: np.ndarray,
    fs: int,
    fmin: float = 80.0,
    fmax: float = 350.0,
) -> float | None:
    x = np.asarray(signal, dtype=float)
    if fs <= 0 or x.size < max(1, int(fs * 0.2)):
        return None
    x = x - np.mean(x)
    if np.std(x) < 1e-6:
        return None

    if x.size > fs:
        mid = x.size // 2
        half = fs // 2
        x = x[max(0, mid - half): mid + half]

    corr = np.correlate(x, x, mode="full")[len(x) - 1:]
    min_lag = max(1, int(fs / fmax))
    max_lag = min(len(corr) - 1, int(fs / fmin))
    if min_lag >= max_lag:
        return None

    lag = min_lag + int(np.argmax(corr[min_lag:max_lag]))
    return float(fs / lag) if lag > 0 else None


def wav_features(path: str | Path) -> dict[str, float | None]:
    """Extract transparent acoustic features from PCM WAV audio."""
    with wave.open(str(path), "rb") as wf:
        fs = wf.getframerate()
        n = wf.getnframes()
        channels = wf.getnchannels()
        sample_width = wf.getsampwidth()
        raw = wf.readframes(n)

    if sample_width == 1:
        x = np.frombuffer(raw, dtype=np.uint8).astype(float) - 128.0
    elif sample_width == 2:
        x = np.frombuffer(raw, dtype=np.int16).astype(float)
    else:
        return {"pitch_hz": None, "rms": None, "jitter_proxy": None}

    if channels > 1:
        x = x.reshape(-1, channels).mean(axis=1)

    centered = x - np.mean(x)
    rms = float(np.sqrt(np.mean(centered ** 2)))
    pitch = estimate_pitch_autocorr(x, fs)
    return {"pitch_hz": pitch, "rms": rms, "jitter_proxy": None}


class VoiceVascEstimator:
    """Transparent, non-diagnostic acoustic proxy.

    The score is intentionally framed as an experimental feature index rather
    than a probability, diagnosis, hormone measurement, or clinical risk
    percentage.
    """

    name = "VoxVasc"
    version = "0.1.0-experimental"

    def score(
        self,
        pitch_hz: float | None,
        mic_rms: float | None = None,
    ) -> tuple[float | None, str]:
        if pitch_hz is None or pitch_hz <= 0:
            return None, "No valid pitch; VoxVasc feature is unavailable."

        # Retains the original concept's monotonic low-pitch proxy while
        # explicitly treating it as experimental and low-confidence.
        low_pitch_index = 100.0 * sigmoid((190.0 - pitch_hz) / 18.0)
        energy_quality = (
            1.0 if mic_rms is None else clamp((mic_rms - 8.0) / 40.0, 0.0, 1.0)
        )
        index = float(clamp(low_pitch_index * energy_quality, 0.0, 100.0))

        return (
            index,
            (
                f"Acoustic pitch feature ≈ {pitch_hz:.1f} Hz. "
                "This weak proxy is not a hormone measurement and is not "
                "PCOS-specific; not clinically validated."
            ),
        )
