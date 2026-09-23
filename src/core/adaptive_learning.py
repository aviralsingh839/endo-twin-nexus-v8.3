"""Continual self-learning layer for the ENDO-TWIN wearable stream.

What this module does
---------------------
ENDO-TWIN already has a *static* personal baseline (``src/core/personal_baseline.py``):
one snapshot is captured after roughly an hour of calm data and every later z-score is
measured against that frozen snapshot.  This module adds the missing half - a model
that keeps learning for as long as the device is worn, and that *upgrades itself* as
evidence accumulates.

The upgrade mechanism is a capability ladder.  Each rung is unlocked automatically
from wearing time, signal quality and coverage - never from a button press, and never
from a number that was not measured:

======================  ===========================================================================
Tier                    What the wearer's model can do once the gates are met
======================  ===========================================================================
``population``          Nothing personal yet. Population priors only, clearly labelled as such.
``personalized``        Robust personal norms (median / MAD / 5-95pct) and z-scores per metric.
``circadian``           Time-of-day conditioned norms, so night and post-waking values are
                        compared with the same hour of previous days instead of a flat average.
``adaptive``            Drift-aware tracking: a *persistent* shift is absorbed into the personal
                        norm over hours, while a *transient* excursion is frozen out of the
                        baseline so a real event can never be learned away.
======================  ===========================================================================

Independently of the ladder, a supervised head unlocks only when the wearer has supplied
enough labelled events and the head beats a base-rate predictor on **unseen, later** labels.
If it does not beat the base rate, it refuses to activate and says so.

Scientific guardrails implemented here
-------------------------------------
* Values are rejected by hard physical bounds before they can touch the model.
* Worn time only accumulates across gaps shorter than ``max_worn_gap_s``; time the device
  spent on the charger is not counted as wearing time.
* Adaptation is rate limited (``max_adapt_sigma_per_hour``) so the model cannot silently
  swallow a genuine acute event, and every absorption is written to an audit trail.
* An unconfirmed deviation *freezes* the baseline; only a change point that persists for
  ``drift_min_persistence_s`` may be absorbed.
* Confidence reported here is an engineering confidence derived from coverage, quality and
  wearing time.  It is NOT clinical validity and is never presented as such.
* All state lives in a local per-wearer JSON file. Nothing leaves the machine.

Provenance: features are MEASURED/DERIVED upstream; everything this module emits is
MODEL_INFERRED or a re-description of measured wearing time, and is labelled as such.
"""
from __future__ import annotations

import json
import math
import os
import random
import time
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Deque, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np

from src.config import DATA_DIR
from src.core.personal_baseline import BASELINE_METRICS

SCHEMA = "endo_twin.adaptive_wearable/1"
DISCLAIMER = (
    "Engineering learning layer on a research prototype. Not a diagnosis, not a medical "
    "device, not clinically validated. Confidence values describe data coverage, not "
    "clinical certainty."
)

# ---------------------------------------------------------------------------
# Metrics this layer learns
# ---------------------------------------------------------------------------
# BASELINE_METRICS includes sleep aggregates that arrive only once per day, so the
# continual layer focuses on the continuously sampled channels and treats any other
# metric as an optional extra when it happens to be present.
LEARNING_METRICS: Tuple[str, ...] = (
    "hr_bpm",
    "resting_hr_bpm",
    "rmssd_ms",
    "skin_temp_c",
    "gsr_tonic",
    "activity_level",
)

# Physically plausible bounds. Anything outside is treated as sensor garbage and is
# counted as rejected rather than learned from.
METRIC_BOUNDS: Dict[str, Tuple[float, float]] = {
    "hr_bpm": (25.0, 240.0),
    "resting_hr_bpm": (25.0, 200.0),
    "rmssd_ms": (1.0, 400.0),
    "skin_temp_c": (15.0, 43.0),
    "gsr_tonic": (0.0, 4095.0),
    "activity_level": (0.0, 1.0),
}

# Population priors = (mean, sd). Used only while the model is still at the
# population tier, and always reported as POPULATION rather than personal.
POPULATION_PRIOR: Dict[str, Tuple[float, float]] = {
    "hr_bpm": (72.0, 12.0),
    "resting_hr_bpm": (62.0, 9.0),
    "rmssd_ms": (42.0, 15.0),
    "skin_temp_c": (32.5, 0.7),
    "gsr_tonic": (450.0, 180.0),
    "activity_level": (0.10, 0.08),
}

METRIC_UNITS: Dict[str, str] = {
    "hr_bpm": "bpm",
    "resting_hr_bpm": "bpm",
    "rmssd_ms": "ms",
    "skin_temp_c": "C",
    "gsr_tonic": "a.u.",
    "activity_level": "index",
}

TIERS: Tuple[str, ...] = ("population", "personalized", "circadian", "adaptive")
TIER_INDEX: Dict[str, int] = {name: i for i, name in enumerate(TIERS)}

TIER_HEADLINES: Dict[str, str] = {
    "population": "Population reference only - the model has not met this wearer yet.",
    "personalized": "Personal norms active: deviations are measured against this wearer, not the population.",
    "circadian": "Time-of-day norms active: values are compared with the same hour of previous days.",
    "adaptive": "Drift-aware: a persistent shift becomes the new normal, a transient event does not.",
}


def metric_label(metric: str) -> str:
    """Human label for a metric name."""
    return BASELINE_METRICS.get(metric, metric)


def _iso(ts: Optional[float]) -> Optional[str]:
    if ts is None:
        return None
    try:
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(float(ts)))
    except (OverflowError, OSError, ValueError):
        return None


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
@dataclass
class AdaptiveConfig:
    """Thresholds for the capability ladder.

    Defaults are the production values used by the workstations. Tests and the demo
    script build accelerated variants with :meth:`scaled` so that weeks of simulated
    wearing can be replayed in a second without changing the logic under test.
    """

    # --- bookkeeping ---
    max_worn_gap_s: float = 300.0          # longer gap = device was not being worn
    save_every: int = 60                   # observations between automatic saves
    reservoir_size: int = 1024             # bounded sample memory per metric
    recent_window: int = 128               # samples defining the "recent regime"
    bucket_size: int = 256                 # bounded sample memory per hour bucket
    recalc_every: int = 30                 # descriptive stats refresh interval (samples)
    norm_init_samples: int = 300           # samples before the personal norm is set
    norm_init_span_s: float = 12 * 3600.0  # the first estimate must span part of a day
    norm_init_min_quality: float = 0.50    # ...and be usable signal
    history_limit: int = 200               # audit events kept on disk

    # --- tier 1: personalized ---
    personal_min_worn_s: float = 3600.0
    personal_min_samples: int = 300
    personal_min_metric_samples: int = 120
    personal_min_quality: float = 0.50
    personal_min_metrics: int = 4

    # --- tier 2: circadian ---
    circadian_min_worn_s: float = 86400.0
    circadian_min_days: int = 2
    circadian_bucket_min: int = 30
    circadian_min_buckets: int = 6

    # --- tier 3: adaptive ---
    adaptive_min_worn_s: float = 3 * 86400.0
    adaptive_min_days: int = 3
    adaptive_min_metric_samples: int = 500
    adaptive_min_metrics: int = 3
    ph_delta_sigma: float = 0.25           # Page-Hinkley slack
    ph_lambda_sigma: float = 8.0           # Page-Hinkley alarm threshold
    drift_min_persistence_s: float = 6 * 3600.0
    drift_min_shift_sigma: float = 1.5
    drift_min_samples: int = 60
    max_adapt_sigma_per_hour: float = 0.35  # absorption rate limit
    max_absorb_sigma: float = 6.0           # one absorption may never exceed this
    settle_sigma: float = 0.35              # |gap| below this ends absorption
    drift_window_sigma: float = 1.5        # |z| above this counts as "under deviation"
    quiet_reset_samples: int = 30          # consecutive normal samples that close a window
    freeze_z: float = 3.5                  # |z| above this freezes gradual tracking

    # --- robustness / rollback ---
    min_scale_fraction: float = 0.02        # scale floor relative to |median|
    quality_floor: float = 0.35             # sustained quality below this demotes
    rollback_window: int = 60
    rollback_cooldown_s: float = 1800.0

    # --- supervised head ---
    head_min_labels: int = 20
    head_min_per_class: int = 5
    head_min_prospective: int = 30
    head_margin: float = 0.15               # relative gain required over the base rate
    head_min_win_rate: float = 0.65         # share of unseen labels it must beat
    head_replay_epochs: int = 3             # experience replay passes per new label
    head_replay_batch: int = 64
    head_lr: float = 0.30
    head_lr_decay: float = 60.0
    head_l2: float = 0.001
    label_match_s: float = 900.0            # label must sit near a stored feature row

    def scaled(self, factor: float = 0.01, **overrides: Any) -> "AdaptiveConfig":
        """Return a copy with time/threshold gates divided by ``factor``.

        Used to replay weeks of wearing in a unit test. The maths is unchanged - only
        the thresholds move - so a scaled run exercises exactly the production code
        path.
        """
        if factor <= 0:
            raise ValueError("factor must be positive")
        data = self.__dict__.copy()
        for key in (
            "personal_min_worn_s",
            "personal_min_samples",
            "personal_min_metric_samples",
            "circadian_min_worn_s",
            "circadian_bucket_min",
            "adaptive_min_worn_s",
            "adaptive_min_metric_samples",
            "drift_min_persistence_s",
            "drift_min_samples",
            "rollback_window",
            "recalc_every",
            "save_every",
        ):
            data[key] = max(1, int(round(data[key] / factor)))
        data.update(overrides)
        return AdaptiveConfig(**data)


