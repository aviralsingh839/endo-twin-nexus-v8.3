"""Simulated wearer stream - SIMULATED data for demos and tests only.

This is the counterpart to ``src/utils/synthetic.py``: where that module models a
90-day clinical timeline, this one models a single person actually *wearing* the
device - a wear schedule with the device off at night, a personal offset from the
population prior, circadian shape, noise, and episodes such as a persistent shift or
a short excursion.

Every row produced here is SIMULATED. The result is used to exercise the continual
learning layer (``src/core/adaptive_learning.py``) and must never be presented as a
measurement from a real person.
"""
from __future__ import annotations

import math
import random
import time
from dataclasses import dataclass, field
from typing import Dict, Iterator, List, Optional, Tuple

from src.config import DATA_LABEL_SIMULATED
from src.data_models import FeatureVector

# Population-shaped baseline the simulator starts from. Individual wearers differ by
# the offsets in WearerProfile.
BASE = {
    "hr_bpm": 70.0,
    "resting_hr_bpm": 62.0,
    "rmssd_ms": 42.0,
    "skin_temp_c": 32.6,
    "gsr_tonic": 450.0,
    "activity_level": 0.10,
}

# Per-sample noise (sd) at the default sampling cadence.
NOISE = {
    "hr_bpm": 2.0,
    "resting_hr_bpm": 1.2,
    "rmssd_ms": 3.0,
    "skin_temp_c": 0.12,
    "gsr_tonic": 25.0,
    "activity_level": 0.02,
}


@dataclass
class WearerProfile:
    """Who is wearing the device, expressed as a deviation from the population prior."""

    patient_id: str = "sim-001"
    hr_offset: float = 0.0
    resting_hr_offset: float = 0.0
    rmssd_offset: float = 0.0
    temp_offset: float = 0.0
    gsr_offset: float = 0.0
    activity_base: float = 0.10
    noise_scale: float = 1.0
    seed: int = 7

    @classmethod
    def shifted(cls, **kwargs) -> "WearerProfile":
        return cls(**kwargs)


@dataclass
class WearEpisode:
    """Something that happens to the wearer while the device is on.

    ``deltas`` are in each metric's own units. ``transient=True`` marks an excursion
    that ends by itself (an event); ``transient=False`` marks a new steady state
    (a genuine change the model is allowed to absorb).
    """

    start_h: float
    duration_h: float
    deltas: Dict[str, float]
    transient: bool = False
    quality: float = 1.0
    label: Optional[str] = None
    symptom: bool = True
    label_delay_h: float = 1.0  # emit the label once the episode is in full effect


