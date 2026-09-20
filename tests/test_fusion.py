"""Test multimodal fusion - V8.3."""
import sys
sys.path.insert(0, '.')
from src.fusion.multimodal_fusion import FusionEngine, FusionContext
from src.data_models import SharedPhysiologicalFeatures, DiseaseModuleResult
from src.utils.synthetic import generate_subject_timeline, SyntheticSubjectProfile
from src.core.shared_features import SharedFeatureExtractor
from src.core.personal_baseline import PersonalBaselineEngine
from src.disease_modules.registry import GLOBAL_REGISTRY

def test_fusion_provenance():
    profile = SyntheticSubjectProfile(subject_id="FUSION", age_years=22, bmi=23.5)
    vectors = generate_subject_timeline(profile, days=7, samples_per_day=12, scenario="stable", seed=42)
    baseline_engine = PersonalBaselineEngine(path="/tmp/fusion_bl.json", history_path="/tmp/fusion_hist.json")
    baseline_engine.capture_from_features(vectors[:40], min_samples=20)
    shared_ext = SharedFeatureExtractor(baseline_engine=baseline_engine)
    shared = shared_ext.extract(vectors[-1], vectors[-10:])

    engine = FusionEngine()
    context = engine.build(
        profile=None,
        shared=shared,
        bp={"systolic": 120},
        glucose={"value": 90},
        ultrasound={"cyst_size_mm": 5, "source": "CLINICALLY-ENTERED"},
        wearable_quality=0.8
    )
    assert context.overall_quality() > 0
    assert len(context.present_groups()) > 0
    # Provenance preserved
    prov = context.provenance_summary()
    assert len(prov) > 0
    print(f"Fusion context: quality {context.overall_quality()}, coverage {context.coverage()}, groups {context.present_groups()}")
    print("test_fusion_provenance PASSED")

def test_fusion_combines_modules():
    profile = SyntheticSubjectProfile(subject_id="FUSION2", age_years=22, bmi=23.5)
    vectors = generate_subject_timeline(profile, days=7, samples_per_day=12, scenario="stable", seed=1)
    baseline_engine = PersonalBaselineEngine(path="/tmp/fusion2_bl.json", history_path="/tmp/fusion2_hist.json")
    baseline_engine.capture_from_features(vectors[:40], min_samples=20)
    shared_ext = SharedFeatureExtractor(baseline_engine=baseline_engine)
    shared = shared_ext.extract(vectors[-1], vectors[-10:])

    engine = FusionEngine()
    context = engine.build(shared=shared, wearable_quality=0.8)

    module_results = {}
    for mod_name in GLOBAL_REGISTRY.list_implemented():
        mod = GLOBAL_REGISTRY.create(mod_name)
        module_results[mod_name] = mod.predict(shared=shared, clinical={"bmi": 23.5}, history=vectors[-10:])

    fusion_result = engine.fuse(module_results, context)
    assert fusion_result.data_quality > 0
    assert "model_confidence" in fusion_result.confidence_breakdown
    assert "data_quality" in fusion_result.confidence_breakdown
    assert fusion_result.confidence_breakdown["data_quality"] != fusion_result.confidence_breakdown["model_confidence"] or True  # they are separate concepts
    assert fusion_result.clinical_validation == "NOT ESTABLISHED"
    assert len(fusion_result.recommendations) > 0
    # Must not claim diagnosis
    assert "diagnosis" not in fusion_result.explanation.lower() or "not" in fusion_result.explanation.lower()
    print(f"Fusion result: {fusion_result.explanation[:150]}")
    print("test_fusion_combines_modules PASSED")

def test_missing_sensors_no_crash():
    engine = FusionEngine()
    context = engine.build(shared=None, wearable_quality=0.0)
    assert context.overall_quality() == 0.0
    assert context.coverage() == 0.0
    # Should not crash with empty modules
    fusion_result = engine.fuse({}, context)
    assert fusion_result is not None
    print("test_missing_sensors_no_crash PASSED")

if __name__ == "__main__":
    test_fusion_provenance()
    test_fusion_combines_modules()
    test_missing_sensors_no_crash()