# ---------------------------------------------------------------------------
# Audit events
# ---------------------------------------------------------------------------
@dataclass
class LearningEvent:
    """One line of the model's upgrade / adaptation audit trail."""

    kind: str                                   # promotion | rollback | drift | capability
    at: float
    detail: str
    from_tier: Optional[str] = None
    to_tier: Optional[str] = None
    metric: Optional[str] = None
    evidence: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kind": self.kind,
            "at": float(self.at),
            "iso": _iso(self.at),
            "detail": self.detail,
            "from_tier": self.from_tier,
            "to_tier": self.to_tier,
            "metric": self.metric,
            "evidence": self.evidence,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LearningEvent":
        return cls(
            kind=data.get("kind", "unknown"),
            at=float(data.get("at", 0.0)),
            detail=data.get("detail", ""),
            from_tier=data.get("from_tier"),
            to_tier=data.get("to_tier"),
            metric=data.get("metric"),
            evidence=dict(data.get("evidence") or {}),
        )


# ---------------------------------------------------------------------------
# Per-metric streaming learner
# ---------------------------------------------------------------------------
class MetricLearning:
    """Streaming, robust, drift-aware statistics for a single metric.

    Three things are kept deliberately separate:

    * **descriptive statistics** (``desc_*``) - what the recent samples actually looked
      like, used for reporting.
    * **the personal norm** (``median`` + ``scale``) - the reference this wearer is
      compared against.  It is initialised once from the first usable window, and after
      that it only moves through the metered, audited paths in :meth:`maybe_absorb`
      (confirmed shift) and :meth:`gentle_track` (gradual drift).
    * **the time-of-day shape** (``hour_stats``) - offsets relative to the norm, learned
      only from periods the model considers normal, so a shift in progress cannot
      quietly rewrite the circadian layer.

    Keeping the norm out of the refresh path is what stops a genuine event from being
    averaged away: the norm cannot chase the data, the data has to earn a change first.
    """

    def __init__(self, metric: str, cfg: AdaptiveConfig, rng: random.Random):
        self.metric = metric
        self.cfg = cfg
        self._rng = rng
        self.bounds = METRIC_BOUNDS.get(metric, (-math.inf, math.inf))

        self.n = 0
        self.rejected = 0
        self.quality_sum = 0.0
        self.first_ts: Optional[float] = None
        self.last_ts: Optional[float] = None
        self.days: List[str] = []
        self._day_set: set = set()

        # descriptive layer (raw values)
        self.reservoir: Deque[float] = deque(maxlen=cfg.reservoir_size)
        self.tail: Deque[float] = deque(maxlen=cfg.recent_window)
        self.hour_buckets: List[Deque[float]] = [deque(maxlen=cfg.bucket_size) for _ in range(24)]
        self.clean_reservoir: Deque[float] = deque(maxlen=cfg.reservoir_size)
        self.desc_median: Optional[float] = None
        self.desc_mad: float = 0.0
        self.desc_scale: float = 0.0
        self.desc_p25: Optional[float] = None
        self.desc_p75: Optional[float] = None
        self.ewma_mean: Optional[float] = None
        self.ewma_var: float = 0.0
        self.hour_stats: Dict[int, Dict[str, float]] = {}

        # personal norm (moves only through adaptation)
        self.median: Optional[float] = None
        self.scale: float = 0.0
        self.norm_set_at: Optional[float] = None
        self.norm_set_n: int = 0
        self.circadian_enabled: bool = False

        # change detection
        self.ph_sum = 0.0
        self.ph_min = 0.0
        self.ph_neg_sum = 0.0
        self.ph_max = 0.0
        self.ph_alarm = False
        self.dev_seconds = 0.0          # accumulated wearing time under deviation
        self.dev_samples = 0
        self.dev_started_at: Optional[float] = None
        self.dev_direction = 0
        self.quiet_samples = 0
        self.absorbing = False
        self.absorb_from: Optional[float] = None
        self.absorbed_total = 0.0
        self.last_absorb_ts: Optional[float] = None
        self.frozen_samples = 0

    # -- helpers ---------------------------------------------------------
    def set_circadian(self, enabled: bool) -> None:
        self.circadian_enabled = bool(enabled)

    def expected(self, ts: float) -> float:
        """What the norm expects at this time of day."""
        centre = self.median if self.median is not None else (self.desc_median or 0.0)
        if self.circadian_enabled:
            stat = self.hour_stats.get(time.localtime(ts).tm_hour)
            if stat and stat["n"] >= 3:
                return centre + stat["offset"]
        return centre

    def residual(self, value: float, ts: float) -> float:
        return float(value) - self.expected(ts)

    def add(self, value: Any, ts: float, quality: float, dt: float = 0.0) -> bool:
        """Feed one sample. Returns False when the value was rejected."""
        try:
            v = float(value)
        except (TypeError, ValueError):
            return False
        if not math.isfinite(v):
            return False
        lo, hi = self.bounds
        if v < lo or v > hi:
            self.rejected += 1
            return False

        self.n += 1
        self.quality_sum += max(0.0, min(1.0, quality))
        if self.first_ts is None:
            self.first_ts = ts
        self.last_ts = ts

        day_key = time.strftime("%Y-%m-%d", time.localtime(ts))
        if day_key not in self._day_set:
            self._day_set.add(day_key)
            self.days.append(day_key)
            if len(self.days) > 400:
                for stale in self.days[:-400]:
                    self._day_set.discard(stale)
                self.days = self.days[-400:]

        self.reservoir.append(v)
        self.tail.append(v)
        # The time-of-day shape is learned from normal periods only, so a shift in
        # progress cannot rewrite the circadian layer and hide itself.
        if not self.absorbing and self.dev_seconds <= 0.0:
            self.hour_buckets[time.localtime(ts).tm_hour].append(v)
            self.clean_reservoir.append(v)

        if self.ewma_mean is None:
            self.ewma_mean = v
            self.ewma_var = 0.0
        else:
            alpha = 2.0 / (min(self.n, 500) + 1.0)
            delta = v - self.ewma_mean
            self.ewma_mean += alpha * delta
            self.ewma_var = (1.0 - alpha) * (self.ewma_var + alpha * delta * delta)

        if self.n % max(1, self.cfg.recalc_every) == 1 or self.desc_median is None:
            self._refresh()

        self._detect(ts, dt)
        return True

    def _refresh(self) -> None:
        """Recompute descriptive statistics. The personal norm is NOT touched here."""
        if not self.reservoir:
            return
        arr = np.fromiter(self.reservoir, dtype=float, count=len(self.reservoir))
        self.desc_median = float(np.median(arr))
        self.desc_mad = float(np.median(np.abs(arr - self.desc_median)))
        self.desc_p25 = float(np.percentile(arr, 25))
        self.desc_p75 = float(np.percentile(arr, 75))
        self.desc_scale = max(1.4826 * self.desc_mad,
                              self.cfg.min_scale_fraction * abs(self.desc_median), 1e-9)

        # Personal norm, initialised exactly once. It waits for a window that spans
        # part of a day (so the centre is not "this morning") and it starts wide on
        # purpose: until the time-of-day layer exists, the norm must tolerate normal
        # circadian variation instead of calling it a deviation.
        span = (self.last_ts or 0.0) - (self.first_ts or 0.0)
        if (
            self.median is None
            and self.n >= self.cfg.norm_init_samples
            and span >= self.cfg.norm_init_span_s
            and self.quality >= self.cfg.norm_init_min_quality
        ):
            self.median = self.desc_median
            self.scale = max(self.desc_scale, self._iqr_scale())
            self.norm_set_n = self.n
            self.norm_set_at = self.last_ts

        # The time-of-day shape is measured against a level reference taken from the
        # SAME clean sample set, so it stays a shape (mean removed) instead of drifting
        # when the norm moves. The prediction norm + offset then follows the norm.
        reference = self.median if self.median is not None else self.desc_median
        if self.clean_reservoir:
            carr = np.fromiter(self.clean_reservoir, dtype=float, count=len(self.clean_reservoir))
            reference = float(np.median(carr))
        hours: Dict[int, Dict[str, float]] = {}
        for hour, bucket in enumerate(self.hour_buckets):
            if len(bucket) < 3:
                continue
            harr = np.fromiter(bucket, dtype=float, count=len(bucket))
            hmed = float(np.median(harr))
            hmad = float(np.median(np.abs(harr - hmed)))
            floor = 0.3 * (self.scale if self.scale > 0 else self.desc_scale)
            hours[hour] = {
                "n": int(len(bucket)),
                "offset": hmed - reference,
                "scale": max(1.4826 * hmad, floor, 1e-9),
            }
        self.hour_stats = hours

    def _iqr_scale(self) -> float:
        if self.desc_p25 is None or self.desc_p75 is None:
            return self.desc_scale
        return max((self.desc_p75 - self.desc_p25) / 1.349, 1e-9)

    @property
    def norm_ready(self) -> bool:
        return self.median is not None and self.scale > 0

    @property
    def quality(self) -> float:
        return self.quality_sum / self.n if self.n else 0.0

    @property
    def days_covered(self) -> int:
        return len(self._day_set)

    @property
    def hour_coverage(self) -> Dict[int, int]:
        return {h: len(b) for h, b in enumerate(self.hour_buckets) if len(b)}

    # -- change detection -------------------------------------------------
    def _detect(self, ts: float, dt: float) -> None:
        if not self.norm_ready or not self.tail:
            return
        r = self.residual(self.tail[-1], ts)
        z = r / self.scale if self.scale > 0 else 0.0

        # Page-Hinkley on the hour-aware residual: the change *trigger*.
        delta = self.cfg.ph_delta_sigma * self.scale
        self.ph_sum += (r - delta)
        self.ph_min = min(self.ph_min, self.ph_sum)
        self.ph_neg_sum += (r + delta)
        self.ph_max = max(self.ph_max, self.ph_neg_sum)
        threshold = self.cfg.ph_lambda_sigma * self.scale
        self.ph_alarm = (self.ph_sum - self.ph_min) > threshold or (self.ph_max - self.ph_neg_sum) > threshold

        # Accumulated time under deviation: the quantity that authorises absorption.
        if abs(z) >= self.cfg.drift_window_sigma:
            if self.dev_seconds <= 0.0:
                self.dev_started_at = ts
                self.dev_direction = 1 if z > 0 else -1
            self.dev_seconds += max(0.0, dt)
            self.dev_samples += 1
            self.quiet_samples = 0
        else:
            self.quiet_samples += 1
            if self.quiet_samples >= self.cfg.quiet_reset_samples:
                self._clear_deviation()

    def _clear_deviation(self) -> None:
        self.ph_sum = 0.0
        self.ph_min = 0.0
        self.ph_neg_sum = 0.0
        self.ph_max = 0.0
        self.ph_alarm = False
        self.dev_seconds = 0.0
        self.dev_samples = 0
        self.dev_started_at = None
        self.dev_direction = 0
        self.quiet_samples = 0

    def z(self, value: Any, at_ts: Optional[float] = None, *, circadian: Optional[bool] = None) -> Optional[float]:
        """Robust z-score of ``value`` against the learned personal norm."""
        try:
            v = float(value)
        except (TypeError, ValueError):
            return None
        if not math.isfinite(v) or not self.norm_ready:
            return None
        use_hour = self.circadian_enabled if circadian is None else circadian
        if use_hour and at_ts is not None:
            return float((v - self.expected(at_ts)) / self.scale)
        if self.scale <= 0:
            return None
        return float((v - self.median) / self.scale)

    def range_personal(self) -> Optional[Tuple[float, float]]:
        """Expected range derived from the personal norm (not from raw samples)."""
        if not self.norm_ready:
            return None
        return (self.median - 1.645 * self.scale, self.median + 1.645 * self.scale)

    def range_population(self) -> Tuple[float, float]:
        mean, sd = POPULATION_PRIOR.get(self.metric, (0.0, 1.0))
        return (mean - 1.645 * sd, mean + 1.645 * sd)

    def hour_range(self, ts: float) -> Optional[Tuple[float, float]]:
        if not self.norm_ready or not self.circadian_enabled:
            return None
        stat = self.hour_stats.get(time.localtime(ts).tm_hour)
        if not stat or stat["n"] < 3:
            return None
        centre = self.expected(ts)
        return (centre - 1.645 * stat["scale"], centre + 1.645 * stat["scale"])

    # -- adaptation ------------------------------------------------------
    def maybe_absorb(self, ts: float, worn_since_last: float, cfg: AdaptiveConfig) -> Optional[Dict[str, Any]]:
        """Move the personal norm toward a shift that has earned it.

        Authority comes from accumulated time under deviation (``dev_seconds``), the
        Page-Hinkley trigger and a minimum effect size. A short excursion never reaches
        the persistence gate, so it can never be absorbed.

        Returns a summary dict on the sample where a drift is confirmed, else None.
        """
        confirmed: Optional[Dict[str, Any]] = None
        if not self.norm_ready or not self.tail:
            return None

        if not self.absorbing:
            gap = self._recent_median() - self.expected(ts)
            earned = (
                self.dev_seconds >= cfg.drift_min_persistence_s
                and self.dev_samples >= cfg.drift_min_samples
                and self.ph_alarm
                and abs(gap) >= cfg.drift_min_shift_sigma * self.scale
            )
            if not earned:
                return None
            self.absorbing = True
            self.absorb_from = self.median
            confirmed = {
                "metric": self.metric,
                "shift": float(gap),
                "persistence_s": float(self.dev_seconds),
                "direction": int(self.dev_direction or (1 if gap > 0 else -1)),
            }

        # Rate limited absorption: at most max_adapt_sigma_per_hour * scale per worn hour,
        # so a confirmed shift becomes the new normal over hours rather than instantly.
        if self.absorb_from is not None and cfg.max_absorb_sigma > 0 and \
                abs(self.median - self.absorb_from) >= cfg.max_absorb_sigma * self.scale:
            # Safety stop: one absorption can never move the norm more than
            # max_absorb_sigma. Something is wrong with the signal, so stop adapting.
            self.absorbing = False
            self.last_absorb_ts = ts
            self._clear_deviation()
            return confirmed
        gap = self._recent_median() - self.expected(ts)
        if abs(gap) <= cfg.settle_sigma * self.scale:
            self.absorbing = False
            self.last_absorb_ts = ts
            self._clear_deviation()
            return confirmed
        budget = cfg.max_adapt_sigma_per_hour * self.scale * max(worn_since_last, 0.0) / 3600.0
        step = math.copysign(min(abs(gap), budget), gap)
        self.median += step
        self.absorbed_total += step
        recent_scale = self._recent_scale()
        if recent_scale > 0:
            # The wearer's variability is re-estimated alongside the centre, slowly.
            self.scale += 0.05 * (recent_scale - self.scale)
        self._clear_deviation()
        return confirmed

    def _recent_scale(self) -> float:
        if len(self.tail) < 8:
            return self.scale
        arr = np.fromiter(self.tail, dtype=float, count=len(self.tail))
        med = float(np.median(arr))
        mad = float(np.median(np.abs(arr - med)))
        return max(1.4826 * mad, self.cfg.min_scale_fraction * abs(self.median or med), 1e-9)

    def gentle_track(self, ts: float, worn_since_last: float, cfg: AdaptiveConfig) -> Optional[float]:
        """Slow, rate-limited pull of the norm toward the recent regime.

        This keeps a *gradual* drift (season, medication, recovery) from becoming a
        permanent false alarm. It is frozen while any deviation window is open, so an
        acute event is never learned away.
        """
        if self.absorbing or self.dev_seconds > 0.0 or not self.norm_ready or not self.tail:
            return None
        # Only adapt while the whole recent window has been normal. Without this, the
        # tail right after an excursion still carries the excursion, and gradual
        # tracking would slowly copy it into the norm - exactly what must not happen.
        if self.quiet_samples < len(self.tail):
            return None
        current = self.tail[-1]
        r = self.residual(current, ts)
        if abs(r) > self.cfg.freeze_z * self.scale:
            self.frozen_samples += 1
            return None
        gap = self._recent_median() - self.expected(ts)
        if abs(gap) < 0.5 * self.scale:
            return None
        budget = cfg.max_adapt_sigma_per_hour * self.scale * max(worn_since_last, 0.0) / 3600.0
        step = math.copysign(min(abs(gap), budget), gap)
        self.median += step
        self.absorbed_total += step
        return float(step)

    def _recent_median(self) -> float:
        """Median of the recent regime (bounded tail window, raw units)."""
        if not self.tail:
            return self.median or 0.0
        return float(np.median(np.asarray(self.tail, dtype=float)))

    # -- persistence -----------------------------------------------------
    def to_dict(self) -> Dict[str, Any]:
        p05_p95 = self.range_personal()
        return {
            "n": int(self.n),
            "rejected": int(self.rejected),
            "quality": round(self.quality, 4),
            "first_ts": self.first_ts,
            "last_ts": self.last_ts,
            "days": self.days[-90:],
            "median": self.median,
            "scale": self.scale,
            "norm_set_at": self.norm_set_at,
            "norm_set_n": int(self.norm_set_n),
            "circadian_enabled": bool(self.circadian_enabled),
            "desc_median": self.desc_median,
            "desc_mad": self.desc_mad,
            "desc_scale": self.desc_scale,
            "desc_p25": self.desc_p25,
            "desc_p75": self.desc_p75,
            "p05": None if p05_p95 is None else p05_p95[0],
            "p95": None if p05_p95 is None else p05_p95[1],
            "ewma_mean": self.ewma_mean,
            "ewma_sd": math.sqrt(self.ewma_var) if self.ewma_var > 0 else 0.0,
            "absorbed_total": self.absorbed_total,
            "frozen_samples": int(self.frozen_samples),
            "reservoir": list(self.reservoir),
            "clean_reservoir": list(self.clean_reservoir),
            "tail": list(self.tail),
            "hour_buckets": {str(h): list(b) for h, b in enumerate(self.hour_buckets) if b},
        }

    @classmethod
    def from_dict(cls, metric: str, data: Dict[str, Any], cfg: AdaptiveConfig,
                  rng: random.Random) -> "MetricLearning":
        obj = cls(metric, cfg, rng)
        obj.n = int(data.get("n", 0))
        obj.rejected = int(data.get("rejected", 0))
        obj.quality_sum = float(data.get("quality", 0.0)) * obj.n
        obj.first_ts = data.get("first_ts")
        obj.last_ts = data.get("last_ts")
        obj.days = list(data.get("days") or [])
        obj._day_set = set(obj.days)
        obj.median = data.get("median")
        obj.scale = float(data.get("scale") or 0.0)
        obj.norm_set_at = data.get("norm_set_at")
        obj.norm_set_n = int(data.get("norm_set_n", 0))
        obj.circadian_enabled = bool(data.get("circadian_enabled", False))
        obj.desc_median = data.get("desc_median")
        obj.desc_mad = float(data.get("desc_mad") or 0.0)
        obj.desc_scale = float(data.get("desc_scale") or 0.0)
        obj.desc_p25 = data.get("desc_p25")
        obj.desc_p75 = data.get("desc_p75")
        obj.ewma_mean = data.get("ewma_mean")
        sd = float(data.get("ewma_sd") or 0.0)
        obj.ewma_var = sd * sd
        obj.absorbed_total = float(data.get("absorbed_total") or 0.0)
        obj.frozen_samples = int(data.get("frozen_samples") or 0)
        for value in data.get("reservoir") or []:
            obj.reservoir.append(float(value))
        for value in data.get("clean_reservoir") or []:
            obj.clean_reservoir.append(float(value))
        for value in data.get("tail") or []:
            obj.tail.append(float(value))
        for hour, values in (data.get("hour_buckets") or {}).items():
            try:
                idx = int(hour)
            except (TypeError, ValueError):
                continue
            if 0 <= idx < 24:
                for value in values:
                    obj.hour_buckets[idx].append(float(value))
        obj._refresh()
        return obj


