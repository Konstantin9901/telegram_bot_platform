from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import SessionLocal
from app.models import Campaign
from app.schemas import CampaignCreate
from app.dependencies import get_db, get_current_advertiser
from app.services.analytics import calculate_roi, aggregate_by_day

router = APIRouter()


@router.post("/campaigns", summary="Создать новую рекламную кампанию")
def create_campaign(
    campaign: CampaignCreate,
    db: Session = Depends(get_db),
    current = Depends(get_current_advertiser)
):
    new_campaign = Campaign(**campaign.dict(), advertiser_id=current.id)
    db.add(new_campaign)
    db.commit()
    db.refresh(new_campaign)
    return {"status": "ok", "id": new_campaign.id}


@router.get("/campaigns/{id}/roi", summary="Получить ROI по кампании")
def get_roi(
    id: int,
    start_date: datetime = Query(None),
    end_date: datetime = Query(None),
    db: Session = Depends(get_db),
    current = Depends(get_current_advertiser)
):
    campaign = db.query(Campaign).filter_by(id=id, advertiser_id=current.id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    result = calculate_roi(
        db=db,
        campaign_id=id,
        cost_per_action=campaign.cost_per_action,
        start_date=start_date,
        end_date=end_date
    )

    return {
        "campaign_id": id,
        **result,
        "start_date": start_date,
        "end_date": end_date
    }


@router.get("/campaigns/{id}/roi/daily", summary="Получить дневную статистику ROI")
def get_daily_roi(
    id: int,
    db: Session = Depends(get_db),
    current = Depends(get_current_advertiser)
):
    campaign = db.query(Campaign).filter_by(id=id, advertiser_id=current.id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    daily_stats = aggregate_by_day(db=db, campaign_id=id)

    return {
        "campaign_id": id,
        "daily": daily_stats
    }

