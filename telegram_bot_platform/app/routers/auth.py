from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from app.database import SessionLocal
from app.models import Advertiser
from app.schemas import (
    AdvertiserCreate,
    AdvertiserLogin,
    Token,
    RegisterResponse
)
from app.auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token
)
from app.config import settings  # ✅ Централизованная конфигурация
from app.dependencies import get_db, get_current_advertiser

router = APIRouter()

@router.post("/register", response_model=RegisterResponse, summary="Регистрация рекламодателя")
def register(data: AdvertiserCreate, db: Session = Depends(get_db)):
    if db.query(Advertiser).filter_by(email=data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed = hash_password(data.password)
    advertiser = Advertiser(name=data.name, email=data.email, password_hash=hashed)
    db.add(advertiser)
    db.commit()
    return {"status": "registered"}

@router.post("/login", response_model=Token, summary="Авторизация и выдача токенов")
def login(data: AdvertiserLogin, db: Session = Depends(get_db)):
    advertiser = db.query(Advertiser).filter_by(email=data.email).first()
    if not advertiser or not verify_password(data.password, advertiser.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token({"sub": str(advertiser.id)})
    refresh_token = create_refresh_token({"sub": str(advertiser.id)})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/refresh", response_model=Token, summary="Обновление токенов по refresh")
def refresh_token(refresh_token: str = Body(..., embed=True)):
    try:
        payload = jwt.decode(refresh_token, settings.REFRESH_SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
        new_access = create_access_token({"sub": user_id})
        new_refresh = create_refresh_token({"sub": user_id})
        return {
            "access_token": new_access,
            "refresh_token": new_refresh,
            "token_type": "bearer"
        }
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

@router.get("/me", summary="Получить профиль текущего рекламодателя")
def get_profile(current: Advertiser = Depends(get_current_advertiser)):
    return {
        "id": current.id,
        "name": current.name,
        "email": current.email
    }







