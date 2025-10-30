from sqlalchemy.orm import Session
from db.models import User
from db.schemas import UserCreate
from db.auth_security import get_password_hash


def get_user_by_username(db: Session, username: str):
    """Найти пользователя по его имени."""
    return db.query(User).filter(User.username == username).first()

def get_user_by_id(db: Session, user_id: int):
    """Найти пользователя по его ID."""
    return db.query(User).filter(User.user_id == user_id).first()

def create_user(db: Session, user: UserCreate):
    """Создать нового пользователя и хешировать его пароль."""
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username, 
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user











