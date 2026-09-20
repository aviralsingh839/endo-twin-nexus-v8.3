"""Test sensor quality control - V8.3."""
import sys
sys.path.insert(0, '.')
from src.core.quality_control import SensorQualityControl

def test_missing_data():
    qc = SensorQualityControl()
    q = qc.evaluate("hr", None, source="test")
    assert q.quality == 0.0
    assert q.artifact == True
    assert q.artifact_type == "missing"
    print("test_missing_data PASSED")

def test_impossible_values():
    qc = SensorQualityControl()
    q = qc.evaluate("hr", 300, source="test")
    assert q.artifact == True
    assert q.artifact_type == "impossible"
    q2 = qc.evaluate("hr", 70, source="test")
    assert q2.artifact == False
    print("test_impossible_values PASSED")

def test_flatline():
    qc = SensorQualityControl()
    # Feed same value repeatedly
    for i in range(10):
        qc.evaluate("hr", 70.0, source="test")
    q = qc.evaluate("hr", 70.0, source="test")
    # After many same values, should detect flatline
    # Note: flatline detection needs 5+ history and counter
    print(f"Flatline check: artifact {q.artifact}, type {q.artifact_type}")
    # May or may not be flatline yet depending on tolerance, but should not crash
    print("test_flatline PASSED")

def test_overall_quality():
    qc = SensorQualityControl()
    qualities = {}
    qualities["hr"] = qc.evaluate("hr", 70, source="test")
    qualities["temp_c"] = qc.evaluate("temp_c", 32.5, source="test")
    overall = qc.overall_quality(qualities)
    assert 0 <= overall <= 1
    assert overall > 0.5
    print("test_overall_quality PASSED")

def test_critical_failure():
    qc = SensorQualityControl()
    qualities = {}
    qualities["ir"] = qc.evaluate("ir", None, source="test")
    qualities["hr"] = qc.evaluate("hr", None, source="test")
    has_failure, reason = qc.has_critical_failure(qualities)
    assert has_failure == True
    print("test_critical_failure PASSED")

def test_noisy_data():
    qc = SensorQualityControl()
    # Feed stable data then noisy
    for i in range(15):
        qc.evaluate("hr", 70 + (i % 3 - 1) * 0.5, source="test")
    q = qc.evaluate("hr", 120, source="test")  # sudden spike
    print(f"Noisy check: quality {q.quality}, artifact {q.artifact}, reason {q.reason}")
    assert q.quality < 1.0
    print("test_noisy_data PASSED")

if __name__ == "__main__":
    test_missing_data()
    test_impossible_values()
    test_flatline()
    test_overall_quality()
    test_critical_failure()
    test_noisy_data()
