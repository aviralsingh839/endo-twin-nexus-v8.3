"""Executable test-mode contracts for ENDO-TWIN sensors and pipeline failures.

This module is deliberately deterministic and side-effect free. It is used by
unit/integration tests and can later be wired to the Doctor workstation.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional


class TestStatus(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"


@dataclass(frozen=True)
class TestResult:
    component: str
    status: TestStatus
    code: str
    message: str
    evidence: Dict[str, Any]


def classify_signal_failure(component: str, *, connected: bool = True,
                            samples: Optional[int] = None,
                            quality: Optional[float] = None,
                            packet_ok: bool = True,
                            sampling_rate_ok: bool = True) -> TestResult:
    """Return an explicit state; never synthesize a measurement on failure."""
    if not connected:
        return TestResult(component, TestStatus.FAIL, "DEVICE_UNAVAILABLE", "Device is not connected", {})
    if not packet_ok:
        return TestResult(component, TestStatus.FAIL, "PACKET_INVALID", "Incoming packet failed validation", {})
    if not sampling_rate_ok:
        return TestResult(component, TestStatus.WARN, "SAMPLE_RATE_MISMATCH", "Observed sampling rate does not match configured profile", {})
    if samples == 0:
        return TestResult(component, TestStatus.FAIL, "FLATLINE", "No usable samples received", {"samples": 0})
    if quality is not None and quality < 0.5:
        return TestResult(component, TestStatus.WARN, "LOW_SIGNAL_QUALITY", "Signal quality is below the research threshold", {"quality": quality})
    return TestResult(component, TestStatus.PASS, "OK", "Component test passed", {"samples": samples, "quality": quality})
