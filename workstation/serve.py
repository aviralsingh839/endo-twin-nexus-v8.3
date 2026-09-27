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
import os
import socket
import socketserver
import sys
import threading
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

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
