from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers import auth, campaigns, stats, payments
from app.api.routes import analytics
from app.dependencies import get_current_advertiser

app = FastAPI()

# ✅ Сначала подключаем API-модули
app.include_router(auth.router)
app.include_router(campaigns.router)
app.include_router(stats.router)
app.include_router(payments.router)
app.include_router(analytics.router)

# ✅ Затем подключаем фронтенд
app.mount("/", StaticFiles(directory="webapp", html=True), name="static")

# ✅ Корневой маршрут для проверки доступности API (можно удалить, если index.html уже отдается)
@app.get("/check", response_class=HTMLResponse)
def root():
    return "<h1>🚀 API работает</h1>"

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
def read_me(advertiser=Depends(get_current_advertiser)):
    return {
        "message": "✅ Авторизация успешна",
        "user": {
            "id": advertiser.id,
            "email": advertiser.email
        }
    }




