"""Application entry point for CHRONO-TWIN NEXUS V8.3."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PySide6.QtWidgets import QApplication
from src.ui.main_window import MainWindow


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="CHRONO-TWIN NEXUS V8.3 offline dashboard")
    parser.add_argument("--demo", action="store_true", help="start synthetic demo stream")
    parser.add_argument("--port", type=str, default=None, help="Arduino serial port, e.g. COM5 or /dev/ttyACM0")
    parser.add_argument("--net", type=str, default=None, help="ESP32-S3 wearable TCP host:port, e.g. 192.168.4.1:7777")
    parser.add_argument("--scenario", type=str, default=None, help="Load a synthetic scenario on start")
    args = parser.parse_args(argv)

    app = QApplication(sys.argv)
    win = MainWindow(start_demo=args.demo, port=args.port, net=args.net)
    if args.scenario:
        win._load_scenario(args.scenario)
    win.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
