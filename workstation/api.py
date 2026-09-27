#!/usr/bin/env python3
"""
ENDO-TWIN NEXUS — Unified Workstation data API.

Reads and writes the REAL local-first SQLite database used by the rest of the
platform (``data/chrono_twin_nexus_v8_3_plus.db``, 22 tables), so the web
workstation shows whatever is actually recorded on this machine:

* patients            -> patients + profiles + workstation_ext
* clinicians          -> providers (type='doctor')
* physiology          -> sensor_sessions + hrv_data / ppg_data /
                         temperature_data / gsr_data / motion_data
* symptoms / cycles   -> symptoms, cycles
* notes / reports     -> doctor_notes, reports
* imaging             -> ultrasound_records
* model output        -> model_results

Nothing is invented here. If a value was never measured the API returns
``null`` and the UI shows "—" instead of a number. Rows written by the
``--seed`` helper carry ``label='SYNTHETIC_DEMO'`` so demo material can always
be told apart from real recordings (and removed again with ``--clear``).

CLI
---
    python3 workstation/api.py --status     # what is in the database
    python3 workstation/api.py --seed       # write a labelled demo cohort
    python3 workstation/api.py --clear      # delete every SYNTHETIC_DEMO row
"""
from __future__ import annotations

import json
import math
import random
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = ROOT / "data" / "chrono_twin_nexus_v8_3_plus.db"
DEMO_LABEL = "SYNTHETIC_DEMO"

# fields the platform schema has no column for; kept in workstation_ext
EXT_FIELDS = (
    "gender", "city", "phone", "email", "height", "weight", "blood",
    "cycleLen", "cycleDay", "doctorId", "status", "cohort", "joined",
    "device", "battery", "adherence", "quality", "risk",
)


# --------------------------------------------------------------------------- #
#  helpers
# --------------------------------------------------------------------------- #
def _now() -> float:
    return time.time()


def _pid(body):
    """Accept patientId / patient / pid from the client."""
    return body.get("patientId") or body.get("patient") or body.get("pid") or body.get("id")


