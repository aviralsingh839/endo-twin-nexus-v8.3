# AI/ML Guide

ENDO-TWIN separates general physiological modelling from disease-specific modelling. CHRONO-PCOS consumes shared features rather than owning the acquisition/database stack.

Every result records model name/version, feature inputs, data quality, uncertainty, limitations and provenance. Research outputs are not diagnoses.

Staged research tooling: SHAP/Captum for explanations; MLflow/DVC/Optuna for experiment lineage and tuning; tsfresh/sktime for temporal research features. Heavy tooling is introduced only with a concrete workflow and tests.
