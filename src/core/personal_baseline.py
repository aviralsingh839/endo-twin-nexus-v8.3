"""Personal Baseline Engine for CHRONO-TWIN NEXUS V8.3.

Improvements over V8.1:
- mean, median, std, robust deviation (MAD)
- rolling baseline (EWMA + rolling window)
- baseline confidence
- minimum observations required
- seasonal/circadian context where possible
- baseline comparison: CURRENT vs PERSONAL BASELINE -> normalized deviation

The system learns what is normal for an individual first, then looks for
persistent deviations from that personal baseline.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import numpy as np

from src.config import DATA_DIR, BASELINE_MIN_DAYS, BASELINE_ROLLING_WINDOW_DAYS
from src.data_models import FeatureVector


BASELINE_METRICS = {
    "hr_bpm": "Heart rate (bpm)",
    "resting_hr_bpm": "Resting HR (bpm)",
    "rmssd_ms": "HRV RMSSD (ms)",
    "skin_temp_c": "Skin temperature (°C)",
    "gsr_tonic": "GSR tonic",
    "activity_level": "Activity level",
    "sleep_duration_h": "Sleep duration (h)",
    "sleep_regularity": "Sleep regularity",
    "circadian_stability_index": "Circadian stability",
}


@dataclass
class MetricStats:
    median: float
    mean: float
    std: float
    mad: float
    p05: float
    p95: float
    p25: float
    p75: float
    count: int
    min_obs_days: int = 0
    # Rolling baseline
    rolling_median: float = 0.0
    rolling_std: float = 0.0
    # Confidence
    confidence: float = 0.0
    last_updated: float = field(default_factory=time.time)
    # Seasonal/circadian context
    hour_of_day_mean: Dict[int, float] = field(default_factory=dict)
    day_of_week_mean: Dict[int, float] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "median": round(float(self.median), 4),
            "mean": round(float(self.mean), 4),
            "std": round(float(self.std), 4),
            "mad": round(float(self.mad), 4),
            "p05": round(float(self.p05), 4),
            "p95": round(float(self.p95), 4),
            "p25": round(float(self.p25), 4),
            "p75": round(float(self.p75), 4),
            "count": int(self.count),
            "min_obs_days": int(self.min_obs_days),
            "rolling_median": round(float(self.rolling_median), 4),
            "rolling_std": round(float(self.rolling_std), 4),
            "confidence": round(float(self.confidence), 3),
            "last_updated": self.last_updated,
            "hour_of_day_mean": self.hour_of_day_mean,
            "day_of_week_mean": self.day_of_week_mean,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "MetricStats":
        return cls(
            median=float(d["median"]),
            mean=float(d.get("mean", d["median"])),
            std=float(d["std"]),
            mad=float(d.get("mad", 0.0)),
            p05=float(d["p05"]),
            p95=float(d["p95"]),
            p25=float(d.get("p25", d["p05"])),
            p75=float(d.get("p75", d["p95"])),
            count=int(d.get("count", 0)),
            min_obs_days=int(d.get("min_obs_days", 0)),
            rolling_median=float(d.get("rolling_median", d["median"])),
            rolling_std=float(d.get("rolling_std", d["std"])),
            confidence=float(d.get("confidence", 0.0)),
            last_updated=float(d.get("last_updated", time.time())),
            hour_of_day_mean=d.get("hour_of_day_mean", {}),
            day_of_week_mean=d.get("day_of_week_mean", {}),
        )


@dataclass
class PersonalBaseline:
    captured_at: float = 0.0
    duration_s: float = 0.0
    samples: int = 0
    days_covered: int = 0
    quality: float = 0.0
    confidence: float = 0.0
    stats: Dict[str, MetricStats] = field(default_factory=dict)
    version: str = "8.3"

    @property
    def has_data(self) -> bool:
        return bool(self.stats) and self.captured_at > 0

    @property
    def is_stable(self) -> bool:
        return self.days_covered >= BASELINE_MIN_DAYS and self.confidence >= 0.5

    def normal_range(self, metric: str) -> Optional[Tuple[float, float]]:
        s = self.stats.get(metric)
        if s is None:
            return None
        return s.p05, s.p95

    def zscore(self, metric: str, value: Optional[float]) -> Optional[float]:
        if value is None or (isinstance(value, float) and (np.isnan(value) or np.isinf(value))):
            return None
        s = self.stats.get(metric)
        if s is None or s.std <= 1e-9:
            return None
        return float((value - s.median) / s.std)

    def robust_zscore(self, metric: str, value: Optional[float]) -> Optional[float]:
        if value is None or (isinstance(value, float) and (np.isnan(value) or np.isinf(value))):
            return None
        s = self.stats.get(metric)
        if s is None:
            return None
        scale = 1.4826 * s.mad if s.mad > 1e-9 else s.std
        if scale <= 1e-9:
            return None
        return float((value - s.median) / scale)

    def deviation_percent(self, metric: str, value: Optional[float]) -> Optional[float]:
        if value is None:
            return None
        s = self.stats.get(metric)
        if s is None or abs(s.median) < 1e-9:
            return None
        return float((value - s.median) / abs(s.median) * 100.0)

    def compare(self, metric: str, value: Optional[float]) -> Dict:
        """CURRENT vs PERSONAL BASELINE comparison."""
        if value is None:
            return {"metric": metric, "current": None, "baseline": None, "deviation_pct": None, "zscore": None, "status": "no_data"}
        s = self.stats.get(metric)
        if s is None:
            return {"metric": metric, "current": value, "baseline": None, "deviation_pct": None, "zscore": None, "status": "no_baseline"}
        z = self.zscore(metric, value)
        rz = self.robust_zscore(metric, value)
        pct = self.deviation_percent(metric, value)
        # Status
        if z is None:
            status = "unknown"
        elif abs(z) < 1.5:
            status = "normal"
        elif abs(z) < 2.5:
            status = "mild_deviation"
        elif abs(z) < 3.5:
            status = "moderate_deviation"
        else:
            status = "significant_deviation"
        return {
            "metric": metric,
            "current": float(value),
            "baseline_median": float(s.median),
            "baseline_mean": float(s.mean),
            "baseline_range": [float(s.p05), float(s.p95)],
            "deviation_pct": float(pct) if pct is not None else None,
            "zscore": float(z) if z is not None else None,
            "robust_zscore": float(rz) if rz is not None else None,
            "confidence": float(s.confidence),
            "status": status,
        }


class PersonalBaselineEngine:
    """Improved baseline engine for V8.3."""

    def __init__(self, path: Path | str | None = None, history_path: Path | str | None = None):
        self.path = Path(path) if path else DATA_DIR / "baselines" / "personal_baseline_v8_3.json"
        self.history_path = Path(history_path) if history_path else DATA_DIR / "baselines" / "calibration_history_v8_3.json"
        self.baseline = PersonalBaseline()
        self._history: List[dict] = []
        self._rolling: Dict[str, List[float]] = {}
        self._rolling_timestamps: Dict[str, List[float]] = {}
        self._updates_since_save = 0
        self.load()

    def capture_from_features(self, features: Iterable[FeatureVector], min_samples: int = 60) -> PersonalBaseline:
        rows = [f for f in features if f is not None]
        if len(rows) < min_samples:
            raise ValueError(f"Not enough samples for calibration ({len(rows)} < {min_samples}). Need at least 5 min calm data.")

        ts = [f.timestamp_s for f in rows]
        if not ts:
            raise ValueError("No timestamps")

        # Calculate days covered
        if len(ts) > 1:
            duration_s = max(ts) - min(ts)
            days_covered = max(1, int(duration_s / 86400) + 1)
        else:
            duration_s = 0.0
            days_covered = 1

        qualities = [f.signal_quality for f in rows if f.signal_quality is not None]
        stats: Dict[str, MetricStats] = {}

        for metric in BASELINE_METRICS:
            values = []
            hour_buckets: Dict[int, List[float]] = {h: [] for h in range(24)}
            dow_buckets: Dict[int, List[float]] = {d: [] for d in range(7)}

            for f in rows:
                v = getattr(f, metric, None)
                if v is None:
                    continue
                try:
                    v = float(v)
                except (TypeError, ValueError):
                    continue
                if not np.isfinite(v):
                    continue
                values.append(v)
                # Circadian context
                import datetime
                dt = datetime.datetime.fromtimestamp(f.timestamp_s)
                hour_buckets[dt.hour].append(v)
                dow_buckets[dt.weekday()].append(v)

            if len(values) < min_samples * 0.4:
                continue
            arr = np.array(values, dtype=float)
            arr = arr[np.isfinite(arr)]
            if arr.size < 10:
                continue

            median = float(np.median(arr))
            mean = float(np.mean(arr))
            std = float(np.std(arr))
            mad = float(np.median(np.abs(arr - median)))
            p05 = float(np.percentile(arr, 5))
            p95 = float(np.percentile(arr, 95))
            p25 = float(np.percentile(arr, 25))
            p75 = float(np.percentile(arr, 75))

            # Confidence based on count, days, quality
            count_conf = min(1.0, len(arr) / 200.0)
            days_conf = min(1.0, days_covered / BASELINE_MIN_DAYS)
            quality_conf = float(np.mean(qualities)) if qualities else 0.0
            confidence = 0.4 * count_conf + 0.3 * days_conf + 0.3 * quality_conf

            # Hourly means
            hour_means = {}
            for h, vals in hour_buckets.items():
                if vals:
                    hour_means[str(h)] = float(np.mean(vals))
            dow_means = {}
            for d, vals in dow_buckets.items():
                if vals:
                    dow_means[str(d)] = float(np.mean(vals))

            stats[metric] = MetricStats(
                median=median, mean=mean, std=std, mad=mad,
                p05=p05, p95=p95, p25=p25, p75=p75,
                count=len(arr), min_obs_days=days_covered,
                rolling_median=median, rolling_std=std,
                confidence=confidence,
                hour_of_day_mean=hour_means,
                day_of_week_mean=dow_means,
            )

        if not stats:
            raise ValueError("No usable signals during calibration window.")

        overall_conf = float(np.mean([s.confidence for s in stats.values()])) if stats else 0.0
        baseline = PersonalBaseline(
            captured_at=ts[-1] if ts else time.time(),
            duration_s=duration_s,
            samples=len(rows),
            days_covered=days_covered,
            quality=float(np.mean(qualities)) if qualities else 0.0,
            confidence=overall_conf,
            stats=stats,
            version="8.3",
        )
        self.baseline = baseline
        self._history.append({
            "captured_at": baseline.captured_at,
            "iso": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(baseline.captured_at)),
            "duration_s": round(baseline.duration_s, 1),
            "samples": baseline.samples,
            "days_covered": baseline.days_covered,
            "quality": round(baseline.quality, 3),
            "confidence": round(baseline.confidence, 3),
            "metrics": list(stats.keys()),
        })
        if len(self._history) > 200:
            self._history = self._history[-200:]
        self.save()
        return baseline

    @property
    def has_baseline(self) -> bool:
        return self.baseline.has_data

    def normal_range(self, metric: str) -> Optional[Tuple[float, float]]:
        return self.baseline.normal_range(metric)

    def zscore(self, metric: str, value: Optional[float]) -> Optional[float]:
        return self.baseline.zscore(metric, value)

    def robust_zscore(self, metric: str, value: Optional[float]) -> Optional[float]:
        return self.baseline.robust_zscore(metric, value)

    def compare_current_vs_baseline(self, fv: FeatureVector) -> Dict[str, Dict]:
        result = {}
        for metric in BASELINE_METRICS:
            v = getattr(fv, metric, None)
            result[metric] = self.baseline.compare(metric, v)
        return result

    def history(self) -> List[dict]:
        return list(self._history)

    def update_observation(self, fv: FeatureVector, alpha: float = 0.05, window: int = 600) -> Optional[PersonalBaseline]:
        if fv is None:
            return None
        ts = float(getattr(fv, "timestamp_s", time.time()))
        touched = False
        for metric in BASELINE_METRICS:
            v = getattr(fv, metric, None)
            if v is None:
                continue
            try:
                v = float(v)
            except (TypeError, ValueError):
                continue
            if not np.isfinite(v):
                continue
            dq = self._rolling.setdefault(metric, [])
            tq = self._rolling_timestamps.setdefault(metric, [])
            dq.append(v)
            tq.append(ts)
            # Keep rolling window by days
            cutoff = ts - BASELINE_ROLLING_WINDOW_DAYS * 86400
            while tq and tq[0] < cutoff:
                tq.pop(0)
                dq.pop(0)
            if len(dq) > window:
                dq = dq[-window:]
                tq = tq[-window:]
                self._rolling[metric] = dq
                self._rolling_timestamps[metric] = tq
            if len(dq) < 30:
                continue
            med = float(np.median(dq))
            mad = float(np.median(np.abs(np.asarray(dq) - med)))
            scale = max(1.4826 * mad, 0.02 * abs(med) + 1e-9)

            cur = self.baseline.stats.get(metric)
            if cur is not None and cur.median != 0.0:
                z = (med - cur.median) / max(scale, cur.std if cur.std > 1e-9 else scale)
                if abs(z) > 3.5:
                    continue
                new_median = (1.0 - alpha) * cur.median + alpha * med
                new_std = (1.0 - alpha) * cur.std + alpha * scale
                new_mad = (1.0 - alpha) * cur.mad + alpha * (scale / 1.4826)
                new_count = cur.count + 1
                new_conf = min(1.0, cur.confidence + 0.001)
            else:
                new_median, new_std, new_mad, new_count = med, scale, scale / 1.4826, len(dq)
                new_conf = min(1.0, len(dq) / 200.0)

            # Preserve circadian context
            hour_means = cur.hour_of_day_mean if cur else {}
            dow_means = cur.day_of_week_mean if cur else {}

            self.baseline.stats[metric] = MetricStats(
                median=float(new_median),
                mean=float(np.mean(dq)),
                std=float(new_std),
                mad=float(new_mad),
                p05=float(np.percentile(dq, 5)),
                p95=float(np.percentile(dq, 95)),
                p25=float(np.percentile(dq, 25)),
                p75=float(np.percentile(dq, 75)),
                count=int(new_count),
                min_obs_days=self.baseline.days_covered,
                rolling_median=float(med),
                rolling_std=float(scale),
                confidence=float(new_conf),
                last_updated=ts,
                hour_of_day_mean=hour_means,
                day_of_week_mean=dow_means,
            )
            touched = True

        if not touched:
            return None
        self.baseline.captured_at = ts
        self.baseline.samples += 1
        # Recalc overall confidence
        if self.baseline.stats:
            self.baseline.confidence = float(np.mean([s.confidence for s in self.baseline.stats.values()]))
        self._updates_since_save += 1
        if self._updates_since_save >= 10:
            self.save()
            self._updates_since_save = 0
        return self.baseline

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "captured_at": self.baseline.captured_at,
            "duration_s": self.baseline.duration_s,
            "samples": self.baseline.samples,
            "days_covered": self.baseline.days_covered,
            "quality": self.baseline.quality,
            "confidence": self.baseline.confidence,
            "version": self.baseline.version,
            "stats": {k: v.to_dict() for k, v in self.baseline.stats.items()},
        }
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        self.history_path.write_text(json.dumps(self._history, indent=2), encoding="utf-8")

    def load(self) -> None:
        try:
            if self.path.exists():
                d = json.loads(self.path.read_text(encoding="utf-8"))
                stats = {k: MetricStats.from_dict(v) for k, v in d.get("stats", {}).items()}
                self.baseline = PersonalBaseline(
                    captured_at=float(d.get("captured_at", 0.0)),
                    duration_s=float(d.get("duration_s", 0.0)),
                    samples=int(d.get("samples", 0)),
                    days_covered=int(d.get("days_covered", 0)),
                    quality=float(d.get("quality", 0.0)),
                    confidence=float(d.get("confidence", 0.0)),
                    stats=stats,
                    version=d.get("version", "8.3"),
                )
        except Exception:
            self.baseline = PersonalBaseline()
        try:
            if self.history_path.exists():
                self._history = json.loads(self.history_path.read_text(encoding="utf-8"))
                if not isinstance(self._history, list):
                    self._history = []
        except Exception:
            self._history = []


# Backward compatibility alias
BaselineManager = PersonalBaselineEngine
