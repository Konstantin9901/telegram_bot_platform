import matplotlib
matplotlib.use("Agg")  # ✅ Отключает GUI, безопасно для серверной генерации PNG

import matplotlib.pyplot as plt
from fastapi import APIRouter, Query, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import date
from sqlalchemy.orm import Session
from io import BytesIO
from fastapi.responses import StreamingResponse

# 🔗 Импорт расчётной логики
from app.analytics.calculations import calculate_roi_metrics
from app.database import get_db
from app.services.analytics import aggregate_by_day
from app.dependencies import get_current_advertiser
from app.models import Advertiser

router = APIRouter(prefix="/analytics")

# 📦 Универсальная функция вычисления метрик
def compute_metric_from_row(row, metric, cost_per_action=None):
    actions = int(row.get("actions", 0) or 0)
    reward = float(row.get("reward", 0) or 0)
    impressions = int(row.get("impressions", row.get("views", 0) or 0) or 0)
    spend = float(row.get("spend", 0) or 0)

    if metric == "roi":
        if "roi_percent" in row:
            return float(row.get("roi_percent", 0))
        if cost_per_action is not None:
            cost = cost_per_action * actions
            return round(((reward - cost) / cost * 100) if cost > 0 else 0, 2)
        return round(((reward - spend) / spend * 100) if spend > 0 else 0, 2)
    if metric == "cpa":
        return round((reward / actions) if actions > 0 else 0, 2)
    if metric == "ctr":
        return round((actions / impressions * 100) if impressions > 0 else 0, 2)
    if metric == "cpc":
        return round((spend / actions) if actions > 0 else 0, 2)
    return 0

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
    return ROIResponse(**metrics)

# 📦 Модель ответа для ROI по дням
class DailyROIResponse(BaseModel):
    date: str
    actions: int
    reward: float
    roi_percent: float

# 📈 Эндпоинт ROI по дням (с поддержкой нескольких кампаний + тестовые данные)
@router.get("/roi/daily", response_model=list[DailyROIResponse])
def get_daily_roi(
    start_date: date = Query(..., description="Формат: YYYY-MM-DD"),
    end_date: date = Query(..., description="Формат: YYYY-MM-DD"),
    campaign_id: list[int] = Query(..., description="ID кампаний (можно несколько)"),
    cost_per_action: float = Query(..., description="Стоимость одного действия"),
    db: Session = Depends(get_db)
):
    results = []

    for cid in campaign_id:
        # 📦 Для тестовых кампаний 1 и 2 — используем встроенные данные
        if cid == 1:
            test_data = [
                {"date": "2025-10-01", "actions": 2, "reward": 150},
                {"date": "2025-10-02", "actions": 3, "reward": 210},
                {"date": "2025-10-03", "actions": 1, "reward": 90},
                {"date": "2025-10-04", "actions": 2, "reward": 180},
                {"date": "2025-10-05", "actions": 3, "reward": 300},
                {"date": "2025-10-06", "actions": 1, "reward": 120},
                {"date": "2025-10-07", "actions": 2, "reward": 200},
                {"date": "2025-10-08", "actions": 3, "reward": 330},
                {"date": "2025-10-09", "actions": 1, "reward": 95},
                {"date": "2025-10-10", "actions": 2, "reward": 180},
                {"date": "2025-10-11", "actions": 3, "reward": 270},
                {"date": "2025-10-12", "actions": 1, "reward": 110},
                {"date": "2025-10-13", "actions": 2, "reward": 190},
                {"date": "2025-10-14", "actions": 3, "reward": 310},
                {"date": "2025-10-15", "actions": 1, "reward": 100},
                {"date": "2025-10-16", "actions": 2, "reward": 200},
                {"date": "2025-10-20", "actions": 3, "reward": 330},
                {"date": "2025-10-21", "actions": 1, "reward": 115},
                {"date": "2025-10-22", "actions": 2, "reward": 220},
                {"date": "2025-10-23", "actions": 3, "reward": 340},
                {"date": "2025-10-24", "actions": 1, "reward": 120},
                {"date": "2025-10-25", "actions": 2, "reward": 230},
                {"date": "2025-10-26", "actions": 3, "reward": 350},
                {"date": "2025-10-27", "actions": 1, "reward": 125},
                {"date": "2025-10-28", "actions": 2, "reward": 240},
                {"date": "2025-10-29", "actions": 3, "reward": 360},
                {"date": "2025-10-30", "actions": 1, "reward": 130},
                {"date": "2025-10-31", "actions": 2, "reward": 250},
            ]
            filtered = [s for s in test_data if start_date <= date.fromisoformat(s["date"]) <= end_date]
        elif cid == 2:
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
            filtered = [s for s in test_data if start_date <= date.fromisoformat(s["date"]) <= end_date]
        else:
            # 📦 Все остальные кампании → из БД
            daily_stats = aggregate_by_day(db, cid)
            filtered = [s for s in daily_stats if start_date <= date.fromisoformat(s["day"]) <= end_date]

        # 📊 Формируем результат
        for s in filtered:
            actions = s["actions"]
            reward = s["reward"]
            day = s.get("date") or s.get("day")
            cost = cost_per_action * actions
            roi = ((reward - cost) / cost * 100) if cost > 0 else 0

            results.append(DailyROIResponse(
                date=day,
                actions=actions,
                reward=reward,
                roi_percent=round(roi, 2)
            ))

    return results

