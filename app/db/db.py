from fastapi import HTTPException
from sqlalchemy import create_engine, exc, text
from sqlalchemy.orm import declarative_base, sessionmaker
import os
import logging

logger = logging.getLogger(__name__)


# DATABASE_URL можно вынести в .env для безопасности
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # Возможно, тут ты можешь поставить заглушку для локальной разработки без Docker
    raise Exception("DATABASE_URL не настроен.")

try:
    engine = create_engine(DATABASE_URL, echo=False)  # echo=True для debug в dev
    # Проверяем подключение при инициализации
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))  # Простой пинг
    logger.info("DB подключение успешно инициализировано")
except exc.OperationalError as e:
    logger.error(f"Ошибка подключения к DB: {e}. Проверьте DATABASE_URL.")
    raise RuntimeError("DB connection failed")
except Exception as e:
    logger.error(f"Неожиданная ошибка инициализации DB: {e}")
    raise

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    except exc.SQLAlchemyError as e:
        logger.error(f"SQLAlchemy ошибка в сессии: {e}")
        db.rollback()  # Откатываем изменения при ошибке
        raise HTTPException(status_code=500, detail="Database error")  # Для FastAPI
    except Exception as e:
        logger.error(f"Неожиданная ошибка в DB сессии: {e}")
        db.rollback()
        raise
    finally:
        db.close()
        logger.debug("DB сессия закрыта")