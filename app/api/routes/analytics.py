from fastapi import APIRouter, Query, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import date
from sqlalchemy.orm import Session
import matplotlib.pyplot as plt
from io import BytesIO
from fastapi.responses import StreamingResponse

# 🔗 Импорт расчётной логики
from app.analytics.calculations import calculate_roi_metrics
from app.database import get_db
from app.services.analytics import aggregate_by_day, calculate_roi
from app.dependencies import get_current_advertiser
from app.models import Advertiser  # ✅ Заменили User на Advertiser

router = APIRouter()

# 📦 Модель ответа для общей ROI-аналитики
class ROIResponse(BaseModel):
    roi: float
    ctr: float
    cpm: float
    cpc: float

# 📊 Эндпоинт ROI-аналитики (общая сводка)
@router.get("/analytics/roi", response_model=ROIResponse)
def get_roi_analytics(
    start_date: date = Query(..., description="Формат: YYYY-MM-DD", example="2025-10-01"),
    end_date: date = Query(..., description="Формат: YYYY-MM-DD", example="2025-10-31"),
    advertiser_id: Optional[int] = Query(None, description="ID рекламодателя (опционально)"),
    advertiser: Advertiser = Depends(get_current_advertiser)
):
    metrics = calculate_roi_metrics(start_date, end_date, advertiser_id)
    print("📊 METRICS RETURNED:", metrics)
    return ROIResponse(**metrics)

# 📦 Модель ответа для ROI по дням
class DailyROIResponse(BaseModel):
    date: str
    actions: int
    reward: float
    roi_percent: float

# 📈 Эндпоинт ROI по дням для WebApp
@router.get("/analytics/roi/daily", response_model=list[DailyROIResponse])
def get_daily_roi(
    start_date: date = Query(..., description="Формат: YYYY-MM-DD"),
    end_date: date = Query(..., description="Формат: YYYY-MM-DD"),
    campaign_id: int = Query(..., description="ID кампании"),
    cost_per_action: float = Query(..., description="Стоимость одного действия"),
    db: Session = Depends(get_db),
    advertiser: Advertiser = Depends(get_current_advertiser)
):
    daily_stats = aggregate_by_day(db, campaign_id)
    filtered = [
        s for s in daily_stats
        if start_date <= date.fromisoformat(s["day"]) <= end_date
    ]

    result = []
    for s in filtered:
        cost = cost_per_action * s["actions"]
        roi = ((s["reward"] - cost) / cost * 100) if cost > 0 else 0
        result.append(DailyROIResponse(
            date=s["day"],
            actions=s["actions"],
            reward=s["reward"],
            roi_percent=round(roi, 2)
        ))

    return result

# 🖼️ Эндпоинт PNG-графика ROI по дням
@router.get("/analytics/roi/plot")
def plot_roi_by_day(
    start_date: date = Query(..., description="Формат: YYYY-MM-DD"),
    end_date: date = Query(..., description="Формат: YYYY-MM-DD"),
    campaign_id: int = Query(..., description="ID кампании"),
    cost_per_action: float = Query(..., description="Стоимость одного действия"),
    db: Session = Depends(get_db),
    advertiser: Advertiser = Depends(get_current_advertiser)
):
    daily_stats = aggregate_by_day(db, campaign_id)
    filtered = [
        s for s in daily_stats
        if start_date <= date.fromisoformat(s["day"]) <= end_date
    ]

    dates = [s["day"] for s in filtered]
    roi_values = []
    for s in filtered:
        cost = cost_per_action * s["actions"]
        roi = ((s["reward"] - cost) / cost * 100) if cost > 0 else 0
        roi_values.append(round(roi, 2))

    plt.figure(figsize=(12, 6))
    plt.plot(dates, roi_values, marker='o', linestyle='-', color='blue')
    plt.title("ROI по дням")
    plt.xlabel("Дата")
    plt.ylabel("ROI (%)")
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.tight_layout()

    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")






