"""Test personal baseline engine - V8.3."""
import time
import sys
sys.path.insert(0, '.')
from src.core.personal_baseline import PersonalBaselineEngine
from src.utils.synthetic import generate_subject_timeline, SyntheticSubjectProfile

def test_baseline_accuracy():
    profile = SyntheticSubjectProfile(subject_id="TEST_BASELINE", age_years=22, bmi=23.5,
                                      resting_hr_baseline=70, hrv_baseline=50)
    vectors = generate_subject_timeline(profile, days=10, samples_per_day=24, scenario="stable", seed=42)
    engine = PersonalBaselineEngine(path="/tmp/test_baseline_accuracy.json", history_path="/tmp/test_baseline_hist.json")
    baseline = engine.capture_from_features(vectors, min_samples=30)
    assert baseline.has_data
    assert baseline.confidence > 0.5
    assert "hr_bpm" in baseline.stats or "resting_hr_bpm" in baseline.stats
    # Check median close to baseline
    hr_stat = baseline.stats.get("hr_bpm") or baseline.stats.get("resting_hr_bpm")
    if hr_stat:
        assert abs(hr_stat.median - 70) < 15, f"median {hr_stat.median} too far from 70"
    print("test_baseline_accuracy PASSED")

def test_baseline_comparison():
    profile = SyntheticSubjectProfile(subject_id="TEST_COMP", age_years=22, bmi=23.5,
                                      resting_hr_baseline=68, hrv_baseline=48)
    vectors = generate_subject_timeline(profile, days=5, samples_per_day=24, scenario="stable", seed=1)
    engine = PersonalBaselineEngine(path="/tmp/test_comp.json", history_path="/tmp/test_comp_hist.json")
    baseline = engine.capture_from_features(vectors, min_samples=20)
    # Current vs baseline
    comp = engine.compare_current_vs_baseline(vectors[-1])
    assert "hr_bpm" in comp or "resting_hr_bpm" in comp
    # Should have status
    for k, v in comp.items():
        if v["current"] is not None and (v.get("baseline") is not None or v.get("baseline_median") is not None):
            assert "status" in v
            assert v["status"] in ("normal", "mild_deviation", "moderate_deviation", "significant_deviation", "no_data", "no_baseline")
    print("test_baseline_comparison PASSED")

def test_baseline_min_obs():
    profile = SyntheticSubjectProfile(subject_id="TEST_MIN", age_years=22, bmi=23.5)
    vectors = generate_subject_timeline(profile, days=1, samples_per_day=5, scenario="stable", seed=2)
    engine = PersonalBaselineEngine(path="/tmp/test_min.json", history_path="/tmp/test_min_hist.json")
    try:
        baseline = engine.capture_from_features(vectors, min_samples=100)
        assert False, "Should have raised ValueError for insufficient samples"
    except ValueError:
        print("test_baseline_min_obs PASSED (correctly rejected insufficient data)")

if __name__ == "__main__":
    test_baseline_accuracy()
    test_baseline_comparison()
    test_baseline_min_obs()
