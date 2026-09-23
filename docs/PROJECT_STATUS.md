# Project status and history

One page replacing the old status dumps (`00_INVENTORY_V8_3`, `DEVELOPMENT_HISTORY`,
`TESTING_REPORT`, `SHOWCASE_GUIDE`, `README_V8_3_PLUS`) and the V8.3 numbered doc
series. Details live in the topic docs listed in `docs/README.md`.

> **Research prototype. Not a medical device. Not clinically validated. Not a
> diagnosis.** Everything here is for engineering and research work on
> physiological signal processing.

## Where the project stands

| Area | State |
|---|---|
| Wearable hardware | ESP32-S3-DevKitC-1: MAX30102 PPG, MPU6050 IMU, DS18B20 skin-contact probe, BH1750, BME280. Build: `docs/WEARABLE_AND_MEGA_BUILD_MANUAL.md` |
| Bench hub | Arduino Mega lab hub (PPG/IMU/temp/light/env + OLED); bench bring-up variant in `hardware/arduino/chrono_pcos_mega_firmware/` |
| Wire format | `$CP3` (24 parts). Legacy `$CP2`/`$CP` still parse. See `docs/WIRE_FORMAT_CP3.md` |
| Retired | GSR/EDA channel and its code - removed; storage slots kept nullable so old databases open |
| Host software | PySide6 workstations (unified / doctor / patient / prototype lab), demo + live sensor modes, local-first SQLite |
| Mobile | Kotlin/Compose patient + doctor apps; live acquisition over TCP, demo data kept separate |
| Science layer | Quality control, HR/HRV, sleep-window and circadian estimates, longitudinal baselines, disease modules with explicit provenance and limitations |
| Website | Static research portal in `website/` |

## How it is verified — and what is not verified here

What actually runs and is checked in this environment:

```bash
.venv/bin/python -m pytest -q                          # 138 passed, 10 pre-existing warnings
python3 scripts/diagnostics/a11y_contrast_audit.py     # 282 colour pairings, 0 below threshold
python3 scripts/diagnostics/qt_api_check.py            # Qt API surface only - no rendering
bash scripts/diagnostics/project_health.sh             # project health summary
```

Never claimed, because it cannot be produced here: a firmware compile or upload
(no `arduino-cli`), an APK build (no Android SDK), a rendered GUI, or any
clinical/accuracy metric. Firmware is verified by reading, field/arity counting
and `tests/test_esp32s3_cp2_compatibility.py`; Kotlin is reviewed, not compiled.
Anyone reporting PASS on those must run them on a machine that has the toolchain.

## Version timeline

- **V8.1 — CHRONO-PCOS (legacy).** Serial PPG/IMU/temperature acquisition, PCOS
  risk and personalisation research code. Preserved twice: `chrono_pcos_project V8/`
  and the extracted documents in `docs/legacy/`.
- **V8.2 — intermediate design.** Added the physiological fusion ideas that became
  `src/fusion/` and the explainability layer.
- **V8.3 — CHRONO-TWIN NEXUS.** Multimodal core (`src/core/`, `src/signal_processing/`,
  `src/disease_modules/`), local database, ultrasound research module, patient/doctor
  workstations, static website.
- **V8.6 / V8.6.1 — workstations and platform split.** Unified workstation with
  startup-only DEMO/LIVE selection, doctor review flow, Android apps, design system
  and scientific methods note (`docs/UI_DESIGN_SYSTEM.md`,
  `docs/SCIENTIFIC_METHODS_V8_6_1.md`).
- **V8.7 — current.** Live sensor path on ESP32-S3 (`$CP3`), self-learning wearable
  layer (`docs/SELF_LEARNING.md`), GSR retirement, accessibility pass, Android
  learning mirror.

## Feature areas (short form; each has a topic doc or code home)

- **Local database and portability.** SQLite, 22 tables in the shipped demo
  database; CSV/JSON export, no cloud. `docs/DATA_ARCHITECTURE.md`,
  `docs/architecture/DATABASE_ARCHITECTURE.md`.
- **Security and privacy by construction.** Local-first, anonymous patient IDs
  (`PXXXXX`), no third-party telemetry, no credentials in the repo. The apps make
  no diagnostic claim; provenance labels carry source and limitations.
- **Offline-first.** Live acquisition, storage, analysis and reporting all work with
  no network; only the optional TCP sensor link and the static website need a network.
- **Care discovery.** A local provider-directory feature in the platforms; it lists
  options and never recommends treatment.
- **Demo mode.** Separated from live data by provenance labels
  (`DEMO_DATA` / `SIMULATED` / `REAL`). `demo/full_showcase.py`,
  `scripts/demo_self_learning.py`.
- **Website.** `website/` static portal; launch with `./START.sh website`.
- **Ultrasound research module.** Simulation and fusion experiments only -
  `docs/ULTRASOUND_PIPELINE.md`.
- **Build and deploy.** `BUILD.md`, `docs/BUILD_GUIDE.md`, `docs/INSTALLATION.md`,
  `docs/ANDROID_BUILD_GUIDE.md`, `docs/LOCAL_UPDATE.md`.
- **Performance.** Runtime measured on demo streams during development; not
  benchmarked on real hardware, and no accuracy claim is made anywhere.
- **Limitations and future work.** `docs/SAFETY_AND_LIMITATIONS.md`,
  `docs/SCIENCE_GUARDRAILS.md`, `docs/science/LIMITATIONS.md`.

## Data note

The PhysioNet *wrist PPG during exercise* recordings under
`chrono_pcos_project V8/data/public/wrist_ppg_during_exercise/` had their large
`.dat` signal binaries removed to stop shipping ~50 MB of re-downloadable public
data. The WFDB headers (`.hea`), annotations (`.atr`), `RECORDS`, `ANNOTATORS` and
`SHA256SUMS.txt` remain, so the exact files can be re-fetched and verified. No
model artifact in this repo depends on them at runtime.

## History and archives

`git log` is the real record. Material kept on disk: `docs/legacy/` (V8.1
documents), `hardware/legacy/` (superseded firmwares), `chrono_pcos_project V8/`
(V8.1 tree, slimmed of byte-identical copies and the dataset binaries).
