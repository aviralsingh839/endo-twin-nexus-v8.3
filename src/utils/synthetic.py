"""Realistic Longitudinal Synthetic Data - V8.3.

Generates synthetic subjects with:
- individual baselines
- age, BMI, activity patterns, resting HR, HRV, sleep timing/duration,
  temperature trends, GSR patterns, menstrual-cycle info, clinical variables,
  gradual changes, temporary disturbances, sensor noise, missing data,
  motion artifacts, recovery periods

Each synthetic subject has a timeline: DAY1 -> DAY30 -> DAY60 -> DAY90
rather than independent random measurements.

Also implements 6 required scenarios:
1. Stable baseline - LOW CHANGE SIGNAL
2. Gradual deviation - EARLY CHANGE SIGNAL
3. Persistent deviation - PERSISTENT MULTIMODAL SIGNAL
4. Temporary disturbance - TEMPORARY EVENT, not disease signal
5. Sensor failure - LOW SENSOR CONFIDENCE
6. Recovery - RECOVERY TREND

Clearly labelled SYNTHETIC.
"""
from __future__ import annotations

import math
import time
import json
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from pathlib import Path

import numpy as np

from src.config import UserProfile, DATA_LABEL_SYNTHETIC
from src.data_models import FeatureVector


@dataclass
class SyntheticSubjectProfile:
    subject_id: str
    age_years: float
    bmi: float
    sex: str = "female"
    # Baselines
    resting_hr_baseline: float = 68.0
    hrv_baseline: float = 45.0
    skin_temp_baseline: float = 32.5
    gsr_baseline: float = 450.0
    activity_baseline: float = 35.0
    sleep_duration_baseline: float = 7.5
    sleep_timing_baseline: float = 23.0  # hour
    # Cycle
    usual_cycle_length: int = 28
    cycle_irregular: bool = False
    # Clinical
    systolic_bp: float = 115.0
    diastolic_bp: float = 75.0
    glucose_mg_dl: float = 90.0
    # Variability
    hr_variability: float = 3.0
    hrv_variability: float = 5.0
    temp_variability: float = 0.15
    # Data quality
    base_quality: float = 0.85
    label: str = DATA_LABEL_SYNTHETIC


def _circadian_modulation(hour: float, amplitude: float = 1.0) -> float:
    """Circadian rhythm: low at night, high during day."""
    # HR: higher during day
    return amplitude * math.sin(2 * math.pi * (hour - 6) / 24.0)


