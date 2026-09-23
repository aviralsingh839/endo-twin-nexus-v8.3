"""
Chrono-Metabolic Fingerprinting V8.3+

Combines:
- Circadian patterns (sleep-wake, HR, temp)
- Autonomic regulation (HRV)
- Variability (HRV metrics, activity)
- Activity (MPU6050 motion)
- Temperature (DS18B20 skin temp)
- Metabolic signals (derived)
- Longitudinal tracking (baseline, trends)

Distinguishes:
- Established measurements (HR, temp directly measured)
- Derived features (HRV, activity counts)
- Experimental research signals (chrono-metabolic fingerprint)
- ML predictions (risk signals, not diagnosis)
- Clinical interpretation (requires professional evaluation)

Explainability: each component has source, quality, confidence, limitations
"""
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from enum import Enum

class SignalCategory(Enum):
    ESTABLISHED_MEASUREMENT = "established_measurement"  # Directly measured HR, temp
    DERIVED_FEATURE = "derived_feature"  # HRV calculated from PPG
    EXPERIMENTAL_RESEARCH = "experimental_research"  # Chrono-metabolic fingerprint
    ML_PREDICTION = "ml_prediction"  # Risk signals from models
    CLINICAL_INTERPRETATION = "clinical_interpretation"  # Requires clinician

@dataclass
class ChronoComponent:
    name: str
    value: Any
    category: SignalCategory
    quality: float  # 0-1
    confidence: Optional[float] = None  # 0-1 if applicable
    source: str = ""
    limitations: str = ""
    explainability: str = ""

