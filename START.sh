#!/usr/bin/env bash
# ============================================================
# ENDO-TWIN NEXUS V8.7 — launcher
#
#   ./START.sh              -> Unified Workstation (web UI: Patient + Doctor)
#   ./START.sh menu         -> full text menu (desktop apps, builds, tests)
#   ./START.sh ui [port]    -> same as default, optional port
#   ./START.sh doctor       -> PySide6 doctor desktop app
#   ./START.sh patient      -> PySide6 patient desktop app
#   ./START.sh help         -> all commands
# ============================================================
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "$0")" && pwd)"
mkdir -p "$ROOT/logs" "$ROOT/DIST/android" "$ROOT/data/bridge/inbox"
VENV="$ROOT/.venv/bin/python"
need(){ [[ -x "$VENV" ]] || { echo "ERROR: .venv missing. Run ./setup_garuda.sh"; exit 1; }; }
runpy(){ need; "$VENV" "$@"; }

# ---- Unified Workstation (web) -----------------------------------------
PY="$(command -v python3 || command -v python || true)"
workstation(){
  [[ -n "$PY" ]] || { echo "ERROR: python3 not found in PATH"; exit 1; }
  local port="${1:-${ENDOTWIN_PORT:-8787}}"
  echo "Starting ENDO-TWIN NEXUS Unified Workstation on port ${port} ..."
  exec "$PY" "$ROOT/workstation/serve.py" --port "$port" --host "${ENDOTWIN_HOST:-0.0.0.0}"
}

menu(){
 while true; do
  clear 2>/dev/null || true
  cat <<'EOF'
============================================================
ENDO-TWIN NEXUS V8.7
Unified Scientific Workstation • Patient + Doctor + Research + Live Sensor
============================================================
  1) Unified Workstation  (WEB UI — Patient + Doctor, one console)  ★
  2) Unified Workstation  (PySide6 desktop)
  3) Doctor Workstation   (PySide6 desktop)
  4) Patient Workstation  (PySide6 desktop)
  5) ENDO-TWIN Platform
  6) Website / Research Portal
  7) Build Android APKs
  8) Setup Android SDK
  9) Run Tests
 10) Project Health
 11) Developer Control Center
 12) Exit
============================================================
EOF
  read -r -p "Select [1-12]: " choice || exit 0
  case "$choice" in
   1) workstation ;;
   2) runpy -m src.ui.main_window ;;
   3) runpy "$ROOT/desktop/doctor_app/main_enhanced.py" ;;
   4) runpy "$ROOT/desktop/patient_app/main.py" ;;
   5) runpy "$ROOT/apps/main/main_app.py" ;;
   6) bash "$ROOT/LAUNCH/WEBSITE.sh" ;;
   7) "$ROOT/build_apks.sh" menu ;;
   8) "$ROOT/setup_android.sh" ;;
   9) need; "$VENV" -m pytest -q ;;
  10) "$ROOT/scripts/diagnostics/project_health.sh" ;;
  11) runpy "$ROOT/launcher/main.py" ;;
  12) exit 0 ;;
   *) echo "Invalid choice"; sleep 1 ;;
  esac
 done
}

MODE=""; [[ $# -ge 1 ]] && MODE="$1"; [[ -n "$MODE" ]] || MODE=workstation
case "$MODE" in
 ui|web|workstation|unified-web|dashboard|nexus) shift || true; workstation "${1:-}" ;;
 menu) menu ;;
 unified|desktop) runpy -m src.ui.main_window ;;
 doctor|doctor-pc) runpy "$ROOT/desktop/doctor_app/main_enhanced.py" ;;
 patient|patient-pc) runpy "$ROOT/desktop/patient_app/main.py" ;;
 endo-twin|endo|general) runpy "$ROOT/apps/main/main_app.py" ;;
 website|web-site|site) bash "$ROOT/LAUNCH/WEBSITE.sh" ;;
 gui|control-center) runpy "$ROOT/launcher/main.py" ;;
 build-apks|build) TARGET=""; [[ $# -ge 2 ]] && TARGET="$2"; [[ -n "$TARGET" ]] || TARGET=menu; "$ROOT/build_apks.sh" "$TARGET" ;;
 setup-android) "$ROOT/setup_android.sh" ;;
 setup) "$ROOT/setup_garuda.sh" ;;
 test|tests) need; "$VENV" -m pytest -q ;;
 test-cross) need; "$VENV" "$ROOT/tests/test_endo_twin_isolation.py"; [[ ! -f "$ROOT/tests/test_multi_patient_isolation.py" ]] || "$VENV" "$ROOT/tests/test_multi_patient_isolation.py" ;;
 health|project-health) "$ROOT/scripts/diagnostics/project_health.sh" ;;
 demo|showcase) runpy "$ROOT/demo/full_showcase.py" ;;
 research|lab) runpy -c 'from src.endo_twin.core.twin_core import EndoTwinCore; c=EndoTwinCore(); print("ENDO-TWIN",c.version)' ;;
 help|--help|-h)
   cat <<'EOF'
ENDO-TWIN NEXUS launcher

  ./START.sh                 Unified Workstation web UI (Patient + Doctor) on :8787
  ./START.sh ui 9000         same, on port 9000
  ./START.sh menu            interactive menu (desktop apps, builds, tests)
  ./START.sh unified         PySide6 unified desktop window
  ./START.sh doctor          PySide6 doctor desktop app
  ./START.sh patient         PySide6 patient desktop app
  ./START.sh endo-twin       ENDO-TWIN platform app
  ./START.sh website         marketing / research portal
  ./START.sh build-apks      Android APK builds
  ./START.sh test | health   pytest / project health

Environment: ENDOTWIN_PORT, ENDOTWIN_HOST, ENDOTWIN_NO_BROWSER=1
EOF
   ;;
 *) echo "Unknown command: $MODE (try ./START.sh help)"; exit 2 ;;
esac
