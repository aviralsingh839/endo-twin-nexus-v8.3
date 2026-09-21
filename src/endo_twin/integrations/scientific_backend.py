from __future__ import annotations

from dataclasses import dataclass
from importlib.util import find_spec
from typing import Any, Dict, Iterable, Optional


@dataclass(frozen=True)
class BackendStatus:
    name: str
    installed: bool
    purpose: str


def optional_backend_status() -> Dict[str, BackendStatus]:
    names = {
        "neurokit2": "PPG/ECG/EDA processing and physiological features",
        "pyhrv": "advanced heart-rate variability features",
        "wfdb": "PhysioNet/WFDB waveform interoperability",
        "monai": "medical-image transforms, training and inference",
        "pydicom": "DICOM import/export and metadata",
        "captum": "deep-model feature attribution",
        "shap": "patient-level model explanations",
        "tsfresh": "automatic time-series feature generation",
        "sktime": "time-series modelling and evaluation",
    }
    return {
        key: BackendStatus(key, find_spec(key) is not None, purpose)
        for key, purpose in names.items()
    }


def process_ppg_with_neurokit(signal: Iterable[float], sampling_rate: float) -> Optional[Dict[str, Any]]:
    """Use NeuroKit2 when installed; otherwise return None without faking output."""
    if find_spec("neurokit2") is None:
        return None
    import neurokit2 as nk
    cleaned = nk.ppg_clean(list(signal), sampling_rate=sampling_rate)
    _, info = nk.ppg_peaks(cleaned, sampling_rate=sampling_rate)
    return {"cleaned": cleaned, "peaks": info.get("PPG_Peaks", []), "backend": "neurokit2"}


def advanced_hrv(nni_ms: Iterable[float]) -> Optional[Dict[str, Any]]:
    """Compute richer HRV metrics with pyHRV when available."""
    if find_spec("pyhrv") is None:
        return None
    from pyhrv import time_domain
    values = list(nni_ms)
    return {
        "sdnn": float(time_domain.sdnn(nni=values)["sdnn"]),
        "rmssd": float(time_domain.rmssd(nni=values)["rmssd"]),
        "backend": "pyhrv",
    }


def imaging_backend_status() -> Dict[str, bool]:
    return {
        "pydicom": find_spec("pydicom") is not None,
        "monai": find_spec("monai") is not None,
    }
