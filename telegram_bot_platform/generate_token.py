from jose import jwt
from app.config import settings
from datetime import datetime, timedelta

def create_token(data: dict, secret: str, expires_in: int = 3600):
    payload = {
        **data,
        "exp": datetime.utcnow() + timedelta(seconds=expires_in),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, secret, algorithm="HS256")

if __name__ == "__main__":
    access = create_token({"sub": settings.EMAIL}, settings.SECRET_KEY)
    refresh = create_token({"sub": settings.EMAIL}, settings.REFRESH_SECRET_KEY, expires_in=86400)
    print("✅ Access Token:\n", access)
    print("🔁 Refresh Token:\n", refresh)
