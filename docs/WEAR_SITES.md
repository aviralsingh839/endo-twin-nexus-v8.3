# Wear sites: wrist or shoulder

The pod is worn on **one of two sites** for a whole session:

| Site | Where exactly | Label you will see |
|---|---|---|
| **Wrist** | forearm, pod on the inner (volar) side, proximal to the wrist crease | `Wrist (forearm, pod on the inner side)` |
| **Shoulder** | upper arm / deltoid, pod against skin on the inner upper arm | `Shoulder (upper arm / deltoid)` |

Set it for the session:

```bash
ENDO_TWIN_WEAR_SITE=shoulder ./START.sh          # or wrist (default)
.venv/bin/python -m src.core.wear_site --both    # printable guide for both sites
.venv/bin/python -m src.core.wear_site shoulder  # one site
```

The default lives in `src/config.py` (`WEAR_SITE = "wrist"`). The site is **host-side
only** — it is never added to the `$CP3` frame, so the wire format is unchanged
(`docs/WIRE_FORMAT_CP3.md`), and it is written into the session provenance
(`MEASURED • SITE=wrist`) and into study exports.

## The one rule

> **A personal baseline belongs to a site.** Switching site changes the limb, the
> perfusion and the clothing around the pod, so it looks like a physiological change
> in the trend when it is only a configuration change. Record the site, keep one site
> per session, and start a new baseline when it changes.

Wrist and shoulder sessions are never compared with each other, and never averaged
together.

## Mounting

### Wrist

- 20–25 mm strap around the forearm; snug enough that the pod cannot rock, loose
  enough to leave no mark after 30 minutes.
- MAX30102 window flat against the inner wrist, proximal to the wrist crease and
  clear of the bony ulnar head.
- BH1750 facing outwards so it can see ambient light; BME280 vent away from skin.
- DS18B20 probe flat on the inner forearm beside the pod, at least 15 mm from the PPG
  window so it neither presses on the optical site nor blocks it.
- Watch for: the strap creeping loose during the day (shows up as a quality drop),
  sleeves covering the light sensor, the probe pressing on the PPG site or the strap seam.

### Shoulder

- Armband over the deltoid or upper arm: it must not slide when the arm swings, and it
  must not be tightened over the shoulder joint itself.
- MAX30102 window flat against **skin** on the inner upper arm — not through a sleeve,
  and not over the outer deltoid where contact is poor.
- BH1750 facing outwards if the sleeve allows it, but expect darkness under clothing.
- BME280 vent away from skin; under clothing it measures an under-garment microclimate.
- DS18B20 probe flat on the inner upper arm, at least 20 mm from the pod body and clear
  of the armpit crease.
- Watch for: fabric between sensor and skin (PPG needs optical contact, not fabric),
  the pod pressed by a bag strap or seat belt, and the probe lifting at one edge so it
  reads trapped warm air.

Full build detail for the pod itself: `WEARABLE_AND_MEGA_BUILD_MANUAL.md` and
`hardware/WIRING.md`. This page is about *where it goes and what that does to the numbers*.

## What each measurement means on each site

`Limit` lines are the honest boundaries. They are not accuracy figures — those would
need a study this project has not run.

### Heart rate (`hr_bpm`, MEASURED — MAX30102)

| Site | What it means | Limits |
|---|---|---|
| Wrist | Heart rate from wrist PPG, quality-gated before use | motion from hand/wrist or a loose strap contaminates beats; ambient light under the strap shows as a quality drop |
| Shoulder | Heart rate from upper-arm PPG, quality-gated before use | the upper arm is **not** the validated site for PPG: expect lower amplitude, rely on the quality gate; fabric between sensor and skin stops the measurement entirely; arm and torso movement couple in |

### HRV (`rmssd_ms`, `sdnn_ms`, DERIVED — from PPG intervals)

