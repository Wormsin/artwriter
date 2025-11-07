import logging
from pathlib import Path
import sys
from fastapi import FastAPI
import uvicorn
from db.db import Base, engine
from api import disk_routes, llm_routes, auth_routes, db_routes, files_routes
from dotenv import load_dotenv

LOG_DIR = Path("logs")
DATA_DIR = Path("projects_root")
LOG_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

# Конфигурация логирования для продакшена (dictConfig)
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
        "json": {  # Опционально: для JSON-логов в проде (интеграция с ELK)
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s %(pathname)s %(lineno)d",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "standard",
            "stream": sys.stdout,
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",  # В файл — больше деталей
            "formatter": "standard",
            "filename": str(LOG_DIR / "app.log"),
            "maxBytes": 10485760,  # 10 MB на файл
            "backupCount": 5,  # Храним 5 бэкапов
            "encoding": "utf-8",
        },
        # Опционально: JSON-логгер для прод-мониторинга
        "json_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "json",
            "filename": str(LOG_DIR / "app.json.log"),
            "maxBytes": 10485760,
            "backupCount": 5,
            "encoding": "utf-8",
        },
    },
    "root": {
        "level": "INFO",  # Глобальный уровень
        "handlers": ["console", "file"],  # Или ["console", "json_file"] для JSON
    },
    # Логгеры для конкретных модулей (опционально, чтобы переопределить)
    "loggers": {
        "uvicorn": {  # Логи Uvicorn (сервер)
            "level": "INFO",
            "handlers": ["console"],
            "propagate": False,
        },
        "db": {  # Для DB-модулей
            "level": "WARNING",
            "handlers": ["file"],
            "propagate": True,
        },
    },
}

# Применяем конфигурацию ВНЕ FastAPI (на уровне модуля)
logging.config.dictConfig(LOGGING_CONFIG)


load_dotenv()

app = FastAPI()
Base.metadata.create_all(bind=engine)

app.include_router(auth_routes.router_auth)
app.include_router(db_routes.router_db)
#app.include_router(disk_routes.router_disk)
app.include_router(llm_routes.router_llm_workflows)
app.include_router(files_routes.router_files)

logger = logging.getLogger(__name__)
logger.info("FastAPI app started with production logging")

#test route
@app.get("/")
def read_root():
    return {"status": "ok", "message": "Welcome to the API"}


#if __name__=="__main__":
#    uvicorn.run(app = "main:app", reload=True)