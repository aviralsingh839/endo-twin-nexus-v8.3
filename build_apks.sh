#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "$0")" && pwd)"
setup(){ "$ROOT/setup_android.sh"; }
label(){ [[ "$1" == patient ]] && echo Patient || echo Doctor; }
apk(){ echo "$ROOT/DIST/android/ENDO-TWIN-$(label "$1")-debug.apk"; }
build_one(){ local app="$1"; setup; cd "$ROOT/android/$app"; chmod +x gradlew; ./gradlew assembleDebug --no-daemon; cd "$ROOT"; mkdir -p "$ROOT/DIST/android"; cp "$ROOT/android/$app/app/build/outputs/apk/debug/app-debug.apk" "$(apk "$app")"; echo "Built: $(apk "$app")"; }
install_one(){ local app="$1"; build_one "$app"; command -v adb >/dev/null 2>&1 || { echo "adb not found on PATH"; exit 1; }; adb install -r "$(apk "$app")"; }
menu(){ cat <<'EOF'
ENDO-TWIN Android Builder
  1) Build Patient APK
  2) Build Doctor APK
  3) Build both APKs
  4) Install Patient APK
  5) Install Doctor APK
  6) Clean Android builds
  7) Exit
EOF
read -r -p "Select [1-7]: " c
case "$c" in
 1) build_one patient ;;
 2) build_one doctor ;;
 3) build_one patient && build_one doctor ;;
 4) install_one patient ;;
 5) install_one doctor ;;
 6) (cd "$ROOT/android/patient" && ./gradlew clean --no-daemon); (cd "$ROOT/android/doctor" && ./gradlew clean --no-daemon) ;;
 7) exit 0 ;;
 *) echo "Invalid choice"; exit 2 ;;
esac
}
MODE="$1"; [[ -n "$MODE" ]] || MODE=menu
case "$MODE" in
 menu) menu ;;
 patient) build_one patient ;;
 doctor) build_one doctor ;;
 all) build_one patient && build_one doctor ;;
 install-patient) install_one patient ;;
 install-doctor) install_one doctor ;;
 clean) (cd "$ROOT/android/patient" && ./gradlew clean --no-daemon); (cd "$ROOT/android/doctor" && ./gradlew clean --no-daemon) ;;
 *) echo "Unknown target: $MODE"; exit 2 ;;
esac
