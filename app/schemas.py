from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime

class AdvertiserCreate(BaseModel):
    name: str = Field(..., example="Konstantin", description="Имя рекламодателя")
    email: EmailStr = Field(..., example="konstantin@example.com", description="Email для входа")
    password: str = Field(..., min_length=8, max_length=72, example="securepass123", description="Пароль от 8 до 72 символов")

class AdvertiserLogin(BaseModel):
    email: EmailStr = Field(..., example="konstantin@example.com", description="Email для входа")
    password: str = Field(..., min_length=8, max_length=72, example="securepass123", description="Пароль от 8 до 72 символов")

class RegisterResponse(BaseModel):
    status: str = Field(..., example="registered", description="Статус регистрации")

class Token(BaseModel):
    access_token: str = Field(..., example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...", description="JWT токен для доступа")
    refresh_token: str = Field(..., example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...", description="JWT токен для обновления")
    token_type: str = Field(..., example="bearer", description="Тип токена")

class CampaignCreate(BaseModel):
    advertiser_id: int = Field(..., example=1, description="ID рекламодателя")
    title: str = Field(..., example="Подписка на канал", description="Название кампании")
    action_type: str = Field(..., example="subscribe", description="Тип действия: click, subscribe, etc.")
    target_url: str = Field(..., example="https://t.me/my_channel", description="Целевая ссылка")
    budget: float = Field(..., example=1000.0, description="Общий бюджет кампании")
    cost_per_action: float = Field(..., example=5.0, description="Стоимость одного действия")
    geo: Optional[str] = Field(None, example="RU", description="Гео-таргетинг (опционально)")

class CampaignStatsCreate(BaseModel):
    user_id: int = Field(..., example=42, description="ID пользователя")
    action_time: datetime = Field(..., example="2025-10-16T22:30:00", description="Время действия")
    is_valid: bool = Field(..., example=True, description="Прошёл ли фильтр качества")
    reward: float = Field(..., example=5.0, description="Начисленное вознаграждение")

# ✅ Добавлено для JWT-декодирования
class TokenData(BaseModel):
    sub: str  # или int, если ты всегда приводишь к числу






