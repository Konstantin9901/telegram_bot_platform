from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Payment
from app.dependencies import get_db, get_current_advertiser

router = APIRouter()

@router.post("/payments")
def create_payment(amount: float, method: str, db: Session = Depends(get_db), current = Depends(get_current_advertiser)):
    payment = Payment(advertiser_id=current.id, amount=amount, method=method)
    db.add(payment)
    db.commit()
    return {"status": "paid", "amount": amount}

@router.get("/payments")
def get_payments(db: Session = Depends(get_db), current = Depends(get_current_advertiser)):
    payments = db.query(Payment).filter_by(advertiser_id=current.id).all()
    return payments
