#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "$0")" && pwd)"
A="$(printenv ANDROID_SDK_ROOT 2>/dev/null || true)"
B="$(printenv ANDROID_HOME 2>/dev/null || true)"
find_sdk(){ local c; for c in "$A" "$B" "$HOME/Android/Sdk" "$HOME/.android/sdk" "/opt/android-sdk"; do if [[ -n "$c" && -d "$c" ]]; then echo "$c"; return 0; fi; done; return 1; }
SDK="$(find_sdk || true)"
[[ -n "$SDK" ]] || { echo "Android SDK not found. Install Android Studio/command-line tools or set ANDROID_SDK_ROOT."; exit 1; }
echo "ENDO-TWIN Android SDK: $SDK"
for app in patient doctor; do printf 'sdk.dir=%s\n' "$SDK" > "$ROOT/android/$app/local.properties"; done
[[ -d "$SDK/platforms/android-34" ]] || echo "WARNING: API 34 platform missing."
[[ -d "$SDK/build-tools/34.0.0" ]] || echo "WARNING: build-tools 34.0.0 missing."
[[ -x "$SDK/platform-tools/adb" ]] || echo "WARNING: adb missing."
echo "Android projects prepared."
