from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from db.db import get_db
from db.models import User
import os
import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Optional
from passlib.context import CryptContext


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a stored hash using passlib."""
    # passlib handles encoding/decoding and Bcrypt format internally
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generates a password hash using passlib."""
    # passlib ensures the output is a correctly formatted string for the DB
    return pwd_context.hash(password)

# Это должно быть секретным ключом, хранящимся в .env
SECRET_KEY = os.getenv("SECRET_KEY_AUTH")
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token") # Эндпоинт для получения токена

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
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.user_id == user_id).first()
    if user is None:
        raise credentials_exception
    return user # Возвращает объект User, если аутентификация успешна


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Генерирует JWT (JSON Web Token), подписывая его секретным ключом.
    
    data: Словарь, содержащий полезную нагрузку (payload), например {"sub": user_id}.
    expires_delta: Необязательный timedelta, определяющий время жизни токена.
    """
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
    
    return encoded_jwt

