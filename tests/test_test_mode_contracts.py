from src.endo_twin.testing.test_mode import TestStatus, classify_signal_failure


def test_disconnect_is_explicit_failure():
    result = classify_signal_failure("MAX30102", connected=False)
    assert result.status is TestStatus.FAIL
    assert result.code == "DEVICE_UNAVAILABLE"


def test_invalid_packet_does_not_produce_value():
    result = classify_signal_failure("Serial", packet_ok=False)
    assert result.code == "PACKET_INVALID"


def test_low_quality_is_not_silently_passed():
    result = classify_signal_failure("PPG", samples=100, quality=0.2)
    assert result.status is TestStatus.WARN
    assert result.code == "LOW_SIGNAL_QUALITY"
