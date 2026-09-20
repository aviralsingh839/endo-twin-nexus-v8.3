# Troubleshooting - CHRONO-PCOS V8.3+

## Common Issues

### libGL.so.1: cannot open shared object file

```
ImportError: libGL.so.1: cannot open shared object file: No such file or directory
```

Cause: Container missing libGL, PySide6 GUI fails, console fallback works.

On Garuda with libGL will succeed, diagnostics still PASS because pip package present.

Fix:

Garuda/Arch:
```bash
sudo pacman -S libgl qt6-base
```

Debian/Ubuntu:
```bash
sudo apt install libgl1 libxcb-cursor0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 libxcb-xinerama0 libxcb-xfixes0
```

Then:
```bash
./setup_garuda.sh
./LAUNCH/COMPLETE_LAUNCHER.sh
```

Console fallback works even without libGL.

### ID_LIKE: unbound variable

```
setup_garuda.sh: line 68: ID_LIKE: unbound variable
```

Cause: set -u + . /etc/os-release where ID_LIKE may be empty on Debian.

Fixed in setup_garuda.sh with `${ID:-} ${ID_LIKE:-} ${NAME:-}` guards.

If still occurs, update setup_garuda.sh:

```bash
. /etc/os-release
ID="${ID:-}"
ID_LIKE="${ID_LIKE:-}"
NAME="${NAME:-}"
```

Then:
```bash
./setup_garuda.sh
```

### ModuleNotFoundError: No module named 'PySide6'

```
ModuleNotFoundError: No module named 'PySide6'
```

Fix:
```bash
./setup_garuda.sh
# Or
python -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
.venv/bin/python -c "import PySide6; print(PySide6.__version__)"
```

### ModuleNotFoundError: No module named 'kivy'

```
ModuleNotFoundError: No module named 'kivy'
```

Fix:
```bash
.venv/bin/pip install kivy
# Or
pip install kivy
python -c "import kivy; print(kivy.__version__)"
```

### Permission denied

```
bash: ./LAUNCH/DOCTOR_PC.sh: Permission denied
```

Fix:
```bash
chmod +x *.sh
chmod +x LAUNCH/*.sh
chmod +x launchers/*.sh
chmod +x BUILD_*.sh
chmod +x LAUNCH/BUILD*.sh
./setup_garuda.sh  # Does chmod automatically
```

### Dolphin asks Run/Display/Cancel

Garuda/Dolphin file manager asks what to do with .sh file.

Fix:

- Choose Run
- Or set Dolphin to auto Run:

Dolphin → Settings → Configure Dolphin → General → Executable files → Run

Or:

System Settings → Applications → File Associations → application/x-shellscript → Add → Run

Or use terminal:

```bash
./LAUNCH/COMPLETE_LAUNCHER.sh
```

### .sh not executable

Right-click .sh → Properties → Permissions → Is executable → Checked → OK

Or:
```bash
chmod +x LAUNCH/*.sh
```

### .venv not found

```
FAIL .venv Not found - run SETUP.sh
```

Fix:
```bash
./setup_garuda.sh
# Or
./SETUP.sh
# Or
./LAUNCH/SETUP.sh
```

### Android APK not built

```
WARN APK not built - use BUILD scripts
⚠ No APK found in android/patient_app/bin/
DIST/android/ empty
```

Expected without Android SDK/NDK, honest reporting not fake.

Fix:

- PC demo available via PATIENT_ANDROID.sh, DOCTOR_ANDROID.sh
- For actual APK building, install Android SDK/NDK:

See docs/ANDROID_BUILD_GUIDE.md

```bash
sudo pacman -S jdk-openjdk android-tools android-sdk android-ndk
export ANDROID_SDK_ROOT=$HOME/Android/Sdk
export ANDROID_NDK_ROOT=$HOME/Android/Sdk/ndk/25.1.8937393
yes | sdkmanager --licenses
.venv/bin/pip install kivy buildozer cython
./BUILD_PATIENT_APK.sh --check-only
./BUILD_PATIENT_APK.sh  # 10-30 min first time
ls -lh DIST/android/
```

If still not built in Debian container, expected - build infrastructure complete, source preserved, PC demo works, APK build scripts work check-only mode, actual APK building requires Android SDK/NDK - honest reporting.

### Android SDK not found

```
FAIL Android SDK not found
```

Fix:
```bash
# Install Android Studio https://developer.android.com/studio
# Or via pacman
sudo pacman -S android-sdk

# Set env
export ANDROID_SDK_ROOT=$HOME/Android/Sdk
export ANDROID_NDK_ROOT=$HOME/Android/Sdk/ndk/25.1.8937393
export PATH=$PATH:$ANDROID_SDK_ROOT/cmdline-tools/latest/bin:$ANDROID_SDK_ROOT/platform-tools

# Check
ls $ANDROID_SDK_ROOT
sdkmanager --list
yes | sdkmanager --licenses
```

### Buildozer fails

```
Buildozer failed
```

Check logs:

```bash
cat logs/build_patient_apk.log
cat logs/build_doctor_apk.log
```

Common fixes:

- Ensure Java 17+: `java -version`, `sudo pacman -S jdk-openjdk`
- Ensure buildozer.spec requirements correct: `cat android/patient_app/buildozer.spec`
- Ensure network for downloads (first build downloads SDK/NDK, dependencies)
- Ensure disk space 2GB+
- Ensure Python 3.10+

### Database locked

```
sqlite3.OperationalError: database is locked
```

Fix:

