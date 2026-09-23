"""Explanation Engine - V8.3.

Every risk signal should explain main contributing factors.

Example:
'Persistent change detected'
Drivers:
- resting HR increased from personal baseline
- HRV decreased from baseline
- sleep regularity decreased
- activity decreased

Then:
'These changes are not specific to one disease and should not be interpreted as a diagnosis.'
"""
from __future__ import annotations

from typing import Dict, List, Optional
from src.data_models import DiseaseModuleResult, SharedPhysiologicalFeatures
from src.core.longitudinal_engine import LongitudinalReport
from src.fusion.multimodal_fusion import FusionResult


class ExplanationEngine:
    """Generates human-readable explanations for risk signals."""

    def explain_longitudinal(self, report: LongitudinalReport) -> str:
        if report.overall_kind == "normal":
            return (
                "No persistent physiological changes detected. "
                "All metrics within personal baseline ranges. "
                "This indicates stable physiology for this individual."
            )
        if report.overall_kind == "missing":
            return "Insufficient longitudinal data for change detection. Collect more data over multiple days."

        lines = [f"Longitudinal analysis: {report.summary}"]
        if report.multimodal_signal:
            lines.append(f"Multimodal signal: {len(report.multimodal_metrics)} related metrics changing: {', '.join(report.multimodal_metrics)}.")
        if report.recovery_detected:
            lines.append("Recovery trend detected - previously abnormal pattern returning toward baseline.")

        for metric, ml in report.per_metric.items():
            if ml.kind in ("persistent", "progressive", "recovery"):
                lines.append(f"- {ml.phrase()} Trend: {ml.trend_direction} (strength {ml.trend_strength:.2f}).")

        lines.append("These changes are not specific to one disease and should not be interpreted as a diagnosis.")
        lines.append(f"Data quality: {report.data_quality:.2f}, Persistence score: {report.persistence_score:.1f}")
        return "\n".join(lines)

    def explain_module(self, result: DiseaseModuleResult, shared: Optional[SharedPhysiologicalFeatures] = None) -> str:
        lines = [
            f"Module: {result.module} v{result.version}",
            f"Signal: {result.signal} ({result.level})",
            f"Confidence: Model {result.confidence:.2f}, Data quality {result.data_quality:.2f}, Clinical validation {result.clinical_validation}",
            "",
            "Contributing factors:",
        ]
        for driver in result.drivers:
            desc = driver.get("description", driver.get("contribution", ""))
            score = driver.get("score", "")
            lines.append(f"- {driver.get('domain')}: {desc} (score {score})")

        if shared and shared.baseline_deviations:
            lines.append("")
            lines.append("Baseline deviations:")
            for metric, z in shared.baseline_deviations.items():
                if abs(z) > 1.5:
                    direction = "above" if z > 0 else "below"
                    lines.append(f"- {metric}: {abs(z):.1f} SD {direction} personal baseline")

        lines.append("")
        lines.append(result.explanation)
        lines.append("")
        lines.append(f"Limitations: {result.limitations}")
        return "\n".join(lines)

    def explain_fusion(self, fusion: FusionResult) -> str:
        lines = [
            "MULTIMODAL FUSION EXPLANATION",
            "=" * 40,
            fusion.explanation,
            "",
            f"Data quality: {fusion.data_quality:.2f}",
            f"Model confidence: {fusion.confidence_breakdown.get('model_confidence', 0):.2f}",
            f"Clinical validation: {fusion.clinical_validation}",
            "",
            "Provenance (where did information come from?):",
        ]
        for group, weight in fusion.context.group_weights().items():
            if weight > 0:
                lines.append(f"- {group}: {weight:.0%} influence")

        if fusion.overall_signals:
            lines.append("")
            lines.append("Elevated research signals:")
            for sig in fusion.overall_signals:
                lines.append(f"- {sig['module']}: {sig['signal']} ({sig['level']}, conf {sig['confidence']:.2f})")

        lines.append("")
        lines.append("Recommendations:")
        for rec in fusion.recommendations:
            lines.append(f"- {rec}")

        lines.append("")
        lines.append("These are research signals, not diagnoses. Discuss relevant findings with qualified healthcare professional.")
        return "\n".join(lines)

    def explain_shared_features(self, shared: SharedPhysiologicalFeatures) -> str:
        lines = [
            "SHARED PHYSIOLOGICAL REPRESENTATION",
            "=" * 40,
            f"Overall quality: {shared.overall_quality:.2f}",
            "",
            "Core vitals:",
            f"- Heart rate: {shared.heart_rate} bpm (resting {shared.resting_heart_rate})",
            f"- HRV RMSSD: {shared.hrv_rmssd} ms",
            f"- Activity: {shared.activity_level:.0f}%",
            f"- Skin temp: {shared.skin_temp_c}°C",
            "",
            "Sleep / Circadian:",
            f"- Sleep duration: {shared.sleep_duration_h}h",
            f"- Sleep regularity: {shared.sleep_regularity:.0f}%",
            f"- Circadian stability: {shared.circadian_stability:.0f}%",
            f"- Day/night activity ratio: {shared.day_night_activity_ratio:.2f}",
            "",
            "Stress / Autonomic:",
            f"- Stress index: {shared.stress_index:.0f}%",
            f"- Autonomic imbalance: {shared.autonomic_imbalance:.0f}%",
            f"- Recovery: {shared.recovery_score:.0f}%",
        ]
        if shared.baseline_deviations:
            lines.append("")
            lines.append("Baseline deviations (personal):")
            for k, v in shared.baseline_deviations.items():
                lines.append(f"- {k}: {v:+.1f} SD")
        if shared.trend_features:
            lines.append("")
            lines.append("Trend features (24h change):")
            for k, v in shared.trend_features.items():
                lines.append(f"- {k}: {v:+.1f}%")
        return "\n".join(lines)

    def generate_report_explanation(self, shared: SharedPhysiologicalFeatures,
                                    longitudinal: LongitudinalReport,
                                    fusion: FusionResult) -> str:
        sections = [
            self.explain_shared_features(shared),
            "",
            "=" * 50,
            "",
            self.explain_longitudinal(longitudinal),
            "",
            "=" * 50,
            "",
            self.explain_fusion(fusion),
        ]
        return "\n".join(sections)
