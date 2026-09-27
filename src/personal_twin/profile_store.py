"""Shared local profile and personal-twin state store.

All desktop surfaces use this single JSON state file so onboarding data and the
local adaptive model remain consistent between the unified, doctor and patient
workstations. No network sync is performed.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from src.config import DATA_DIR

STATE_PATH = DATA_DIR / "personal_twin_state.json"
EVENTS_PATH = DATA_DIR / "personal_twin_events.jsonl"


def _default_state() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "profile": {},
        "learning": {
            "version": "adaptive-personal-twin-v1",
            "samples": 0,
            "quality_weighted_samples": 0.0,
            "metrics": {},
            "hourly_profiles": {},
            "updated_at": None,
        },
        "created_at": None,
        "updated_at": None,
    }


def load_state() -> dict[str, Any]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not STATE_PATH.exists():
        return _default_state()
    try:
        data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        base = _default_state()
        if isinstance(data, dict):
            base.update(data)
            if not isinstance(base.get("profile"), dict):
                base["profile"] = {}
            if not isinstance(base.get("learning"), dict):
                base["learning"] = _default_state()["learning"]
            return base
    except Exception:
        pass
    return _default_state()


def save_profile(profile: dict[str, Any]) -> dict[str, Any]:
    state = load_state()
    now = time.time()
    state["profile"] = dict(profile)
    state["created_at"] = state.get("created_at") or now
    state["updated_at"] = now
    state["profile"]["saved_at"] = now
    STATE_PATH.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")
    return state


def append_event(event: dict[str, Any]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    payload = dict(event)
    payload.setdefault("ts", time.time())
    with EVENTS_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")


def upsert_state(state: dict[str, Any]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    now = time.time()
    state["updated_at"] = now
    state["created_at"] = state.get("created_at") or now
    STATE_PATH.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")


def profile_summary(profile: dict[str, Any] | None = None) -> str:
    p = profile if profile is not None else load_state().get("profile", {})
    parts = []
    for key, label, suffix in [
        ("age_years", "Age", "y"), ("height_cm", "Height", "cm"),
        ("weight_kg", "Weight", "kg"), ("bmi", "BMI", ""),
        ("sex", "Sex", ""), ("usual_cycle_length_days", "Cycle", "d"),
    ]:
        value = p.get(key)
        if value not in (None, ""):
            parts.append(f"{label} {value}{suffix}")
    return " • ".join(parts) if parts else "Profile not configured"