class SyntheticWearer:
    """Deterministic simulated stream of ``FeatureVector`` rows."""

    def __init__(
        self,
        profile: Optional[WearerProfile] = None,
        *,
        start_ts: Optional[float] = None,
        sample_interval_s: float = 60.0,
        wear_start_hour: Optional[float] = 7.0,
        wear_end_hour: Optional[float] = 22.0,
        episodes: Optional[List[WearEpisode]] = None,
    ):
        self.profile = profile or WearerProfile()
        self.start_ts = float(start_ts if start_ts is not None else time.time())
        # Anchor the simulated clock at midnight of the start day so that "hour" is
        # predictable in tests regardless of when the suite runs.
        day = time.localtime(self.start_ts)
        midnight = time.mktime((day.tm_year, day.tm_mon, day.tm_mday, 0, 0, 0, 0, 0, -1))
        self.start_ts = midnight + 60.0
        self.sample_interval_s = float(sample_interval_s)
        self.wear_start_hour = wear_start_hour
        self.wear_end_hour = wear_end_hour
        self.episodes = list(episodes or [])
        self._rng = random.Random(self.profile.seed)
        self._labels: List[Tuple[float, bool, str]] = []

    # -- helpers ---------------------------------------------------------
    def _episode_at(self, hour_of_wear: float) -> Optional[WearEpisode]:
        for episode in self.episodes:
            if episode.start_h <= hour_of_wear < episode.start_h + episode.duration_h:
                return episode
        return None

    def _worn(self, dt: time.struct_time) -> bool:
        if self.wear_start_hour is None or self.wear_end_hour is None:
            return True
        hour = dt.tm_hour + dt.tm_min / 60.0
        return self.wear_start_hour <= hour < self.wear_end_hour

    def _row(self, ts: float, hour_of_wear: float) -> Optional[FeatureVector]:
        dt = time.localtime(ts)
        if not self._worn(dt):
            return None
        episode = self._episode_at(hour_of_wear)
        deltas = dict(episode.deltas) if episode else {}
        quality = episode.quality if episode else 1.0

        # Circadian shape: HR and temperature peak late afternoon, HRV is higher at night.
        hr_phase = math.sin(2 * math.pi * (dt.tm_hour + dt.tm_min / 60.0 - 16.0) / 24.0)
        temp_phase = math.sin(2 * math.pi * (dt.tm_hour + dt.tm_min / 60.0 - 18.0) / 24.0)
        hrv_phase = -math.sin(2 * math.pi * (dt.tm_hour + dt.tm_min / 60.0 - 16.0) / 24.0)

        p = self.profile
        scale = max(0.0, p.noise_scale)

        def noisy(metric: str, base: float) -> float:
            return base + self._rng.gauss(0.0, NOISE[metric] * scale)

        hr = noisy("hr_bpm", BASE["hr_bpm"] + p.hr_offset + 4.0 * hr_phase + deltas.get("hr_bpm", 0.0))
        resting = noisy(
            "resting_hr_bpm",
            BASE["resting_hr_bpm"] + p.resting_hr_offset + 1.5 * hr_phase + deltas.get("resting_hr_bpm", 0.0),
        )
        rmssd = noisy(
            "rmssd_ms",
            BASE["rmssd_ms"] + p.rmssd_offset + 4.0 * hrv_phase + deltas.get("rmssd_ms", 0.0),
        )
        temp = noisy(
            "skin_temp_c",
            BASE["skin_temp_c"] + p.temp_offset + 0.25 * temp_phase + deltas.get("skin_temp_c", 0.0),
        )
        gsr = noisy(
            "gsr_tonic",
            BASE["gsr_tonic"] + p.gsr_offset + deltas.get("gsr_tonic", 0.0),
        )
        activity = max(
            0.0,
            min(1.0, p.activity_base + deltas.get("activity_level", 0.0)
                + self._rng.gauss(0.0, NOISE["activity_level"] * scale)),
        )

        return FeatureVector(
            timestamp_s=ts,
            hr_bpm=round(hr, 2),
            resting_hr_bpm=round(resting, 2),
            rmssd_ms=round(max(5.0, rmssd), 2),
            skin_temp_c=round(temp, 3),
            gsr_tonic=round(max(0.0, gsr), 2),
            activity_level=round(activity, 4),
            signal_quality=max(0.0, min(1.0, quality)),
        )

    # -- public API ------------------------------------------------------
    def stream(self, days: float) -> Iterator[FeatureVector]:
        """Yield simulated rows for ``days`` days of wall-clock time."""
        total_s = float(days) * 86400.0
        elapsed = 0.0
        self._labels = []
        labelled: set = set()
        while elapsed < total_s:
            ts = self.start_ts + elapsed
            hour_of_wear = elapsed / 3600.0
            row = self._row(ts, hour_of_wear)
            if row is not None:
                episode = self._episode_at(hour_of_wear)
                if (
                    episode is not None
                    and episode.label
                    and id(episode) not in labelled
                    and hour_of_wear >= episode.start_h + min(episode.label_delay_h, episode.duration_h)
                ):
                    labelled.add(id(episode))
                    self._labels.append((ts, bool(episode.symptom), episode.label))
                yield row
            elapsed += self.sample_interval_s

    def labels(self) -> List[Tuple[float, bool, str]]:
        """Labels generated by labelled episodes during the last :meth:`stream` call."""
        return list(self._labels)


__all__ = ["BASE", "NOISE", "SyntheticWearer", "WearEpisode", "WearerProfile"]