# 🖼️ Эндпоинт PNG-графика ROI по дням (с заглушкой при отсутствии данных)
@router.get("/roi/plot")
def plot_roi_by_day(
    start_date: date = Query(..., description="Формат: YYYY-MM-DD"),
    end_date: date = Query(..., description="Формат: YYYY-MM-DD"),
    campaign_id: int = Query(..., description="ID кампании"),
    cost_per_action: float = Query(..., description="Стоимость одного действия"),
    db: Session = Depends(get_db)
):
    daily_stats = aggregate_by_day(db, campaign_id)
    filtered = [s for s in daily_stats if start_date <= date.fromisoformat(s["day"]) <= end_date]

    buf = BytesIO()

    if not filtered:
        plt.figure(figsize=(6, 3))
        plt.text(0.5, 0.5, "Нет данных для графика", ha='center', va='center', fontsize=18)
        plt.axis('off')
        plt.tight_layout()
        plt.savefig(buf, format='png')
        buf.seek(0)
        return StreamingResponse(buf, media_type="image/png")

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

# 🖼️ Универсальный PNG-график по метрике
@router.get("/export/png")
def export_png(
    metric: str = Query(..., regex="^(roi|ctr|cpa|cpc)$"),
    start_date: date = Query(...),
    end_date: date = Query(...),
    campaign_id: list[int] = Query(..., description="ID кампаний (можно несколько)"),
    db: Session = Depends(get_db),
    cost_per_action: Optional[float] = Query(None)
):
    results = []
    for cid in campaign_id:
        daily_stats = aggregate_by_day(db, cid)
        filtered = [s for s in daily_stats if start_date <= date.fromisoformat(s["day"]) <= end_date]
        for s in filtered:
            value = compute_metric_from_row(s, metric, cost_per_action)
            results.append({"day": s["day"], "campaign_id": cid, metric: value})

    buf = BytesIO()
    if not results:
        plt.figure(figsize=(6, 3))
        plt.text(0.5, 0.5, "Нет данных", ha='center', va='center', fontsize=18)
        plt.axis('off')
        plt.savefig(buf, format="png")
        buf.seek(0)
        return StreamingResponse(buf, media_type="image/png")

    dates = sorted(list({r["day"] for r in results}))
    values_by_date = {d: 0 for d in dates}
    counts_by_date = {d: 0 for d in dates}
    for r in results:
        values_by_date[r["day"]] += r[metric]
        counts_by_date[r["day"]] += 1
    values = [round(values_by_date[d] / counts_by_date[d], 2) for d in dates]

    plt.figure(figsize=(12, 6))
    plt.plot(dates, values, marker="o", linestyle="-", color="blue")
    plt.title(f"{metric.upper()} по дням")
    plt.xlabel("Дата")
    plt.ylabel(metric.upper())
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.tight_layout()

    plt.savefig(buf, format="png")
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")

# 📊 Экспорт Excel по метрике
@router.get("/export/excel")
def export_excel(
    metric: str = Query(..., regex="^(roi|ctr|cpa|cpc)$"),
    start_date: date = Query(...),
    end_date: date = Query(...),
    campaign_id: list[int] = Query(..., description="ID кампаний (можно несколько)"),
    db: Session = Depends(get_db),
    cost_per_action: Optional[float] = Query(None)
):
    import pandas as pd

    results = []
    for cid in campaign_id:
        daily_stats = aggregate_by_day(db, cid)
        filtered = [s for s in daily_stats if start_date <= date.fromisoformat(s["day"]) <= end_date]
        for s in filtered:
            value = compute_metric_from_row(s, metric, cost_per_action)
            results.append({"Дата": s["day"], "Кампания": cid, metric.upper(): value})

    if not results:
        results.append({"Дата": "-", "Кампания": "-", metric.upper(): 0})

    df = pd.DataFrame(results)
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Report")
    buf.seek(0)
    return StreamingResponse(buf, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# 📝 Экспорт Markdown по метрике
@router.get("/export/md")
def export_md(
    metric: str = Query(..., regex="^(roi|ctr|cpa|cpc)$"),
    start_date: date = Query(...),
    end_date: date = Query(...),
    campaign_id: list[int] = Query(..., description="ID кампаний (можно несколько)"),
    db: Session = Depends(get_db),
    cost_per_action: Optional[float] = Query(None)
):
    lines = [f"# Сводка по метрике {metric.upper()}"]
    for cid in campaign_id:
        daily_stats = aggregate_by_day(db, cid)
        filtered = [s for s in daily_stats if start_date <= date.fromisoformat(s["day"]) <= end_date]
        if not filtered:
            lines.append(f"- Кампания {cid}: нет данных")
        else:
            for s in filtered:
                value = compute_metric_from_row(s, metric, cost_per_action)
                lines.append(f"- Кампания {cid}, {s['day']}: {value}")

    md_content = "\n".join(lines)
    output = BytesIO(md_content.encode("utf-8"))

    return StreamingResponse(
        output,
        media_type="text/markdown",
        headers={"Content-Disposition": f"attachment; filename={metric}-report.md"}
    )

# 🧪 Тестовый эндпоинт для проверки авторизации
@router.get("/roi/debug")
def debug_roi_auth(current_user=Depends(get_current_advertiser)):
    return {"user": current_user}








