from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from db.db import get_db
from db.schemas import UserCreate, Token
from datetime import timedelta
from db.auth_security import create_access_token, verify_password
from fastapi.security import OAuth2PasswordRequestForm
import os
from db.crud_auth import (
    create_user,
    get_user_by_username
)

router_auth = APIRouter(
    prefix="/users",
    tags=["Users"]
)

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

# --- 1. РЕГИСТРАЦИЯ НОВОГО ЮЗЕРА (CREATE User) ---
@router_auth.post("/users/register", status_code=status.HTTP_201_CREATED)
def register_new_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    new_user = create_user(db, user=user)
    return {"message": "User registered successfully", "username": new_user.username}


# --- 2. ВХОД И ПОЛУЧЕНИЕ ТОКЕНА (LOGIN) ---
@router_auth.post("/token", response_model=Token)
async def login_for_access_token(
    # Использует форму, отправленную клиентом (username и password)
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
):
    user = get_user_by_username(db, username=form_data.username)
    if not user:
        user = None
    elif not verify_password(form_data.password, user.hashed_password):
        user = None
    if not user:
        # Стандартный ответ при неверных данных OAuth2
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # 2. Генерация токена с установкой срока жизни
    # ACCESS_TOKEN_EXPIRE_MINUTES должна быть константой, например, 30 или 60 минут.
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    access_token = create_access_token(
        # 'sub' (subject) должен быть строкой, поэтому str(user.user_id)
        data={"sub": str(user.user_id)}, 
        expires_delta=access_token_expires
    )
    
    # 3. Возврат токена клиенту
    return {"access_token": access_token, "token_type": "bearer"}