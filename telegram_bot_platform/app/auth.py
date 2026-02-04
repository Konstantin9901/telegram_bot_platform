import hashlib
import json  # ✅ Добавлено для логирования payload
from datetime import datetime, timedelta
from uuid import uuid4
from jose import jwt, JWTError
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.models import Advertiser

# 🔐 Конфигурация токенов
SECRET_KEY = settings.SECRET_KEY
REFRESH_SECRET_KEY = settings.REFRESH_SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_MINUTES = 1440

# 🔐 Авторизация через заголовок
security = HTTPBearer()

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain: str, hashed: str) -> bool:
    return hash_password(plain) == hashed

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({
        "exp": int(expire.timestamp()),  # ✅ округлено
        "iat": int(datetime.utcnow().timestamp()),  # ✅ округлено
        "jti": str(uuid4()),
        "token_type": "access",
        "sub": str(data["sub"])  # ✅ принудительно строка
    })
    print("📦 FINAL PAYLOAD:", json.dumps(to_encode, indent=2))  # ✅ лог перед кодированием
    print("🔐 ACCESS TOKEN CREATED")
    print("🕒 TOKEN EXPIRES AT:", expire)
    print("🕒 UTC NOW:", datetime.utcnow())
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES))
    to_encode.update({
        "exp": int(expire.timestamp()),
        "iat": int(datetime.utcnow().timestamp()),
        "jti": str(uuid4()),
        "token_type": "refresh",
        "sub": str(data["sub"])  # ✅ тоже безопасно
    })
    return jwt.encode(to_encode, REFRESH_SECRET_KEY, algorithm=ALGORITHM)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_advertiser(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    print("🔍 TOKEN RECEIVED:", credentials.credentials)
    print("🔐 SERVER UTC TIME:", datetime.utcnow())

    token = credentials.credentials

    try:
        # ✅ Отключаем автоматическую проверку срока действия
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"verify_exp": False}
        )
        print("📦 PAYLOAD DECODED:", payload)

        # ✅ Ручная проверка срока действия
        exp = payload.get("exp")
        now = int(datetime.utcnow().timestamp())

        print("🕒 TOKEN EXP (timestamp):", exp)
        print("🕒 TOKEN EXP (UTC):", datetime.utcfromtimestamp(exp))
        print("🕒 SERVER UTC NOW:", now, datetime.utcfromtimestamp(now))

        if now < exp:
            print("✅ TOKEN IS VALID: now < exp")
        else:
            print("❌ TOKEN EXPIRED: now >= exp")
            raise HTTPException(status_code=403, detail="Token expired")

        sub = payload.get("sub")
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







