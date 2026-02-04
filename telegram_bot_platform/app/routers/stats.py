from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import CampaignStats
from app.schemas import CampaignStatsCreate
from app.dependencies import get_db

router = APIRouter()

@router.post("/campaigns/{id}/stats")
def add_stat(id: int, stat: CampaignStatsCreate, db: Session = Depends(get_db)):
    new_stat = CampaignStats(campaign_id=id, **stat.dict())