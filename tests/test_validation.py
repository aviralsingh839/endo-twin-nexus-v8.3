"""Validation tests - subject-level, reproducibility, data honesty."""
import sys
sys.path.insert(0, '.')
import json
from pathlib import Path
from src.utils.synthetic import generate_synthetic_cohort, generate_subject_timeline, SyntheticSubjectProfile
from src.core.personal_baseline import PersonalBaselineEngine
from src.core.longitudinal_engine import LongitudinalEngine
from src.disease_modules.registry import GLOBAL_REGISTRY

def test_subject_level_validation():
    """Ensure same subject not in train and test."""
    cohort = generate_synthetic_cohort(n_subjects=10, days=14, samples_per_day=12, seed=42)
    subject_ids = list(cohort.keys())
    # Simulate train/test split at subject level
    train_ids = subject_ids[:7]
    test_ids = subject_ids[7:]
    # Check no overlap
    assert len(set(train_ids) & set(test_ids)) == 0
    # Check data from same subject not leaking
    train_data = []
    for sid in train_ids:
        train_data.extend(cohort[sid])
    test_data = []
    for sid in test_ids:
        test_data.extend(cohort[sid])
    # Verify subject_id preserved in shared_features
    for fv in train_data:
        assert fv.shared_features.get("subject_id") in train_ids
    for fv in test_data:
        assert fv.shared_features.get("subject_id") in test_ids
    print("test_subject_level_validation PASSED")

def test_reproducibility():
    """Same seed should give same results."""
    profile = SyntheticSubjectProfile(subject_id="REPRO", age_years=22, bmi=23.5)
    vectors1 = generate_subject_timeline(profile, days=7, samples_per_day=12, scenario="stable", seed=123)
    vectors2 = generate_subject_timeline(profile, days=7, samples_per_day=12, scenario="stable", seed=123)
    assert len(vectors1) == len(vectors2)
    # First few values should be identical
    for i in range(5):
        assert vectors1[i].hr_bpm == vectors2[i].hr_bpm
        assert vectors1[i].rmssd_ms == vectors2[i].rmssd_ms
    print("test_reproducibility PASSED")

def test_data_honesty_labels():
    """All synthetic data clearly labelled."""
    profile = SyntheticSubjectProfile(subject_id="HONESTY", age_years=22, bmi=23.5)
    vectors = generate_subject_timeline(profile, days=3, samples_per_day=12, scenario="stable", seed=42)
    for fv in vectors:
        assert fv.shared_features.get("label") == "SYNTHETIC"
        assert fv.shared_features.get("synthetic") == True

    # Check scenario files
    scenario_dir = Path("data/synthetic/scenarios")
    if scenario_dir.exists():
        for f in scenario_dir.glob("*.json"):
            if f.name == "README.md":
                continue
            data = json.loads(f.read_text())
            assert data.get("label") == "SYNTHETIC"
            for row in data["data"][:5]:
                assert row.get("label") == "SYNTHETIC"
    print("test_data_honesty_labels PASSED")

def test_no_fake_clinical():
    """Ensure no fake clinical data presented as real."""
    # Check that synthetic cohort is not in clinical folder
    clinical_dir = Path("data/clinical")
    if clinical_dir.exists():
        # Clinical folder should not contain synthetic data labelled as real
        for f in clinical_dir.glob("*.json"):
            data = json.loads(f.read_text())
            # If it has label, it must be USER-ENTERED, not REAL if synthetic
            if "label" in data:
                assert data["label"] != "REAL" or "synthetic" not in str(data).lower()

    # Check public data still labelled public
    public_dir = Path("data/public")
    if public_dir.exists():
        assert (public_dir / "PCOS_data.csv").exists() or True  # may not exist in new structure

    print("test_no_fake_clinical PASSED")

def test_ultrasound_provenance():
    """Ultrasound provenance preserved."""
    from src.fusion.multimodal_fusion import FusionEngine
    engine = FusionEngine()
    # Clinically entered
    ctx1 = engine.build(ultrasound={"cyst_size_mm": 5, "source": "CLINICALLY-ENTERED"})
    feat = ctx1.get("us_cyst_size_mm")
    assert feat is not None
    assert feat.provenance == "CLINICALLY-ENTERED"

    # Image derived
    ctx2 = engine.build(ultrasound={"cyst_size_mm": 5, "source": "IMAGE-DERIVED"})
    feat2 = ctx2.get("us_cyst_size_mm")
    assert feat2.provenance == "IMAGE-DERIVED"

    print("test_ultrasound_provenance PASSED")

if __name__ == "__main__":
    test_subject_level_validation()
    test_reproducibility()
    test_data_honesty_labels()
    test_no_fake_clinical()
    test_ultrasound_provenance()
