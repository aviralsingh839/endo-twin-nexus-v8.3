"""Run CHRONO-TWIN NEXUS V8.3 in demo mode."""
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from src.app import main

if __name__ == "__main__":
    raise SystemExit(main(["--demo"]))
