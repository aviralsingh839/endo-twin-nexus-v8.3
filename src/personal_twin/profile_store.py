"""Shared local, patient-scoped Personal Twin registry.

Schema v2:
- people[participant_id].profile
- people[participant_id].learning
- active_participant_id
The old single-profile schema is migrated automatically on read.
No cloud/network synchronization is performed.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from src.config import DATA_DIR

STATE_PATH = DATA_DIR / "personal_twin_state.json"
EVENTS_PATH = DATA_DIR / "personal_twin_events.jsonl"


def _empty_learning() -> dict[str, Any]:
    return {
        "version": "adaptive-personal-twin-v1",
        "samples": 0,
        "quality_weighted_samples": 0.0,
        "metrics": {},
        "hourly_profiles": {},
        "updated_at": None,
    }


def _default_state() -> dict[str, Any]:
    return {
        "schema_version": 2,
        "active_participant_id": None,
        "people": {},
        "profile": {},
        "learning": _empty_learning(),
        "created_at": None,
        "updated_at": None,
    }


def _migrate(data: dict[str, Any]) -> dict[str, Any]:
    base = _default_state()
    if not isinstance(data, dict):
        return base

    people = data.get("people")
    if isinstance(people, dict):
        base["people"] = people

    legacy_profile = data.get("profile")
    legacy_learning = data.get("learning")
    if not base["people"] and isinstance(legacy_profile, dict) and legacy_profile.get("participant_id"):
        pid = str(legacy_profile["participant_id"])
        base["people"][pid] = {
            "profile": dict(legacy_profile),
            "learning": dict(legacy_learning) if isinstance(legacy_learning, dict) else _empty_learning(),
        }

    active = data.get("active_participant_id")
    if active and str(active) in base["people"]:
        base["active_participant_id"] = str(active)
    elif base["people"]:
        base["active_participant_id"] = str(next(iter(base["people"])))
    elif isinstance(legacy_profile, dict) and legacy_profile.get("participant_id"):
        base["active_participant_id"] = str(legacy_profile["participant_id"])

    base["created_at"] = data.get("created_at")
    base["updated_at"] = data.get("updated_at")
    base["schema_version"] = 2
    _ensure_person_shape(base)
    _sync_aliases(base)
    return base


def _ensure_person_shape(state: dict[str, Any]) -> None:
    people = state.setdefault("people", {})
    for pid, record in list(people.items()):
        if not isinstance(record, dict):
            record = {}
            people[pid] = record
        profile = record.setdefault("profile", {})
        if not isinstance(profile, dict):
            record["profile"] = {}
        record.setdefault("learning", _empty_learning())
        if not isinstance(record["learning"], dict):
            record["learning"] = _empty_learning()


def _sync_aliases(state: dict[str, Any]) -> None:
    """Expose active profile/learning at top level for compatibility."""
    _ensure_person_shape(state)
    pid = state.get("active_participant_id")
    record = state["people"].get(str(pid)) if pid else None
    if record:
        state["profile"] = record["profile"]
        state["learning"] = record["learning"]
    else:
        state["profile"] = {}
        state["learning"] = _empty_learning()


def load_state() -> dict[str, Any]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not STATE_PATH.exists():
        return _default_state()
    try:
        data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        state = _migrate(data)
        return state
    except Exception:
        return _default_state()


def list_profiles() -> list[dict[str, Any]]:
    state = load_state()
    active = state.get("active_participant_id")
    out = []
    for pid, record in state.get("people", {}).items():
        p = dict(record.get("profile", {}))
        p.setdefault("participant_id", pid)
        p["_active"] = str(pid) == str(active)
        out.append(p)
    return sorted(out, key=lambda p: (not p.get("_active", False), str(p.get("alias") or p.get("participant_id", "")).lower()))


def get_profile(participant_id: str | None = None) -> dict[str, Any]:
    state = load_state()
    pid = str(participant_id or state.get("active_participant_id") or "")
    record = state.get("people", {}).get(pid)
    return dict(record.get("profile", {})) if isinstance(record, dict) else {}


def get_learning(participant_id: str | None = None) -> dict[str, Any]:
    state = load_state()
    pid = str(participant_id or state.get("active_participant_id") or "")
    record = state.get("people", {}).get(pid)
    if isinstance(record, dict) and isinstance(record.get("learning"), dict):
        return dict(record["learning"])
    return _empty_learning()


def ensure_person(participant_id: str, profile: dict[str, Any] | None = None, make_active: bool = False) -> dict[str, Any]:
    state = load_state()
    pid = str(participant_id)
    record = state.setdefault("people", {}).setdefault(pid, {"profile": {}, "learning": _empty_learning()})
    record.setdefault("profile", {})
    record.setdefault("learning", _empty_learning())
    if profile:
        record["profile"].update(dict(profile))
    record["profile"].setdefault("participant_id", pid)
    if make_active or not state.get("active_participant_id"):
        state["active_participant_id"] = pid
    _sync_aliases(state)
    upsert_state(state)
    return state


def save_profile(profile: dict[str, Any], set_active: bool = True) -> dict[str, Any]:
    pid = str(profile.get("participant_id") or "")
    if not pid:
        raise ValueError("profile requires participant_id")
    state = load_state()
    record = state.setdefault("people", {}).setdefault(pid, {"profile": {}, "learning": _empty_learning()})
    record["profile"] = dict(profile)
    record["profile"]["participant_id"] = pid
    record.setdefault("learning", _empty_learning())
    if set_active:
        state["active_participant_id"] = pid
    _sync_aliases(state)
    upsert_state(state)
    return state


def select_participant(participant_id: str) -> dict[str, Any]:
    state = load_state()
    pid = str(participant_id)
    if pid not in state.get("people", {}):
        raise KeyError(f"Unknown participant: {pid}")
    state["active_participant_id"] = pid
    _sync_aliases(state)
    upsert_state(state)
    append_event({"kind": "participant_selected", "participant_id": pid})
    return state


def remove_profile(participant_id: str) -> None:
    state = load_state()
    pid = str(participant_id)
    state.get("people", {}).pop(pid, None)
    if state.get("active_participant_id") == pid:
        state["active_participant_id"] = next(iter(state.get("people", {})), None)
    _sync_aliases(state)
    upsert_state(state)
    append_event({"kind": "profile_removed", "participant_id": pid})


def replace_learning(participant_id: str, learning: dict[str, Any]) -> None:
    state = load_state()
    pid = str(participant_id)
    if pid not in state.get("people", {}):
        ensure_person(pid, make_active=False)
        state = load_state()
    state["people"][pid]["learning"] = dict(learning)
    if state.get("active_participant_id") == pid:
        _sync_aliases(state)
    upsert_state(state)


def upsert_state(state: dict[str, Any]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    state = _migrate(state)
    now = time.time()
    state["updated_at"] = now
    state["created_at"] = state.get("created_at") or now
    _sync_aliases(state)
    STATE_PATH.write_text(
        json.dumps(state, indent=2, sort_keys=True, ensure_ascii=False),
        encoding="utf-8",
    )


def append_event(event: dict[str, Any]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    payload = dict(event)
    payload.setdefault("participant_id", load_state().get("active_participant_id"))
    payload.setdefault("ts", time.time())
    with EVENTS_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")


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
