# Garuda Launch Guide - CHRONO-PCOS V8.3+

## Overview

Garuda Linux is Arch-based, uses Dolphin file manager, supports double-click .sh launchers with executable permission.

Project supports:

- Root: `COMPLETE_LAUNCHER.sh`, `SETUP.sh`, `DIAGNOSTICS.sh`, `BUILD_*.sh`
- `LAUNCH/`: 20+ individual launchers + SETUP + BUILD + setup_garuda.sh
- `launchers/`: Same as LAUNCH/ for compatibility
- `launcher/main.py`: Complete Control Center GUI 1450x950 polished
- Direct Python: `python launcher/main.py`, `python desktop/doctor_app/main_enhanced.py`, etc

All launchers auto-detect project root, use .venv/bin/python if available, log to logs/, work from any directory.

## Double-Click Launch - Garuda/Dolphin

### First Time Setup

1. Open Dolphin
2. Navigate to CHRONO-PCOS V8.3+ folder
3. Right-click `LAUNCH/SETUP.sh` → Properties → Permissions → Is executable → Checked → OK
4. Double-click `LAUNCH/SETUP.sh` → If asks Run/Display/Cancel → Run → Terminal shows 10-step setup
5. Wait for .venv creation, PySide6 install (80.1MB+175.1MB), diagnostics PASS 7

### Complete Control Center

1. Double-click `LAUNCH/COMPLETE_LAUNCHER.sh` or `COMPLETE_LAUNCHER.sh` in root
2. Control Center GUI appears 1450x950 min 1200x800
3. Header gradient #0f172a #1e293b title 32px bold white subtitle 18px #cbd5e1 tagline 14px #0ea5e9 disclaimer #fbbf24
4. Status overview grid 4 cols cards 200x60 max80 left border 4px color PASS green #10b981 WARN orange #f59e0b FAIL red #ef4444
5. Categories PATIENT/DOCTOR/SCIENCE/CARE/DATA/PUBLIC/SYSTEM/ANDROID APK BUILD
6. Each category GroupBox border #cbd5e1 bg #f8fafc grid 3 cols spacing 12
7. AppCard Frame min 320x180 max 400x220 Expanding Fixed border 2px color radius 12px hover #0ea5e9 bg #f8fafc
   - Title WordWrap minHeight 30 14px bold #0f172a
   - Description WordWrap min 40 max 60 11px #64748b
   - Status WordWrap min 30 10px color with detail[:50] tooltip full detail
   - Button minHeight 36 12px bold #0ea5e9 radius 6px OPEN XXX
   - Tooltip launcher details
8. Footer #0f172a wrapping project root logs DIST website
9. Info footer #f8fafc border Dolphin instructions
10. Scroll area widgetResizable main_layout margins 20 spacing 16 responsive no clipped text overlapping
11. Click any OPEN button → launches corresponding .sh non-blocking Popen logs to logs/launcher.log

### Individual Launchers

Double-click any in `LAUNCH/`:

- `PATIENT_APP.sh` - Patient App PC demo Dashboard/Profile/Measurements/Symptoms/Cycle/Results/Reports/Sharing/Find Care Kivy
- `PATIENT_ANDROID.sh` - Patient Android APK build workflow, PC demo if APK not built, touch-friendly mobile UI
- `DOCTOR_PC.sh` - Doctor PC full workstation Dashboard/Patient Management/Physiological/Advanced/Ultrasound/Longitudinal/Notes/Reports PySide6 1450x950 polished
- `DOCTOR_ANDROID.sh` - Doctor Android mobile review patient list/search/profiles/recent/trends/screening/ultrasound/reports/notes/follow-up
- `SCIENTIFIC_CORE.sh` - Scientific Core main dashboard sensor quality signal processing feature extraction baseline longitudinal disease modules fusion
- `FULL_SHOWCASE.sh` - 16 steps demo with NEXT/SKIP/EXIT real operations DEMO/SIMULATED labeled
- `AI_ML.sh` - AI/ML Laboratory PCOS Sleep Cardiometabolic Autonomic risk signals only confidence limitations NOT ESTABLISHED
- `ULTRASOUND.sh` - Ultrasound research pipeline loading preprocessing quality segmentation inference visualization no invented accuracy
- `CHRONO_METABOLIC.sh` - Chrono-metabolic fingerprinting circadian autonomic variability activity temp metabolic longitudinal provenance
- `SIGNAL_PROCESSING.sh` - Filtering baseline removal artifact detection missing handling quality control feature extraction
- `CARE_FINDER.sh` - FIND CARE map/list distance/specialty/address/hours/services/contact/directions/verification OSM no API key demo clearly marked
- `DATABASE.sh` - 18 tables local-first SQLite users patients profiles symptoms cycles sensor sessions PPG/HRV/GSR/motion/temp/quality ultrasound model_results reports providers supplies audit access
- `REPORTS.sh` - Professional reports Research / risk-screening output — not a medical diagnosis model transparency
- `WEBSITE.sh` - Public scientific website Home Problem How it Works Technology Patient App Doctor App Care Discovery Research Benefits Safety Privacy Documentation
- `DIAGNOSTICS.sh` - System check actual checks PASS/WARN/FAIL never fake
- `SETUP.sh` - Environment setup 10 steps
- `BUILD_PATIENT_APK.sh` - Check prerequisites python pip buildozer kivy java SDK NDK build APK to DIST/android/CHRONO_PCOS_Patient.apk logs/build_patient_apk.log honest reporting
- `BUILD_DOCTOR_APK.sh` - Same for doctor
- `BUILD_ALL_APKS.sh` - Wrapper both