def _uid(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"


def _f(v) -> Optional[float]:
    try:
        if v is None or v == "":
            return None
        return float(v)
    except (TypeError, ValueError):
        return None


def _i(v) -> Optional[int]:
    f = _f(v)
    return None if f is None else int(round(f))


def _round(v, nd=1):
    return None if v is None else round(float(v), nd)


def _mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def _downsample(rows: List[float], n: int) -> List[float]:
    """Average-pool a series down to n points (keeps shape, bounds payload)."""
    rows = [r for r in rows if r is not None]
    if not rows:
        return []
    if len(rows) <= n:
        return [round(float(r), 3) for r in rows]
    step = len(rows) / n
    out = []
    for i in range(n):
        chunk = rows[int(i * step): max(int((i + 1) * step), int(i * step) + 1)]
        out.append(round(sum(chunk) / len(chunk), 3))
    return out


# --------------------------------------------------------------------------- #
#  API
# --------------------------------------------------------------------------- #
class WorkstationAPI:
    def __init__(self, db_path: Path | str | None = None):
        self.db_path = Path(db_path) if db_path else DEFAULT_DB
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.ensure_schema()

    # ----------------------------- plumbing -------------------------------- #
    def connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(str(self.db_path), timeout=10)
        con.row_factory = sqlite3.Row
        return con

    def ensure_schema(self) -> None:
        """Create the platform schema (via LocalDatabase when importable)."""
        fresh = not self.db_path.exists()
        try:  # preferred: the project's own schema definition
            import sys
            if str(ROOT) not in sys.path:
                sys.path.insert(0, str(ROOT))
            from database.database import LocalDatabase  # noqa: WPS433
            LocalDatabase(self.db_path)
        except Exception:  # pragma: no cover - fallback keeps the UI alive
            if fresh:
                with self.connect() as con:
                    con.executescript(_MINIMAL_SCHEMA)
        with self.connect() as con:
            con.execute(
                """CREATE TABLE IF NOT EXISTS workstation_ext (
                       entity_type TEXT NOT NULL,
                       entity_id   TEXT NOT NULL,
                       data_json   TEXT NOT NULL,
                       updated_at  REAL NOT NULL,
                       PRIMARY KEY (entity_type, entity_id))"""
            )

    def _ext(self, con, kind: str, eid: str) -> Dict[str, Any]:
        row = con.execute(
            "SELECT data_json FROM workstation_ext WHERE entity_type=? AND entity_id=?",
            (kind, eid),
        ).fetchone()
        if not row:
            return {}
        try:
            return json.loads(row["data_json"])
        except Exception:
            return {}

    def _set_ext(self, con, kind: str, eid: str, patch: Dict[str, Any]) -> Dict[str, Any]:
        data = self._ext(con, kind, eid)
        data.update({k: v for k, v in patch.items() if v is not None})
        con.execute(
            "INSERT INTO workstation_ext(entity_type,entity_id,data_json,updated_at) VALUES(?,?,?,?) "
            "ON CONFLICT(entity_type,entity_id) DO UPDATE SET data_json=excluded.data_json, updated_at=excluded.updated_at",
            (kind, eid, json.dumps(data), _now()),
        )
        return data

    # ------------------------------ status --------------------------------- #
    def counts(self) -> Dict[str, int]:
        out: Dict[str, int] = {}
        with self.connect() as con:
            for table in ("patients", "providers", "sensor_sessions", "hrv_data",
                          "ppg_data", "temperature_data", "gsr_data", "symptoms",
                          "cycles", "doctor_notes", "ultrasound_records",
                          "model_results", "reports"):
                try:
                    out[table] = con.execute(f"SELECT COUNT(*) c FROM {table}").fetchone()["c"]
                except sqlite3.Error:
                    out[table] = 0
            try:
                out["demo_rows"] = con.execute(
                    "SELECT COUNT(*) c FROM sensor_sessions WHERE label=?", (DEMO_LABEL,)
                ).fetchone()["c"]
            except sqlite3.Error:
                out["demo_rows"] = 0
        return out

    def health(self) -> Dict[str, Any]:
        c = self.counts()
        return {
            "ok": True,
            "source": "database",
            "db": str(self.db_path),
            "exists": self.db_path.exists(),
            "size_bytes": self.db_path.stat().st_size if self.db_path.exists() else 0,
            "counts": c,
            "empty": c.get("patients", 0) == 0,
            "has_signals": c.get("hrv_data", 0) + c.get("ppg_data", 0) > 0,
            "demo_seeded": c.get("demo_rows", 0) > 0,
            "server_time": _now(),
        }

    # ----------------------------- patients -------------------------------- #
    def _patient_record(self, con, row: sqlite3.Row, deep: bool = True) -> Dict[str, Any]:
        pid = row["patient_id"]
        ext = self._ext(con, "patient", pid)
        rec: Dict[str, Any] = {
            "id": pid,
            "name": row["display_name"] or row["anonymous_id"] or pid,
            "anonymousId": row["anonymous_id"],
            "age": _i(row["age_years"]),
            "bmi": _round(row["bmi"], 1),
            "archived": bool(row["is_archived"]),
            "joined": time.strftime("%Y-%m-%d", time.localtime(row["created_at"] or _now())),
            "source": "database",
        }
        for f in EXT_FIELDS:
            rec[f] = ext.get(f)
        rec["status"] = "Archived" if rec["archived"] else (ext.get("status") or "Active")
        rec["cohort"] = ext.get("cohort") or "Unassigned"
        rec["device"] = ext.get("device") or "Not paired"
        if rec.get("bmi") is None and ext.get("height") and ext.get("weight"):
            try:
                rec["bmi"] = round(float(ext["weight"]) / (float(ext["height"]) / 100) ** 2, 1)
            except Exception:
                pass

        sig = self._signals(con, pid)
        rec.update(sig)

        model = con.execute(
            "SELECT * FROM model_results WHERE patient_id=? ORDER BY created_at DESC LIMIT 1", (pid,)
        ).fetchone()
        if model:
            conf = _f(model["confidence"])
            rec["risk"] = _i(conf * 100) if conf is not None and conf <= 1 else _i(conf)
            rec["riskLevel"] = model["level"]
            rec["model"] = f'{model["module_name"]} {model["module_version"] or ""}'.strip()
            rec["modelExplanation"] = model["explanation"]
            try:
                drivers = json.loads(model["drivers_json"] or "[]")
            except Exception:
                drivers = []
            rec["drivers"] = [
                {"k": d.get("name", d.get("k", "driver")), "v": _i((d.get("weight", d.get("v", 0)) or 0) * (100 if abs(_f(d.get("weight", d.get("v", 0))) or 0) <= 1 else 1))}
                for d in drivers
            ] if isinstance(drivers, list) else []
            rec["limitations"] = model["limitations"]
        else:
            rec.setdefault("riskLevel", None)
            rec["drivers"] = rec.get("drivers") or []
        if rec.get("risk") is None:
            rec["risk"] = ext.get("risk")

        if not deep:
            return rec

        rec["symptoms"] = [
            {
                "name": r["symptom_type"],
                "severity": _i(r["severity"]) or 1,
                "days": max(1, int((_now() - (r["logged_at"] or _now())) // 86400) or 1),
                "trend": "up" if (_i(r["severity"]) or 0) >= 3 else "down",
                "notes": r["notes"],
                "label": r["label"],
            }
            for r in con.execute(
                "SELECT * FROM symptoms WHERE patient_id=? ORDER BY logged_at DESC LIMIT 12", (pid,)
            )
        ]
        rec["notes"] = [
            {
                "by": r["doctor_id"] or "clinician",
                "when": time.strftime("%d %b", time.localtime(r["created_at"] or _now())),
                "text": r["note_text"],
            }
            for r in con.execute(
                "SELECT * FROM doctor_notes WHERE patient_id=? ORDER BY created_at DESC LIMIT 20", (pid,)
            )
        ]
        rec["reports"] = [
            {
                "id": r["report_id"],
                "title": (r["report_type"] or "Report").replace("_", " ").title(),
                "date": time.strftime("%d %b", time.localtime(r["created_at"] or _now())),
                "kind": r["report_type"] or "Report",
                "pages": max(1, len((r["content_text"] or "")) // 1800 + 1),
            }
            for r in con.execute(
                "SELECT * FROM reports WHERE patient_id=? ORDER BY created_at DESC LIMIT 20", (pid,)
            )
        ]
        us = con.execute(
            "SELECT * FROM ultrasound_records WHERE patient_id=? ORDER BY created_at DESC LIMIT 1", (pid,)
        ).fetchone()
        rec["ultrasound"] = {
            "date": time.strftime("%d %b", time.localtime(us["created_at"] or _now())),
            "follicles": _us_note(us["notes"]).get("follicle_count"),
            "largest": _round(us["cyst_size_mm"], 1),
            "volume": _round(us["volume_cc"], 1),
            "pattern": us["morphology"] or "Not described",
            "quality": _round(us["quality"], 2),
            "confidence": _round(us["confidence"], 2),
            "source": us["source"],
            "endometrium": _us_note(us["notes"]).get("endometrium_mm"),
            "note": _us_note(us["notes"]).get("note"),
        } if us else None

        cyc = con.execute(
            "SELECT * FROM cycles WHERE patient_id=? ORDER BY logged_at DESC LIMIT 1", (pid,)
        ).fetchone()
        if cyc:
            rec["cycleLen"] = _i(cyc["cycle_length_days"]) or _i(cyc["usual_length_days"]) or rec.get("cycleLen")
            if cyc["start_date"]:
                day = int((_now() - cyc["start_date"]) // 86400) + 1
                if rec["cycleLen"]:
                    day = ((day - 1) % rec["cycleLen"]) + 1
                rec["cycleDay"] = day
        rec["meds"] = ext.get("meds") or []
        rec["labs"] = ext.get("labs") or []
        return rec

    def _signals(self, con, pid: str) -> Dict[str, Any]:
        """Real sensor series for a patient. Empty lists when nothing recorded."""
        sessions = [r["session_id"] for r in con.execute(
            "SELECT session_id FROM sensor_sessions WHERE patient_id=? ORDER BY start_at DESC LIMIT 30", (pid,))]
        empty = {
            "live": {k: [] for k in ("hr", "hrv", "temp", "gsr", "steps", "spo2")},
            "trend30": {k: [] for k in ("hr", "hrv", "temp", "gsr", "sleep", "steps", "risk", "weight")},
            "vitals": {k: None for k in ("hr", "hrv", "temp", "gsr", "steps", "spo2", "sleep", "resp", "bp", "bmi")},
            "hasSignals": False,
            "quality": None,
            "lastSync": None,
            "sessionCount": len(sessions),
        }
        if not sessions:
            return empty
        q = ",".join("?" * len(sessions))
        latest = sessions[0]

        hrv = con.execute(
            f"SELECT timestamp_s, hr_bpm, rmssd_ms, quality FROM hrv_data WHERE session_id=? ORDER BY timestamp_s DESC LIMIT 600",
            (latest,)).fetchall()[::-1]
        ppg = con.execute(
            f"SELECT timestamp_s, spo2_pct, hr_bpm, quality FROM ppg_data WHERE session_id=? ORDER BY timestamp_s DESC LIMIT 600",
            (latest,)).fetchall()[::-1]
        tmp = con.execute(
            f"SELECT timestamp_s, skin_temp_c, quality FROM temperature_data WHERE session_id=? ORDER BY timestamp_s DESC LIMIT 600",
            (latest,)).fetchall()[::-1]
        gsr = con.execute(
            f"SELECT timestamp_s, gsr_tonic, gsr_raw, quality FROM gsr_data WHERE session_id=? ORDER BY timestamp_s DESC LIMIT 600",
            (latest,)).fetchall()[::-1]
        mot = con.execute(
            f"SELECT timestamp_s, activity_level FROM motion_data WHERE session_id=? ORDER BY timestamp_s DESC LIMIT 600",
            (latest,)).fetchall()[::-1] if _has_column(con, "motion_data", "activity_level") else []

        live = {
            "hr": _downsample([_f(r["hr_bpm"]) for r in hrv] or [_f(r["hr_bpm"]) for r in ppg], 60),
            "hrv": _downsample([_f(r["rmssd_ms"]) for r in hrv], 60),
            "temp": _downsample([_f(r["skin_temp_c"]) for r in tmp], 60),
            "gsr": _downsample([_f(r["gsr_tonic"]) if r["gsr_tonic"] is not None else _f(r["gsr_raw"]) for r in gsr], 60),
            "spo2": _downsample([_f(r["spo2_pct"]) for r in ppg], 60),
            "steps": _downsample([_f(r["activity_level"]) for r in mot], 60),
        }
        if not live["steps"]:
            live["steps"] = []

        # 30-day trend = per-session means, oldest -> newest
        trend = {k: [] for k in ("hr", "hrv", "temp", "gsr", "sleep", "steps", "risk", "weight")}
        for sid in reversed(sessions):
            row = con.execute(
                "SELECT AVG(hr_bpm) hr, AVG(rmssd_ms) hrv FROM hrv_data WHERE session_id=?", (sid,)).fetchone()
            t = con.execute("SELECT AVG(skin_temp_c) t FROM temperature_data WHERE session_id=?", (sid,)).fetchone()
            g = con.execute("SELECT AVG(COALESCE(gsr_tonic,gsr_raw)) g FROM gsr_data WHERE session_id=?", (sid,)).fetchone()
            if row and row["hr"] is not None:
                trend["hr"].append(round(row["hr"], 2))
            if row and row["hrv"] is not None:
                trend["hrv"].append(round(row["hrv"], 2))
            if t and t["t"] is not None:
                trend["temp"].append(round(t["t"], 2))
            if g and g["g"] is not None:
                trend["gsr"].append(round(g["g"], 3))
        for r in con.execute(
                "SELECT confidence, created_at FROM model_results WHERE patient_id=? ORDER BY created_at ASC LIMIT 60", (pid,)):
            c = _f(r["confidence"])
            if c is not None:
                trend["risk"].append(round(c * 100 if c <= 1 else c, 1))

        sess = con.execute("SELECT * FROM sensor_sessions WHERE session_id=?", (latest,)).fetchone()
        vitals = {
            "hr": _i(live["hr"][-1]) if live["hr"] else None,
            "hrv": _i(live["hrv"][-1]) if live["hrv"] else None,
            "temp": _round(live["temp"][-1], 1) if live["temp"] else None,
            "gsr": _round(live["gsr"][-1], 2) if live["gsr"] else None,
            "spo2": _i(live["spo2"][-1]) if live["spo2"] else None,
            "steps": _i(sum(live["steps"])) if live["steps"] else None,
            "sleep": None, "resp": None, "bp": None, "bmi": None,
        }
        return {
            "live": live,
            "trend30": trend,
            "vitals": vitals,
            "hasSignals": any(live[k] for k in live),
            "quality": _round(sess["data_quality"], 2) if sess and sess["data_quality"] is not None else None,
            "lastSync": time.strftime("%d %b %H:%M", time.localtime(sess["end_at"] or sess["start_at"] or _now())) if sess else None,
            "sessionCount": len(sessions),
        }

    def list_patients(self, deep: bool = True) -> List[Dict[str, Any]]:
        with self.connect() as con:
            rows = con.execute("SELECT * FROM patients ORDER BY created_at DESC").fetchall()
            return [self._patient_record(con, r, deep=deep) for r in rows]

    def get_patient(self, pid: str) -> Optional[Dict[str, Any]]:
        with self.connect() as con:
            row = con.execute("SELECT * FROM patients WHERE patient_id=?", (pid,)).fetchone()
            return self._patient_record(con, row) if row else None

    def create_patient(self, body: Dict[str, Any]) -> Dict[str, Any]:
        pid = (body.get("id") or "").strip() or _uid("ETN")
        now = _now()
        height, weight = _f(body.get("height")), _f(body.get("weight"))
        bmi = round(weight / (height / 100) ** 2, 1) if height and weight else _f(body.get("bmi"))
        with self.connect() as con:
            con.execute(
                "INSERT OR REPLACE INTO patients(patient_id,user_id,anonymous_id,display_name,age_years,bmi,created_at,updated_at,is_archived)"
                " VALUES(?,?,?,?,?,?,?,?,?)",
                (pid, body.get("user_id"), body.get("anonymousId") or pid, body.get("name") or pid,
                 _f(body.get("age")), bmi, now, now, 1 if body.get("status") == "Archived" else 0),
            )
            self._set_ext(con, "patient", pid, {k: body.get(k) for k in EXT_FIELDS})
            con.commit()
        return self.get_patient(pid)

    def update_patient(self, pid: str, body: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        with self.connect() as con:
            row = con.execute("SELECT * FROM patients WHERE patient_id=?", (pid,)).fetchone()
            if not row:
                return None
            height, weight = _f(body.get("height")), _f(body.get("weight"))
            bmi = round(weight / (height / 100) ** 2, 1) if height and weight else row["bmi"]
            con.execute(
                "UPDATE patients SET display_name=?, age_years=?, bmi=?, updated_at=?, is_archived=? WHERE patient_id=?",
                (body.get("name") or row["display_name"], _f(body.get("age")) if body.get("age") is not None else row["age_years"],
                 bmi, _now(), 1 if body.get("status") == "Archived" else 0, pid),
            )
            self._set_ext(con, "patient", pid, {k: body.get(k) for k in EXT_FIELDS})
            con.commit()
        return self.get_patient(pid)

    def delete_patient(self, pid: str) -> Dict[str, Any]:
        with self.connect() as con:
            sessions = [r["session_id"] for r in con.execute(
                "SELECT session_id FROM sensor_sessions WHERE patient_id=?", (pid,))]
            for sid in sessions:
                for t in ("hrv_data", "ppg_data", "temperature_data", "gsr_data", "motion_data", "sensor_quality"):
                    try:
                        con.execute(f"DELETE FROM {t} WHERE session_id=?", (sid,))
                    except sqlite3.Error:
                        pass
            for t in ("sensor_sessions", "symptoms", "cycles", "doctor_notes", "reports",
                      "ultrasound_records", "model_results", "analysis_results", "profiles"):
                try:
                    con.execute(f"DELETE FROM {t} WHERE patient_id=?", (pid,))
                except sqlite3.Error:
                    pass
            con.execute("DELETE FROM patients WHERE patient_id=?", (pid,))
            con.execute("DELETE FROM workstation_ext WHERE entity_type='patient' AND entity_id=?", (pid,))
            con.commit()
        return {"deleted": pid}

    # ----------------------------- clinicians ------------------------------ #
    def list_doctors(self) -> List[Dict[str, Any]]:
        out = []
        with self.connect() as con:
            rows = con.execute(
                "SELECT * FROM providers WHERE type IN ('doctor','clinician') OR type IS NULL ORDER BY created_at"
            ).fetchall()
            for r in rows:
                ext = self._ext(con, "doctor", r["provider_id"])
                contact = (r["contact_info"] or "").split("|")
                out.append({
                    "id": r["provider_id"],
                    "name": r["name"],
                    "specialty": r["specialty"] or ext.get("specialty") or "General",
                    "clinic": r["address"] or ext.get("clinic") or "—",
                    "email": ext.get("email") or (contact[0].strip() if contact else "—"),
                    "phone": ext.get("phone") or (contact[1].strip() if len(contact) > 1 else "—"),
                    "slot": r["opening_hours"] or ext.get("slot") or "—",
                    "reg": ext.get("reg") or "—",
                    "exp": ext.get("exp"),
                    "room": ext.get("room") or "—",
                    "days": ext.get("days") or "—",
                    "status": ext.get("status") or "Available",
                    "verification": r["verification_status"],
                    "isDemo": bool(r["is_demo"]),
                    "source": "database",
                })
        return out

    def create_doctor(self, body: Dict[str, Any]) -> Dict[str, Any]:
        did = (body.get("id") or "").strip() or _uid("DR")
        now = _now()
        with self.connect() as con:
            con.execute(
                "INSERT OR REPLACE INTO providers(provider_id,name,type,specialty,address,latitude,longitude,distance_km,"
                "opening_hours,services_json,contact_info,verification_status,is_demo,created_at,updated_at)"
                " VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (did, body.get("name") or did, "doctor", body.get("specialty"), body.get("clinic"),
                 None, None, None, body.get("slot"),
                 json.dumps({"services": [body.get("specialty") or "Consultation"],
                             "label": DEMO_LABEL if body.get("isDemo") else "USER_ENTERED"}),
                 f'{body.get("email") or ""} | {body.get("phone") or ""}',
                 body.get("verification") or "unverified", 1 if body.get("isDemo") else 0, now, now),
            )
            self._set_ext(con, "doctor", did, {k: body.get(k) for k in
                                               ("reg", "exp", "room", "days", "status", "email", "phone", "clinic", "specialty", "slot")})
            con.commit()
        return next((d for d in self.list_doctors() if d["id"] == did), {"id": did})

    def update_doctor(self, did: str, body: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        with self.connect() as con:
            row = con.execute("SELECT * FROM providers WHERE provider_id=?", (did,)).fetchone()
            if not row:
                return None
            con.execute(
                "UPDATE providers SET name=?, specialty=?, address=?, opening_hours=?, contact_info=?, updated_at=? WHERE provider_id=?",
                (body.get("name") or row["name"], body.get("specialty") or row["specialty"],
                 body.get("clinic") or row["address"], body.get("slot") or row["opening_hours"],
                 f'{body.get("email") or ""} | {body.get("phone") or ""}', _now(), did),
            )
            self._set_ext(con, "doctor", did, {k: body.get(k) for k in
                                               ("reg", "exp", "room", "days", "status", "email", "phone", "clinic", "specialty", "slot")})
            con.commit()
        return next((d for d in self.list_doctors() if d["id"] == did), None)

    def delete_doctor(self, did: str) -> Dict[str, Any]:
        with self.connect() as con:
            con.execute("DELETE FROM providers WHERE provider_id=?", (did,))
            con.execute("DELETE FROM workstation_ext WHERE entity_type='doctor' AND entity_id=?", (did,))
            con.commit()
        return {"deleted": did}

    # ------------------------------ writes --------------------------------- #
    def add_note(self, body: Dict[str, Any]) -> Dict[str, Any]:
        nid = _uid("NOTE")
        with self.connect() as con:
            con.execute(
                "INSERT INTO doctor_notes(note_id,patient_id,doctor_id,note_text,created_at,updated_at,is_private)"
                " VALUES(?,?,?,?,?,?,?)",
                (nid, _pid(body), body.get("by"), body.get("text"), _now(), _now(), 0))
            con.commit()
        return {"note_id": nid}

    def add_symptom(self, body: Dict[str, Any]) -> Dict[str, Any]:
        sid = _uid("SYM")
        with self.connect() as con:
            con.execute(
                "INSERT INTO symptoms(symptom_id,patient_id,symptom_type,severity,notes,logged_at,label)"
                " VALUES(?,?,?,?,?,?,?)",
                (sid, _pid(body), body.get("name") or body.get("symptom"), _i(body.get("severity")) or 1,
                 body.get("notes") or body.get("note"), _now(), body.get("label") or "CLINICALLY_ENTERED"))
            con.commit()
        return {"symptom_id": sid}

    def add_cycle(self, body: Dict[str, Any]) -> Dict[str, Any]:
        cid = _uid("CYC")
        day = _i(body.get("cycleDay")) or 1
        with self.connect() as con:
            con.execute(
                "INSERT INTO cycles(cycle_id,patient_id,start_date,end_date,cycle_length_days,usual_length_days,"
                "irregularity,symptoms_json,notes,logged_at,label) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (cid, _pid(body), _now() - (day - 1) * 86400, None,
                 _i(body.get("cycleLen")), _i(body.get("cycleLen")), None, "[]", None, _now(),
                 "CLINICALLY_ENTERED"))
            self._set_ext(con, "patient", _pid(body), {
                "cycleDay": day, "cycleLen": _i(body.get("cycleLen"))})
            con.commit()
        return {"cycle_id": cid}

    def add_report(self, body: Dict[str, Any]) -> Dict[str, Any]:
        rid = _uid("RPT")
        with self.connect() as con:
            con.execute(
                "INSERT INTO reports(report_id,patient_id,session_id,report_type,content_text,file_path,created_at,created_by,label)"
                " VALUES(?,?,?,?,?,?,?,?,?)",
                (rid, _pid(body), None, body.get("kind") or body.get("title") or "summary", body.get("text") or body.get("title"),
                 None, _now(), body.get("by"), "GENERATED"))
            con.commit()
        return {"report_id": rid}

    # ---------------------------- bootstrap -------------------------------- #
    def bootstrap(self) -> Dict[str, Any]:
        health = self.health()
        return {
            "source": "database",
            "health": health,
            "patients": self.list_patients(),
            "doctors": self.list_doctors(),
        }

    # ------------------------------- demo ---------------------------------- #
    def seed_demo(self, n_sessions: int = 12, samples: int = 90) -> Dict[str, Any]:
        """Write a clearly labelled synthetic cohort into the real database."""
        from_demo = _DEMO_COHORT
        created = []
        now = _now()
        for spec in from_demo:
            rnd = random.Random(spec["id"])
            self.create_patient(spec)
            pid = spec["id"]
            risk = spec["risk"] / 100.0
            with self.connect() as con:
                for s in range(n_sessions):
                    sid = f"{pid}-S{s:02d}"
                    start = now - (n_sessions - s) * 86400 - 3600
                    con.execute(
                        "INSERT OR REPLACE INTO sensor_sessions(session_id,patient_id,source,start_at,end_at,"
                        "sample_count,data_quality,notes,label,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
                        (sid, pid, "ESP32-S3 (synthetic)", start, start + 3000, samples,
                         spec["quality"], "generated demo session", DEMO_LABEL, now))
                    hr = 64 + risk * 16
                    hrv = 68 - risk * 34
                    tmp = 33.4 + risk * 1.4
                    gsr = 0.16 + risk * 0.30
                    spo2 = 99 - risk * 2.2
                    for i in range(samples):
                        ts = start + i * 30
                        hr += (rnd.random() - .5) * 4 + (64 + risk * 16 - hr) * .15
                        hrv += (rnd.random() - .5) * 5 + (68 - risk * 34 - hrv) * .15
                        tmp += (rnd.random() - .5) * .18 + (33.4 + risk * 1.4 - tmp) * .15
                        gsr += (rnd.random() - .5) * .05 + (0.16 + risk * .3 - gsr) * .15
                        sp = spo2 + (rnd.random() - .5) * .8
                        act = max(0.0, 30 + math.sin(i / 7) * 22 + (rnd.random() - .5) * 14 - risk * 8)
                        q = spec["quality"] + (rnd.random() - .5) * .06
                        con.execute("INSERT INTO hrv_data(session_id,timestamp_s,hr_bpm,resting_hr_bpm,rmssd_ms,sdnn_ms,pnn50_pct,quality,label)"
                                    " VALUES(?,?,?,?,?,?,?,?,?)",
                                    (sid, ts, round(hr, 1), round(hr - 6, 1), round(hrv, 1), round(hrv * 1.4, 1), round(hrv / 2, 1), round(q, 2), DEMO_LABEL))
                        con.execute("INSERT INTO ppg_data(session_id,timestamp_s,ir,red,hr_bpm,spo2_pct,pulse_amplitude,quality,label)"
                                    " VALUES(?,?,?,?,?,?,?,?,?)",
                                    (sid, ts, int(18000 + rnd.random() * 2000), int(15000 + rnd.random() * 2000),
                                     round(hr, 1), round(sp, 1), round(1 + rnd.random(), 2), round(q, 2), DEMO_LABEL))
                        con.execute("INSERT INTO temperature_data(session_id,timestamp_s,skin_temp_c,room_temp_c,temp_slope_c_per_min,quality,label)"
                                    " VALUES(?,?,?,?,?,?,?)",
                                    (sid, ts, round(tmp, 2), round(24 + rnd.random() * 2, 1), round((rnd.random() - .5) * .05, 3), round(q, 2), DEMO_LABEL))
                        con.execute("INSERT INTO gsr_data(session_id,timestamp_s,gsr_raw,gsr_tonic,gsr_phasic_per_min,quality,label)"
                                    " VALUES(?,?,?,?,?,?,?)",
                                    (sid, ts, int(gsr * 1000), round(gsr, 3), round(rnd.random() * 4, 2), round(q, 2), DEMO_LABEL))
                        if _has_column(con, "motion_data", "activity_level"):
                            con.execute("INSERT INTO motion_data(session_id,timestamp_s,activity_level,quality,label)"
                                        " VALUES(?,?,?,?,?)", (sid, ts, round(act, 1), round(q, 2), DEMO_LABEL))

                # clinical rows
                for sname, sev in spec["symptoms"]:
                    con.execute("INSERT INTO symptoms(symptom_id,patient_id,symptom_type,severity,notes,logged_at,label)"
                                " VALUES(?,?,?,?,?,?,?)",
                                (_uid("SYM"), pid, sname, sev, None, now - rnd.random() * 6 * 86400, DEMO_LABEL))
                con.execute("INSERT INTO cycles(cycle_id,patient_id,start_date,end_date,cycle_length_days,usual_length_days,"
                            "irregularity,symptoms_json,notes,logged_at,label) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                            (_uid("CYC"), pid, now - (spec["cycleDay"] - 1) * 86400, None, spec["cycleLen"],
                             spec["cycleLen"], "irregular" if spec["cycleLen"] > 35 else "regular", "[]", None, now, DEMO_LABEL))
                con.execute("INSERT INTO doctor_notes(note_id,patient_id,doctor_id,note_text,created_at,updated_at,is_private)"
                            " VALUES(?,?,?,?,?,?,?)",
                            (_uid("NOTE"), pid, spec["doctorId"],
                             "Synthetic demo note: longitudinal pattern reviewed; research signal only, not a diagnosis.",
                             now - 3 * 86400, now - 3 * 86400, 0))
                con.execute("INSERT INTO ultrasound_records(record_id,patient_id,image_path,cyst_size_mm,volume_cc,morphology,"
                            "quality,source,confidence,notes,created_at,label) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                            (_uid("USG"), pid, None, round(6 + risk * 6, 1), round(6 + risk * 8, 1),
                             "Possible PCOM" if risk > .7 else "Indeterminate" if risk > .45 else "Not suggested",
                             round(.62 + rnd.random() * .34, 2), "IMAGE-DERIVED (synthetic)", round(.6 + rnd.random() * .3, 2),
                             json.dumps({"follicle_count": int(6 + risk * 16),
                                         "endometrium_mm": round(6 + spec["cycleDay"] / 4, 1),
                                         "note": "Generated demo study"}),
                             now - 5 * 86400, DEMO_LABEL))
                drivers = [{"name": k, "weight": v} for k, v in (
                    ("Cycle length variability", round(.18 + risk * .46, 2)),
                    ("HRV below personal baseline", round(.12 + risk * .44, 2)),
                    ("Night skin-temp elevation", round(.10 + risk * .34, 2)),
                    ("Sleep fragmentation", round(.08 + risk * .30, 2)),
                    ("Activity decline", round(.06 + risk * .26, 2)))]
                for s in range(n_sessions):
                    con.execute("INSERT INTO model_results(result_id,patient_id,session_id,module_name,module_version,signal,level,"
                                "confidence,data_quality,clinical_validation,drivers_json,explanation,provenance_json,limitations,extra_json,created_at,label)"
                                " VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                                (_uid("MR"), pid, f"{pid}-S{s:02d}", "pcos_risk_gbm", "2.4.1", "pcos_research_signal",
                                 "high" if risk > .7 else "moderate" if risk > .45 else "low",
                                 round(min(1.0, max(0.0, risk + (rnd.random() - .5) * .06)), 3), spec["quality"],
                                 "not_validated", json.dumps(drivers),
                                 "Longitudinal deviation from the participant's own baseline across HRV, skin temperature and cycle length.",
                                 json.dumps({"hr": "MEASURED", "hrv": "DERIVED", "risk": "MODEL-INFERRED"}),
                                 "PPG-derived HRV is less accurate than ECG; no external validation; serum hormones unknown.",
                                 "{}", now - (n_sessions - s) * 86400, DEMO_LABEL))
                con.execute("INSERT INTO reports(report_id,patient_id,session_id,report_type,content_text,file_path,created_at,created_by,label)"
                            " VALUES(?,?,?,?,?,?,?,?,?)",
                            (_uid("RPT"), pid, None, "Longitudinal Physiology", "Generated demo report body.",
                             None, now - 4 * 86400, spec["doctorId"], DEMO_LABEL))
                con.commit()
            created.append(pid)

        for doc in _DEMO_DOCTORS:
            self.create_doctor(dict(doc, verification="demo", isDemo=True))
        return {"seeded": created, "doctors": [d["id"] for d in _DEMO_DOCTORS], "label": DEMO_LABEL,
                "health": self.health()}

    def clear_demo(self) -> Dict[str, Any]:
        removed = 0
        with self.connect() as con:
            sessions = [r["session_id"] for r in con.execute(
                "SELECT session_id FROM sensor_sessions WHERE label=?", (DEMO_LABEL,))]
            pids = [r["patient_id"] for r in con.execute(
                "SELECT DISTINCT patient_id FROM sensor_sessions WHERE label=?", (DEMO_LABEL,))]
            for sid in sessions:
                for t in ("hrv_data", "ppg_data", "temperature_data", "gsr_data", "motion_data", "sensor_quality"):
                    try:
                        removed += con.execute(f"DELETE FROM {t} WHERE session_id=?", (sid,)).rowcount
                    except sqlite3.Error:
                        pass
            for t in ("sensor_sessions", "symptoms", "cycles", "ultrasound_records", "model_results", "reports"):
                try:
                    removed += con.execute(f"DELETE FROM {t} WHERE label=?", (DEMO_LABEL,)).rowcount
                except sqlite3.Error:
                    pass
            for pid in pids:
                con.execute("DELETE FROM doctor_notes WHERE patient_id=?", (pid,))
                con.execute("DELETE FROM patients WHERE patient_id=?", (pid,))
                con.execute("DELETE FROM workstation_ext WHERE entity_type='patient' AND entity_id=?", (pid,))
            # clinicians written by seed_demo carry the label inside services_json
            seeded = [r["provider_id"] for r in con.execute(
                "SELECT provider_id FROM providers WHERE services_json LIKE ?", (f'%"{DEMO_LABEL}"%',))]
            for did in seeded:
                removed += con.execute("DELETE FROM providers WHERE provider_id=?", (did,)).rowcount
                con.execute("DELETE FROM workstation_ext WHERE entity_type='doctor' AND entity_id=?", (did,))
            con.commit()
        return {"removed_rows": removed, "health": self.health()}

    # ------------------------------ router --------------------------------- #
    def handle(self, method: str, path: str, body: Dict[str, Any]) -> Tuple[int, Any]:
        parts = [p for p in path.strip("/").split("/") if p]      # ['api', ...]
        parts = parts[1:]                                          # drop 'api'
        try:
            if not parts:
                return 200, self.health()
            head = parts[0]
            if head == "health":
                return 200, self.health()
            if head == "bootstrap":
                return 200, self.bootstrap()
            if head == "patients":
                if len(parts) == 1:
                    if method == "GET":
                        return 200, {"patients": self.list_patients()}
                    if method == "POST":
                        return 201, self.create_patient(body)
                pid = parts[1]
                if len(parts) == 3 and parts[2] == "series":
                    with self.connect() as con:
                        return 200, self._signals(con, pid)
                if method == "GET":
                    rec = self.get_patient(pid)
                    return (200, rec) if rec else (404, {"error": "unknown patient"})
                if method in ("PUT", "PATCH"):
                    rec = self.update_patient(pid, body)
                    return (200, rec) if rec else (404, {"error": "unknown patient"})
                if method == "DELETE":
                    return 200, self.delete_patient(pid)
            if head == "doctors":
                if len(parts) == 1:
                    if method == "GET":
                        return 200, {"doctors": self.list_doctors()}
                    if method == "POST":
                        return 201, self.create_doctor(body)
                did = parts[1]
                if method in ("PUT", "PATCH"):
                    rec = self.update_doctor(did, body)
                    return (200, rec) if rec else (404, {"error": "unknown doctor"})
                if method == "DELETE":
                    return 200, self.delete_doctor(did)
            if head == "notes" and method == "POST":
                return 201, self.add_note(body)
            if head == "symptoms" and method == "POST":
                return 201, self.add_symptom(body)
            if head == "cycles" and method == "POST":
                return 201, self.add_cycle(body)
            if head == "reports" and method == "POST":
                return 201, self.add_report(body)
            if head == "seed-demo" and method == "POST":
                return 200, self.seed_demo()
            if head == "clear-demo" and method == "POST":
                return 200, self.clear_demo()
            return 404, {"error": f"no route for /{'/'.join(parts)}"}
        except Exception as exc:  # pragma: no cover
            import traceback
            traceback.print_exc()
            return 500, {"error": str(exc)}


def _us_note(raw) -> Dict[str, Any]:
    """Ultrasound extras live in the notes column as JSON (schema has no column)."""
    if not raw:
        return {}
    try:
        val = json.loads(raw)
        return val if isinstance(val, dict) else {"note": raw}
    except Exception:
        return {"note": raw}


def _has_column(con, table: str, column: str) -> bool:
    try:
        return any(r[1] == column for r in con.execute(f"PRAGMA table_info('{table}')"))
    except sqlite3.Error:
        return False


# --------------------------------------------------------------------------- #
#  demo cohort definition (only written when explicitly seeded)
# --------------------------------------------------------------------------- #
_DEMO_COHORT = [
    dict(id="ETN-2041", name="Aviral Singh",  age=21, gender="Female", city="Ghaziabad, UP", phone="+91 98765 41020", email="aviral@demo.health",  height=163, weight=58, blood="O+",  cycleLen=28, cycleDay=14, risk=73, doctorId="DR-1001", status="Active",       cohort="Chrono-PCOS Cohort A", device="ESP32-S3 · ETN-W12", battery=85, adherence=92, quality=0.91, symptoms=[("Mood swing", 3), ("Acne", 2), ("Fatigue", 3)]),
    dict(id="ETN-2042", name="Priya Sharma",  age=27, gender="Female", city="New Delhi",     phone="+91 98111 23344", email="priya.s@demo.health", height=158, weight=67, blood="B+",  cycleLen=34, cycleDay=22, risk=81, doctorId="DR-1001", status="Needs review", cohort="Chrono-PCOS Cohort A", device="ESP32-S3 · ETN-W04", battery=62, adherence=78, quality=0.86, symptoms=[("Hair fall", 4), ("Bloating", 3)]),
    dict(id="ETN-2043", name="Neha Verma",    age=24, gender="Female", city="Noida, UP",     phone="+91 99900 77812", email="neha.v@demo.health",  height=166, weight=54, blood="A+",  cycleLen=27, cycleDay=6,  risk=34, doctorId="DR-1002", status="Active",       cohort="Control Cohort",       device="ESP32-S3 · ETN-W19", battery=94, adherence=96, quality=0.94, symptoms=[("Cramps", 2)]),
    dict(id="ETN-2044", name="Ritika Nair",   age=31, gender="Female", city="Gurugram, HR",  phone="+91 90000 65401", email="ritika.n@demo.health",height=161, weight=72, blood="AB+", cycleLen=41, cycleDay=33, risk=88, doctorId="DR-1003", status="Needs review", cohort="Chrono-PCOS Cohort B", device="ESP32-S3 · ETN-W07", battery=41, adherence=64, quality=0.72, symptoms=[("Fatigue", 4), ("Sugar craving", 4), ("Sleep trouble", 3)]),
    dict(id="ETN-2045", name="Aisha Khan",    age=19, gender="Female", city="Lucknow, UP",   phone="+91 87654 30099", email="aisha.k@demo.health", height=155, weight=49, blood="O-",  cycleLen=30, cycleDay=11, risk=46, doctorId="DR-1002", status="Active",       cohort="Chrono-PCOS Cohort B", device="ESP32-S3 · ETN-W22", battery=77, adherence=88, quality=0.89, symptoms=[("Acne", 3), ("Oily skin", 2)]),
    dict(id="ETN-2046", name="Divya Menon",   age=29, gender="Female", city="Bengaluru, KA", phone="+91 96000 41277", email="divya.m@demo.health", height=169, weight=63, blood="B-",  cycleLen=29, cycleDay=19, risk=52, doctorId="DR-1004", status="Active",       cohort="Sleep / Circadian",    device="ESP32-S3 · ETN-W31", battery=58, adherence=81, quality=0.83, symptoms=[("Sleep trouble", 4), ("Headache", 2)]),
    dict(id="ETN-2047", name="Sanya Kapoor",  age=35, gender="Female", city="Mumbai, MH",    phone="+91 91111 20087", email="sanya.k@demo.health", height=160, weight=78, blood="A-",  cycleLen=45, cycleDay=38, risk=91, doctorId="DR-1001", status="Escalated",    cohort="Chrono-PCOS Cohort B", device="ESP32-S3 · ETN-W02", battery=23, adherence=55, quality=0.68, symptoms=[("Fatigue", 5), ("Hair fall", 4), ("Low energy", 4)]),
    dict(id="ETN-2048", name="Fatima Sheikh", age=23, gender="Female", city="Hyderabad, TS", phone="+91 93333 88120", email="fatima.s@demo.health",height=157, weight=56, blood="O+",  cycleLen=26, cycleDay=3,  risk=28, doctorId="DR-1005", status="Active",       cohort="Control Cohort",       device="ESP32-S3 · ETN-W28", battery=88, adherence=93, quality=0.92, symptoms=[("Cramps", 2), ("Back pain", 1)]),
    dict(id="ETN-2049", name="Tanvi Joshi",   age=26, gender="Female", city="Pune, MH",      phone="+91 95555 30014", email="tanvi.j@demo.health", height=164, weight=61, blood="B+",  cycleLen=32, cycleDay=27, risk=59, doctorId="DR-1003", status="Active",       cohort="Chrono-PCOS Cohort A", device="ESP32-S3 · ETN-W16", battery=70, adherence=85, quality=0.87, symptoms=[("Bloating", 3), ("Mood swing", 3)]),
    dict(id="ETN-2050", name="Ishita Bose",   age=33, gender="Female", city="Kolkata, WB",   phone="+91 98300 55471", email="ishita.b@demo.health",height=168, weight=69, blood="AB-", cycleLen=36, cycleDay=15, risk=67, doctorId="DR-1004", status="Archived",     cohort="Chrono-PCOS Cohort B", device="ESP32-S3 · ETN-W09", battery=0,  adherence=38, quality=0.61, symptoms=[("Fatigue", 3)]),
]

_DEMO_DOCTORS = [
    dict(id="DR-1001", name="Dr. Ananya Rao",     specialty="Endocrinology",         reg="MCI-88213", clinic="ENDO-TWIN Research Clinic, Delhi", email="a.rao@endotwin.health",       phone="+91 98110 22113", exp=12, room="Consult 2", status="Available",  days="Mon–Fri", slot="09:00 – 16:00"),
    dict(id="DR-1002", name="Dr. Kabir Menon",    specialty="Gynaecology",           reg="MCI-71904", clinic="ENDO-TWIN Research Clinic, Delhi", email="k.menon@endotwin.health",     phone="+91 98110 55210", exp=9,  room="Consult 4", status="In consult", days="Mon–Sat", slot="10:00 – 18:00"),
    dict(id="DR-1003", name="Dr. Meera Iyer",     specialty="Reproductive Medicine", reg="MCI-64118", clinic="Noida Satellite Unit",             email="m.iyer@endotwin.health",      phone="+91 99990 44512", exp=15, room="Consult 1", status="Available",  days="Tue–Sat", slot="11:00 – 17:00"),
    dict(id="DR-1004", name="Dr. Rohan Desai",    specialty="Sleep & Chronobiology", reg="MCI-59033", clinic="ENDO-TWIN Research Clinic, Delhi", email="r.desai@endotwin.health",     phone="+91 90011 78345", exp=7,  room="Lab A",     status="Off duty",   days="Wed–Sun", slot="08:00 – 14:00"),
    dict(id="DR-1005", name="Dr. Sara Fernandes", specialty="Clinical Nutrition",    reg="RD-20871",  clinic="Ghaziabad Care Point",             email="s.fernandes@endotwin.health", phone="+91 87000 11229", exp=6,  room="Consult 3", status="Available",  days="Mon–Thu", slot="12:00 – 19:00"),
]

_MINIMAL_SCHEMA = """
CREATE TABLE IF NOT EXISTS patients(patient_id TEXT PRIMARY KEY,user_id TEXT,anonymous_id TEXT,display_name TEXT,age_years REAL,bmi REAL,created_at REAL,updated_at REAL,is_archived INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS providers(provider_id TEXT PRIMARY KEY,name TEXT,type TEXT,specialty TEXT,address TEXT,latitude REAL,longitude REAL,distance_km REAL,opening_hours TEXT,services_json TEXT,contact_info TEXT,verification_status TEXT,is_demo INTEGER,created_at REAL,updated_at REAL);
CREATE TABLE IF NOT EXISTS sensor_sessions(session_id TEXT PRIMARY KEY,patient_id TEXT,source TEXT,start_at REAL,end_at REAL,sample_count INTEGER,data_quality REAL,notes TEXT,label TEXT,created_at REAL);
CREATE TABLE IF NOT EXISTS hrv_data(id INTEGER PRIMARY KEY AUTOINCREMENT,session_id TEXT,timestamp_s REAL,hr_bpm REAL,resting_hr_bpm REAL,rmssd_ms REAL,sdnn_ms REAL,pnn50_pct REAL,quality REAL,label TEXT);
CREATE TABLE IF NOT EXISTS ppg_data(id INTEGER PRIMARY KEY AUTOINCREMENT,session_id TEXT,timestamp_s REAL,ir INTEGER,red INTEGER,hr_bpm REAL,spo2_pct REAL,pulse_amplitude REAL,quality REAL,label TEXT);
CREATE TABLE IF NOT EXISTS temperature_data(id INTEGER PRIMARY KEY AUTOINCREMENT,session_id TEXT,timestamp_s REAL,skin_temp_c REAL,room_temp_c REAL,temp_slope_c_per_min REAL,quality REAL,label TEXT);
CREATE TABLE IF NOT EXISTS gsr_data(id INTEGER PRIMARY KEY AUTOINCREMENT,session_id TEXT,timestamp_s REAL,gsr_raw INTEGER,gsr_tonic REAL,gsr_phasic_per_min REAL,quality REAL,label TEXT);
CREATE TABLE IF NOT EXISTS motion_data(id INTEGER PRIMARY KEY AUTOINCREMENT,session_id TEXT,timestamp_s REAL,activity_level REAL,quality REAL,label TEXT);
CREATE TABLE IF NOT EXISTS symptoms(symptom_id TEXT PRIMARY KEY,patient_id TEXT,symptom_type TEXT,severity INTEGER,notes TEXT,logged_at REAL,label TEXT);
CREATE TABLE IF NOT EXISTS cycles(cycle_id TEXT PRIMARY KEY,patient_id TEXT,start_date REAL,end_date REAL,cycle_length_days INTEGER,usual_length_days INTEGER,irregularity TEXT,symptoms_json TEXT,notes TEXT,logged_at REAL,label TEXT);
CREATE TABLE IF NOT EXISTS doctor_notes(note_id TEXT PRIMARY KEY,patient_id TEXT,doctor_id TEXT,note_text TEXT,created_at REAL,updated_at REAL,is_private INTEGER);
CREATE TABLE IF NOT EXISTS reports(report_id TEXT PRIMARY KEY,patient_id TEXT,session_id TEXT,report_type TEXT,content_text TEXT,file_path TEXT,created_at REAL,created_by TEXT,label TEXT);
CREATE TABLE IF NOT EXISTS ultrasound_records(record_id TEXT PRIMARY KEY,patient_id TEXT,image_path TEXT,cyst_size_mm REAL,volume_cc REAL,morphology TEXT,quality REAL,source TEXT,confidence REAL,notes TEXT,created_at REAL,label TEXT);
CREATE TABLE IF NOT EXISTS model_results(result_id TEXT PRIMARY KEY,patient_id TEXT,session_id TEXT,module_name TEXT,module_version TEXT,signal TEXT,level TEXT,confidence REAL,data_quality REAL,clinical_validation TEXT,drivers_json TEXT,explanation TEXT,provenance_json TEXT,limitations TEXT,extra_json TEXT,created_at REAL,label TEXT);
CREATE TABLE IF NOT EXISTS analysis_results(analysis_id TEXT PRIMARY KEY,patient_id TEXT,session_id TEXT,fingerprint_json TEXT,circadian_json TEXT,autonomic_json TEXT,metabolic_json TEXT,longitudinal_json TEXT,created_at REAL,label TEXT);
CREATE TABLE IF NOT EXISTS profiles(profile_id TEXT PRIMARY KEY,patient_id TEXT,data_json TEXT,label TEXT,created_at REAL,updated_at REAL);
CREATE TABLE IF NOT EXISTS sensor_quality(id INTEGER PRIMARY KEY AUTOINCREMENT,session_id TEXT,timestamp_s REAL,channel TEXT,value REAL,quality REAL,source TEXT,artifact INTEGER,artifact_type TEXT,reason TEXT,label TEXT);
"""


# --------------------------------------------------------------------------- #
#  CLI
# --------------------------------------------------------------------------- #
def _cli() -> int:
    import argparse
    ap = argparse.ArgumentParser(description="ENDO-TWIN workstation database helper")
    ap.add_argument("--db", default=None)
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--seed", action="store_true", help="write a labelled synthetic demo cohort")
    ap.add_argument("--clear", action="store_true", help="delete every SYNTHETIC_DEMO row")
    a = ap.parse_args()
    api = WorkstationAPI(a.db)
    if a.seed:
        res = api.seed_demo()
        print(f"Seeded {len(res['seeded'])} participants and {len(res['doctors'])} clinicians "
              f"(label={DEMO_LABEL}) into {api.db_path}")
    if a.clear:
        res = api.clear_demo()
        print(f"Removed {res['removed_rows']} labelled demo rows from {api.db_path}")
    h = api.health()
    print(json.dumps(h, indent=2))
    if h["empty"]:
        print("\nDatabase has no patients yet — the workstation will show empty states.\n"
              "Run:  python3 workstation/api.py --seed    (or click 'Seed demo cohort' in the UI)")
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