def generate_subject_timeline(
    profile: SyntheticSubjectProfile,
    days: int = 90,
    samples_per_day: int = 24,
    seed: int = 42,
    scenario: str = "stable",
    scenario_params: Optional[Dict] = None,
) -> List[FeatureVector]:
    """
    Generate longitudinal timeline for one subject.

    scenario:
    - stable: physiology within normal personal variation -> LOW CHANGE SIGNAL
    - gradual: gradual deviation -> EARLY CHANGE SIGNAL
    - persistent: persistent multimodal -> PERSISTENT MULTIMODAL SIGNAL
    - temporary: brief disturbance then return -> TEMPORARY EVENT
    - sensor_failure: one sensor stops -> LOW SENSOR CONFIDENCE
    - recovery: abnormal then returns -> RECOVERY TREND
    """
    rng = np.random.default_rng(seed)
    scenario_params = scenario_params or {}
    vectors: List[FeatureVector] = []

    start_ts = time.time() - days * 86400

    # Scenario-specific modifiers
    gradual_hr_slope = scenario_params.get("hr_slope_per_day", 0.15)  # bpm per day
    gradual_hrv_slope = scenario_params.get("hrv_slope_per_day", -0.3)
    persistent_start_day = scenario_params.get("persistent_start_day", 20)
    temporary_start_day = scenario_params.get("temporary_start_day", 30)
    temporary_duration_days = scenario_params.get("temporary_duration_days", 3)
    sensor_failure_day = scenario_params.get("sensor_failure_day", 40)
    sensor_failure_channel = scenario_params.get("sensor_failure_channel", "hr")
    recovery_start_day = scenario_params.get("recovery_start_day", 10)
    recovery_duration = scenario_params.get("recovery_duration_days", 30)

    for day in range(days):
        day_progress = day / max(days - 1, 1)
        for sample_idx in range(samples_per_day):
            hour = sample_idx * (24.0 / samples_per_day)
            ts = start_ts + day * 86400 + hour * 3600

            # Base values with circadian
            circadian_hr = _circadian_modulation(hour, 5.0)
            is_night = hour >= 22 or hour <= 6

            # Scenario adjustments
            hr_adjust = 0.0
            hrv_adjust = 0.0
            temp_adjust = 0.0
            activity_adjust = 0.0
            gsr_adjust = 0.0
            sleep_adjust = 0.0
            quality = profile.base_quality + rng.normal(0, 0.05)
            artifact = False

            if scenario == "stable":
                # Small random variation around baseline
                hr_adjust = rng.normal(0, profile.hr_variability * 0.5)
                hrv_adjust = rng.normal(0, profile.hrv_variability * 0.5)

            elif scenario == "gradual":
                # Gradual deviation over time
                hr_adjust = day * gradual_hr_slope + rng.normal(0, 1.0)
                hrv_adjust = day * gradual_hrv_slope + rng.normal(0, 1.5)
                temp_adjust = day * 0.01 + rng.normal(0, 0.05)
                activity_adjust = -day * 0.2 + rng.normal(0, 2.0)

            elif scenario == "persistent":
                if day >= persistent_start_day:
                    days_persistent = day - persistent_start_day
                    hr_adjust = 8.0 + days_persistent * 0.1 + rng.normal(0, 1.0)
                    hrv_adjust = -12.0 - days_persistent * 0.1 + rng.normal(0, 1.5)
                    temp_adjust = 0.4 + rng.normal(0, 0.05)
                    activity_adjust = -10.0 + rng.normal(0, 2.0)
                    gsr_adjust = 80.0 + rng.normal(0, 10)
                    sleep_adjust = -0.8 + rng.normal(0, 0.2)
                else:
                    hr_adjust = rng.normal(0, 1.0)
                    hrv_adjust = rng.normal(0, 1.5)

            elif scenario == "temporary":
                if temporary_start_day <= day < temporary_start_day + temporary_duration_days:
                    # Brief disturbance
                    hr_adjust = 15.0 + rng.normal(0, 2.0)
                    hrv_adjust = -15.0 + rng.normal(0, 2.0)
                    gsr_adjust = 120.0 + rng.normal(0, 15)
                    quality = max(0.3, quality - 0.1)
                else:
                    hr_adjust = rng.normal(0, 1.0)
                    hrv_adjust = rng.normal(0, 1.5)

            elif scenario == "sensor_failure":
                if day >= sensor_failure_day:
                    if sensor_failure_channel == "hr":
                        # HR missing or flatline
                        if rng.random() < 0.7:
                            hr_adjust = None  # missing
                            quality = 0.2
                        else:
                            hr_adjust = 0.0  # flatline
                            artifact = True
                    elif sensor_failure_channel == "temp":
                        temp_adjust = None
                        quality = 0.3
                else:
                    hr_adjust = rng.normal(0, 1.0)

            elif scenario == "recovery":
                if day < recovery_start_day:
                    hr_adjust = rng.normal(0, 1.0)
                    hrv_adjust = rng.normal(0, 1.5)
                elif day < recovery_start_day + recovery_duration:
                    # Gradually returning to baseline
                    days_in_recovery = day - recovery_start_day
                    recovery_progress = days_in_recovery / recovery_duration
                    # Start from abnormal, move to normal
                    initial_hr_offset = 12.0
                    initial_hrv_offset = -15.0
                    hr_adjust = initial_hr_offset * (1 - recovery_progress) + rng.normal(0, 1.0)
                    hrv_adjust = initial_hrv_offset * (1 - recovery_progress) + rng.normal(0, 1.5)
                else:
                    hr_adjust = rng.normal(0, 1.0)
                    hrv_adjust = rng.normal(0, 1.5)

            # Build feature vector
            # Handle missing HR
            if hr_adjust is None:
                hr = None
                resting_hr = None
            else:
                hr_base = profile.resting_hr_baseline + (0 if is_night else 8) + circadian_hr
                hr = hr_base + hr_adjust + rng.normal(0, 1.5)
                resting_hr = profile.resting_hr_baseline + hr_adjust + rng.normal(0, 1.0)

            # HRV
            if hrv_adjust is None:
                hrv = None
            else:
                hrv = max(10.0, profile.hrv_baseline + hrv_adjust + rng.normal(0, 2.0))

            # Temperature
            if temp_adjust is None:
                temp = None
            else:
                temp_circadian = 0.5 * math.sin(2 * math.pi * (hour - 4) / 24.0)
                temp = profile.skin_temp_baseline + temp_circadian + temp_adjust + rng.normal(0, profile.temp_variability)

            # Activity
            if is_night:
                activity_base = 5.0 + rng.normal(0, 2)
            else:
                activity_base = profile.activity_baseline + 15 * math.exp(-((hour - 17) ** 2) / 8) + rng.normal(0, 3)
            activity = max(0.0, activity_base + activity_adjust)

            # GSR
            gsr = profile.gsr_baseline + gsr_adjust + rng.normal(0, 20) + (80 if 12 <= hour <= 14 else 0)

            # Sleep
            sleep_duration = profile.sleep_duration_baseline + sleep_adjust + rng.normal(0, 0.3)
            sleep_regularity = 85.0 + rng.normal(0, 5) if scenario == "stable" else 60.0 + rng.normal(0, 10)
            if scenario == "persistent" and day >= persistent_start_day:
                sleep_regularity = 45.0 + rng.normal(0, 8)

            # Stress
            stress = 25.0 + (20 if 12 <= hour <= 14 else 0) + rng.normal(0, 5)
            if scenario in ("gradual", "persistent"):
                if day >= (persistent_start_day if scenario == "persistent" else 0):
                    stress += day * 0.15 if scenario == "gradual" else 15.0

            # Circadian
            circadian_stability = 75.0 + rng.normal(0, 5) if scenario == "stable" else 55.0 + rng.normal(0, 8)
            circadian_disruption = 100.0 - circadian_stability

            # Motion
            motion = rng.normal(0.05 if is_night else 0.25, 0.05)

            # Sensor noise, missing data, artifacts
            # Random missing
            if rng.random() < 0.02:  # 2% missing
                if rng.random() < 0.5:
                    temp = None
                else:
                    gsr = None

            # Motion artifact
            if rng.random() < 0.03:
                motion = rng.uniform(1.0, 2.5)
                if hr is not None:
                    hr += rng.normal(0, 8)
                quality = max(0.1, quality - 0.3)

            fv = FeatureVector(
                timestamp_s=ts,
                hr_bpm=float(hr) if hr is not None else None,
                resting_hr_bpm=float(resting_hr) if resting_hr is not None else None,
                rmssd_ms=float(hrv) if hrv is not None else None,
                sdnn_ms=float(hrv * 1.2) if hrv is not None else None,
                skin_temp_c=float(temp) if temp is not None else None,
                gsr_tonic=float(gsr) if gsr is not None else None,
                motion_index=float(motion),
                activity_level=float(activity),
                sleep_duration_h=float(max(0, sleep_duration)),
                sleep_regularity=float(max(0, min(100, sleep_regularity))),
                sleep_probability=float(80 if is_night else 15),
                sleep_status="sleep" if is_night and rng.random() < 0.7 else "wake",
                circadian_stability_index=float(max(0, min(100, circadian_stability))),
                circadian_disruption=float(max(0, min(100, circadian_disruption))),
                stress_index=float(max(0, min(100, stress))),
                acute_stress=float(max(0, min(100, stress))),
                chronic_stress=float(max(0, min(100, stress * 0.7))),
                autonomic_imbalance=float(max(0, min(100, 60 - (hrv or 40) + rng.normal(0, 3)))),
                signal_quality=float(max(0.0, min(1.0, quality))),
                baseline_completeness=1.0 if day > 3 else day / 3.0,
                quality_per_feature={
                    "hr": float(max(0, min(1, quality + rng.normal(0, 0.05)))),
                    "hrv": float(max(0, min(1, quality + rng.normal(0, 0.05)))),
                    "temp": float(max(0, min(1, quality + rng.normal(0, 0.05)))) if temp is not None else 0.0,
                    "gsr": float(max(0, min(1, quality + rng.normal(0, 0.05)))) if gsr is not None else 0.0,
                },
                anomaly_score=float(rng.uniform(0, 10)),
            )

            # Label synthetic
            fv.shared_features = {"synthetic": True, "scenario": scenario, "subject_id": profile.subject_id, "label": DATA_LABEL_SYNTHETIC}

            vectors.append(fv)

    return vectors


