# Self-learning wearable layer

A wearable that "upgrades itself while you wear it" is implemented here as a
**continual-learning layer that lives with the wearer's data**, not as firmware
reflashing. The ESP32-S3 pod streams frames over USB or TCP (`hardware/esp32s3/endo_twin_wearable/endo_twin_wearable.ino`);
it has no OTA path, no version register and no capability table, so the thing that
changes over time is the learned state the platform keeps *about that wearer*.

Two mechanisms run together, both offline, both measurable:

| | mechanism | what advances it | what it may claim |
|---|---|---|---|
| 1 | **capability ladder** | wearing time + signal coverage + quality | a personal norm exists, time-of-day context is used, drift is absorbed |
| 2 | **supervised head** | wearer-reported symptom / normal-day labels | only that it beats a base-rate predictor on unseen labels — never a diagnosis |

Implementation: `src/core/adaptive_learning.py`. Simulator for offline work:
`src/utils/wear_simulator.py`. Demo: `scripts/demo_self_learning.py`.

---

## 1. The capability ladder

The ladder promotes one rung at a time, and only when the evidence for that rung is
already on disk. No rung can be skipped.

| tier | meaning | gates (defaults, `AdaptiveConfig`) |
|---|---|---|
| `population` | nothing personal yet; population priors only | start state |
| `personalized` | robust personal norms (median / MAD) and personal z-scores | ≥ 3600 s worn, ≥ 120 samples per qualifying metric, ≥ 4 metrics with a norm, recent quality ≥ 0.50, and the norm itself needs ≥ 300 samples spanning ≥ 12 h at quality ≥ 0.50 |
| `circadian` | values are compared with the same hour of previous days | ≥ 86 400 s worn, ≥ 2 days covered, ≥ 6 hours of day with ≥ 30 samples each |
| `adaptive` | a persistent shift becomes the new normal | ≥ 3 days worn, ≥ 3 days covered, ≥ 3 metrics with ≥ 500 samples |

"Worn" is earned, not assumed: `observe()` credits time only when the gap between
samples is ≤ 300 s (`max_worn_gap_s`). A device sitting in a drawer does not
accumulate wearing hours.

Promotion is recorded as a `LearningEvent(kind="promotion")` with the timestamp, the
requirements that were met, and the wearing time at that moment, and it bumps the model
version (minor). The full history is shown in the UI and stored with the state.

## 2. How the norm is allowed to move

A baseline that follows every fluctuation is worthless — it would learn a genuine
event away. The rules are therefore asymmetric:

* **The norm is set once per metric** and only from a representative, quiet window
  (300 samples, 12 h span, quality ≥ 0.50). Before that, z-scores are simply not
  available and the UI says so.
* **Descriptive statistics** (what the samples looked like) are kept separately from
  the norm and never feed a decision.
* **Metered absorption** — a shift may only be absorbed when all of these hold:
  Page–Hinkley alarm (δ = 0.25 σ, λ = 8 σ) **and** the deviation has persisted for
  ≥ 6 h of worn time **and** the shift is ≥ 1.5 σ **and** there are ≥ 60 samples.
  Absorption then proceeds at ≤ 0.35 σ per hour and may never exceed 6 σ in one go.
* **Freeze** — gradual tracking stops while |z| > 3.5, and a deviation window only
  closes after 30 consecutive normal samples. A short excursion is left as an event
  and is never copied into the baseline.
* **Rollback** — if recent signal quality stays below 0.35 (60-sample window), the
  model demotes one rung and records why; a 30-minute cooldown stops it flapping.
  Re-promotion requires the full gate again.

Verified behaviour (simulated, `scripts/demo_self_learning.py`):

```
    19.0 h worn  PROMOTION  personalized (v1.1.0) after 12.0 h of wearing and 721 samples
    40.0 h worn  PROMOTION  circadian    (v1.2.0) after 24.0 h of wearing and 1442 samples
   115.0 h worn  PROMOTION  adaptive     (v1.3.0) after 72.0 h of wearing and 4325 samples

  deviation z of a +9 bpm shift   120 h   132 h   144 h   168 h   186 h
      adaptive model               3.57    4.88    2.13    0.42    0.42   (3 absorbed)
      circadian model              3.57    3.57    3.57    3.57    3.57   (cannot absorb)
      a 3 h excursion                            -> 0 absorbed, norm moved +0.00 bpm
```

