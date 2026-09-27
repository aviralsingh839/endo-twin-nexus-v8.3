#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "$0")" && pwd)"
mkdir -p "$ROOT/logs" "$ROOT/DIST/android" "$ROOT/data/bridge/inbox"
VENV="$ROOT/.venv/bin/python"
INTERACTIVE=0

# Build the virtualenv on demand instead of dead-ending the user.
make_venv(){
  echo "Creating .venv and installing requirements (this takes a few minutes)..."
  python3 -m venv "$ROOT/.venv" || { echo "Could not create .venv - is python3-venv installed?"; return 1; }
  "$ROOT/.venv/bin/python" -m pip install --upgrade pip || return 1
  "$ROOT/.venv/bin/python" -m pip install -r "$ROOT/requirements.txt" || return 1
  echo "Environment ready."
}

need(){
  [[ -x "$VENV" ]] && return 0
  echo
  echo "The Python environment (.venv) has not been created yet."
  echo "Everything in this launcher needs it: PySide6, numpy, pandas, scikit-learn, pyserial."
  if [[ "$INTERACTIVE" == "1" ]]; then
    read -r -p "Create it now? [Y/n] " yn
    if [[ ! "$yn" =~ ^([nN]|[nN][oO])$ ]]; then make_venv && return 0; fi
    echo "Skipped. Run ./setup_garuda.sh (or ./START.sh setup) when you are ready."
    return 1
  fi
  echo "Run:  ./setup_garuda.sh      (or ./START.sh setup)"
  return 1
}

runpy(){ need || return 1; "$VENV" "$@"; }

# Run a menu entry without letting a failure tear down the whole launcher.
try(){
  if "$@"; then return 0; fi
  local code=$?
  echo
  echo "That option exited with status $code."
  return 0
}
pause(){ [[ "$INTERACTIVE" == "1" ]] && read -r -p "Press Enter to return to the menu... " _ || true; }

menu(){
 INTERACTIVE=1
 while true; do
  clear 2>/dev/null || true
  cat <<'EOF'
============================================================
ENDO-TWIN NEXUS V8.7
Unified Scientific Workstation • Patient + Doctor + Research + Live Sensor
============================================================
  1) Unified Workstation (Patient + Doctor + Prototype Lab)
  2) Doctor Workstation
  3) Patient Workstation
  4) ENDO-TWIN Platform
  5) Website / Research Portal
  6) Build Android APKs
  7) Android Build Diagnostics
  8) Run Tests
  9) Project Health
 10) Developer Control Center
 11) Exit
============================================================
EOF
  read -r -p "Select [1-11]: " choice || exit 0
  case "$choice" in
   1) try runpy -m src.ui.main_window; pause ;;
   2) try runpy "$ROOT/desktop/doctor_app/main_enhanced.py"; pause ;;
   3) try runpy "$ROOT/desktop/patient_app/main.py"; pause ;;
   4) try runpy "$ROOT/apps/main/main_app.py"; pause ;;
   5) try bash "$ROOT/LAUNCH/WEBSITE.sh"; pause ;;
   6) try bash "$ROOT/BUILD_ALL_APKS.sh"; pause ;;
   7) try bash "$ROOT/scripts/diagnostics/android.sh"; pause ;;
   8) if need; then try "$VENV" -m pytest -q; fi; pause ;;
   9) try bash "$ROOT/scripts/diagnostics/project_health.sh"; pause ;;
  10) try runpy "$ROOT/launcher/main.py"; pause ;;
  11) exit 0 ;;
   *) echo "Invalid choice"; sleep 1 ;;
  esac
 done
}

MODE=""; [[ $# -ge 1 ]] && MODE="$1"; [[ -n "$MODE" ]] || MODE=menu
case "$MODE" in
 menu) menu ;;
 unified|workstation) runpy -m src.ui.main_window ;;
 doctor|doctor-pc) runpy "$ROOT/desktop/doctor_app/main_enhanced.py" ;;
 patient|patient-pc) runpy "$ROOT/android/patient_app/main.py" ;;
 endo-twin|endo|general) runpy "$ROOT/apps/main/main_app.py" ;;
 website|web|site) bash "$ROOT/LAUNCH/WEBSITE.sh" ;;
 gui|control-center) runpy "$ROOT/launcher/main.py" ;;
 build-apks|build) TARGET=""; [[ $# -ge 2 ]] && TARGET="$2"; [[ -n "$TARGET" ]] || TARGET=all
    case "$TARGET" in
      patient) bash "$ROOT/BUILD_PATIENT_APK.sh" ;;
      doctor)  bash "$ROOT/BUILD_DOCTOR_APK.sh" ;;
      *)       bash "$ROOT/BUILD_ALL_APKS.sh" ;;
    esac ;;
 setup-android|android-check) bash "$ROOT/scripts/diagnostics/android.sh" ;;
 setup) "$ROOT/setup_garuda.sh" ;;
 test|tests) need && "$VENV" -m pytest -q ;;
 test-cross) need && "$VENV" "$ROOT/tests/test_endo_twin_isolation.py"; [[ ! -f "$ROOT/tests/test_multi_patient_isolation.py" ]] || "$VENV" "$ROOT/tests/test_multi_patient_isolation.py" ;;
 health|project-health) "$ROOT/scripts/diagnostics/project_health.sh" ;;
 demo|showcase) runpy "$ROOT/demo/full_showcase.py" ;;
 research|lab) runpy -c 'from src.endo_twin.core.twin_core import EndoTwinCore; c=EndoTwinCore(); print("ENDO-TWIN",c.version)' ;;
 help|--help|-h) echo "Run ./START.sh for the menu. Direct targets: setup, unified, doctor, patient-pc, endo-twin, website, build-apks [patient|doctor|all], android-check, test, health, gui, demo." ;;
 *) echo "Unknown command: $MODE"; exit 2 ;;
esac