def generate_synthetic_cohort(
    n_subjects: int = 20,
    days: int = 90,
    samples_per_day: int = 24,
    output_dir: Optional[Path] = None,
    seed: int = 42,
) -> Dict[str, List[FeatureVector]]:
    """Generate a cohort of synthetic subjects with diverse baselines."""
    rng = np.random.default_rng(seed)
    cohort = {}

    for i in range(n_subjects):
        subject_id = f"SYNTH_{i:03d}"
        # Diverse baselines
        profile = SyntheticSubjectProfile(
            subject_id=subject_id,
            age_years=float(rng.integers(16, 45)),
            bmi=float(rng.uniform(18.5, 32.0)),
            resting_hr_baseline=float(rng.uniform(60, 80)),
            hrv_baseline=float(rng.uniform(30, 60)),
            skin_temp_baseline=float(rng.uniform(31.5, 33.5)),
            gsr_baseline=float(rng.uniform(400, 600)),
            activity_baseline=float(rng.uniform(20, 50)),
            sleep_duration_baseline=float(rng.uniform(6.5, 8.5)),
            usual_cycle_length=int(rng.integers(21, 35)),
            cycle_irregular=bool(rng.random() < 0.2),
            base_quality=float(rng.uniform(0.7, 0.95)),
        )
        # Mix scenarios
        scenarios = ["stable", "gradual", "persistent", "temporary", "recovery"]
        scenario = rng.choice(scenarios, p=[0.4, 0.2, 0.15, 0.15, 0.1])
        vectors = generate_subject_timeline(
            profile, days=days, samples_per_day=samples_per_day,
            seed=seed + i, scenario=scenario
        )
        cohort[subject_id] = vectors

    # Optionally save
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        for sid, vecs in cohort.items():
            # Save as JSON lines with metadata
            data = []
            for fv in vecs:
                data.append({
                    "timestamp_s": fv.timestamp_s,
                    "hr_bpm": fv.hr_bpm,
                    "resting_hr_bpm": fv.resting_hr_bpm,
                    "rmssd_ms": fv.rmssd_ms,
                    "skin_temp_c": fv.skin_temp_c,
                    "gsr_tonic": fv.gsr_tonic,
                    "activity_level": fv.activity_level,
                    "sleep_duration_h": fv.sleep_duration_h,
                    "sleep_regularity": fv.sleep_regularity,
                    "circadian_stability_index": fv.circadian_stability_index,
                    "stress_index": fv.stress_index,
                    "signal_quality": fv.signal_quality,
                    "scenario": fv.shared_features.get("scenario"),
                    "label": DATA_LABEL_SYNTHETIC,
                })
            out_file = output_dir / f"{sid}.json"
            out_file.write_text(json.dumps({"subject_id": sid, "label": DATA_LABEL_SYNTHETIC, "data": data}, indent=2))

    return cohort