# ---------------------------------------------------------------------------
# Supervised head (online logistic regression, prospective validation)
# ---------------------------------------------------------------------------
HEAD_FEATURES: Tuple[str, ...] = (
    "hr_z", "rmssd_z", "temp_z", "gsr_z", "activity_z", "hour_sin", "hour_cos",
)


@dataclass
class HeadStatus:
    status: str = "collecting"          # collecting | active | withheld
    n_train: int = 0
    n_pos: int = 0
    n_neg: int = 0
    n_prospective: int = 0
    prospective_logloss: Optional[float] = None
    baseline_logloss: Optional[float] = None
    prospective_wins: int = 0
    reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "n_train": int(self.n_train),
            "n_pos": int(self.n_pos),
            "n_neg": int(self.n_neg),
            "n_prospective": int(self.n_prospective),
            "prospective_logloss": self.prospective_logloss,
            "baseline_logloss": self.baseline_logloss,
            "prospective_wins": int(self.prospective_wins),
            "reason": self.reason,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HeadStatus":
        return cls(
            status=data.get("status", "collecting"),
            n_train=int(data.get("n_train", 0)),
            n_pos=int(data.get("n_pos", 0)),
            n_neg=int(data.get("n_neg", 0)),
            n_prospective=int(data.get("n_prospective", 0)),
            prospective_logloss=data.get("prospective_logloss"),
            baseline_logloss=data.get("baseline_logloss"),
            prospective_wins=int(data.get("prospective_wins", 0)),
            reason=data.get("reason", ""),
        )


