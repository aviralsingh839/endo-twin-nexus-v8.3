"""Anonymous three-day public wearable study coordinator."""
from __future__ import annotations

import secrets
import time
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from src.utils.history_store import HistoryStore


@dataclass
class PublicStudy:
    study_id: str
    participant_id: str
    started_at: float
    planned_end_at: float
    session_id: int
    status: str = "ACTIVE"

    @property
    def elapsed_days(self) -> float:
        return max(0.0, (time.time() - self.started_at) / 86400.0)

    @property
    def complete(self) -> bool:
        return time.time() >= self.planned_end_at


class PublicStudyManager:
    """Keeps public-test identity de-identified and local."""

    def __init__(self, store: HistoryStore):
        self.store = store
        self.study: PublicStudy | None = None

    def start(self) -> PublicStudy:
        participant = "PUBLIC-" + secrets.token_hex(4).upper()
        study_id = "STUDY-" + secrets.token_hex(4).upper()
        now = time.time()
        session_id = self.store.start_session(
            source="public_test",
            note="Anonymous 3-day wearable study; local-only research prototype",
            participant_id=participant,
        )
        self.study = PublicStudy(study_id, participant, now, now + 3 * 86400, session_id)
        self.store.log_event(session_id, "public_study_started", study_id)
        return self.study

    def attach_latest(self) -> PublicStudy | None:
        import sqlite3
        conn = self.store._connect()
        try:
            row = conn.execute(
                "SELECT id, started_at, participant_id, ended_at FROM sessions "
                "WHERE source='public_test' ORDER BY started_at DESC LIMIT 1"
            ).fetchone()
        finally:
            conn.close()
        if not row or not row["participant_id"]:
            return None
        start = float(row["started_at"])
        end = float(row["ended_at"] or (start + 3 * 86400))
        self.study = PublicStudy(
            study_id=f"STUDY-SESSION-{row['id']}",
            participant_id=str(row["participant_id"]),
            started_at=start,
            planned_end_at=end,
            session_id=int(row["id"]),
            status="COMPLETE" if row["ended_at"] else "ACTIVE",
        )
        return self.study

    def record_feature(self, feature) -> None:
        if not self.study:
            return
        self.store.log_feature(
            self.study.session_id,
            {
                "ts": feature.timestamp_s,
                "hr": feature.hr_bpm,
                "rmssd": feature.rmssd_ms,
                "spo2": getattr(feature, "spo2", None),
                "skin_temp": feature.skin_temp_c,
                "gsr": feature.gsr_tonic,
                "motion": feature.motion_index,
                "activity": feature.activity_level,
                "stress": feature.stress_index,
                "sleep_prob": feature.sleep_probability,
                "circadian": feature.circadian_stability,
                "signal_quality": feature.signal_quality,
            },
            extra_json='{"provenance":"REAL","study":"PUBLIC_3_DAY"}',
        )

    def daily_summary(self) -> list[dict]:
        if not self.study:
            return []
        df = self.store.features_for_session(self.study.session_id)
        if df.empty:
            return []
        dt = pd.to_datetime(df["ts"], unit="s")
        df = df.assign(day=dt.dt.date)
        out = []
        for day, g in df.groupby("day"):
            out.append({
                "day": str(day),
                "samples": int(len(g)),
                "quality": float(g["signal_quality"].mean()) if g["signal_quality"].notna().any() else 0.0,
                "hr": float(g["hr"].median()) if g["hr"].notna().any() else None,
                "rmssd": float(g["rmssd"].median()) if g["rmssd"].notna().any() else None,
                "gsr": float(g["gsr"].median()) if g["gsr"].notna().any() else None,
                "activity": float(g["activity"].mean()) if g["activity"].notna().any() else None,
                "temp": float(g["skin_temp"].median()) if g["skin_temp"].notna().any() else None,
            })
        return out[-3:]

    def finish(self) -> None:
        if not self.study:
            return
        self.store.end_session(self.study.session_id)
        self.store.log_event(self.study.session_id, "public_study_finished", self.study.study_id)
        self.study.status = "COMPLETE"

    def export_csv(self, path: Path | str) -> int:
        if not self.study:
            return 0
        return self.store.export_features_csv(path, days=365, include_demo=False)
