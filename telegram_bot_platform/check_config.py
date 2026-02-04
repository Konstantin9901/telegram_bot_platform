from app.config import settings

print("✅ Конфигурация загружена:")
for key, value in settings.model_dump().items():
    print(f"   {key}: {value}")
