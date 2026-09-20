"""V8.6.1 science guard tests."""
from src.data_models import SharedPhysiologicalFeatures
from src.disease_modules.pcos import PCOSModule


def _shared():
    return SharedPhysiologicalFeatures(
        heart_rate=72,
        hrv_rmssd=48,
        activity_level=35,
        skin_temp_c=32.5,
        overall_quality=0.9,
    )


def test_pcos_does_not_generate_disease_signal_from_wearables_alone():
    result = PCOSModule().predict(_shared(), clinical=None, ultrasound=None)
    assert result.level == "unknown"
    assert result.signal == "insufficient_disease_evidence"
    assert result.extra["research_index"] is None


def test_adolescent_context_does_not_use_ultrasound_as_diagnostic_criterion():
    clinical = {
        "age_years": 16,
        "years_post_menarche": 4,
        "usual_cycle_length_days": 50,
        "clinical_hyperandrogenism": False,
        "pcom_present": True,
        "exclusions_completed": True,
    }
    result = PCOSModule().predict(_shared(), clinical=clinical)
    assert result.level == "unknown"
    assert result.extra["diagnostic_context"]["pcom_or_amh"] is True
    assert result.extra["diagnostic_context"]["adolescent"] is True


def test_adult_context_requires_supported_diagnostic_groups_and_exclusions():
    clinical = {
        "age_years": 27,
        "usual_cycle_length_days": 50,
        "clinical_hyperandrogenism": True,
        "exclusions_completed": True,
    }
    result = PCOSModule().predict(_shared(), clinical=clinical)
    assert result.signal == "pcos_context_signal"
    assert result.extra["research_index_is_probability"] is False
    assert result.extra["diagnostic_context"]["criterion_groups"] >= 2