All launchers:

- Detect project root via SCRIPT_DIR PROJECT_ROOT BASE_NAME LAUNCH/launchers/ handling
- Use .venv/bin/python if available else python3
- Log to logs/
- Work from any directory (cd to project root)
- Show console output if run in terminal
- Show GUI if PySide6 available, fallback console if not
- Handle libGL missing gracefully console fallback

### Dolphin Settings

If Dolphin asks "What do you want to do with this file?" every time:

Dolphin → Settings → Configure Dolphin → General → Confirmations → Uncheck "Ask what to do" or Set Executable files → Run

Or:

System Settings → Applications → File Associations → application/x-shellscript → Add → Run

## Terminal Launch

```bash
cd chrono-pcos-v8.1

# Setup
./setup_garuda.sh
./SETUP.sh
./LAUNCH/SETUP.sh

# Complete Control Center
./COMPLETE_LAUNCHER.sh
./LAUNCH/COMPLETE_LAUNCHER.sh
python launcher/main.py

# Individual
./LAUNCH/DOCTOR_PC.sh
./LAUNCH/PATIENT_APP.sh
./LAUNCH/FULL_SHOWCASE.sh
./LAUNCH/WEBSITE.sh
./LAUNCH/DIAGNOSTICS.sh
./LAUNCH/BUILD_PATIENT_APK.sh --check-only
./LAUNCH/BUILD_DOCTOR_APK.sh --check-only
./LAUNCH/BUILD_ALL_APKS.sh

# Direct Python
.venv/bin/python launcher/main.py
.venv/bin/python desktop/doctor_app/main_enhanced.py
.venv/bin/python android/patient_app/main.py
.venv/bin/python demo/full_showcase.py

# Diagnostics
./DIAGNOSTICS.sh
./LAUNCH/DIAGNOSTICS.sh
```

## Project Root Detection

All launchers handle being in:

- Project root: `COMPLETE_LAUNCHER.sh` → PROJECT_ROOT = SCRIPT_DIR
- LAUNCH/: `LAUNCH/DOCTOR_PC.sh` → BASE_NAME = LAUNCH → PROJECT_ROOT = SCRIPT_DIR/..
- launchers/: `launchers/DOCTOR_PC.sh` → same
- Any subdirectory: via SCRIPT_DIR/.. logic

Example:

```bash
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
BASE_NAME="$(basename "$SCRIPT_DIR")"
if [[ "$BASE_NAME" == "LAUNCH" || "$BASE_NAME" == "launchers" || "$BASE_NAME" == "launcher" ]]; then
    PROJECT_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
fi
cd "$PROJECT_ROOT"
```

## .venv Handling

Launchers check:

```bash
if [[ -f ".venv/bin/python" ]]; then
    PYTHON=".venv/bin/python"
else
    PYTHON="python3"
fi
$PYTHON launcher/main.py
```

If .venv missing, show FAIL .venv Not found - run SETUP.sh, still try system python.

## Logs

- `logs/launcher.log` - Control Center launches
- `logs/build_patient_apk.log` - Patient APK build
- `logs/build_doctor_apk.log` - Doctor APK build
- `logs/build_all_apks.log` - All APKs
- `logs/diagnostics.log` - Diagnostics
- `logs/setup_garuda.log` - Setup

All logs mkdir -p logs created by setup_garuda.sh and BUILD scripts.

## DIST Output

- `DIST/android/CHRONO_PCOS_Patient.apk` - Patient APK if built
- `DIST/android/CHRONO_PCOS_Doctor.apk` - Doctor APK if built
- `DIST/android/.gitkeep` - Placeholder tracked

Created by setup_garuda.sh and BUILD scripts mkdir -p DIST/android.

## Permissions

```bash
chmod +x *.sh
chmod +x LAUNCH/*.sh
chmod +x launchers/*.sh
```

Setup does this automatically.

## Why Garuda?

Garuda Linux is Arch-based, gaming/performance oriented, supports:

- PySide6 with libGL available (unlike Debian container where libGL missing causes fallback console)
- Android SDK/NDK via pacman
- Python 3.11+
- Dolphin double-click launch
- Modern hardware

On Garuda, Control Center GUI launches polished, no libGL error, all diagnostics PASS except APKs WARN if SDK not installed.

On Debian container (current build env), libGL missing causes PySide6 GUI fails console fallback works, APKs WARN not built honest reporting - expected.

## Troubleshooting

- `libGL.so.1: cannot open shared object file`: `sudo pacman -S libgl` (Garuda) or `sudo apt install libgl1` (Debian), on Garuda libgl available
- `Permission denied`: `chmod +x LAUNCH/*.sh`
- `Dolphin asks Run/Display/Cancel`: Choose Run, or configure Dolphin to auto Run
- `.sh not executable`: Right-click → Properties → Permissions → Is executable checked
- `ModuleNotFoundError`: Run `./setup_garuda.sh`
- `APK not built`: Expected without Android SDK/NDK, PC demo available

See docs/TROUBLESHOOTING.md

## Safety

Research prototype not medical diagnosis, local-first offline privacy-focused, no cloud upload, no prescription sales, no treatment decisions, encourage professional consultation.
