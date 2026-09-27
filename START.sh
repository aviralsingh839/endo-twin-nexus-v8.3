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
ENDO-TWIN NEXUS V9.0
Personal Twin • Wearable • Unified Workstation • Research
============================================================
  1) Self-Learning Model • Patients + Baselines
  2) Unified Workstation + Wearable
  3) Doctor Workstation
  4) Patient Workstation
  5) ENDO-TWIN Platform
  6) Website / Research Portal
  7) Run Tests
  8) Project Health
  9) Developer Control Center
 10) Exit
============================================================
EOF
  read -r -p "Select [1-10]: " choice || exit 0
  case "$choice" in
   1) runpy -m src.personal_twin.self_learning_app ;;
   2) runpy "$ROOT/desktop/unified_workstation.py" ;;
   3) runpy "$ROOT/desktop/doctor_app/main_enhanced.py" ;;
   4) runpy "$ROOT/desktop/patient_app/main.py" ;;
   5) runpy "$ROOT/apps/main/main_app.py" ;;
   6) bash "$ROOT/LAUNCH/WEBSITE.sh" ;;
   7) need; "$VENV" -m pytest -q ;;
   8) "$ROOT/scripts/diagnostics/project_health.sh" ;;
   9) runpy "$ROOT/launcher/main.py" ;;
  10) exit 0 ;;
   *) echo "Invalid choice"; sleep 1 ;;
  esac
 done
}

MODE=""; [[ $# -ge 1 ]] && MODE="$1"
if [[ -z "$MODE" ]]; then
  menu
  exit 0
fi
case "$MODE" in
 menu) menu ;;
 self-learning|personal-twin) runpy -m src.personal_twin.self_learning_app ;;
 onboard|profile) runpy -m src.personal_twin.onboarding ;;
 unified|workstation) runpy "$ROOT/desktop/unified_workstation.py" ;;
 doctor|doctor-pc) runpy "$ROOT/desktop/doctor_app/main_enhanced.py" ;;
 patient|patient-pc) runpy "$ROOT/desktop/patient_app/main.py" ;;
 endo-twin|endo|general) runpy "$ROOT/apps/main/main_app.py" ;;
 website|web|site) bash "$ROOT/LAUNCH/WEBSITE.sh" ;;
 gui|control-center) runpy "$ROOT/launcher/main.py" ;;
 build-apks|build) echo "Android build scripts retained; wearable-first workflow is desktop." ; TARGET=""; [[ $# -ge 2 ]] && TARGET="$2"; [[ -n "$TARGET" ]] || TARGET=menu; "$ROOT/build_apks.sh" "$TARGET" ;;
 setup-android) "$ROOT/setup_android.sh" ;;
 setup) "$ROOT/setup_garuda.sh" ;;
 test|tests) need; "$VENV" -m pytest -q ;;
 test-cross) need; "$VENV" "$ROOT/tests/test_endo_twin_isolation.py"; [[ ! -f "$ROOT/tests/test_multi_patient_isolation.py" ]] || "$VENV" "$ROOT/tests/test_multi_patient_isolation.py" ;;
 health|project-health) "$ROOT/scripts/diagnostics/project_health.sh" ;;
 demo|showcase) runpy "$ROOT/demo/full_showcase.py" ;;
 research|lab) runpy -c 'from src.endo_twin.core.twin_core import EndoTwinCore; c=EndoTwinCore(); print("ENDO-TWIN",c.version)' ;;
 help|--help|-h) echo "Run ./START.sh for the menu. Self-learning collects patient details and person-specific baselines. Direct: self-learning, unified, doctor, patient-pc, endo-twin, website, test, health, gui." ;;
 *) echo "Unknown command: $MODE"; exit 2 ;;
esac
