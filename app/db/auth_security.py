from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from db.db import get_db
from db.models import User
import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from passlib.context import CryptContext
import logging

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a stored hash using passlib."""
    try:
        # passlib handles encoding/decoding and Bcrypt format internally
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"Ошибка верификации пароля: {e}")
        return False  # Не раскрываем детали ошибки для security

def get_password_hash(password: str) -> str:
    """Generates a password hash using passlib."""
    try:
        # passlib ensures the output is a correctly formatted string for the DB
        return pwd_context.hash(password)
    except Exception as e:
        logger.error(f"Ошибка хэширования пароля: {e}")
        raise ValueError("Не удалось сгенерировать хэш пароля")

# Это должно быть секретным ключом, хранящимся в .env
SECRET_KEY = os.getenv("SECRET_KEY_AUTH")
if not SECRET_KEY:
    logger.error("SECRET_KEY_AUTH не установлен в .env! Аутентификация не будет работать.")
    raise ValueError("SECRET_KEY_AUTH required")

ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")  # Эндпоинт для получения токена

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            logger.warning(f"Невалидный user_id в токене: {user_id}")
            raise credentials_exception
    except JWTError as e:
        logger.warning(f"JWT ошибка: {e} (токен: {token[:20]}...)")  # Не логируем полный токен для security
        raise credentials_exception
    
    # Обработка DB-запроса с логами и обработкой ошибок
    try:
        logger.debug(f"Поиск пользователя по ID: {user_id}")
        user = db.query(User).filter(User.user_id == user_id).first()
        if user is None:
            logger.warning(f"Пользователь не найден по ID: {user_id}")
            raise credentials_exception
        logger.info(f"Успешная аутентификация пользователя: {user.username}")  # Аудит
        return user  # Возвращает объект User, если аутентификация успешна
    except SQLAlchemyError as e:
        logger.error(f"DB ошибка при поиске пользователя {user_id}: {e}")
        db.rollback()  # Откат при ошибке
        raise HTTPException(status_code=500, detail="Database error during authentication")
    except Exception as e:
        logger.error(f"Неожиданная ошибка при аутентификации пользователя {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Генерирует JWT (JSON Web Token), подписывая его секретным ключом.
    
    data: Словарь, содержащий полезную нагрузку (payload), например {"sub": user_id}.
    expires_delta: Необязательный timedelta, определяющий время жизни токена.
    """
    try:
        logger.debug(f"Создание токена для data: {data}")  # Debug для payload без чувствительных данных
        to_encode = data.copy()
        
        # 1. Установка срока действия (Expiration Time)
        if expires_delta:
            # Устанавливаем время истечения, используя переданный timedelta
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            # Стандартное время жизни токена, если expires_delta не передан
            expire = datetime.now(timezone.utc) + timedelta(minutes=30) 
            
        # Добавляем стандартное поле "exp" (expiration time) в полезную нагрузку
        to_encode.update({"exp": expire})
        
        # 2. Подписание и кодирование токена
        # SECRET_KEY используется здесь для криптографической подписи токена.
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        logger.info(f"Токен создан для пользователя {data.get('sub')}, expires: {expire}")
        return encoded_jwt
    except Exception as e:
        logger.error(f"Ошибка создания токена: {e}")
        raise ValueError("Не удалось создать токен")