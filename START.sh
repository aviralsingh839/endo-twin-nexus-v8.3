#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "$0")" && pwd)"
mkdir -p "$ROOT/logs" "$ROOT/DIST/android" "$ROOT/data/bridge/inbox"
VENV="$ROOT/.venv/bin/python"
need(){ [[ -x "$VENV" ]] || { echo "ERROR: .venv missing. Run ./setup_garuda.sh"; exit 1; }; }
runpy(){ need; "$VENV" "$@"; }
menu(){
 while true; do
  clear 2>/dev/null || true
  cat <<'EOF'
============================================================
ENDO-TWIN V8.5
Personalized Physiological Modelling Platform
============================================================
  1) Doctor Workstation
  2) Patient Workstation
  3) ENDO-TWIN Platform
  4) Build Android APKs
  5) Setup Android SDK
  6) Run Tests
  7) Project Health
  8) Developer Control Center
  9) Exit
============================================================
EOF
  read -r -p "Select [1-9]: " choice || exit 0
  case "$choice" in
   1) runpy "$ROOT/desktop/doctor_app/main_enhanced.py" ;;
   2) runpy "$ROOT/desktop/patient_app/main.py" ;;
   3) runpy "$ROOT/apps/main/main_app.py" ;;
   4) "$ROOT/build_apks.sh" menu ;;
   5) "$ROOT/setup_android.sh" ;;
   6) need; "$VENV" -m pytest -q ;;
   7) "$ROOT/scripts/diagnostics/project_health.sh" ;;
   8) runpy "$ROOT/launcher/main.py" ;;
   9) exit 0 ;;
   *) echo "Invalid choice"; sleep 1 ;;
  esac
 done
}
MODE=""; [[ $# -ge 1 ]] && MODE="$1"; [[ -n "$MODE" ]] || MODE=menu
case "$MODE" in
 menu) menu ;;
 doctor|doctor-pc) runpy "$ROOT/desktop/doctor_app/main_enhanced.py" ;;
 patient|patient-pc) runpy "$ROOT/desktop/patient_app/main.py" ;;
 endo-twin|endo|general) runpy "$ROOT/apps/main/main_app.py" ;;
 gui|control-center) runpy "$ROOT/launcher/main.py" ;;
 build-apks|build) TARGET=""; [[ $# -ge 2 ]] && TARGET="$2"; [[ -n "$TARGET" ]] || TARGET=menu; "$ROOT/build_apks.sh" "$TARGET" ;;
 setup-android) "$ROOT/setup_android.sh" ;;
 setup) "$ROOT/setup_garuda.sh" ;;
 test|tests) need; "$VENV" -m pytest -q ;;
 test-cross) need; "$VENV" "$ROOT/tests/test_endo_twin_isolation.py"; [[ ! -f "$ROOT/tests/test_multi_patient_isolation.py" ]] || "$VENV" "$ROOT/tests/test_multi_patient_isolation.py" ;;
 health|project-health) "$ROOT/scripts/diagnostics/project_health.sh" ;;
 demo|showcase) runpy "$ROOT/demo/full_showcase.py" ;;
 research|lab) runpy -c 'from src.endo_twin.core.twin_core import EndoTwinCore; c=EndoTwinCore(); print("ENDO-TWIN",c.version)' ;;
 help|--help|-h) echo "Run ./START.sh for menu. Direct: doctor, patient-pc, endo-twin, build-apks, setup-android, test, health, gui." ;;
 *) echo "Unknown command: $MODE"; exit 2 ;;
esac