class SupervisedHead:
    """Per-wearer logistic regression trained online on the wearer's own labels.

    Honesty rules baked in:
    * It never trains on a label before scoring it.  New labels form a *prospective*
      set that the model has not seen, which is the only way to make an accuracy-ish
      claim that is not self-congratulatory.
    * It activates only when it beats a base-rate predictor by ``head_margin`` on those
      unseen labels, and refuses (``withheld``) when it does not.
    * The numbers it reports are log-loss on a handful of labels - an engineering
      check, never a clinical performance claim.
    """

    def __init__(self, cfg: AdaptiveConfig):
        self.cfg = cfg
        self.w = np.zeros(len(HEAD_FEATURES), dtype=float)
        self.b = 0.0
        self.status = HeadStatus()
        self.rows: List[Tuple[np.ndarray, float]] = []
        self._next_retry = 0

    # -- training / scoring ---------------------------------------------
    def _sigmoid(self, z: float) -> float:
        if z >= 0:
            ez = math.exp(-z)
            return 1.0 / (1.0 + ez)
        ez = math.exp(z)
        return ez / (1.0 + ez)

    def predict(self, x: Sequence[float]) -> float:
        vec = np.asarray(x, dtype=float)
        return self._sigmoid(float(np.dot(self.w, vec) + self.b))

    def observe(self, x: Sequence[float], target: float) -> Optional[str]:
        """Score-then-learn. Returns a new head status string when it changes."""
        vec = np.asarray(x, dtype=float)
        if not np.all(np.isfinite(vec)):
            return None
        previous = self.status.status

        # 1. prospective scoring (before any training on this label)
        if self.status.n_train >= self.cfg.head_min_labels and \
                self.status.n_pos >= self.cfg.head_min_per_class and \
                self.status.n_neg >= self.cfg.head_min_per_class:
            p = min(max(self.predict(vec), 1e-9), 1 - 1e-9)
            ll = -math.log(p if target >= 0.5 else 1 - p)
            base = self._base_rate()
            base_p = base if target >= 0.5 else 1 - base
            base_ll = -math.log(min(max(base_p, 1e-9), 1 - 1e-9))
            n = self.status.n_prospective
            self.status.prospective_logloss = (
                ll if n == 0 else (self.status.prospective_logloss * n + ll) / (n + 1)
            )
            self.status.baseline_logloss = (
                base_ll if n == 0 else (self.status.baseline_logloss * n + base_ll) / (n + 1)
            )
            self.status.prospective_wins += 1 if ll < base_ll else 0
            self.status.n_prospective = n + 1
            self._reconsider()

        # 2. training update
        self.rows.append((vec, float(target)))
        if len(self.rows) > 4000:
            self.rows = self.rows[-4000:]
        self.status.n_train += 1
        if target >= 0.5:
            self.status.n_pos += 1
        else:
            self.status.n_neg += 1
        self._sgd(vec, float(target))
        self._replay()
        self._reconsider()
        return self.status.status if self.status.status != previous else None

    def _replay(self) -> None:
        """Experience replay: a few passes over bounded history per new label.

        A single online step per label learns far too slowly to be useful; replay keeps
        the head honest (it still only ever sees the wearer's own labels) and stable.
        Prospective scoring happens before any of this, so the reported numbers stay
        leak-free.
        """
        if len(self.rows) < 2 or self.cfg.head_replay_epochs <= 0:
            return
        rng = random.Random(10000 + self.status.n_train)
        batch = max(2, self.cfg.head_replay_batch)
        sample = self.rows if len(self.rows) <= batch else rng.sample(self.rows, batch)
        for _ in range(self.cfg.head_replay_epochs):
            for vec, target in sample:
                self._sgd(vec, target)

    def _base_rate(self) -> float:
        n = max(1, self.status.n_pos + self.status.n_neg)
        return min(max((self.status.n_pos + 1.0) / (n + 2.0), 1e-6), 1 - 1e-6)

    def _sgd(self, vec: np.ndarray, target: float) -> None:
        p = self.predict(vec)
        # balanced weights so a rare symptom day is not drowned by everyday rows
        prevalence = self._base_rate()
        weight = 0.5 / prevalence if target >= 0.5 else 0.5 / (1 - prevalence)
        lr = self.cfg.head_lr / (1.0 + self.status.n_train / self.cfg.head_lr_decay)
        grad = (p - target) * weight
        self.w -= lr * (grad * vec + self.cfg.head_l2 * self.w)
        self.b -= lr * grad

    def _can_score(self) -> bool:
        return (
            self.status.n_train >= self.cfg.head_min_labels
            and self.status.n_pos >= self.cfg.head_min_per_class
            and self.status.n_neg >= self.cfg.head_min_per_class
        )

    def _reconsider(self) -> None:
        if not self._can_score():
            self.status.status = "collecting"
            self.status.reason = (
                f"needs {self.cfg.head_min_labels} labelled events "
                f"(>= {self.cfg.head_min_per_class} per class); has "
                f"{self.status.n_train} ({self.status.n_pos} event / {self.status.n_neg} normal)"
            )
            return
        if self.status.n_prospective < self.cfg.head_min_prospective:
            self.status.status = "collecting"
            self.status.reason = (
                f"scoring on unseen labels: {self.status.n_prospective}"
                f"/{self.cfg.head_min_prospective}"
            )
            return
        ll = self.status.prospective_logloss
        base_ll = self.status.baseline_logloss
        win_rate = self.status.prospective_wins / max(1, self.status.n_prospective)
        gain = 0.0 if (ll is None or base_ll in (None, 0)) else 1.0 - (ll / base_ll)
        better = (
            ll is not None
            and base_ll not in (None, 0)
            and gain >= self.cfg.head_margin
            and win_rate >= self.cfg.head_min_win_rate
        )
        if better:
            self.status.status = "active"
            self.status.reason = (
                f"beats the base-rate predictor on {self.status.n_prospective} unseen labels: "
                f"log-loss {ll:.3f} vs {base_ll:.3f} ({gain:.0%} better), "
                f"better on {win_rate:.0%} of them - engineering check only, not clinical validation"
            )
        else:
            self.status.status = "withheld"
            self.status.reason = (
                f"after {self.status.n_prospective} unseen labels it does not clear the bar "
                f"(log-loss {ll:.3f} vs base rate {base_ll:.3f}, {gain:.0%} better, "
                f"better on {win_rate:.0%} - needs {self.cfg.head_margin:.0%} and "
                f"{self.cfg.head_min_win_rate:.0%}); the unsupervised layers stay active and no "
                "claim is made"
            )

    # -- persistence -----------------------------------------------------
    def to_dict(self) -> Dict[str, Any]:
        return {
            "w": [float(v) for v in self.w],
            "b": float(self.b),
            "status": self.status.to_dict(),
            "rows": [[float(v) for v in vec] + [float(y)] for vec, y in self.rows[-500:]],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], cfg: AdaptiveConfig) -> "SupervisedHead":
        obj = cls(cfg)
        w = data.get("w") or []
        if len(w) == len(HEAD_FEATURES):
            obj.w = np.asarray(w, dtype=float)
        obj.b = float(data.get("b", 0.0))
        obj.status = HeadStatus.from_dict(data.get("status") or {})
        for row in data.get("rows") or []:
            if len(row) == len(HEAD_FEATURES) + 1:
                obj.rows.append((np.asarray(row[:-1], dtype=float), float(row[-1])))
        return obj


