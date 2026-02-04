from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime
from app.models import CampaignStats


def calculate_roi(
    db: Session,
    campaign_id: int,
    cost_per_action: float,
    start_date: datetime = None,
    end_date: datetime = None
) -> dict:
    """
    Расчёт ROI по кампании с фильтрацией по дате.
    ROI = (reward - cost) / cost * 100%
    """
    filters = [
        CampaignStats.campaign_id == campaign_id,
        CampaignStats.is_valid == True
    ]
    if start_date:
        filters.append(CampaignStats.action_time >= start_date)
    if end_date:
        filters.append(CampaignStats.action_time <= end_date)

    stats = db.query(CampaignStats).filter(and_(*filters)).all()

    actions = len(stats)
    total_reward = sum(s.reward for s in stats)
    cost = cost_per_action * actions
    roi = ((total_reward - cost) / cost * 100) if cost > 0 else 0

    return {
        "actions": actions,
        "reward": round(total_reward, 2),
        "cost": round(cost, 2),
        "roi_percent": round(roi, 2)
    }


def aggregate_by_day(db: Session, campaign_id: int) -> list:
    """
    Агрегация статистики по дням: количество действий и сумма наград.
    """
    result = db.query(
        func.date(CampaignStats.action_time).label("day"),
        func.count().label("actions"),
        func.sum(CampaignStats.reward).label("reward")
    ).filter(
        CampaignStats.campaign_id == campaign_id,
        CampaignStats.is_valid == True
    ).group_by(
        func.date(CampaignStats.action_time)
    ).order_by("day").all()

    return [
        {
            "day": r.day.isoformat(),
            "actions": r.actions,
            "reward": float(r.reward)
        }
        for r in result
    ]

