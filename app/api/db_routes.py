from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from db.db import get_db
from db.auth_security import get_current_user 
from db.schemas import UserCreate, ProjectInitialization, ProjectShare, ProjectResponse
from db.models import User, Project
from typing import List
from db.crud_auth import get_user_by_username
from db.crud_project import (
    create_user_project, 
    get_project_by_id,
    get_user_accessible_projects,
    add_project_access, 
    get_access_level 
)


router_db = APIRouter(
    prefix="/data",
    tags=["Projects Base"]
)


# --- 2. СОЗДАНИЕ НОВОГО ПРОЕКТА (CREATE Project) ---
@router_db.post("/projects/create", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_new_project(
    project_data: ProjectInitialization,
    current_user: User = Depends(get_current_user), # Защита: требуется токен
    db: Session = Depends(get_db)
):
    # Используем owner_id из текущего аутентифицированного пользователя
    new_project = create_user_project(db, project_data, owner_id=current_user.user_id)
    return new_project


# --- 3. ПОЛУЧЕНИЕ ДАННЫХ ПО ПРОЕКТУ (READ Project) ---
@router_db.get("/projects/{project_id}", response_model=ProjectResponse)
def get_project_data(
    project_id: int,
    current_user: User = Depends(get_current_user), # Защита
    db: Session = Depends(get_db)
):
    project = get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Проверка прав доступа: убедимся, что текущий пользователь имеет право READ
    access_level = get_access_level(db, project_id, current_user.user_id)
    if access_level not in ["READ", "WRITE", "ADMIN"]: # Проверка, что есть хотя бы READ
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this project")
        
    return project


@router_db.get("/projects/my", response_model=List[ProjectResponse])
def list_my_projects(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    projects = get_user_accessible_projects(db, current_user.user_id)
    return projects


# --- 4. РАСШАРИВАНИЕ ПРОЕКТА (CREATE ProjectAccess) ---
@router_db.post("/projects/share", status_code=status.HTTP_200_OK)
def share_project_access(
    share_data: ProjectShare,
    current_user: User = Depends(get_current_user), # Только владелец/админ может расшаривать
    db: Session = Depends(get_db)
):
    project = get_project_by_id(db, share_data.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # 1. Проверка, что текущий пользователь имеет право на расшаривание (например, является владельцем)
    if project.owner_id != current_user.user_id:
        # Можно добавить проверку на уровень 'ADMIN' из таблицы ProjectAccess
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the project owner can share.")

    # 2. Найти пользователя, которому даем доступ
    target_user = get_user_by_username(db, username=share_data.target_username)
    if not target_user:
        raise HTTPException(status_code=404, detail=f"User '{share_data.target_username}' not found.")
        
    # 3. Добавление/обновление права доступа
    add_project_access(
        db, 
        project_id=project.project_id, 
        user_id=target_user.user_id, 
        level=share_data.permission_level
    )
    
    return {"message": f"Access level '{share_data.permission_level}' granted to {target_user.username}."}
