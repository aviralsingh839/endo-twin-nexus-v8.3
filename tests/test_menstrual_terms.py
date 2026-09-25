import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from disease_models.chrono_pcos.features.menstrual_terms import (
    normalize_terms,
    summarize_context,
    vocabulary_metadata,
)


def test_legible_menstrual_terms_are_normalized():
    result = normalize_terms([
        "higher flow during initial days",
        "pain in lower back and lower abdomen",
        "5-6 days common",
        "cravings of food",
        "irritation",
        "feeling uneasy",
        "normal white discharge",
        "usual lifestyle",
        "mental health disturbance",
    ])
    assert "heavy_flow_initial_days" in result["terms_found"]
    assert "lower_back_pain" in result["terms_found"]
    assert "lower_abdominal_pain" in result["terms_found"]
    assert "food_cravings" in result["terms_found"]
    assert "irritability" in result["terms_found"]
    assert "white_discharge" in result["terms_found"]
    assert result["model_ready"] is False


def test_one_phrase_can_contain_multiple_terms():
    result = normalize_terms(["pain in lower back and lower abdomen"])
    assert result["terms_found"] == ["lower_back_pain", "lower_abdominal_pain"]


def test_unknown_terms_are_not_silently_mapped():
    result = normalize_terms(["an unclear handwritten phrase"])
    assert result["terms_found"] == []
    assert result["unmapped_terms"] == ["an unclear handwritten phrase"]


def test_similar_vs_dissimilar_is_descriptive_only():
    result = summarize_context(
        ["lower back pain", "food cravings"],
        ["no alteration"],
    )
    assert result["comparison_available"] is True
    assert result["interpretation"].startswith("Descriptive comparison only")


def test_vocabulary_has_stable_schema():
    metadata = vocabulary_metadata()
    assert metadata
    assert all(
        {"key", "display_name", "aliases", "domain", "temporal_context", "source_note"}
        <= item.keys()
        for item in metadata
    )