| Site | What it means | Limits |
|---|---|---|
| Wrist | RMSSD/SDNN derived from wrist PPG intervals, not an ECG measurement | PPG-derived HRV is less accurate than ECG-derived HRV; arm movement makes the window unusable rather than merely noisy |
| Shoulder | Same derivation on a non-standard site — treat as exploratory | the quality gate matters more here than on the wrist; not comparable with wrist sessions |

### SpO₂ indicator (`spo2_pct`, ratio-derived)

| Site | What it means | Limits |
|---|---|---|
| Wrist | Ratio-derived indicator, shown only above a stricter quality gate | not a clinical pulse-oximeter reading |
| Shoulder | Same ratio on a non-standard site — context only | never a clinical reading |

### Skin temperature (`skin_temp_c`, MEASURED — DS18B20 in skin contact)

| Site | What it means | Limits |
|---|---|---|
| Wrist | Local skin temperature trend on the forearm | the wrist is distal and follows the environment more than a proximal site; not core temperature; a lifted probe reports the air beside the arm (status bit 3) |
| Shoulder | Local skin temperature trend on the upper arm | far more often clothed, so the probe measures skin **plus trapped warm air**; absolute values sit differently from the wrist; not core temperature |

### Motion / activity (`motion_index`, `activity_level`, MEASURED — MPU6050)

| Site | What it means | Limits |
|---|---|---|
| Wrist | Forearm motion classified into an activity level | the wrist amplifies arm swing, so the same walk looks larger than it does from the shoulder; desk work and phone use register as movement; not whole-body calorimetry or step counting |
| Shoulder | Upper-arm/torso motion classified into an activity level | arm-only movement looks smaller than from the wrist; bag straps, seat belts and leaning add motion that is not activity; not whole-body calorimetry |

### Ambient light (`lux`, MEASURED — BH1750)

| Site | What it means | Limits |
|---|---|---|
| Wrist | Illuminance used as day/night and light-exposure context | a sleeve over the pod turns this into a clothing sensor |
| Shoulder | Usable only when the sleeve leaves the sensor exposed | under clothing it reads darkness regardless of the actual light level |

### Environment (`roomT`, `hum`, `press`, MEASURED — BME280)

| Site | What it means | Limits |
|---|---|---|
| Wrist | Temperature/humidity/pressure behind the pod vents, close to ambient air | not a calibrated room sensor; body heat biases temperature upward |
| Shoulder | Under-garment microclimate — warm and humid compared with the room | do not read it as room temperature or humidity |

### Sleep and circadian features (MODEL-INFERRED)

Both sites: inferred from HR/HRV and activity patterns, not polysomnography. A change of
site invalidates the comparison for the same reason as everywhere else on this page —
the activity and HRV inputs change meaning.

## Recoding a session to a different site

There is nothing to change in the firmware. Change the environment variable (or
`src/config.py`), reseat the pod, and treat everything recorded afterwards as a
**new session on a new site**:

1. stop the running session;
2. re-mount the pod and probe on the new site, checking contact;
3. set `ENDO_TWIN_WEAR_SITE` (or edit `config.WEAR_SITE`);
4. verify the label in the UI header reads the new site before trusting numbers;
5. start a fresh baseline — do not merge it with the previous site's baseline.

## Where this is enforced and shown

| Surface | What you see |
|---|---|
| Live feature rows | `wear_site` field plus `MEASURED • SITE=…` provenance (`desktop/workstation_runtime.py`) |
| Doctor workstation | site caption under *Live Sensor Signals*, site in the event log |
| Patient workstation | site in the measurement status line |
| Prototype Lab | hardware cards name the mount site requirement |
| Reports | wear-site line with the site label and the cross-site rule |
| Study export | `wear_site` in the per-row provenance JSON |
| CLI | `python -m src.core.wear_site` prints the mounting and measurement guide |

Tests: `tests/test_wear_site.py` covers site validation, the environment override, the
per-channel notes for both sites, and the guarantee that the site stays out of the wire
format.
