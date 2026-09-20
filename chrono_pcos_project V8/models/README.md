# Models folder

Training scripts in `../scripts/` save `.joblib` bundles here. Two artifacts are
checked in; the rest are optional and the app falls back to transparent
formulas when they are absent.

- `pcos_risk_model.joblib`: clinical-variable PCOS risk baseline trained from
  the bundled public Kaggle cohort (`data/public/PCOS_data_without_infertility.xlsx`,
  541 patients) with

      python scripts/train_pcos_risk_model.py \
          --csv data/public/PCOS_data_without_infertility.xlsx \
          --out models/pcos_risk_model.joblib

  Patient-level 5-fold CV on that cohort: ROC-AUC 0.959, average precision
  0.932 (full details in the bundle's `meta` dict). The pregnancy-screen columns
  (beta-HCG, Pregnant, abortions) are excluded on purpose. This is a
  model-development result on a clinical-variable referral cohort; it is never
  presented as wearable or ultrasound accuracy, and it is not the live engine.

- `ppg_quality_model.joblib`: PPG signal-quality and motion-artifact model
  (`scripts/train_ppg_quality_model.py`) trained on the PhysioNet wrist-PPG-
  during-exercise database (8 subjects, 19 recordings of chest ECG plus wrist
  PPG plus IMU). For each 10 s window it predicts whether the app's PPG heart-
  rate estimate is reliable (within 5 bpm of the ECG reference). Subject-level
  5-fold CV: ROC-AUC about 0.62; at a 0.5 threshold it keeps about 28% of
  windows with about 58% usable precision against a 35% base rate. The app
  blends this probability at 40% weight into the `ppg_quality()` heuristic when
  the file exists; deleting the file reverts to the pure heuristic. The wrist
  PPG sensor differs from the MAX30102, which is why the weight stays small.

Earlier revisions could blend optional trained stress and sleep models. Those
trainers and artifacts were removed in the V8.1 cleanup: both estimators now
run purely on the transparent formulas in `src/models/`. The hormone
illustration reads `models/hormone_priors.json` when present and otherwise
falls back to its documented defaults.