- Close other apps using DB
- Check .db file permissions
- Backup and recreate:

```bash
cp data/chrono_pcos.db data/chrono_pcos.db.bak
rm data/chrono_pcos.db
python -c "from database.database import LocalDatabase; db=LocalDatabase(); print('recreated', len(db.list_providers()))"
```

### Website not opening

```
xdg-open: no method available
```

Fix:
```bash
python -m http.server 8000 --directory website
# Then open http://localhost:8000 in browser
# Or
xdg-open website/index.html
# Or
firefox website/index.html
```

### Demo full_showcase.py duplicate definition

```
NameError: name 'QMainWindow' is not defined
```

Cause: class ShowcaseGUI defined twice, second outside PYSIDE_AVAILABLE causing NameError when PySide6 missing.

Fixed by rewriting file clean with single conditional if PYSIDE_AVAILABLE: class ShowcaseGUI.

If still occurs, update demo/full_showcase.py to ensure QMainWindow only used inside PYSIDE_AVAILABLE block.

### ReportGenerator() takes no arguments

```
TypeError: ReportGenerator() takes no arguments
```

Cause: desktop/doctor_app/patient_management.py ReportGenerator had only generate method no __init__, but full_showcase called ReportGenerator(self.db); reports/report_generator.py had __init__ with db optional causing inconsistency.

Fixed by adding __init__(self, db=None) to patient_management ReportGenerator.

If still occurs, check reports/report_generator.py has __init__(self, db=None).

### Diagnostics FAIL

Run diagnostics to see which FAIL:

```bash
./LAUNCH/DIAGNOSTICS.sh
./DIAGNOSTICS.sh
python -m launchers.diagnostics 2>&1 | tee logs/diagnostics.log
```

Each check shows PASS/WARN/FAIL with detail, never fake.

If FAIL:

- Python FAIL: Check python3 --version, install python
- .venv FAIL: Run ./setup_garuda.sh
- PySide6 FAIL: .venv/bin/pip install PySide6
- Core Deps FAIL: .venv/bin/pip install -r requirements.txt
- Database FAIL: Check database/database.py, python -c "from database.database import LocalDatabase; db=LocalDatabase()"
- Scientific Core FAIL: Check src/core/feature_extraction.py, python -c "from src.core.feature_extraction import RealtimeFeatureExtractor"
- AI/ML WARN: Check src/disease_modules/, may be WARN if not all modules, but core AI wrappers should PASS
- Ultrasound WARN: Check docs/ULTRASOUND_PIPELINE.md exists
- Doctor PC FAIL: Check desktop/doctor_app/main_enhanced.py exists
- Patient App FAIL: Check android/patient_app/main.py exists
- Android APKs WARN: Expected without SDK, use BUILD scripts
- Website FAIL: Check website/index.html exists
- Care Discovery FAIL: Check provider_network/care_discovery.py, python -c "from provider_network.care_discovery import CareDiscoveryEngine"
- Chrono-Metabolic FAIL: Check core/chrono_metabolic.py, python -c "from core.chrono_metabolic import ChronoMetabolicFingerprint"

### Launcher UI clipped text

Fixed in launcher/main.py:

- AppCard class min 320x180 max 400x220 Expanding Fixed WordWrap title 30px 14px bold #0f172a desc 40-60px 11px #64748b status 30px 10px color detail[:50] tooltip full detail button 36px 12px bold #0ea5e9 radius 6px QFrame border 2px color radius 12px hover #0ea5e9 bg #f8fafc
- Header_frame gradient #0f172a #1e293b radius 12px padding 10px title 32px bold white subtitle 18px #cbd5e1 letter-spacing 2px tagline 14px #0ea5e9 3px disclaimer #fbbf24 bg rgba border
- Status overview grid 4 cols cards 200x60 max80 left border 4px
- Category GroupBox border #cbd5e1 bg #f8fafc grid 3 cols spacing 12
- Footer #0f172a wrapping info footer #f8fafc border
- Main_layout margins 20 spacing 16 scroll widgetResizable responsive no clipped text overlapping Fusion style

If still clipped, ensure you have latest launcher/main.py (check git log).

### Website not polished

Fixed in website/index.html 40K+ extensive scientific site and style.css polished modern CSS and script.js minimal JS.

If website still basic 26K, update from git:

```bash
git pull origin arena/01a0ab67-chrono-pcos-v8-1
ls -lh website/index.html  # Should be 40K+
```

### No logs

```bash
mkdir -p logs
chmod 755 logs
./setup_garuda.sh  # Creates logs/
ls -lh logs/
```

### No DIST/android

```bash
mkdir -p DIST/android
touch DIST/android/.gitkeep
./setup_garuda.sh  # Creates DIST/android/
ls -lh DIST/android/
```

## Getting Help

- Read docs/INSTALLATION.md
- Read docs/BUILD_GUIDE.md
- Read docs/GARUDA_LAUNCH_GUIDE.md
- Read docs/SHOWCASE_GUIDE.md
- Read docs/ARCHITECTURE.md
- Read docs/ANDROID_BUILD_GUIDE.md
- Run ./LAUNCH/DIAGNOSTICS.sh and check logs/diagnostics.log
- Check logs/launcher.log logs/build_*.log
- Run python launcher/main.py from terminal to see console output

## Safety

Research prototype not medical diagnosis, local-first offline privacy-focused, no cloud upload, no prescription sales, no treatment decisions, encourage professional consultation.

If something cannot be completed in current environment identify why, implement everything possible, create required setup/build mechanism, clearly report remaining limitation, never fake.
