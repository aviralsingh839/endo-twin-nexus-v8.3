#!/usr/bin/env python3
"""Bench simulator for the ENDO-TWIN wearable link.

Speaks the exact $CP2 protocol the ESP32-S3 firmware prints, over the Wi-Fi /
HTTP ingest route, so the whole chain (parse -> CRC -> calibration -> DSP ->
SQLite) can be exercised without hardware.

    python3 tools/simulate_wearable.py ETN-2041
    python3 tools/simulate_wearable.py ETN-2041 --seconds 30 --hr 88 --record
"""
import argparse, json, math, os, random, sys, time, urllib.error, urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "workstation"))
from signals import xor_crc  # noqa: E402


def post(base, path, payload):
    req = urllib.request.Request(base + path, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"}, method="POST")
    return json.loads(urllib.request.urlopen(req, timeout=15).read())


def frame(ms, pulse, temp_c, gsr_raw):
    body = ("$CP2,%d,%d,-1,0.0200,-0.0100,1.0000,0.100,0.050,0.020,%.2f,nan,%d,"
            "0,0.00,0.0,-1,-1,-1,nan,nan,nan,0,%u" % (ms, pulse, temp_c, gsr_raw, 1 << 12))
    return "%s,%02X" % (body, xor_crc(body))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("patient", nargs="?", default="ETN-2041")
    ap.add_argument("--base", default="http://127.0.0.1:8787")
    ap.add_argument("--seconds", type=float, default=12.0)
    ap.add_argument("--hr", type=float, default=74.0)
    ap.add_argument("--fs", type=float, default=50.0)
    ap.add_argument("--record", action="store_true", help="open a session and save rows to the database")
    a = ap.parse_args()

    try:
        post(a.base, "/api/device/connect", {"transport": "wifi", "name": "ENDO-TWIN-ESP32 (simulator)",
                                             "firmware": "ANALOG-PULSE v8.8", "patientId": a.patient})
    except urllib.error.URLError as e:
        sys.exit("cannot reach %s — start the workstation first (./START.sh)\n  %s" % (a.base, e))
    print("connected  transport=wifi  patient=%s" % a.patient)

    if a.record:
        sid = post(a.base, "/api/device/session/start", {"patientId": a.patient})["session"]["id"]
        print("recording  session=%s" % sid)

    total, sent, status = int(a.seconds * a.fs), 0, None
    for start in range(0, total, int(a.fs)):
        lines = []
        for i in range(min(int(a.fs), total - start)):
            t = (start + i) / a.fs
            ph = 2 * math.pi * (a.hr / 60.0) * t
            pulse = 2048 + 500 * math.sin(ph) + 170 * math.sin(2 * ph) + random.gauss(0, 16)
            lines.append(frame(int(t * 1000), int(pulse),
                               34.1 + 0.05 * math.sin(t / 30) + random.gauss(0, 0.01),
                               int(1380 + 40 * math.sin(t / 7) + random.gauss(0, 5))))
        status = post(a.base, "/api/device/ingest", {"lines": lines})["status"]
        sent += len(lines)
        print("  sent %4d frames   hr=%-6s temp=%-6s gsr=%-6s quality=%.2f" % (
            sent,
            round(status["live"]["hr_bpm"], 1) if status["live"].get("hr_bpm") else "—",
            status["live"].get("skin_temp_c") or "—",
            round(status["live"]["gsr_us"], 1) if status["live"].get("gsr_us") else "—",
            status.get("quality") or 0))
        time.sleep(0.05)

    print("packets=%d  badCrc=%d  spo2=%s" % (status["packets"], status["badCrc"],
                                              status["live"].get("spo2_pct") or "unavailable (single-channel sensor)"))
    if a.record:
        r = post(a.base, "/api/device/session/stop", {})
        print("saved      %d rows into session %s" % (r["rows"], r["session_id"]))
    post(a.base, "/api/device/disconnect", {})
    print("disconnected")


if __name__ == "__main__":
    main()
