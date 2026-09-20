# CHRONO-PCOS V8.1

Low-cost longitudinal physiological phenotyping plus periodic clinical imaging,
as an offline research prototype for PCOS-focused monitoring. Not a diagnostic
device and not clinically validated.

The project asks one question: can continuous, personalised physiological
information collected *between* clinical assessments provide useful longitudinal
context, and does combining it with periodic clinical information such as
ultrasound improve PCOS-related risk phenotyping? The wearable only acquires
data. The contribution is the longitudinal framework: personal baseline,
persistent-change detection, the evidence-linked "WHAT CHANGED?" summary,
provenance-aware fusion of continuous and clinical information, and
low-infrastructure digital reporting.

Medical safety note: PCOS diagnosis requires a clinician and accepted
diagnostic criteria. Every score here is a research estimate. No sensor
measures hormones. The app never starts, stops, changes or prescribes
medication. No ultrasound image is converted into a diagnosis, and no
cyst-rupture prediction exists or is claimed.

---

## Documentation

Read these in order:

1. `docs/HOW_THE_PROJECT_WORKS.md` : what the system is, every feature, the
   physiology behind each signal, and a study plan to master the project.
2. `docs/CODE_EXPLANATION.md` : module-by-module code walkthrough with the real
   formulas and constants, plus the judge pitch, demo script and question bank.
3. `docs/ARDUINO_WIRING_GUIDE.md` : full wiring for the Arduino Mega 2560 bench
   hub and the Arduino Nano wearable pod, firmware upload, packet protocol,
   power, testing, troubleshooting and bill of materials.
4. `docs/V8_1_BUILD_SPECIFICATION.md` : the engineering specification for this
   release, including the dataset and privacy rules and the pending
   experiments.
5. `docs/scientific_model.md` : the mathematics of every score, exactly as
   implemented.
6. `docs/validation.md` : what is validated today and what is pending.

`data/README.md` and `models/README.md` explain those folders.

---

## Hardware

Two boards, both documented in the wiring guide:

- **Arduino Nano** wearable pod: MAX30102 PPG, DS18B20 skin temperature,
  MPU6050 motion, optional GSR. Streams 20 Hz `$CP2` packets.
- **Arduino Mega 2560** bench hub and base station: the pod sensors plus ECG,
  microphone, FSR, light and environment sensors, OLED, LEDs, buzzer and
  buttons. In relay mode it forwards the pod stream to the PC.
- Optional **ESP8266** Wi-Fi bridge relays the same packets over TCP port 7777.

The dashboard also runs with no hardware at all: demo mode, manual entries and
replay of recorded sessions all exercise the same longitudinal engine.

Firmware lives in `arduino/`: `chrono_pcos_mega_firmware` (bench hub),
`chrono_pcos_nano_pod` (wearable pod) and `chrono_pcos_esp8266_bridge`
(Wi-Fi relay).

---

## What the system does

- Reads wearable packets over USB serial or the ESP8266 TCP bridge: PPG (pulse
  waveform, HR, HRV, pulse amplitude, educational SpO2), skin temperature,
  motion, optional GSR, periodic ECG checkpoints, plus manual inputs for BP,
  glucose, cycle, symptoms and weight.
- Scores every sensor's signal quality and withholds the risk number when
  quality or confidence is insufficient, showing a banner instead of a guess.
- Builds a personal baseline and the personal physiological fingerprint from
  it, then classifies changes as single, persistent, progressive or recovery
  with quality gates.
- Produces the evidence-linked WHAT CHANGED summary and the CARE JOURNEY
  SUMMARY with OBSERVED / ASSOCIATED / UNKNOWN separation.
- Runs the ultrasound pipeline: image quality gate, structured features with
  provenance (image-derived values stay UNKNOWN until a validated labelled
  dataset exists), and descriptive exam comparison.
- Fuses every input group with provenance tags and per-group reliability
  weights, listing missing modalities explicitly.
- Computes the PCOS-related risk estimate from nine transparent domains with
  confidence, a bootstrap interval and explainable contributions.
- Records care-plan adherence and reminders without any treatment decisions.
- Generates a one-page clinical summary (text and PDF), a full longitudinal
  HTML report, and a QR code carrying only a random de-identified token, using
  a dependency-free QR encoder.
- Stores everything in a local SQLite database and runs fully offline.

Ten dashboard tabs cover Overview, Live Wearable, Longitudinal, PCOS Analysis,
Patient Inputs, Care and Adherence, Clinical Dashboard, Ultrasound + Fusion,
Validation / Research, and Advanced / Research Tools. Modes: LIVE, DEMO
(labelled synthetic), Judge Mode (scripted demonstration) and replay.

---

## Run it

```bash
pip install -r requirements.txt

# Demo mode (synthetic stream, clearly labelled):
python -m src.app --demo
# or: python run_demo.py

# Live mode from a board:
python -m src.app --port COM5            # Windows
python -m src.app --port /dev/ttyACM0    # Linux / macOS

# Live mode over the Wi-Fi bridge:
python -m src.app --net 192.168.4.1:7777

# Tests:
python -m pytest tests/ -q
```

Launcher scripts: `run_demo_windows.bat`, `run_demo_linux_mac.sh`,
`run_arduino_windows.bat`, `run_arduino_linux_mac.sh`.

The 124-test suite covers the packet CRC, signal-quality heuristics, baseline
calibration and its outlier guard, change detection, the risk equation, the
cosinor and sleep estimators, the QR encoder round-trips and Reed-Solomon
syndromes, the ultrasound quality gate and UNKNOWN-by-design features,
patient-level split integrity, fusion weighting, reporting and tokens, and the
validation lab.

---

## Current status

- The live risk engine is a transparent fallback equation with research-prior
  weights, not a trained calibrated model. Labelled longitudinal wearable data
  does not exist publicly; an ethics-approved pilot is the only realistic path.
- Ultrasound image-derived features are UNKNOWN by design until a validated,
  labelled, patient-grouped dataset exists. The quality gate works on real
  images today; nothing is invented.
- The Model A-E experiment (does longitudinal or ultrasound information add
  value?) is PENDING by design.
- The Python BLE client is not written yet, so the pod connects over USB serial
  or the ESP8266 bridge.
- Care-plan reminders are bookkeeping only.

Everything unproven is labelled PENDING or UNKNOWN in the interface, in the
code and in the documentation.
