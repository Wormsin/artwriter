from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Table, Boolean
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from . db import Base
from datetime import datetime
from sqlalchemy.orm import relationship
from typing import Literal
import logging


logger = logging.getLogger(__name__)


# --- 1. Таблица Пользователей ---
class User(Base):
    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    # Новое поле: словарь использования токенов по месяцам (JSONB для PostgreSQL)
    # Формат: {"YYYY-MM": tokens, ...}, обновляется ежемесячно
    token_usage = Column(JSONB, default=dict, nullable=False)

    # Отношение: один пользователь может владеть многими проектами
    projects_owned = relationship("Project", back_populates="owner")
    # Отношение: пользователь может иметь доступ ко многим проектам (через таблицу ProjectAccess)
    access_rights = relationship("ProjectAccess", back_populates="user")


# --- 2. Таблица Проектов ---
class Project(Base):
    __tablename__ = 'projects'

    project_id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    topic_name = Column(String, index=True, nullable=False)
    # Путь к папке проекта на сервере (например, /data/projects/12345/)
    file_path = Column(String, nullable=False) 

    # Отношение: один проект принадлежит одному владельцу
    
    owner = relationship("User", back_populates="projects_owned")
    # Отношение: проект имеет много прав доступа
    accessors = relationship("ProjectAccess", back_populates="project")


# --- 3. Таблица Доступа и Обмена (Project_Access) ---
# Определяем возможные уровни доступа
PermissionLevel = Literal['READ', 'WRITE', 'ADMIN']

class ProjectAccess(Base):
    __tablename__ = 'project_access'
    
    # Составной первичный ключ
    project_access_id = Column(Integer, primary_key=True) 
    
    project_id = Column(Integer, ForeignKey('projects.project_id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    
    # Уровень доступа: READ (только чтение) или WRITE (изменение)
    permission_level = Column(String, default='READ', nullable=False) 

    # Отношения
    project = relationship("Project", back_populates="accessors")
    user = relationship("User", back_populates="access_rights")