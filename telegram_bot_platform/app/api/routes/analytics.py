import matplotlib
matplotlib.use("Agg")  # ✅ Отключает GUI, безопасно для серверной генерации PNG

import matplotlib.pyplot as plt
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
from app.models import Advertiser

router = APIRouter(prefix="/analytics")

# 📦 Модель ответа для общей ROI-аналитики
class ROIResponse(BaseModel):
    roi: float
    ctr: float
    cpm: float
    cpc: float

# 📊 Эндпоинт ROI-аналитики (общая сводка)
@router.get("/roi", response_model=ROIResponse)
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

# 📈 Эндпоинт ROI по дням для WebApp (авторизация временно отключена)
@router.get("/roi/daily", response_model=list[DailyROIResponse])
def get_daily_roi(
    start_date: date = Query(..., description="Формат: YYYY-MM-DD"),
    end_date: date = Query(..., description="Формат: YYYY-MM-DD"),
    campaign_id: int = Query(..., description="ID кампании"),
    cost_per_action: float = Query(..., description="Стоимость одного действия"),
    db: Session = Depends(get_db)
    # advertiser: Advertiser = Depends(get_current_advertiser)  ← временно отключено
):   
    if campaign_id == 2:
        # 📦 Тестовые данные для Кампании 2
        test_data = [
            {"date": "2025-10-01", "actions": 1, "reward": 120},
            {"date": "2025-10-02", "actions": 2, "reward": 180},
            {"date": "2025-10-03", "actions": 3, "reward": 360},
            {"date": "2025-10-04", "actions": 2, "reward": 220},
            {"date": "2025-10-05", "actions": 1, "reward": 80},
            {"date": "2025-10-06", "actions": 2, "reward": 250},
            {"date": "2025-10-07", "actions": 3, "reward": 270},
            {"date": "2025-10-08", "actions": 2, "reward": 240},
            {"date": "2025-10-09", "actions": 1, "reward": 60},
            {"date": "2025-10-10", "actions": 2, "reward": 200},
            {"date": "2025-10-11", "actions": 3, "reward": 390},
            {"date": "2025-10-12", "actions": 2, "reward": 180},
            {"date": "2025-10-13", "actions": 1, "reward": 110},
            {"date": "2025-10-14", "actions": 2, "reward": 160},
            {"date": "2025-10-15", "actions": 3, "reward": 390},
            {"date": "2025-10-16", "actions": 2, "reward": 240},
            {"date": "2025-10-17", "actions": 1, "reward": 70},
            {"date": "2025-10-18", "actions": 2, "reward": 220},
            {"date": "2025-10-19", "actions": 3, "reward": 330},
            {"date": "2025-10-20", "actions": 2, "reward": 180},
            {"date": "2025-10-21", "actions": 1, "reward": 100},
            {"date": "2025-10-22", "actions": 2, "reward": 260},
            {"date": "2025-10-23", "actions": 3, "reward": 390},
            {"date": "2025-10-24", "actions": 2, "reward": 160},
            {"date": "2025-10-25", "actions": 1, "reward": 90},
            {"date": "2025-10-26", "actions": 2, "reward": 240},
            {"date": "2025-10-27", "actions": 3, "reward": 330},
            {"date": "2025-10-28", "actions": 2, "reward": 200},
            {"date": "2025-10-29", "actions": 1, "reward": 110},
            {"date": "2025-10-30", "actions": 2, "reward": 180},
            {"date": "2025-10-31", "actions": 3, "reward": 390}
        ]

        filtered = [
            s for s in test_data
            if start_date <= date.fromisoformat(s["date"]) <= end_date
        ]

        result = []
        for s in filtered:
            cost = cost_per_action * s["actions"]
            roi = ((s["reward"] - cost) / cost * 100) if cost > 0 else 0
            result.append(DailyROIResponse(
                date=s["date"],
                actions=s["actions"],
                reward=s["reward"],
                roi_percent=round(roi, 2)
            ))

        return result

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

# 🖼️ Эндпоинт PNG-графика ROI по дням (с заглушкой при отсутствии данных)
@router.get("/roi/plot")
def plot_roi_by_day(
    start_date: date = Query(..., description="Формат: YYYY-MM-DD"),
    end_date: date = Query(..., description="Формат: YYYY-MM-DD"),
    campaign_id: int = Query(..., description="ID кампании"),
    cost_per_action: float = Query(..., description="Стоимость одного действия"),
    db: Session = Depends(get_db)
    # advertiser: Advertiser = Depends(get_current_advertiser)  ← временно отключено
):
    daily_stats = aggregate_by_day(db, campaign_id)
    filtered = [
        s for s in daily_stats
        if start_date <= date.fromisoformat(s["day"]) <= end_date
    ]

    buf = BytesIO()

    if not filtered:
        # 📉 Заглушка при отсутствии данных
        plt.figure(figsize=(6, 3))
        plt.text(0.5, 0.5, "Нет данных для графика", ha='center', va='center', fontsize=18)
        plt.axis('off')
        plt.tight_layout()
        plt.savefig(buf, format='png')
        buf.seek(0)
        return StreamingResponse(buf, media_type="image/png")

    # 📈 Построение графика ROI
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

    plt.savefig(buf, format='png')
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")

# 🧪 Тестовый эндпоинт для проверки авторизации
@router.get("/roi/debug")
def debug_roi_auth(current_user=Depends(get_current_advertiser)):
    return {"user": current_user}










