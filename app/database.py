from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

# ✅ Подключение к базе через .env
engine = create_engine(settings.DATABASE_URL, echo=False)

# ✅ Конфигурация с явным управлением транзакциями
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ✅ Базовый класс для моделей
Base = declarative_base()

# ✅ Зависимость для FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


