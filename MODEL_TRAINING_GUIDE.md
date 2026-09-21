# Model Training Guide

1. Define target and clinical/research question.
2. Freeze feature definitions and algorithm versions.
3. Split data at the subject/patient level where leakage is possible.
4. Version dataset, preprocessing, model and training run.
5. Track metrics and limitations.
6. Preserve a held-out evaluation set.
7. Never convert missing data into fabricated positives/negatives.
8. Register the trained model only with its actual lineage.

No model in this repository should be described as clinically validated unless evidence is actually present.
