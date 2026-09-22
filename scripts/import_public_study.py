#!/usr/bin/env python3
"""Import an Android public-study CSV into the desktop ENDO-TWIN feature pipeline.

Usage:
  python scripts/import_public_study.py study.csv --participant PUBLIC-XXXX

The CSV is the user-selected export from the Patient Android app. No network
access is performed. The imported study is labelled REAL/public_test and is
kept separate from demo/synthetic sessions.
"""
from __future__ import annotations

import argparse
import csv
import time
from pathlib import Path

from src.config import DATA_DIR
from src.serial_io.packet_parser import PacketParser, PacketParseError
from src.data_models import FeatureVector
from src.core.personal_baseline import PersonalBaselineEngine
from src.core.feature_extraction import RealtimeFeatureExtractor
from src.utils.history_store import HistoryStore


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("csv_file", type=Path)
    ap.add_argument("--participant", required=True)
    ap.add_argument("--db", type=Path, default=None)
    args = ap.parse_args()

    store = HistoryStore(args.db)
    session_id = store.start_session(
        source="public_test",
        note="Imported from Android three-day public wearable study",
        participant_id=args.participant,
    )

    baseline = PersonalBaselineEngine()
    extractor = RealtimeFeatureExtractor(baseline_engine=baseline)
    parser = PacketParser(require_crc=True)

    good = bad = features = 0
    last_feature_ts = 0.0

    with args.csv_file.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            raw = row.get("payload", "").strip()
            try:
                sample = parser.parse(raw)
                sample.timestamp_s = float(row.get("received_at_ms", "0")) / 1000.0
                extractor.add_sample(sample)
                good += 1
            except (PacketParseError, ValueError, TypeError):
                bad += 1
                continue

            # Feature logging every ~10 seconds keeps the imported DB compact.
            if sample.timestamp_s - last_feature_ts >= 10.0:
                try:
                    fv = extractor.compute()
                    store.log_feature(
                        session_id,
                        {
                            "ts": fv.timestamp_s,
                            "hr": fv.hr_bpm,
                            "rmssd": fv.rmssd_ms,
                            "spo2": fv.spo2_pct,
                            "skin_temp": fv.skin_temp_c,
                            "gsr": fv.gsr_tonic,
                            "motion": fv.motion_index,
                            "activity": fv.activity_level,
                            "stress": fv.stress_index,
                            "sleep_prob": fv.sleep_probability,
                            "circadian": fv.circadian_stability_index,
                            "signal_quality": fv.signal_quality,
                        },
                        extra_json='{"provenance":"REAL","study":"PUBLIC_3_DAY","imported":true}',
                    )
                    features += 1
                    last_feature_ts = sample.timestamp_s
                except Exception as exc:
                    store.log_error(session_id, "feature_import", str(exc))

    store.end_session(session_id, sample_count=good)
    print("Imported public study")
    print(f"Participant: {args.participant}")
    print(f"Valid CP2 packets: {good}")
    print(f"Rejected packets: {bad}")
    print(f"Feature rows: {features}")
    print(f"Database: {store.path}")
    print("Next: open the desktop app and review the 3-Day Public Test tab, then capture/review the personal baseline.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
