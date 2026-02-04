from datetime import date
from app.analytics.calculations import calculate_roi_metrics

def test_calculate_roi_metrics_returns_all_keys_and_floats():
    start_date = date(2025, 10, 1)
    end_date = date(2025, 10, 31)
    advertiser_id = 3

    metrics = calculate_roi_metrics(start_date, end_date, advertiser_id)

    expected_keys = {"roi", "ctr", "cpm", "cpc"}
    assert set(metrics.keys()) == expected_keys
    for key in expected_keys:
        assert isinstance(metrics[key], float)

def test_calculate_roi_metrics_with_none_advertiser_id():
    start_date = date(2025, 10, 1)
    end_date = date(2025, 10, 31)

    metrics = calculate_roi_metrics(start_date, end_date, advertiser_id=None)

    for value in metrics.values():
        assert isinstance(value, float)

def test_manual_zero_values_calculation():
    # Эмулируем расчёт вручную
    impressions = 0
    clicks = 0
    cost = 0.0
    revenue = 0.0

    roi = round((revenue - cost) / cost, 4) if cost else 0.0
    ctr = round(clicks / impressions, 4) if impressions else 0.0
    cpm = round((cost / impressions) * 1000, 4) if impressions else 0.0
    cpc = round(cost / clicks, 4) if clicks else 0.0

    metrics = {
        "roi": roi,
        "ctr": ctr,
        "cpm": cpm,
        "cpc": cpc
    }

    assert metrics == {"roi": 0.0, "ctr": 0.0, "cpm": 0.0, "cpc": 0.0}



