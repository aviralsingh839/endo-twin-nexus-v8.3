# Data folder

Runtime state and public development datasets.

```text
data/public/PCOS_data.csv                       Kaggle PCOS cohort (with infertility columns)
data/public/PCOS_infertility.csv                infertility subset of the same cohort
data/public/PCOS_data_without_infertility.xlsx  original xlsx, training input for the risk baseline model
data/public/wrist_ppg_during_exercise/          PhysioNet wrist PPG during exercise (WFDB), used by the
                                                PPG quality model; the source page has been withdrawn,
                                                so this local copy is the only source
data/ai_config.example.json                     template for the optional assistant config
```

Runtime files are created by the app on this machine and are gitignored:

```text
data/chrono_pcos.db            local SQLite history (sessions, features, logs, care plan, reports)
data/raw/                      raw and feature CSV exports
data/baselines/                personal baseline and calibration history
data/training_audit.jsonl      training audit log
data/ai_config.json            optional assistant endpoint config, never committed
```

Do not invent medical datasets. The dashboard runs without any of
the public files using transparent fallback equations and the demo stream;
model training and validation need the real public data above. Download links
for optional datasets (WESAD, BIDSleep, MESA, MMASH, mcPHASES, NHANES) are
printed by `scripts/dataset_links.py`.
