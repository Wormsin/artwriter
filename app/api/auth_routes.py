from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from db.db import get_db
from db.schemas import UserCreate, Token
from datetime import timedelta
from db.auth_security import create_access_token, verify_password
from fastapi.security import OAuth2PasswordRequestForm
import os
import logging
from db.crud_auth import create_user, get_user_by_username

# Глобальный логгер (подхватит config из main.py)
logger = logging.getLogger(__name__)

router_auth = APIRouter(
    prefix="/users",
    tags=["Users"]
)

# Константа с fallback для безопасности (app не крашнется)
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

# --- 1. РЕГИСТРАЦИЯ НОВОГО ЮЗЕРА (CREATE User) ---
@router_auth.post("/register", status_code=status.HTTP_201_CREATED, response_model=dict)  # Добавил response_model для consistency
def register_new_user(user: UserCreate, db: Session = Depends(get_db)):
    try:
        # Проверка на существующего пользователя
        db_user = get_user_by_username(db, username=user.username)
        if db_user:
            logger.warning(f"Попытка регистрации существующего username: {user.username}")
            raise HTTPException(status_code=400, detail="Username already registered")
        
        # Создание пользователя
        new_user = create_user(db, user=user)
        logger.info(f"Пользователь зарегистрирован: {new_user.username} (ID: {new_user.user_id})")
        
        return {"message": "User registered successfully", "username": new_user.username}
    
    except HTTPException:
        # Пропускаем дальше — FastAPI сам обработает корректный статус
        raise
    except SQLAlchemyError as e:
        db.rollback()  # Откат при DB-ошибке
        logger.error(f"DB ошибка при регистрации {user.username}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during registration")
    except Exception as e:
        logger.error(f"Неожиданная ошибка при регистрации {user.username}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# --- 2. ВХОД И ПОЛУЧЕНИЕ ТОКЕНА (LOGIN) ---
@router_auth.post("/token", response_model=Token)
async def login_for_access_token(
    # Использует форму, отправленную клиентом (username и password)
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
):
    try:
        # Поиск пользователя
        user = get_user_by_username(db, username=form_data.username)
        
        # Проверка пароля (если пользователь не найден или пароль неверный — общий error)
        if not user or not verify_password(form_data.password, user.hashed_password):
            logger.warning(f"Неуспешная попытка логина для username: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Генерация токена
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.user_id)}, 
            expires_delta=access_token_expires
        )
        
        logger.info(f"Успешный логин для пользователя: {user.username} (ID: {user.user_id})")
        
        # Возврат токена клиенту
        return {"access_token": access_token, "token_type": "bearer"}
    
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"DB ошибка при логине для {form_data.username}: {e}")
        raise HTTPException(status_code=500, detail="Database error during login")
    except Exception as e:
        logger.error(f"Неожиданная ошибка при логине для {form_data.username}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

