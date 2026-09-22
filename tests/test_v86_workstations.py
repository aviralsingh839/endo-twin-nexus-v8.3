from desktop.demo_data import condition_list, sorted_cases

def test_demo_cases_have_pcos_and_priority_order():
    rows = sorted_cases()
    assert any(x.condition == "CHRONO-PCOS" for x in rows)
    order = {"High": 4, "Elevated": 3, "Moderate": 2, "Low": 1, "Unknown": 0}
    tiers = [order[x.tier] for x in rows]
    assert tiers == sorted(tiers, reverse=True)

def test_condition_filter_and_risk_sort():
    rows = sorted_cases("CHRONO-PCOS", "risk")
    assert rows and all(x.condition == "CHRONO-PCOS" for x in rows)
    assert [x.risk for x in rows] == sorted([x.risk for x in rows], reverse=True)