# ---------------------------------------------------------------------------
# The self-learning wearable model
# ---------------------------------------------------------------------------
class AdaptiveWearableModel:
    """One wearer's continually-learning model.

    Typical use::

        model = AdaptiveWearableModel("patient-001")
        for fv in stream:
            model.observe(fv)                  # learns, promotes, absorbs drift
        model.status()                         # JSON-able snapshot for the UI

    The instance is scoped to a single wearer.  Its state is written to
    ``data/adaptive/<patient_id>/wearable_model.json`` so that taking the device off,
    closing the app or restarting the machine resumes at the tier that was already
    earned instead of starting again from the population prior.
    """

    def __init__(
        self,
        patient_id: str = "default",
        *,
        config: Optional[AdaptiveConfig] = None,
        path: Optional[Path | str] = None,
        rng_seed: Optional[int] = None,
        autoload: bool = True,
    ):
        self.patient_id = str(patient_id)
        self.cfg = config or AdaptiveConfig()
        self.path = Path(path) if path else DATA_DIR / "adaptive" / _safe_id(self.patient_id) / "wearable_model.json"
        seed = rng_seed if rng_seed is not None else abs(hash(self.patient_id)) % (2 ** 31)
        self._rng = random.Random(seed)

        self.tier = "population"
        self.model_version = "1.0.0"
        self.upgrade_count = 0
        self.worn_seconds = 0.0
        self.observations = 0
        self.quality_reported = 0
        self.created_at = time.time()
        self.updated_at = self.created_at
        self.last_ts: Optional[float] = None
        self.events: List[LearningEvent] = []
        self._quality_window: Deque[float] = deque(maxlen=self.cfg.rollback_window)
        self._recent_z: Deque[Tuple[float, np.ndarray]] = deque(maxlen=4096)
        self._cooldown_until = 0.0
        self._samples_since_save = 0

        self.metrics: Dict[str, MetricLearning] = {
            metric: MetricLearning(metric, self.cfg, self._rng) for metric in LEARNING_METRICS
        }
        self.head = SupervisedHead(self.cfg)
        if autoload:
            self.load()

    # ------------------------------------------------------------------
    # Learning
    # ------------------------------------------------------------------
    def observe(
        self,
        features: Any,
        *,
        quality: Optional[float] = None,
        now: Optional[float] = None,
    ) -> List[LearningEvent]:
        """Feed one feature row (a ``FeatureVector`` or any mapping) to the model.

        Returns the list of audit events produced by this sample (usually empty).
        """
        ts = self._timestamp(features, now)
        q = _quality(features, quality)
        self.quality_reported += 1 if q is not None else 0
        qc = 1.0 if q is None else max(0.0, min(1.0, float(q)))

        gap = (ts - self.last_ts) if self.last_ts is not None else 0.0
        worn_delta = gap if 0.0 < gap <= self.cfg.max_worn_gap_s else 0.0
        self.worn_seconds += worn_delta
        self.last_ts = ts
        self.observations += 1
        self.updated_at = ts
        self._quality_window.append(qc)

        produced: List[LearningEvent] = []
        for metric, learner in self.metrics.items():
            value = _get(features, metric)
            if value is None:
                continue
            accepted = learner.add(value, ts, qc, worn_delta)
            if not accepted:
                continue
            if self._tier_index() >= TIER_INDEX["adaptive"]:
                confirmed = learner.maybe_absorb(ts, worn_delta, self.cfg)
                if confirmed:
                    produced.append(self._drift_event(confirmed, ts))
                elif not learner.absorbing:
                    learner.gentle_track(ts, worn_delta, self.cfg)

        self._recent_z.append((ts, self._z_vector(features, ts)))

        evaluation = self._evaluate_tier(ts)
        if evaluation:
            produced.append(evaluation)

        self._samples_since_save += 1
        if self._samples_since_save >= max(1, self.cfg.save_every):
            self._samples_since_save = 0
            try:
                self.save(quiet=True)
            except OSError:
                pass
        return produced

    def _timestamp(self, features: Any, now: Optional[float]) -> float:
        """Use the sample's own clock when it carries one, else wall time."""
        if now is not None:
            return float(now)
        ts = _as_float(_get(features, "timestamp_s"))
        if ts is None:
            ts = _as_float(_get(features, "timestamp"))
        return ts if ts and ts > 0 else time.time()

    # ------------------------------------------------------------------
    # Tier machinery
    # ------------------------------------------------------------------
    def _tier_index(self) -> int:
        return TIER_INDEX.get(self.tier, 0)

    def gate_report(self) -> Dict[str, Any]:
        """Structured answer to "what is met, what is missing, what unlocks next"."""
        idx = self._tier_index()
        next_tier = TIERS[idx + 1] if idx + 1 < len(TIERS) else None
        requirements: List[Dict[str, Any]] = []
        ready = False
        if next_tier == "personalized":
            qualifying = self._qualifying_metrics("personal")
            requirements = [
                _req("worn_seconds", "Wear the device", self.worn_seconds,
                     self.cfg.personal_min_worn_s, "s"),
                _req("samples", "Usable samples", self._min_metric_samples(),
                     self.cfg.personal_min_metric_samples, "count"),
                _req("metrics", "Signals with a personal norm", qualifying,
                     self.cfg.personal_min_metrics, "count"),
                # Recent quality, not a lifetime average: a wearer whose sensor just
                # started failing must not be promoted on the strength of last week.
                _req("quality", "Recent signal quality",
                     self._recent_quality() if self._recent_quality() is not None
                     else self._mean_quality(),
                     self.cfg.personal_min_quality, "ratio"),
            ]
            ready = all(r["met"] for r in requirements)
        elif next_tier == "circadian":
            requirements = [
                _req("worn_seconds", "Wear the device", self.worn_seconds,
                     self.cfg.circadian_min_worn_s, "s"),
                _req("days", "Days covered", self._days_covered(), self.cfg.circadian_min_days, "count"),
                _req("hours", "Hours of day covered", self._covered_hours(),
                     self.cfg.circadian_min_buckets, "count"),
            ]
            ready = all(r["met"] for r in requirements)
        elif next_tier == "adaptive":
            requirements = [
                _req("worn_seconds", "Wear the device", self.worn_seconds,
                     self.cfg.adaptive_min_worn_s, "s"),
                _req("days", "Days covered", self._days_covered(), self.cfg.adaptive_min_days, "count"),
                _req("history", "Signals with enough history",
                     self._qualifying_metrics("adaptive"), self.cfg.adaptive_min_metrics, "count"),
            ]
            ready = all(r["met"] for r in requirements)
        return {
            "current_tier": self.tier,
            "next_tier": next_tier,
            "ready": bool(ready),
            "requirements": requirements,
        }

    def _evaluate_tier(self, ts: float) -> Optional[LearningEvent]:
        """Promote when the gates pass; demote when the evidence is lost."""
        # 1. rollback first: sustained poor quality invalidates what we claimed
        if self._tier_index() > 0:
            q = self._recent_quality()
            if len(self._quality_window) >= min(20, self.cfg.rollback_window) and \
                    q is not None and q < self.cfg.quality_floor and ts >= self._cooldown_until:
                self._cooldown_until = ts + self.cfg.rollback_cooldown_s
                return self._demote(ts, f"signal quality fell to {q:.2f} over the last "
                                        f"{len(self._quality_window)} samples", "evidence_lost")

        # 2. promote if the next rung is earned
        report = self.gate_report()
        if report["next_tier"] and report["ready"] and ts >= self._cooldown_until:
            return self._promote(report["next_tier"], ts, report["requirements"])
        return None

    def _apply_tier_to_metrics(self) -> None:
        enabled = self._tier_index() >= TIER_INDEX["circadian"]
        for learner in self.metrics.values():
            learner.set_circadian(enabled)

    def _promote(self, tier: str, ts: float, requirements: Sequence[Dict[str, Any]]) -> LearningEvent:
        from_tier = self.tier
        self.tier = tier
        major, minor, patch = (int(p) for p in self.model_version.split("."))
        minor += 1
        patch = 0
        self.model_version = f"{major}.{minor}.{patch}"
        self.upgrade_count += 1
        self._apply_tier_to_metrics()
        event = LearningEvent(
            kind="promotion",
            at=ts,
            from_tier=from_tier,
            to_tier=tier,
            detail=(
                f"model upgraded to {tier} (v{self.model_version}) after "
                f"{self.worn_seconds / 3600.0:.1f} h of wearing and {self.observations} samples"
            ),
            evidence={
                "model_version": self.model_version,
                "worn_hours": round(self.worn_seconds / 3600.0, 3),
                "observations": self.observations,
                "requirements": requirements,
            },
        )
        self._record(event)
        return event

    def _demote(self, ts: float, reason: str, kind: str) -> LearningEvent:
        from_tier = self.tier
        target = TIERS[max(0, self._tier_index() - 1)]
        self.tier = target
        self._apply_tier_to_metrics()
        major, minor, patch = (int(p) for p in self.model_version.split("."))
        self.model_version = f"{major}.{minor + 1}.0"
        event = LearningEvent(
            kind="rollback",
            at=ts,
            from_tier=from_tier,
            to_tier=target,
            detail=f"model rolled back to {target}: {reason}",
            evidence={"model_version": self.model_version, "reason_kind": kind},
        )
        self._record(event)
        return event

    def _record(self, event: LearningEvent) -> None:
        self.events.append(event)
        if len(self.events) > self.cfg.history_limit:
            self.events = self.events[-self.cfg.history_limit:]

    def _drift_event(self, info: Dict[str, Any], ts: float) -> LearningEvent:
        metric = str(info["metric"])
        shift = float(info["shift"])
        hours = float(info["persistence_s"]) / 3600.0
        major, minor, patch = (int(p) for p in self.model_version.split("."))
        self.model_version = f"{major}.{minor}.{patch + 1}"
        event = LearningEvent(
            kind="drift",
            at=ts,
            metric=metric,
            detail=(
                f"persistent shift in {metric_label(metric)} ({shift:+.2f} "
                f"{METRIC_UNITS.get(metric, '')}) held for {hours:.1f} h of good signal; "
                "absorbing it into the personal norm at the rate limit"
            ),
            evidence={
                "shift": round(shift, 4),
                "persistence_h": round(hours, 3),
                "direction": info.get("direction"),
                "model_version": self.model_version,
            },
        )
        self._record(event)
        return event

    # ------------------------------------------------------------------
    # Reading the model
    # ------------------------------------------------------------------
    def z(self, metric: str, value: Any, *, at_ts: Optional[float] = None) -> Optional[float]:
        """Tier-aware z-score. ``None`` while the model has only population priors."""
        idx = self._tier_index()
        if idx < TIER_INDEX["personalized"]:
            return None
        learner = self.metrics.get(metric)
        if learner is None:
            return None
        return learner.z(value, at_ts, circadian=idx >= TIER_INDEX["circadian"])

    def personalised(self, metric: str) -> bool:
        return self._tier_index() >= TIER_INDEX["personalized"] and metric in self.metrics

    def evaluate(self, metric: str, value: Any, *, at_ts: Optional[float] = None) -> Dict[str, Any]:
        """Deviation report for one metric, honest about which basis was used."""
        learner = self.metrics.get(metric)
        value_f = _as_float(value)
        if learner is None or value_f is None:
            return {"metric": metric, "current": None, "basis": "none", "z": None,
                    "level": "no_data", "range": None, "provenance": "UNKNOWN"}
        if self._tier_index() < TIER_INDEX["personalized"] or learner.median is None:
            lo, hi = learner.range_population()
            return {
                "metric": metric,
                "current": value_f,
                "basis": "population",
                "z": None,
                "level": "population_only",
                "range": [lo, hi],
                "provenance": "POPULATION_PRIOR",
                "note": "no personal baseline yet - this is a population reference, not yours",
            }
        basis = "personal"
        z = learner.z(value_f, at_ts, circadian=False)
        rng = learner.range_personal()
        hour_range = learner.hour_range(at_ts) if at_ts is not None else None
        if hour_range is not None:
            hour_z = learner.z(value_f, at_ts)
            if hour_z is not None:
                basis = "hour_of_day"
                z = hour_z
                rng = hour_range
        level = "normal"
        if z is not None:
            az = abs(z)
            if az >= 3.5:
                level = "significant_deviation"
            elif az >= 2.5:
                level = "moderate_deviation"
            elif az >= 1.5:
                level = "mild_deviation"
        return {
            "metric": metric,
            "current": value_f,
            "basis": basis,
            "z": None if z is None else round(float(z), 3),
            "level": level,
            "range": None if rng is None else [round(float(rng[0]), 3), round(float(rng[1]), 3)],
            "provenance": "PERSONAL_MEASURED" if basis == "personal" else "MODEL_INFERRED",
        }

    def status(self) -> Dict[str, Any]:
        """JSON-able snapshot for the UIs, the report and the audit trail."""
        report = self.gate_report()
        hours = self.worn_seconds / 3600.0
        return {
            "schema": SCHEMA,
            "patient_id": self.patient_id,
            "tier": self.tier,
            "tier_index": self._tier_index(),
            "tier_headline": TIER_HEADLINES.get(self.tier, ""),
            "model_version": self.model_version,
            "upgrades": self.upgrade_count,
            "worn_hours": round(hours, 3),
            "worn_seconds": round(self.worn_seconds, 2),
            "observations": self.observations,
            "days_covered": self._days_covered(),
            "mean_quality": round(self._mean_quality(), 3),
            "confidence": self._confidence(),
            "next_tier": report["next_tier"],
            "ready_to_upgrade": report["ready"],
            "requirements": report["requirements"],
            "metrics": {
                metric: {
                    "n": learner.n,
                    "rejected": learner.rejected,
                    "rejected_hint": (
                        f"{learner.rejected} out-of-range samples were refused, not learned from"
                        if learner.rejected else None
                    ),
                    "median": None if learner.median is None else round(learner.median, 3),
                    "scale": round(learner.scale, 3) if learner.scale else None,
                    "quality": round(learner.quality, 3),
                    "hours_covered": sorted(learner.hour_coverage.keys()),
                    "absorbed_total": round(learner.absorbed_total, 4),
                    "frozen_samples": learner.frozen_samples,
                }
                for metric, learner in self.metrics.items()
            },
            "head": dict(
                self.head.status.to_dict(),
                reason=self.head.status.reason or "no wearer-labelled events recorded yet",
            ),
            "head_features": list(HEAD_FEATURES),
            "events": [e.to_dict() for e in self.events[-25:]],
            "confidence_note": "engineering confidence from coverage, quality and wearing time - not clinical validity",
            "disclaimer": DISCLAIMER,
        }

    def summary_line(self) -> str:
        """One-line status for a label or a log."""
        return (
            f"{self.tier.upper()} v{self.model_version} - {self.worn_seconds / 3600.0:.1f} h worn, "
            f"{self.observations} samples"
        )

    def requirement_lines(self, limit: int = 4) -> List[str]:
        lines: List[str] = []
        for req in self.gate_report()["requirements"][:limit]:
            mark = "OK" if req["met"] else ".."
            lines.append(f"[{mark}] {req['label']}: {_fmt_value(req['current'], req['unit'])}"
                         f" / {_fmt_value(req['target'], req['unit'])}")
        return lines

    # ------------------------------------------------------------------
    # Labels (wearer-reported events)
    # ------------------------------------------------------------------
    def record_label(self, label: str, *, target: bool = True, at: Optional[float] = None,
                     features: Any = None) -> bool:
        """Attach a wearer-reported event to the model.

        ``target=True`` marks an event ("this was a symptom day"), ``False`` a normal
        day.  Returns False when there is no nearby feature row to learn from - the
        label is then not counted, rather than silently matched to the wrong moment.
        """
        ts = float(at) if at is not None else (self.last_ts if self.last_ts else time.time())
        vec: Optional[np.ndarray] = None
        if features is not None:
            vec = self._z_vector(features, ts)
        else:
            for row_ts, row_vec in reversed(self._recent_z):
                if abs(row_ts - ts) <= self.cfg.label_match_s:
                    vec = row_vec
                    break
        if vec is None or not np.all(np.isfinite(vec)):
            return False
        changed = self.head.observe(vec, 1.0 if target else 0.0)
        if changed:
            self._record(LearningEvent(
                kind="capability",
                at=ts,
                detail=f"supervised head {self.head.status.status}: {self.head.status.reason}",
                evidence=self.head.status.to_dict(),
            ))
            self._samples_since_save = 0
            try:
                self.save(quiet=True)
            except OSError:
                pass
        return True

    def _z_vector(self, features: Any, ts: float) -> np.ndarray:
        def z_of(metric: str) -> float:
            value = _as_float(_get(features, metric))
            if value is None:
                return 0.0
            z = self.z(metric, value, at_ts=ts)
            if z is None:
                mean, sd = POPULATION_PRIOR.get(metric, (0.0, 1.0))
                z = (value - mean) / sd
            return float(max(-8.0, min(8.0, z)))

        hour = time.localtime(ts).tm_hour + time.localtime(ts).tm_min / 60.0
        angle = 2.0 * math.pi * hour / 24.0
        return np.asarray([
            z_of("hr_bpm"),
            z_of("rmssd_ms"),
            z_of("skin_temp_c"),
            z_of("gsr_tonic"),
            z_of("activity_level"),
            math.sin(angle),
            math.cos(angle),
        ], dtype=float)

    # ------------------------------------------------------------------
    # Aggregates used by the gates
    # ------------------------------------------------------------------
    def _min_metric_samples(self) -> int:
        return min((l.n for l in self.metrics.values()), default=0)

    def _mean_quality(self) -> float:
        learners = [l for l in self.metrics.values() if l.n]
        if not learners:
            return 0.0
        return float(np.mean([l.quality for l in learners]))

    def _recent_quality(self) -> Optional[float]:
        if not self._quality_window:
            return None
        return float(np.mean(np.asarray(self._quality_window, dtype=float)))

    def _days_covered(self) -> int:
        return max((l.days_covered for l in self.metrics.values()), default=0)

    def _covered_hours(self) -> int:
        need = self.cfg.circadian_bucket_min
        counts: Dict[int, int] = {}
        for learner in self.metrics.values():
            for hour, n in learner.hour_coverage.items():
                if n >= need:
                    counts[hour] = counts.get(hour, 0) + 1
        return sum(1 for hour, metrics in counts.items() if metrics >= min(3, len(LEARNING_METRICS)))

    def _qualifying_metrics(self, kind: str) -> int:
        if kind == "personal":
            return sum(1 for l in self.metrics.values() if l.norm_ready)
        need = self.cfg.adaptive_min_metric_samples
        return sum(1 for l in self.metrics.values() if l.n >= need)

    def _confidence(self) -> float:
        """Engineering confidence in the learned norm (coverage x quality x time)."""
        hours = self.worn_seconds / 3600.0
        coverage = min(1.0, self._min_metric_samples() / max(1.0, float(self.cfg.adaptive_min_metric_samples)))
        quality = self._mean_quality() if self.observations else 0.0
        time_term = min(1.0, hours / max(1.0, self.cfg.adaptive_min_worn_s / 3600.0))
        value = 0.45 * time_term + 0.35 * coverage + 0.20 * quality
        return round(float(max(0.0, min(1.0, value))), 3)

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema": SCHEMA,
            "patient_id": self.patient_id,
            "tier": self.tier,
            "model_version": self.model_version,
            "upgrade_count": self.upgrade_count,
            "worn_seconds": self.worn_seconds,
            "observations": self.observations,
            "quality_reported": self.quality_reported,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_ts": self.last_ts,
            "cooldown_until": self._cooldown_until,
            "metrics": {m: l.to_dict() for m, l in self.metrics.items()},
            "head": self.head.to_dict(),
            "events": [e.to_dict() for e in self.events],
            "disclaimer": DISCLAIMER,
        }

    def save(self, *, quiet: bool = False) -> Path:
        payload = self.to_dict()
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(payload, indent=2, allow_nan=False), encoding="utf-8")
            os.replace(tmp, self.path)
        except OSError:
            if not quiet:
                raise
        return self.path

    def load(self) -> bool:
        """Resume a previously earned tier from disk. Returns True when state was loaded."""
        try:
            if not self.path.exists():
                return False
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return False
        if data.get("schema") != SCHEMA:
            return False
        try:
            self.tier = data.get("tier", "population")
            if self.tier not in TIER_INDEX:
                self.tier = "population"
            self.model_version = str(data.get("model_version", "1.0.0"))
            self.upgrade_count = int(data.get("upgrade_count", 0))
            self.worn_seconds = float(data.get("worn_seconds", 0.0))
            self.observations = int(data.get("observations", 0))
            self.quality_reported = int(data.get("quality_reported", 0))
            self.created_at = float(data.get("created_at", time.time()))
            self.updated_at = float(data.get("updated_at", self.created_at))
            self.last_ts = data.get("last_ts")
            self._cooldown_until = float(data.get("cooldown_until", 0.0))
            for metric, metric_data in (data.get("metrics") or {}).items():
                if metric in self.metrics:
                    self.metrics[metric] = MetricLearning.from_dict(
                        metric, metric_data, self.cfg, self._rng
                    )
            self.head = SupervisedHead.from_dict(data.get("head") or {}, self.cfg)
            self.events = [LearningEvent.from_dict(e) for e in (data.get("events") or [])]
            self._apply_tier_to_metrics()
        except (TypeError, ValueError):
            return False
        return True

    @classmethod
    def load_or_create(cls, patient_id: str, **kwargs: Any) -> "AdaptiveWearableModel":
        return cls(patient_id, **kwargs)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _safe_id(patient_id: str) -> str:
    keep = [c if (c.isalnum() or c in "-_.") else "_" for c in str(patient_id)]
    cleaned = "".join(keep).strip("._") or "default"
    return cleaned[:64]


