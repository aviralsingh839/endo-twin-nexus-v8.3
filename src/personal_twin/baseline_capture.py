"""Shared real-data baseline capture for ENDO-TWIN V9.

The capture is patient-scoped and quality-gated. It never uses demo/synthetic
rows and stores the resulting baseline through baseline_store.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Any

from src.personal_twin.baseline_store import baseline_engine

@dataclass
class BaselineCapture:
    participant_id: str
    duration_s: float = 60.0
    min_samples: int = 60
    min_quality: float = 0.45
    active: bool = False
    started_at: float | None = None
    accepted_rows: list[dict[str, Any]] = field(default_factory=list)
    last_result: dict[str, Any] | None = None

    def start(self) -> None:
        self.active = True
        self.started_at = time.time()
        self.accepted_rows.clear()
        self.last_result = None

    def stop(self) -> dict[str, Any]:
        self.active = False
        return self.finalize(force=True)

    @property
    def progress(self) -> float:
        if not self.active or not self.started_at:
            return 0.0
        elapsed = max(0.0, time.time() - self.started_at)
        return max(0.0, min(1.0, elapsed / max(self.duration_s, 1.0)))

    @property
    def accepted(self) -> int:
        return len(self.accepted_rows)

    def add_row(self, row: dict[str, Any]) -> dict[str, Any] | None:
        if not self.active:
            return None
        if not self._is_usable_live(row):
            return None
        self.accepted_rows.append(dict(row))
        if self.progress >= 1.0 and len(self.accepted_rows) >= self.min_samples:
            return self.finalize(force=True)
        return None

    def finalize(self, force: bool = False) -> dict[str, Any]:
        elapsed = 0.0 if not self.started_at else max(0.0, time.time() - self.started_at)
        if not force and (elapsed < self.duration_s or len(self.accepted_rows) < self.min_samples):
            return {"ready": False, "samples": len(self.accepted_rows), "progress": self.progress}
        if len(self.accepted_rows) < self.min_samples:
            self.active = False
            result = {
                "ready": False,
                "samples": len(self.accepted_rows),
                "progress": self.progress,
                "error": f"Not enough quality-gated windows ({len(self.accepted_rows)} < {self.min_samples}).",
            }
            self.last_result = result
            return result

        rows = [SimpleNamespace(**r) for r in self.accepted_rows[-max(self.min_samples, 120):]]
        try:
            engine = baseline_engine(self.participant_id)
            b = engine.capture_from_features(rows, min_samples=self.min_samples)
            result = {
                "ready": True,
                "samples": len(rows),
                "confidence": float(b.confidence),
                "quality": float(b.quality),
                "metrics": list(b.stats.keys()),
                "captured_at": b.captured_at,
            }
        except Exception as exc:
            result = {
                "ready": False,
                "samples": len(rows),
                "progress": self.progress,
                "error": str(exc),
            }
        self.active = False
        self.last_result = result
        return result

    def _is_usable_live(self, row: dict[str, Any]) -> bool:
        source = str(row.get("source", "")).lower()
        if source in {"demo", "synthetic"} or source.startswith("demo"):
            return False
        try:
            q = float(row.get("signal_quality", 0.0) or 0.0)
        except (TypeError, ValueError):
            return False
        if q < self.min_quality:
            return False
        if str(row.get("gating", "QUALITY_GATE")) != "USABLE":
            return False
        return True
