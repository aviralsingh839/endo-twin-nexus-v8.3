"""Menstrual symptom terminology normalizer for ENDO-TWIN / CHRONO-PCOS.

This module converts clinician/patient-entered free-text or structured symptom
terms into a stable vocabulary for longitudinal research analysis.

IMPORTANT:
- Terms are contextual descriptors, not diagnoses.
- These terms are NOT injected into the existing 37-feature clinical PCOS
  classifier because that trained artifact does not contain these inputs.
- Vocabulary is based only on legible terms from the handwritten research note.
- Ambiguous or illegible phrases are deliberately excluded.
- A future menstrual-context predictor must be trained on labelled,
  patient-level data before these terms affect a predictive output.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, Iterable, List
import re


@dataclass(frozen=True)
class MenstrualTerm:
    key: str
    display_name: str
    aliases: tuple[str, ...]
    domain: str
    temporal_context: str
    source_note: str


VOCABULARY: tuple[MenstrualTerm, ...] = (
    MenstrualTerm(
        "heavy_flow_initial_days",
        "Higher flow during initial days",
        ("higher flow", "heavy flow", "more flow", "increased flow"),
        "flow",
        "during_period",
        "handwritten research note",
    ),
    MenstrualTerm(
        "lower_back_pain",
        "Lower back pain",
        ("lower back pain", "pain in lower back", "back pain", "lumbar pain"),
        "pain",
        "during_period",
        "handwritten research note",
    ),
    MenstrualTerm(
        "lower_abdominal_pain",
        "Lower abdominal pain",
        ("lower abdomen pain", "pain in lower abdomen", "lower abdominal pain", "pelvic pain"),
        "pain",
        "during_period",
        "handwritten research note",
    ),
    MenstrualTerm(
        "typical_duration_5_6_days",
        "Typical bleeding duration 5–6 days",
        ("5-6 days", "5 to 6 days", "five to six days"),
        "duration",
        "during_period",
        "handwritten research note",
    ),
    MenstrualTerm(
        "food_cravings",
        "Food cravings",
        ("food cravings", "cravings of food", "craving food", "cravings"),
        "appetite",
        "during_period",
        "handwritten research note",
    ),
    MenstrualTerm(
        "irritability",
        "Irritability",
        ("irritation", "irritable", "irritability"),
        "mood",
        "during_period",
        "handwritten research note",
    ),
    MenstrualTerm(
        "sleep_change",
        "Sleep-cycle change",
        ("sleep cycle change", "sleep changes", "sleep disturbance"),
        "sleep",
        "during_period",
        "handwritten research note",
    ),
    MenstrualTerm(
        "uneasy_feeling",
        "Feeling uneasy",
        ("feeling uneasy", "uneasy", "restless feeling"),
        "mood",
        "during_period",
        "handwritten research note",
    ),
    MenstrualTerm(
        "white_discharge",
        "White discharge",
        ("white discharge", "normal white discharge"),
        "discharge",
        "during_period_or_menstrual_window",
        "handwritten research note",
    ),
    MenstrualTerm(
        "lifestyle_unchanged",
        "Usual lifestyle / no alteration",
        ("usual lifestyle", "no alteration", "lifestyle unchanged"),
        "function",
        "during_period",
        "handwritten research note",
    ),
    MenstrualTerm(
        "mental_health_disturbance",
        "Mental-health disturbance",
        ("mental health disturbance", "mental-health disturbance"),
        "mental_health",
        "during_period",
        "handwritten research note",
    ),
)


def _norm(text: Any) -> str:
    value = str(text or "").lower().strip()
    value = value.replace("–", "-").replace("—", "-")
    value = re.sub(r"[^a-z0-9\-\s]", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def vocabulary_metadata() -> List[Dict[str, Any]]:
    return [asdict(term) for term in VOCABULARY]


def normalize_terms(terms: Iterable[Any]) -> Dict[str, Any]:
    """Normalize structured/free-text terms into stable research features.

    Strings and dictionaries are supported. For dictionaries, common
    keys symptom_type/type/term/name/notes are inspected.

    Unknown text is retained as unmapped_terms rather than silently converted.
    """
    found: List[str] = []
    evidence: Dict[str, List[str]] = {}
    unmapped: List[str] = []

    for item in terms or []:
        if isinstance(item, dict):
            raw_parts = [
                item.get("symptom_type"),
                item.get("type"),
                item.get("term"),
                item.get("name"),
                item.get("notes"),
            ]
            raw = " ".join(str(v) for v in raw_parts if v not in (None, ""))
        else:
            raw = str(item)

        text = _norm(raw)
        if not text:
            continue

        matched = False
        for term in VOCABULARY:
            aliases = (_norm(term.key), _norm(term.display_name), *map(_norm, term.aliases))
            if any(alias and (alias in text or text in alias) for alias in aliases):
                if term.key not in found:
                    found.append(term.key)
                evidence.setdefault(term.key, []).append(raw)
                matched = True

        if not matched:
            unmapped.append(raw)

    domains = sorted({term.domain for term in VOCABULARY if term.key in found})
    return {
        "feature_schema": "menstrual_context_v1",
        "terms_found": found,
        "term_count": len(found),
        "domains": domains,
        "evidence": evidence,
        "unmapped_terms": unmapped,
        "provenance": "CLINICALLY_ENTERED/USER_ENTERED vocabulary normalization",
        "label": "RESEARCH_FEATURE",
        "model_ready": False,
        "model_ready_reason": (
            "Terminology is normalized for longitudinal research. The existing "
            "37-feature PCOS classifier does not accept these terms."
        ),
    }


def summarize_context(similar_terms: Iterable[Any], dissimilar_terms: Iterable[Any]) -> Dict[str, Any]:
    """Represent similar-vs-dissimilar symptom observations without inference."""
    similar = normalize_terms(similar_terms)
    dissimilar = normalize_terms(dissimilar_terms)
    return {
        "feature_schema": "menstrual_context_comparison_v1",
        "similar": similar,
        "dissimilar": dissimilar,
        "comparison_available": bool(
            similar["terms_found"] or dissimilar["terms_found"]
        ),
        "interpretation": (
            "Descriptive comparison only. Similar/dissimilar symptom presence "
            "must not be interpreted as a disease label."
        ),
    }