from types import SimpleNamespace

from src.models.complications import compute_complication_signals


def test_complications_with_no_sensor_data_are_withheld():
    shared = SimpleNamespace(
        overall_quality=0.0,
        heart_rate=None,
        hrv_rmssd=None,
        activity_level=0.0,
        sleep_regularity=0.0,
        circadian_disruption=50.0,
    )
    results = compute_complication_signals(shared, {})
    assert results
    assert all(r.signal_percent is None for r in results)
    assert all(r.status == "NOT ESTABLISHED" for r in results)


def test_complication_signal_is_not_claimed_as_probability():
    shared = SimpleNamespace(
        overall_quality=0.8,
        heart_rate=72.0,
        hrv_rmssd=45.0,
        activity_level=40.0,
        sleep_regularity=80.0,
        circadian_disruption=20.0,
    )
    results = compute_complication_signals(shared, {"profile": SimpleNamespace(bmi=23.5, systolic_bp=115, glucose_mg_dl=None, cycle_regularity=90)})
    assert all(0 <= r.signal_percent <= 100 for r in results if r.signal_percent is not None)
    assert all("probability" in r.limitation.lower() for r in results)


if __name__ == "__main__":
    test_complications_with_no_sensor_data_are_withheld()
    test_complication_signal_is_not_claimed_as_probability()
    print("complication tests passed")
