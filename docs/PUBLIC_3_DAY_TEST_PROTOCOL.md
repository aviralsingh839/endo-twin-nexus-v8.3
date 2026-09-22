# ENDO-TWIN NEXUS — 3-Day Public Wearable Test Protocol

## Purpose

This mode is for an engineering/research prototype test with a volunteer, not a clinical study.

The volunteer wears the ESP32-S3 pod for three days so the team can evaluate:

- sensor stability;
- packet continuity;
- GSR electrode usability;
- motion/PPG artifact behaviour;
- BME280/BH1750 environmental context;
- data-quality scoring;
- baseline construction;
- longitudinal change display;
- recovery/persistence logic;
- Android recording reliability.

## Participant privacy

Use a generated code such as PUBLIC-A1B2C3D4.

Do not store:

- name;
- phone number;
- email;
- address;
- school/workplace;
- photographs;
- government identifiers;
- medical record number;
- diagnosis;
- unrelated personal notes.

The public-test Android recorder validates the incoming 20 Hz CP2 stream but archives every fourth valid frame (~5 Hz) locally in Room to keep three-day phone storage practical. The participant sees a persistent recording notification.

The project should not upload the volunteer's raw physiological data to a public website by default.

## Consent

Before starting:

1. Explain that this is an experimental prototype.
2. Explain what sensors are being used.
3. Explain that the device is not a medical diagnostic device.
4. Explain that the participant can stop the test.
5. Confirm that only a generated participant code will be used.
6. Do not collect unnecessary personal information.

## Test window

Target:

- Day 1: 0–24 h
- Day 2: 24–48 h
- Day 3: 48–72 h

The Android app uses a foreground connected-device service for continuous recording while the study is active. Android requires appropriate foreground-service declarations and permissions for long-running connected-device work. 

Start the foreground service from a visible user action in the app. Android restricts arbitrary background foreground-service starts on modern Android versions. 

## During the test

The participant should use the device normally unless the test protocol says otherwise.

Record engineering notes separately if needed:

- pod removed;
- charging;
- Wi-Fi disconnected;
- finger electrodes removed;
- unusual movement;
- sensor repositioned;
- device restarted.

Do not turn those notes into physiological conclusions.

## What the app records

The CP2 stream contains:

- PPG IR/red;
- acceleration;
- gyroscope;
- GSR;
- ambient light;
- BME280 temperature;
- BME280 humidity;
- BME280 pressure;
- quality/status information;
- timestamp and CRC.

The MAX30102 is an optical heart-rate/pulse-oximetry sensor intended for wearable applications. The underlying IC itself is not intended for direct skin contact; the wearable should use an appropriate cover/encapsulation over the optical sensor. 

The BME280 provides temperature, humidity and pressure and is intended for low-power mobile/wearable applications. 

## Day-by-day engineering review

### Day 1

Check:

- connection remains stable;
- CP2 packets are arriving;
- CRC-valid percentage is high;
- PPG is not continuously saturated/missing;
- GSR electrodes remain usable;
- BME280 has plausible environmental values;
- BH1750 responds to environmental light changes.

Do not tune the baseline to make Day 1 look normal.

### Day 2

Check:

- recording survived normal phone use;
- reconnects work;
- data is still separated by participant code;
- day 2 contains actual observations;
- quality remains visible;
- timeline shows the second day independently.

### Day 3

Check:

- three calendar days are represented;
- no major unexplained data gaps;
- quality is known for each day;
- baseline engine has enough observations;
- longitudinal engine has a genuine multi-day history.

## Baseline review

The ENDO-TWIN desktop baseline engine uses personal observations rather than a fixed population value.

The project configuration requires a minimum of 3 days for stable longitudinal baseline coverage.

Three days means baseline eligibility, not clinical validation.

After importing/processing the study:

1. verify sample count;
2. verify day coverage;
3. verify signal quality;
4. inspect metric distributions;
5. calculate baseline;
6. inspect baseline confidence;
7. compare each day against the baseline;
8. inspect whether deviations persist or recover.

Do not label a change as abnormal merely because it differs from the baseline.

## Three-day timeline

The final UI should make the sequence visually obvious:

DAY 1 → DAY 2 → DAY 3 → BASELINE → CHANGE → RECOVERY/PERSISTENCE

Each day should show:

- number of observations;
- quality;
- HR median;
- HRV RMSSD median where available;
- GSR median;
- activity;
- temperature/environment context;
- missing-data indicators.

## What counts as a successful engineering test

A successful test is not "the model found a disease."

It is:

- data survived three days;
- sensor quality was measurable;
- packet corruption was detectable;
- missing data was visible;
- personal baseline could be constructed;
- day-to-day changes could be visualized;
- persistent vs transient changes were distinguishable in the data;
- the system did not silently turn missing/poor data into conclusions.

## After the test

Export the study data.

Keep:

- raw data;
- processed features;
- baseline snapshot;
- timeline summary;
- data-quality summary;
- firmware version;
- app version;
- participant code;
- test dates.

Keep synthetic/demo data in separate labelled datasets. Never mix DEMO_DATA or SYNTHETIC rows into the volunteer's real longitudinal analysis.

## Public-release rule

Before giving the pod to another volunteer:

- reset the previous participant's local study state;
- generate a new participant code;
- verify no previous raw packets are visible;
- verify no previous baseline is reused;
- verify the Android timeline is empty;
- verify the desktop study is assigned to the new participant;
- verify the export contains only the selected study.

Room supports explicit migration paths for schema changes; the current app adds a non-destructive 2→3 migration for the public-study table so existing patient data is not intentionally discarded during this feature update. 


## Android → Desktop handoff

After Day 3, use the Android app's **Export CSV** button. The export contains only the selected participant's locally recorded CP2 packets.

On the desktop:

```bash
python scripts/import_public_study.py /path/to/STUDY-XXXXXXXX.csv --participant PUBLIC-XXXXXXXX
```

Then open the desktop application and use:

1. **3-Day Public Test → Load Into Analysis**
2. **Baseline → Capture Baseline**
3. **Trends → inspect Day 1 / Day 2 / Day 3**
4. **Data Quality → inspect sensor quality**
5. **Report → generate the research report**

The importer is offline-only. It verifies CP2 CRC before processing packets and labels imported feature rows as REAL / PUBLIC_3_DAY.


### Sampling limitation

The wearable firmware emits CP2 at approximately 20 Hz. The public Android archive intentionally keeps approximately 5 Hz by retaining every fourth valid frame. This is a storage trade-off for a three-day volunteer test. Treat fine-grained PPG/HRV analysis from this public archive as engineering/research output requiring validation; do not present it as clinical-grade HRV.
