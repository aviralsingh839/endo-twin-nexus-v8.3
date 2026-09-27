"""Patient-scoped Personal Baseline storage helpers."""
from __future__ import annotations
import re
from pathlib import Path

from src.config import DATA_DIR
from src.core.personal_baseline import PersonalBaselineEngine

def _safe_id(participant_id: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "_", str(participant_id or "LOCAL"))
    return value[:100] or "LOCAL"

def baseline_engine(participant_id: str) -> PersonalBaselineEngine:
    safe = _safe_id(participant_id)
    root = DATA_DIR / "baselines"
    return PersonalBaselineEngine(
        path=root / f"{safe}.json",
        history_path=root / f"{safe}_history.json",
    )

def baseline_summary(participant_id: str) -> dict:
    engine = baseline_engine(participant_id)
    b = engine.baseline
    if not b.has_data:
        return {
            "available": False,
            "samples": 0,
            "quality": 0.0,
            "confidence": 0.0,
            "duration_s": 0.0,
            "captured_at": None,
            "metrics": [],
        }
    return {
        "available": True,
        "samples": b.samples,
        "quality": b.quality,
        "confidence": b.confidence,
        "duration_s": b.duration_s,
        "captured_at": b.captured_at,
        "metrics": list(b.stats.keys()),
    }
