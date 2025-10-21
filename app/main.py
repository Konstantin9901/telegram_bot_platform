from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware  # ✅ Добавлен CORS

from app.config import settings  # ✅ Импорт готовой конфигурации
from app.routers import auth, campaigns, stats, payments
from app.api.routes import analytics  # ✅ Подключаем роутер аналитики
from app.dependencies import get_current_advertiser  # ✅ Используем отлаженную авторизацию

app = FastAPI()

# ✅ Включаем CORS для локального теста
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ← на проде замени на ["https://web.telegram.org"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Защищённый маршрут /me с полной отладкой через get_current_advertiser
@app.get("/me")
def read_me(advertiser = Depends(get_current_advertiser)):
    return {
        "message": "✅ Авторизация успешна",
        "user": {
            "id": advertiser.id,
            "email": advertiser.email
        }
    }

# 📦 Подключение всех модулей
app.include_router(auth.router)
app.include_router(campaigns.router)
app.include_router(stats.router)
app.include_router(payments.router)
app.include_router(analytics.router)  # ✅ Регистрируем /analytics/roi