def generate_scenario_dataset(output_dir: Path, seed: int = 42) -> Dict[str, Dict]:
    """Generate the 6 required longitudinal scenarios."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    base_profile = SyntheticSubjectProfile(
        subject_id="BASE",
        age_years=22,
        bmi=23.5,
        resting_hr_baseline=68.0,
        hrv_baseline=48.0,
        skin_temp_baseline=32.5,
        gsr_baseline=450.0,
        activity_baseline=35.0,
        sleep_duration_baseline=7.5,
    )

    scenarios = {
        "scenario_1_stable": {
            "scenario": "stable",
            "expected": "LOW CHANGE SIGNAL",
            "description": "Physiology stays within normal personal variation.",
        },
        "scenario_2_gradual": {
            "scenario": "gradual",
            "params": {"hr_slope_per_day": 0.12, "hrv_slope_per_day": -0.25},
            "expected": "EARLY CHANGE SIGNAL",
            "description": "A parameter slowly moves away from baseline.",
        },
        "scenario_3_persistent": {
            "scenario": "persistent",
            "params": {"persistent_start_day": 20},
            "expected": "PERSISTENT MULTIMODAL SIGNAL",
            "description": "Multiple related signals remain abnormal for extended period.",
        },
        "scenario_4_temporary": {
            "scenario": "temporary",
            "params": {"temporary_start_day": 30, "temporary_duration_days": 3},
            "expected": "TEMPORARY EVENT, not disease signal",
            "description": "Signals change briefly and return to baseline.",
        },
        "scenario_5_sensor_failure": {
            "scenario": "sensor_failure",
            "params": {"sensor_failure_day": 25, "sensor_failure_channel": "hr"},
            "expected": "LOW SENSOR CONFIDENCE",
            "description": "One sensor stops producing valid data. Must not be interpreted as physiological abnormality.",
        },
        "scenario_6_recovery": {
            "scenario": "recovery",
            "params": {"recovery_start_day": 10, "recovery_duration_days": 25},
            "expected": "RECOVERY TREND",
            "description": "Previously abnormal pattern gradually returns toward baseline.",
        },
    }

    results = {}
    for name, cfg in scenarios.items():
        profile = SyntheticSubjectProfile(
            subject_id=name,
            age_years=base_profile.age_years,
            bmi=base_profile.bmi,
            resting_hr_baseline=base_profile.resting_hr_baseline,
            hrv_baseline=base_profile.hrv_baseline,
            skin_temp_baseline=base_profile.skin_temp_baseline,
            gsr_baseline=base_profile.gsr_baseline,
            activity_baseline=base_profile.activity_baseline,
            sleep_duration_baseline=base_profile.sleep_duration_baseline,
        )
        vectors = generate_subject_timeline(
            profile,
            days=60,
            samples_per_day=24,
            seed=seed + hash(name) % 1000,
            scenario=cfg["scenario"],
            scenario_params=cfg.get("params"),
        )
        # Save
        data = []
        for fv in vectors:
            data.append({
                "timestamp_s": fv.timestamp_s,
                "hr_bpm": fv.hr_bpm,
                "rmssd_ms": fv.rmssd_ms,
                "skin_temp_c": fv.skin_temp_c,
                "activity_level": fv.activity_level,
                "sleep_regularity": fv.sleep_regularity,
                "circadian_stability_index": fv.circadian_stability_index,
                "stress_index": fv.stress_index,
                "signal_quality": fv.signal_quality,
                "label": DATA_LABEL_SYNTHETIC,
            })
        out_file = output_dir / f"{name}.json"
        payload = {
            "scenario": name,
            "type": cfg["scenario"],
            "expected_result": cfg["expected"],
            "description": cfg["description"],
            "label": DATA_LABEL_SYNTHETIC,
            "subject_profile": {
                "age": profile.age_years,
                "bmi": profile.bmi,
                "resting_hr_baseline": profile.resting_hr_baseline,
            },
            "data": data,
        }
        out_file.write_text(json.dumps(payload, indent=2))
        results[name] = payload

    # Write README
    readme = output_dir / "README.md"
    readme.write_text(
        "# Synthetic Longitudinal Scenarios - CHRONO-TWIN NEXUS V8.3\n\n"
        "All data in this folder is SYNTHETIC - clearly labelled.\n"
        "Never presented as real clinical data.\n\n"
        "## Scenarios\n\n"
        + "\n".join([f"### {k}\n- Type: {v['scenario']}\n- Expected: {v['expected']}\n- Description: {v['description']}\n" for k, v in scenarios.items()])
        + "\n## Usage\n\n"
        "Each file contains 60 days of 24 samples/day with realistic:\n"
        "- individual baselines\n- circadian modulation\n- sensor noise, missing data, motion artifacts\n- scenario-specific deviations\n"
    )
    return results


# Backward compatibility for old import path
def generate_week(*args, **kwargs):
    """Legacy function - redirects to new timeline generator."""
    profile = SyntheticSubjectProfile(
        subject_id="LEGACY_SYNTH",
        age_years=17,
        bmi=23,
        resting_hr_baseline=68,
        hrv_baseline=48,
    )
    vectors = generate_subject_timeline(profile, days=7, samples_per_day=24, scenario="stable")
    return vectors
