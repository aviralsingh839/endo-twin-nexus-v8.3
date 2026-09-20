"""Longitudinal Engine - Heart of CHRONO-TWIN NEXUS V8.3.

Implements:
- rolling windows (short, medium, long)
- persistence detection
- trend detection
- change-point detection
- recovery detection
- missing-data handling
- confidence scoring

Concept:
ONE ABNORMAL READING -> weak signal
REPEATED CHANGE -> stronger signal
MULTIPLE RELATED FEATURES CHANGING -> multimodal signal
PERSISTENT CHANGE + GOOD DATA QUALITY -> higher-confidence research signal
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import time
import math

import numpy as np

from src.data_models import FeatureVector
from src.core.personal_baseline import PersonalBaselineEngine


DEFAULT_METRICS = [
    "hr_bpm", "resting_hr_bpm", "rmssd_ms", "skin_temp_c",
    "gsr_tonic", "activity_level", "sleep_duration_h",
    "circadian_stability_index", "stress_index"
]

Z_NORMAL = 2.0
Z_ALERT = 3.0
PERSIST_POINTS = 3
PROGRESSIVE_SLOPE = 0.8
MIN_POINTS = 5


@dataclass
class MetricLongitudinal:
    metric: str
    kind: str  # normal | single | persistent | progressive | recovery | insufficient | missing
    latest_value: float
    baseline_median: float
    z_latest: float
    abs_change: float
    pct_change: float
    slope_per_day: float
    persistence_points: int
    persistence_hours: float
    confidence: float
    quality_ok: bool
    n_points: int = 0
    # Trend
    trend_direction: str = "stable"  # increasing, decreasing, stable
    trend_strength: float = 0.0
    # Recovery
    is_recovering: bool = False
    recovery_progress: float = 0.0
    # Change point
    change_points: List[float] = field(default_factory=list)

    def phrase(self) -> str:
        if self.kind == "normal":
            return f"{self.metric} within personal range (|z|={self.z_latest:.1f})."
        if self.kind == "insufficient":
            return f"{self.metric} deviates but data quality too low - no alert."
        if self.kind == "missing":
            return f"{self.metric} insufficient data."
        base = f"{self.metric}: {self.abs_change:+.1f} ({self.pct_change:+.0f}% vs baseline, |z|={self.z_latest:.1f})"
        if self.kind == "single":
            return base + ", single-point deviation."
        if self.kind == "persistent":
            return base + f", persistent {self.persistence_points} points (~{self.persistence_hours:.1f}h)."
        if self.kind == "progressive":
            return base + f", progressive ({self.slope_per_day:+.2f}/day, {self.persistence_points} pts rising)."
        if self.kind == "recovery":
            return base + f", recovering toward baseline ({self.recovery_progress:.0%} recovered)."
        return base


@dataclass
class LongitudinalReport:
    per_metric: Dict[str, MetricLongitudinal] = field(default_factory=dict)
    overall_kind: str = "normal"
    summary: str = "No persistent change detected."
    contributors: List[str] = field(default_factory=list)
    data_quality: float = 0.0
    n_windows: int = 0
    # Multimodal signals
    multimodal_signal: bool = False
    multimodal_metrics: List[str] = field(default_factory=list)
    persistence_score: float = 0.0
    recovery_detected: bool = False
    # Confidence breakdown
    confidence_breakdown: Dict[str, float] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "overall_kind": self.overall_kind,
            "summary": self.summary,
            "contributors": self.contributors,
            "data_quality": round(self.data_quality, 3),
            "n_windows": self.n_windows,
            "multimodal_signal": self.multimodal_signal,
            "multimodal_metrics": self.multimodal_metrics,
            "persistence_score": round(self.persistence_score, 3),
            "recovery_detected": self.recovery_detected,
            "confidence_breakdown": self.confidence_breakdown,
            "per_metric": {k: v.__dict__ for k, v in self.per_metric.items()},
        }


def _robust_scale(values: np.ndarray) -> float:
    med = float(np.median(values))
    mad = float(np.median(np.abs(values - med)))
    scale = 1.4826 * mad
    return max(scale, 0.02 * abs(med) + 1e-9)


class LongitudinalEngine:
    """Core longitudinal change detection."""

    def __init__(
        self,
        baseline: Optional[PersonalBaselineEngine] = None,
        metrics: Optional[List[str]] = None,
        z_normal: float = Z_NORMAL,
        z_alert: float = Z_ALERT,
        persist_points: int = PERSIST_POINTS,
        progressive_slope: float = PROGRESSIVE_SLOPE,
        min_points: int = MIN_POINTS,
        slope_window: int = 12,
        quality_threshold: float = 0.5,
    ):
        self.baseline = baseline
        self.metrics = metrics or DEFAULT_METRICS
        self.z_normal = z_normal
        self.z_alert = z_alert
        self.persist_points = persist_points
        self.progressive_slope = progressive_slope
        self.min_points = min_points
        self.slope_window = slope_window
        self.quality_threshold = quality_threshold

    def _series(self, features: List[FeatureVector], metric: str):
        ts, vals, q = [], [], []
        for f in features:
            v = getattr(f, metric, None)
            if v is None:
                continue
            try:
                v = float(v)
            except (TypeError, ValueError):
                continue
            if not np.isfinite(v):
                continue
            ts.append(float(f.timestamp_s))
            vals.append(v)
            q.append(float(f.signal_quality) if f.signal_quality is not None else 0.0)
        return ts, vals, q

    def _baseline_ref(self, metric: str, values: np.ndarray):
        if self.baseline is not None and self.baseline.has_baseline:
            s = self.baseline.baseline.stats.get(metric)
            if s is not None and s.std > 1e-9:
                return s.median, max(s.std, 1e-9), s.confidence
        # Use earliest stable quarter as reference
        n = max(self.min_points, int(np.ceil(len(values) * 0.25)))
        early = values[:n]
        if early.size < 3:
            return None, None, 0.0
        return float(np.median(early)), _robust_scale(early), 0.5

    def _detect_change_points(self, values: np.ndarray, timestamps: np.ndarray) -> List[float]:
        """Simple CUSUM-like change point detection."""
        if len(values) < 10:
            return []
        # Rolling mean comparison
        change_points = []
        window = max(5, len(values) // 4)
        for i in range(window, len(values) - window, window):
            before = values[i-window:i]
            after = values[i:i+window]
            if len(before) < 3 or len(after) < 3:
                continue
            mean_before = float(np.mean(before))
            mean_after = float(np.mean(after))
            std_before = float(np.std(before)) + 1e-9
            # Significant shift
            if abs(mean_after - mean_before) > 2.0 * std_before:
                change_points.append(float(timestamps[i]))
        return change_points

    def _trend_analysis(self, values: np.ndarray, timestamps: np.ndarray) -> Tuple[str, float, float]:
        """Returns (direction, strength, slope_per_day)."""
        if len(values) < 3:
            return "stable", 0.0, 0.0
        tail_n = min(self.slope_window, len(values))
        tail_ts = timestamps[-tail_n:]
        tail_vals = values[-tail_n:]
        if np.std(tail_vals) < 1e-9 or np.std(tail_ts) < 1e-9:
            return "stable", 0.0, 0.0
        x_hours = (tail_ts - tail_ts[0]) / 3600.0
        slope_per_hour = float(np.polyfit(x_hours, tail_vals, 1)[0])
        slope_per_day = slope_per_hour * 24.0
        # Direction
        if slope_per_day > self.progressive_slope:
            direction = "increasing"
        elif slope_per_day < -self.progressive_slope:
            direction = "decreasing"
        else:
            direction = "stable"
        # Strength via R^2 approximation
        corr = np.corrcoef(x_hours, tail_vals)[0, 1] if len(x_hours) > 2 else 0.0
        strength = float(corr ** 2) if np.isfinite(corr) else 0.0
        return direction, strength, slope_per_day

    def _recovery_detection(self, z_scores: np.ndarray, values: np.ndarray, baseline_median: float) -> Tuple[bool, float]:
        """Detect if a previously deviated signal is returning to baseline."""
        if len(z_scores) < 6:
            return False, 0.0
        # Check if max deviation was in first half and now closer to baseline
        half = len(z_scores) // 2
        max_z_early = float(np.max(np.abs(z_scores[:half]))) if half > 0 else 0.0
        latest_z = float(abs(z_scores[-1]))
        if max_z_early > self.z_alert and latest_z < max_z_early * 0.5:
            # Recovery progress: how much closer to baseline
            progress = 1.0 - (latest_z / max_z_early) if max_z_early > 0 else 0.0
            return True, float(max(0.0, min(1.0, progress)))
        return False, 0.0

    def evaluate(self, features: List[FeatureVector]) -> LongitudinalReport:
        if not features:
            return LongitudinalReport(summary="No feature history yet.", overall_kind="missing")

        report = LongitudinalReport(
            n_windows=len(features),
            data_quality=float(np.mean([f.signal_quality for f in features if f.signal_quality is not None] or [0.0])),
        )

        alerts = []
        recovery_metrics = []

        for metric in self.metrics:
            ts_list, vals_list, q_list = self._series(features, metric)
            if len(vals_list) < self.min_points:
                report.per_metric[metric] = MetricLongitudinal(
                    metric=metric, kind="missing", latest_value=0.0,
                    baseline_median=0.0, z_latest=0.0, abs_change=0.0,
                    pct_change=0.0, slope_per_day=0.0, persistence_points=0,
                    persistence_hours=0.0, confidence=0.0, quality_ok=False,
                    n_points=len(vals_list)
                )
                continue

            arr = np.asarray(vals_list, dtype=float)
            ts_arr = np.asarray(ts_list, dtype=float)
            med, scale, baseline_conf = self._baseline_ref(metric, arr)
            if med is None or scale is None:
                continue

            z = np.abs(arr - med) / scale
            latest = float(arr[-1])
            z_latest = float(z[-1])
            mean_q = float(np.mean(q_list)) if q_list else 0.0
            n = len(arr)

            # Persistence: trailing consecutive out-of-band
            persistence = 0
            for zi in z[::-1]:
                if zi > self.z_normal:
                    persistence += 1
                else:
                    break

            tail_q_n = max(persistence, 1)
            tail_quality = float(np.mean(q_list[-tail_q_n:])) if q_list else 0.0
            quality_ok = tail_quality >= self.quality_threshold

            # Trend
            trend_dir, trend_strength, slope_per_day = self._trend_analysis(arr, ts_arr)

            # Change points
            change_points = self._detect_change_points(arr, ts_arr)

            # Recovery
            is_recovering, recovery_progress = self._recovery_detection(z, arr, med)

            # Recent excursion for recovery classification
            recent_n = max(3, n // 2)
            max_z_recent = float(z[-recent_n:].max()) if len(z) >= recent_n else 0.0

            kind = self._classify(
                z_latest, persistence, slope_per_day, scale, z,
                latest, med, quality_ok, max_z_recent, is_recovering
            )

            # Confidence
            base_conf = 0.30 + 0.12 * min(persistence, 6) + 0.15 * min(n / 60.0, 1.0)
            quality_factor = 0.8 + 0.2 * mean_q
            baseline_factor = 0.5 + 0.5 * baseline_conf
            confidence = min(0.95, base_conf * quality_factor * baseline_factor)

            abs_change = latest - med
            pct_change = abs_change / abs(med) * 100.0 if abs(med) > 1e-9 else 0.0

            pers_hours = 0.0
            if persistence >= 2 and len(ts_list) >= 2:
                idx = min(persistence, len(ts_list) - 1)
                pers_hours = (ts_list[-1] - ts_list[-(idx + 1)]) / 3600.0

            ml = MetricLongitudinal(
                metric=metric,
                kind=kind,
                latest_value=latest,
                baseline_median=float(med),
                z_latest=z_latest,
                abs_change=float(abs_change),
                pct_change=float(pct_change),
                slope_per_day=slope_per_day,
                persistence_points=persistence,
                persistence_hours=pers_hours,
                confidence=float(confidence),
                quality_ok=quality_ok,
                n_points=n,
                trend_direction=trend_dir,
                trend_strength=trend_strength,
                is_recovering=is_recovering,
                recovery_progress=recovery_progress,
                change_points=change_points,
            )
            report.per_metric[metric] = ml

            if kind in ("persistent", "progressive"):
                alerts.append(ml)
            if is_recovering:
                recovery_metrics.append(metric)

        # Overall assessment
        self._finalize(report, alerts, recovery_metrics)
        return report

    def _classify(self, z_latest: float, persistence: int, slope_per_day: float,
                  scale: float, z: np.ndarray, latest: float, med: float,
                  quality_ok: bool, max_z_recent: float, is_recovering: bool) -> str:
        if is_recovering and max_z_recent > self.z_alert:
            return "recovery"
        if z_latest <= self.z_normal:
            if max_z_recent > self.z_alert:
                return "recovery"
            return "normal"
        if not quality_ok:
            return "insufficient"
        direction = 1.0 if latest > med else -1.0
        moving_away = slope_per_day * direction > 0
        if persistence >= self.persist_points and moving_away and abs(slope_per_day) >= self.progressive_slope:
            return "progressive"
        if persistence >= self.persist_points:
            return "persistent"
        return "single"

    def _finalize(self, report: LongitudinalReport, alerts: List[MetricLongitudinal], recovery_metrics: List[str]) -> None:
        insufficient = [m for m in report.per_metric.values() if m.kind == "insufficient"]
        if alerts:
            report.overall_kind = "deviation"
            report.contributors = [f"{m.metric} ({m.kind}, {m.pct_change:+.0f}%)" for m in alerts]
            report.summary = (
                "Persistent change detected: " + "; ".join(
                    f"{m.metric} {m.pct_change:+.0f}% from baseline, {m.kind} ({m.persistence_points} pts)"
                    for m in alerts[:4]
                ) + ". Research pattern detection - not a diagnosis."
            )
            # Multimodal: multiple related features changing
            if len(alerts) >= 2:
                report.multimodal_signal = True
                report.multimodal_metrics = [m.metric for m in alerts]
            report.persistence_score = float(np.mean([m.persistence_points for m in alerts])) if alerts else 0.0
            report.confidence_breakdown = {
                "persistence": float(np.mean([m.persistence_points for m in alerts]) / 6.0) if alerts else 0.0,
                "data_quality": report.data_quality,
                "n_metrics": len(alerts) / len(self.metrics),
            }
        elif insufficient:
            report.overall_kind = "insufficient_quality"
            report.summary = "Apparent deviation but signal quality too low - no alert. Improve sensor contact."
        else:
            # Check for recovery
            if recovery_metrics:
                report.overall_kind = "recovery"
                report.recovery_detected = True
                report.summary = f"Recovery trend detected in: {', '.join(recovery_metrics)}. Returning toward baseline."
            else:
                report.overall_kind = "normal"
                report.summary = "No persistent change detected. Physiology within personal baseline."


# Backward compatibility alias
ChangeDetector = LongitudinalEngine
