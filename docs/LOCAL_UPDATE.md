# Updating your local copy (Garuda / Arch)

The current work lives on the branch **`arena/01a0ce2b-endo-twin-nexus-v8-3`**
(tip at the time of writing: `5dc25c1`). `main` does **not** have it.

## 1. Pull

```bash
cd ~/Downloads/endo-twin-nexus-v8.3          # your clone; adjust the path
git status                                    # local edits? stash them first
git fetch origin
git checkout arena/01a0ce2b-endo-twin-nexus-v8-3   # first time: creates the local branch
git pull --ff-only origin arena/01a0ce2b-endo-twin-nexus-v8-3
git log --oneline -3
```

Expect to see `5dc25c1 fix(build): register the ESP32 board index…` and
`0089300 feat(hardware)!: retire the GSR channel…`.

If you have local changes you do not want to lose:

```bash
git stash -u          # before the checkout/pull
git stash pop         # after
```

The pull **deletes `src/signal_processing/gsr.py`** — that is intended, not a
merge problem.

## 2. Verify the Python side

```bash
./SETUP.sh            # only if .venv is missing or broken
.venv/bin/python -m pytest -q                          # expect 138 passed
python3 scripts/diagnostics/a11y_contrast_audit.py     # expect 282 pairings, 0 below
python3 scripts/diagnostics/qt_api_check.py            # API surface only, no rendering
./START.sh            # menu: 8 = tests, 9 = project health
```

## 3. Re-flash the firmware (required for the new frame)

The packet format changed from `$CP2` to `$CP3`, so a board still running the
old binary keeps sending the old frame. It will still parse, but without the
skin-temperature fixes.

```bash
sudo pacman -S arduino-cli                 # Arch/Garuda "extra" repo
bash scripts/build/build_firmware.sh       # installs cores + libs, then compiles
arduino-cli board list                     # find the port, e.g. /dev/ttyACM0
arduino-cli upload -p /dev/ttyACM0 --fqbn esp32:esp32:esp32s3 hardware/esp32s3/endo_twin_wearable
arduino-cli upload -p /dev/ttyACM0 --fqbn arduino:avr:mega    hardware/arduino/endo_twin_mega_lab
```

ESP32-S3 notes: it usually appears as `/dev/ttyACM0` (native USB) or
`/dev/ttyUSB0` (bridge chip). If the port never shows up, hold **BOOT**, tap
**RESET**, release **BOOT**, then retry. Add yourself to the `uucp` group if the
port exists but is not writable: `sudo usermod -aG uucp "$USER"` (re-login).

The build script now registers Espressif's board index itself; `arduino-cli core
install esp32:esp32` cannot resolve without it.

## 4. Rebuild the Android apps (only if you use them)

Both TCP clients changed (CP3 parsing, the learning panel):

```bash
./build_apks.sh        # 1 = Patient, 2 = Doctor, 3 = both
                       # 4/5 = build + adb install; 7 (START.sh) = set up the SDK
```

## 5. Data and database — nothing to do

- No migration: the GSR columns and the `gsr_data` table are still declared but
  stay empty, so existing databases open unchanged.
- `data/synthetic/cohort/*.json` lost their `gsr_tonic` keys; the pull updates
  those tracked files for you.

## 6. Preview the website

```bash
bash LAUNCH/WEBSITE.sh
# or
python3 -m http.server 8080 --directory website   # then http://localhost:8080
```

## 7. Fresh clone instead of pulling

```bash
git clone -b arena/01a0ce2b-endo-twin-nexus-v8-3 \
  https://github.com/aviralsingh839/endo-twin-nexus-v8.3.git
cd endo-twin-nexus-v8.3 && ./SETUP.sh
```

## 8. One CI line that is not in the branch

Commits pushed from this project's automation cannot touch files under
`.github/workflows/`, so add this line yourself in
`.github/workflows/arduino_firmware.yml` (job `compile`, step
*Install active cores*) and push it:

```yaml
      - name: Install active cores
        run: |
          arduino-cli config add board_manager.additional_urls https://espressif.github.io/arduino-esp32/package_esp32_index.json
          arduino-cli core update-index
          arduino-cli core install arduino:avr
          arduino-cli core install esp32:esp32
```

Without it the CI firmware gate fails at the core-install step on a clean
runner, the same way it fails locally.
