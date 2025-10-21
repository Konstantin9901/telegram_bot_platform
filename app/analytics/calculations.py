from datetime import date
from typing import Optional

def calculate_roi_metrics(start_date: date, end_date: date, advertiser_id: Optional[int] = None) -> dict:
    """
    Возвращает метрики ROI, CTR, CPM, CPC на основе фиктивных данных.
    Позже можно заменить на реальные SQL-запросы.
    """

    # 🔧 Фиктивные данные (эмулируем выборку из БД)
    impressions = 100_000     # показы
    clicks = 4_500            # клики
    cost = 1500.0             # затраты ($)
    revenue = 3500.0          # доход ($)

    # 📊 Формулы
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

    # ✅ Проверка: все ключи присутствуют и являются float
    assert all(k in metrics for k in ["roi", "ctr", "cpm", "cpc"]), "❌ Missing keys in ROI metrics"
    assert all(isinstance(metrics[k], float) for k in metrics), "❌ Non-float value in ROI metrics"

    return metrics