class ChronoMetabolicFingerprint:
    """
    Chrono-metabolic fingerprinting engine.

    Combines circadian, autonomic, variability, activity, temp, metabolic, longitudinal
    into fingerprint with clear provenance and explainability.
    """

    def __init__(self):
        self.version = "8.3+"
        self.components: List[ChronoComponent] = []

    def add_component(self, comp: ChronoComponent):
        self.components.append(comp)

    def build_from_features(self, features: Dict[str, Any], quality_scores: Dict[str, float]) -> Dict[str, Any]:
        """
        Build fingerprint from extracted features.
        """
        self.components = []

        # Circadian - experimental research, model-inferred
        if 'sleep_regularity' in features or 'circadian' in str(features):
            self.add_component(ChronoComponent(
                name='circadian_rhythm',
                value=features.get('sleep_regularity', features.get('circadian_pattern', 'unknown')),
                category=SignalCategory.EXPERIMENTAL_RESEARCH,
                quality=quality_scores.get('ppg', 0.5),
                source='PPG-derived sleep-wake estimation, model-inferred',
                limitations='Sleep-wake from wrist PPG is model-inferred, not polysomnography, requires validation',
                explainability='Estimated from HR/HRV circadian variation, 24h pattern analysis'
            ))

        # Autonomic - derived + experimental
        if 'hrv_rmssd' in features or 'hrv' in str(features).lower():
            self.add_component(ChronoComponent(
                name='autonomic_regulation',
                value=features.get('hrv_rmssd', 0),
                category=SignalCategory.DERIVED_FEATURE,
                quality=quality_scores.get('hrv', quality_scores.get('ppg', 0.5)),
                source='PPG-derived HRV, time-domain RMSSD',
                limitations='PPG-derived HRV less accurate than ECG, motion artifacts affect',
                explainability='RMSSD reflects parasympathetic activity, lower values may indicate autonomic dysregulation research signal'
            ))

        # Variability
        if 'hrv' in features or 'variability' in features:
            self.add_component(ChronoComponent(
                name='variability_index',
                value=features.get('hrv_variability', features.get('variability', 0)),
                category=SignalCategory.DERIVED_FEATURE,
                quality=quality_scores.get('ppg', 0.5),
                source='PPG HR variability',
                limitations='Requires good quality PPG, motion artifacts reduce reliability',
                explainability='Variability metrics from HR time series'
            ))

        # Activity - established measurement via MPU6050
        if any(k in features for k in ['activity', 'motion', 'activity_level', 'motion_activity']):
            self.add_component(ChronoComponent(
                name='activity_level',
                value=features.get('activity_level', features.get('motion_activity', features.get('activity', 0))),
                category=SignalCategory.ESTABLISHED_MEASUREMENT,
                quality=quality_scores.get('motion', 0.8),
                source='MPU6050 accelerometer, activity counts',
                limitations='Wrist activity, not whole-body calorimetry',
                explainability='Accelerometer magnitude, classified into sedentary/light/moderate'
            ))

        # Temperature - established
        if any(k in features for k in ['temperature', 'temp', 'skin_temperature']):
            self.add_component(ChronoComponent(
                name='skin_temperature',
                value=features.get('skin_temperature', features.get('temperature', features.get('temp', 0))),
                category=SignalCategory.ESTABLISHED_MEASUREMENT,
                quality=quality_scores.get('temperature', 0.8),
                source='DS18B20 skin temperature sensor',
                limitations='Skin temp, not core temp, affected by environment',
                explainability='Direct temperature measurement, circadian variation'
            ))

        # Metabolic - experimental research, derived
        if 'metabolic' in features or True:  # Always include as experimental
            self.add_component(ChronoComponent(
                name='metabolic_signal',
                value=features.get('metabolic_index', 0),
                category=SignalCategory.EXPERIMENTAL_RESEARCH,
                quality=min(quality_scores.values()) if quality_scores else 0.5,
                source='Multimodal combination: HR, HRV, activity, temp',
                limitations='Experimental research signal, not clinical metabolic measurement, requires validation',
                explainability='Research combination of autonomic, activity, temperature patterns hypothesized to relate to metabolic regulation'
            ))

        # Longitudinal - if baseline exists
        if 'baseline_deviation' in features:
            self.add_component(ChronoComponent(
                name='longitudinal_trend',
                value=features.get('baseline_deviation', 0),
                category=SignalCategory.EXPERIMENTAL_RESEARCH,
                quality=0.6,
                source='Personal baseline comparison, longitudinal tracking',
                limitations='Requires sufficient history, baseline calibration needed',
                explainability='Deviation from personal baseline, not population norm'
            ))

        # Build fingerprint dict
        fingerprint = {
            'version': self.version,
            'components': [
                {
                    'name': c.name,
                    'value': c.value,
                    'category': c.category.value,
                    'quality': c.quality,
                    'confidence': c.confidence,
                    'source': c.source,
                    'limitations': c.limitations,
                    'explainability': c.explainability
                } for c in self.components
            ],
            'disclaimer': 'Research / experimental chrono-metabolic fingerprint - not a medical diagnosis, requires clinical evaluation',
            'provenance': 'V8.3+ chrono-metabolic engine, distinguishes established/derived/experimental/ML/clinical'
        }

        return fingerprint

    def get_summary_text(self) -> str:
        """Understandable language summary"""
        if not self.components:
            return "No chrono-metabolic data yet - collect sensor data"

        texts = []
        for c in self.components:
            if c.category == SignalCategory.ESTABLISHED_MEASUREMENT:
                texts.append(f"{c.name}: {c.value} (measured, quality {c.quality:.2f})")
            elif c.category == SignalCategory.DERIVED_FEATURE:
                texts.append(f"{c.name}: {c.value} (derived, quality {c.quality:.2f})")
            elif c.category == SignalCategory.EXPERIMENTAL_RESEARCH:
                texts.append(f"{c.name}: {c.value} (experimental research, quality {c.quality:.2f}) - {c.limitations[:50]}...")
            elif c.category == SignalCategory.ML_PREDICTION:
                texts.append(f"{c.name}: {c.value} (ML prediction, confidence {c.confidence}) - research risk signal")

        return "\n".join(texts) + "\n\nResearch / risk-screening - not a medical diagnosis"

__all__ = ['ChronoMetabolicFingerprint', 'ChronoComponent', 'SignalCategory']
