#!/usr/bin/env python3
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
from desktop.doctor_app.main_enhanced import EnhancedDoctorApp
def main():
    if "--test-mode" in sys.argv:
        from desktop.doctor_app.test_workstation import launch_gui
        raise SystemExit(launch_gui())
    app = EnhancedDoctorApp()
    try:
        import PySide6
        app.run_gui()
    except Exception as e:
        print(f"GUI failed: {e}, running console demo")
        app.run_console_demo()
if __name__ == "__main__":
    main()