def _get(row: Any, key: str) -> Any:
    """Read ``key`` from an object attribute or a mapping."""
    if row is None:
        return None
    if isinstance(row, dict):
        return row.get(key)
    return getattr(row, key, None)


def _as_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def _req(rid: str, label: str, current: float, target: float, unit: str) -> Dict[str, Any]:
    return {
        "id": rid,
        "label": label,
        "current": float(current),
        "target": float(target),
        "unit": unit,
        "met": bool(current >= target),
        "remaining": float(max(0.0, target - current)),
    }


def _fmt_value(value: float, unit: str) -> str:
    if unit == "s":
        if value >= 3600:
            return f"{value / 3600.0:.1f} h"
        if value >= 60:
            return f"{value / 60.0:.0f} min"
        return f"{value:.0f} s"
    if unit == "ratio":
        return f"{value:.2f}"
    return f"{value:.0f}"


def _quality(row: Any, explicit: Optional[float]) -> Optional[float]:
    if explicit is not None:
        return explicit
    value = _get(row, "signal_quality")
    return _as_float(value)


__all__ = [
    "AdaptiveConfig",
    "AdaptiveWearableModel",
    "HEAD_FEATURES",
    "LEARNING_METRICS",
    "METRIC_BOUNDS",
    "METRIC_UNITS",
    "POPULATION_PRIOR",
    "TIERS",
    "TIER_HEADLINES",
    "TIER_INDEX",
    "LearningEvent",
    "MetricLearning",
    "SupervisedHead",
    "metric_label",
]
