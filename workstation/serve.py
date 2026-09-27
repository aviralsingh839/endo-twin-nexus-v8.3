#!/usr/bin/env python3
"""
ENDO-TWIN NEXUS — Unified Workstation (web UI) static server.

Serves workstation/ on http://<host>:<port>/ with no-cache headers so edits
show up immediately. Dependency-free: Python 3 standard library only.

Usage:
    python3 workstation/serve.py [--port 8787] [--host 0.0.0.0] [--no-browser]
"""
from __future__ import annotations

import argparse
import contextlib
import http.server
import json
import os
import socket
import socketserver
import sys
import threading
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

try:
    from api import WorkstationAPI          # real SQLite-backed data layer
    API = WorkstationAPI()
    API_ERROR = None
except Exception as exc:                    # pragma: no cover - UI still works in demo mode
    API, API_ERROR = None, str(exc)


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    # ----------------------------- API routing -------------------------- #
    def _is_api(self) -> bool:
        return self.path.split("?")[0].startswith("/api")

    def _read_body(self):
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = 0
        if not length:
            return {}
        try:
            return json.loads(self.rfile.read(length).decode("utf-8") or "{}")
        except Exception:
            return {}

    def _api(self, method: str):
        path = self.path.split("?")[0]
        body = self._read_body() if method in ("POST", "PUT", "PATCH", "DELETE") else {}
        if API is None:
            status, payload = 503, {"error": "data layer unavailable", "detail": API_ERROR}
        else:
            status, payload = API.handle(method, path, body)
        raw = json.dumps(payload, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if self._is_api():
            return self._api("GET")
        return super().do_GET()

    def do_HEAD(self):
        if self._is_api():
            return self._api("GET")
        return super().do_HEAD()

    def do_POST(self):
        return self._api("POST") if self._is_api() else self.send_error(405)

    def do_PUT(self):
        return self._api("PUT") if self._is_api() else self.send_error(405)

    def do_PATCH(self):
        return self._api("PATCH") if self._is_api() else self.send_error(405)

    def do_DELETE(self):
        return self._api("DELETE") if self._is_api() else self.send_error(405)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("X-Content-Type-Options", "nosniff")
        super().end_headers()

    def log_message(self, fmt, *args):  # quieter, still useful
        sys.stdout.write("  %s - %s\n" % (self.address_string(), fmt % args))
        sys.stdout.flush()


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def free_port(host: str, port: int, tries: int = 20) -> int:
    for candidate in range(port, port + tries):
        with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind((host, candidate))
                return candidate
            except OSError:
                continue
    raise SystemExit(f"ERROR: no free port in range {port}-{port + tries}")


def main() -> int:
    ap = argparse.ArgumentParser(description="ENDO-TWIN NEXUS unified workstation server")
    ap.add_argument("--port", type=int, default=int(os.environ.get("ENDOTWIN_PORT", 8787)))
    ap.add_argument("--host", default=os.environ.get("ENDOTWIN_HOST", "0.0.0.0"))
    ap.add_argument("--no-browser", action="store_true", help="do not open a browser window")
    args = ap.parse_args()

    port = free_port(args.host, args.port)
    url = f"http://localhost:{port}/"

    print("=" * 62)
    print("  ENDO-TWIN NEXUS V8.7 — Unified Workstation")
    print("  Patient + Doctor in one console (switch from the top-right)")
    print("=" * 62)
    print(f"  Serving : {ROOT}")
    print(f"  URL     : {url}")
    if API is not None:
        h = API.health()
        c = h["counts"]
        print(f"  Database: {h['db']}")
        print(f"  Records : {c['patients']} patients · {c['providers']} providers · "
              f"{c['sensor_sessions']} sessions · {c['hrv_data'] + c['ppg_data']} sensor rows")
        if h["empty"]:
            print("  NOTE    : database has no patients yet -> the UI shows empty states.")
            print("            Seed a labelled demo cohort:  python3 workstation/api.py --seed")
    else:
        print(f"  Database: UNAVAILABLE ({API_ERROR}) -> UI falls back to built-in demo data")
    if args.host not in ("127.0.0.1", "localhost"):
        print(f"  LAN     : http://{socket.gethostbyname(socket.gethostname())}:{port}/")
    print("  Stop    : Ctrl+C")
    print("=" * 62)

    if not args.no_browser and os.environ.get("ENDOTWIN_NO_BROWSER") != "1":
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()

    with Server((args.host, port), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n  Workstation stopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
