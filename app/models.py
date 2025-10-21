from sqlalchemy import Column, Integer, String, Numeric, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.sql import func
from app.database import Base

class Advertiser(Base):
    __tablename__ = "advertisers"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

class Campaign(Base):
    __tablename__ = "campaigns"
    id = Column(Integer, primary_key=True)
    advertiser_id = Column(Integer, ForeignKey("advertisers.id"), nullable=False)
    title = Column(String, nullable=False)
    action_type = Column(String, nullable=False)
    target_url = Column(Text, nullable=False)
    budget = Column(Numeric, nullable=False)
    cost_per_action = Column(Numeric, nullable=False)
    geo = Column(String, nullable=False)
    status = Column(String, nullable=False, server_default="active")
    created_at = Column(DateTime, server_default=func.now())

class CampaignStats(Base):
    __tablename__ = "campaign_stats"
    id = Column(Integer, primary_key=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    user_id = Column(Integer, nullable=False)
    action_time = Column(DateTime, nullable=False)
    is_valid = Column(Boolean, nullable=False, server_default="true")
    reward = Column(Numeric, nullable=False)

class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True)
    advertiser_id = Column(Integer, ForeignKey("advertisers.id"), nullable=False)
    amount = Column(Numeric, nullable=False)
    method = Column(String, nullable=False)
    status = Column(String, nullable=False, server_default="completed")
    created_at = Column(DateTime, server_default=func.now())

