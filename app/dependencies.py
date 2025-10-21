from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from datetime import datetime
import os

from app.database import SessionLocal, get_db
from app.models import Advertiser
from app.schemas import TokenData
from app.auth import SECRET_KEY, ALGORITHM
from app.config import settings  # ✅ добавлен импорт settings

# ✅ Поддержка OAuth2 (например, для Swagger UI)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# ✅ Поддержка HTTPBearer (например, для Telegram WebApp)
security = HTTPBearer()

# ✅ Авторизация через Swagger UI
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception

    return token_data

# ✅ Авторизация через Telegram WebApp (HTTPBearer)
def get_current_advertiser(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials
    print("🔐 TOKEN RECEIVED:", token)
    print("🕒 SERVER TIME:", datetime.utcnow())

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"verify_exp": False}
        )
        print("📦 PAYLOAD DECODED:", payload)

        sub = payload.get("sub")
        print("🧠 SUB VALUE:", sub)

        advertiser_id = int(sub)
        print("🔎 ADVERTISER ID:", advertiser_id)

    except JWTError as e:
        print("❌ JWT ERROR:", str(e))
        raise HTTPException(status_code=403, detail="Token decode failed")
    except (TypeError, ValueError) as e:
        print("❌ SUB CONVERSION ERROR:", str(e))
        raise HTTPException(status_code=401, detail="Invalid token: bad subject format")

    advertiser = db.query(Advertiser).filter_by(id=advertiser_id).first()
    if advertiser is None:
        print(f"❌ Advertiser with id={advertiser_id} not found in DB")
        raise HTTPException(status_code=404, detail="Advertiser not found")

    print(f"✅ Advertiser found: {advertiser.email}")
    return advertiser

# ✅ Альтернативная версия для DEV-режима или Swagger UI
def get_current_advertiser_oauth(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        advertiser_id = payload.get("sub")
        email = payload.get("email")

        if advertiser_id is None or email is None:
            raise HTTPException(status_code=401, detail="Недопустимый токен")

        return {
            "id": advertiser_id,
            "email": email
        }

    except JWTError:
        raise HTTPException(status_code=403, detail="Ошибка авторизации")




