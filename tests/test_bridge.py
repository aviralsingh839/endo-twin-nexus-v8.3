import json
import threading
import urllib.request
from pathlib import Path

from services.bridge.server import EndoTwinBridgeServer


def request(url, data=None, headers=None):
    payload = None if data is None else json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers=headers or {}, method="POST" if data is not None else "GET")
    with urllib.request.urlopen(req, timeout=3) as response:
        return response.status, json.loads(response.read().decode("utf-8"))


def test_bridge_pair_and_upload(tmp_path: Path):
    bridge = EndoTwinBridgeServer(tmp_path, port=0)
    bridge.start()
    try:
        port = bridge.server.server_address[1]
        endpoint = f"http://127.0.0.1:{port}"
        status, health = request(endpoint + "/v1/health")
        assert status == 200
        assert health["status"] == "ready"

        status, paired = request(endpoint + "/v1/pair", {"code": bridge.pair_code}, {"Content-Type": "application/json"})
        assert status == 200
        assert paired["paired"] is True
        token = paired["token"]

        payload = {
            "patient_id": "DEMO-001",
            "label": "DEMO_DATA",
            "provenance": "DEMO_DATA",
        }
        status, uploaded = request(
            endpoint + "/v1/upload",
            payload,
            {"Content-Type": "application/json", "X-Endo-Token": token},
        )
        assert status == 200
        assert uploaded["status"] == "received"
        assert bridge.received_count == 1
        files = list((tmp_path / "data" / "bridge" / "inbox").glob("*.json"))
        assert len(files) == 1
        assert json.loads(files[0].read_text(encoding="utf-8"))["label"] == "DEMO_DATA"
    finally:
        bridge.stop()
