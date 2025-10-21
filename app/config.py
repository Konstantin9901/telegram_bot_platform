from pydantic_settings import BaseSettings
from pydantic import Field, ValidationError


class Settings(BaseSettings):
    # 🔐 JWT ключи
    SECRET_KEY: str = Field(..., description="Ключ для подписи access_token")
    REFRESH_SECRET_KEY: str = Field(..., description="Ключ для подписи refresh_token")

    # 🔐 Авторизация
    EMAIL: str = Field(..., description="Email для логина")
    PASSWORD: str = Field(..., description="Пароль для логина")

    # 🌐 API
    BASE_URL: str = Field(..., description="Базовый URL API")

    # 🗄️ База данных
    DATABASE_URL: str = Field(..., description="Строка подключения к PostgreSQL")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8"
    }

    @classmethod
    def validate(cls):
        try:
            instance = cls()
            print("✅ Загружены переменные из .env:")
            for field in instance.model_fields:
                value = getattr(instance, field)
                print(f"   {field}: {value}")
            return instance
        except ValidationError as e:
            print("❌ Ошибка загрузки переменных из .env:")
            print(e)
            raise RuntimeError("Конфигурация .env неполная или содержит ошибки")


# 📦 Экземпляр конфигурации
settings = Settings.validate()