## 3. The supervised head

Seven features (`hr_z, rmssd_z, temp_z, gsr_z, activity_z, hour_sin, hour_cos`), fed
only by labels the wearer logs. It is deliberately hard to switch on:

* ≥ 20 labels with ≥ 5 in each class;
* every label is scored **before** it is trained on (no leakage), so the reported
  numbers are prospective;
* after ≥ 30 unseen labels it must show ≥ 15 % relative log-loss gain over a base-rate
  predictor **and** win on ≥ 65 % of them;
* otherwise its status is `withheld` and the panel states "no claim is made".

Demo, both arms labelled identically, one with labels that follow physiology and one
with labels that carry no signal:

```
  labels follow physiology -> ACTIVE    labelled 64, unseen 44, wins 40,
                                        log-loss 0.262 vs base rate 0.708
  labels carry no signal   -> WITHHELD  labelled 64, unseen 44, wins 24,
                                        log-loss 0.865 vs base rate 0.714
```

## 4. State, privacy, and where things live

* One file per wearer: `data/adaptive/<patient_id>/wearable_model.json`
  (schema `endo_twin.adaptive_wearable/1`), written atomically and ignored by git —
  `data/adaptive/` sits in `.gitignore` with the other local runtime state.
* Nothing is uploaded. The layer is local-only, consistent with the project's
  offline-first rule, and it stores aggregates (norms, windows, counters, audit
  events) rather than raw waveforms.
* The demo writes to a temporary directory and deletes it unless `--keep` is passed.

## 5. Where it surfaces

| surface | what it shows |
|---|---|
| workstation, baseline tab (`src/ui/main_window.py`) | tier, wearing hours, what unlocks next, promotion / drift / rollback history |
| workstation hero line | `model <TIER> v<version>` next to the baseline status |
| patient app (`desktop/patient_app/main.py`) | same panel, plus the two label buttons the supervised head learns from |

The panel widget (`src/ui/learning_panel.py`) carries **no colours of its own**: both
apps hand it colours from their own contrast-audited palettes, and a test enforces it.

## 6. Android

`android/patient/app/src/main/java/org/chronopcos/patient/learning/WearableLearningModel.kt`
mirrors the ladder (same tiers, same default thresholds, same freeze / absorption /
rollback rules, same head gates) with state in `SharedPreferences`.

**It has not been compiled or run here** — this environment has no Android SDK, Gradle
or device. Treat it as review-only code until an APK build is executed elsewhere.

## 7. How to verify

```bash
.venv/bin/python -m pytest tests/test_adaptive_learning.py tests/test_learning_wiring.py -q
.venv/bin/python scripts/demo_self_learning.py --days 8        # full disclosure printed
python3 scripts/diagnostics/a11y_contrast_audit.py             # panel colours stay AA
```

* `tests/test_adaptive_learning.py` — 29 tests: ladder order, gates, worn-time
  accounting, out-of-range refusal, absorption vs excursion, rate limit, rollback and
  recovery, head activation / withholding, state round-trip, per-wearer isolation.
* `tests/test_learning_wiring.py` — 9 tests: the live feature path feeds the learner,
  learner norms take precedence over the frozen snapshot, the panel's status contract
  holds, host palettes reuse audited colours, state survives a restart.

## 8. What this is not

* Not a diagnosis, not a medical device, not clinically validated.
* The confidence figure is engineering confidence (coverage × quality × wearing time),
  not clinical certainty.
* No accuracy, sensitivity or specificity is claimed anywhere; the only performance
  number the head may show is a prospective log-loss comparison against a base-rate
  predictor on the wearer's own labels.
* All demo and test streams are synthetic (`src/utils/wear_simulator.py`); no real
  person was measured for them.
