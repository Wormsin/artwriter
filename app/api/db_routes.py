from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from db.db import get_db
from db.auth_security import get_current_user 
from db.schemas import UserCreate, ProjectInitialization, ProjectShare, ProjectResponse, ProjectResponseWithAccess
from db.models import User, Project
from typing import List, Annotated
from pathlib import Path
from db.crud_auth import get_user_by_username
import os
import logging
from db.crud_project import (
    create_user_project, 
    get_project_by_id,
    get_user_accessible_projects,
    add_project_access, 
    get_access_level,
    save_reports_to_project
)

# Глобальный логгер (подхватит config из main.py)
logger = logging.getLogger(__name__)

router_db = APIRouter(  # Переименовал для краткости
    prefix="/data",
    tags=["Projects Base"]
)


# --- 1. СОЗДАНИЕ НОВОГО ПРОЕКТА (CREATE Project) ---
@router_db.post("/projects/create", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_new_project(
    project_data: ProjectInitialization,
    current_user: User = Depends(get_current_user), # Защита: требуется токен
    db: Session = Depends(get_db)
):
    try:
        # Используем owner_id из текущего аутентифицированного пользователя
        new_project = create_user_project(db, project_data, owner_id=current_user.user_id)
        logger.info(f"Проект '{project_data.topic_name}' создан для пользователя {current_user.user_id} (ID: {new_project.project_id})")
        return new_project


    except ValueError as e:
        # Если проект с таким именем уже существует, возвращаем 400 с текстом ошибки
        raise HTTPException(status_code=400, detail=str(e))
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"DB ошибка при создании проекта '{project_data.topic_name}' для {current_user.user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during project creation")
    except Exception as e:
        logger.error(f"Неожиданная ошибка при создании проекта '{project_data.topic_name}' для {current_user.user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    

# --- 3. ПОЛУЧЕНИЕ ДАННЫХ ПО ПРОЕКТУ (READ Project) ---
@router_db.get("/projects/{project_id}", response_model=ProjectResponse)
def get_project_data(
    project_id: int,
    current_user: User = Depends(get_current_user), # Защита
    db: Session = Depends(get_db)
):
    try:
        project = get_project_by_id(db, project_id)
        if not project:
            logger.warning(f"Попытка доступа к несуществующему проекту {project_id} от {current_user.user_id}")
            raise HTTPException(status_code=404, detail="Project not found")

        # Проверка прав доступа: убедимся, что текущий пользователь имеет право READ
        access_level = get_access_level(db, project_id, current_user.user_id)
        if access_level not in ["READ", "WRITE", "ADMIN"]: # Проверка, что есть хотя бы READ
            logger.warning(f"Отказано в доступе к проекту {project_id} для {current_user.user_id} (уровень: {access_level})")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this project")
        
        logger.info(f"Данные проекта {project_id} возвращены для {current_user.user_id}")
        return project
    
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"DB ошибка при получении проекта {project_id} для {current_user.user_id}: {e}")
        raise HTTPException(status_code=500, detail="Database error during project retrieval")
    except Exception as e:
        logger.error(f"Неожиданная ошибка при получении проекта {project_id} для {current_user.user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router_db.get("/myprojects", response_model=List[ProjectResponseWithAccess])
def list_my_projects(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        projects = get_user_accessible_projects(db, current_user.user_id)
        logger.info(f"Список проектов возвращен для {current_user.user_id}: {len(projects)} проектов")
        return projects
    
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"DB ошибка при получении списка проектов для {current_user.user_id}: {e}")
        raise HTTPException(status_code=500, detail="Database error during projects list retrieval")
    except Exception as e:
        logger.error(f"Неожиданная ошибка при получении списка проектов для {current_user.user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# --- 4. РАСШАРИВАНИЕ ПРОЕКТА (CREATE ProjectAccess) ---
@router_db.post("/projects/share", status_code=status.HTTP_200_OK, response_model=dict)  # Добавил response_model для consistency
def share_project_access(
    share_data: ProjectShare,
    current_user: User = Depends(get_current_user), # Только владелец/админ может расшаривать
    db: Session = Depends(get_db)
):
    try:
        project = get_project_by_id(db, share_data.project_id)
        if not project:
            logger.warning(f"Попытка шаринга несуществующего проекта {share_data.project_id} от {current_user.user_id}")
            raise HTTPException(status_code=404, detail="Project not found")

        # 1. Проверка, что текущий пользователь имеет право на расшаривание (owner или ADMIN)
        access_level = get_access_level(db, share_data.project_id, current_user.user_id)
        if access_level not in ["WRITE", "ADMIN"] and project.owner_id != current_user.user_id:
            logger.warning(f"Отказано в шаринге проекта {share_data.project_id} для {current_user.user_id} (уровень: {access_level})")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the project owner or admin can share.")

        # 2. Найти пользователя, которому даем доступ
        target_user = get_user_by_username(db, username=share_data.target_username)
        if not target_user:
            logger.warning(f"Пользователь '{share_data.target_username}' не найден для шаринга проекта {share_data.project_id}")
            raise HTTPException(status_code=404, detail=f"User '{share_data.target_username}' not found.")
        
        # 3. Добавление/обновление права доступа
        result = add_project_access(
            db, 
            project_id=project.project_id, 
            user_id=target_user.user_id, 
            level=share_data.permission_level
        )
        
        logger.info(f"Доступ '{share_data.permission_level}' предоставлен {target_user.username} к проекту {share_data.project_id} от {current_user.user_id}")
        return {"message": f"Access level '{share_data.permission_level}' granted to {target_user.username}.", "action": result["action"]}
    
    except HTTPException:
        # Пропускаем дальше — FastAPI сам обработает корректный статус
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"DB ошибка при шаринге проекта {share_data.project_id} для {current_user.user_id}: {e}")
        raise HTTPException(status_code=500, detail="Database error during sharing")
    except Exception as e:
        logger.error(f"Неожиданная ошибка при шаринге проекта {share_data.project_id} для {current_user.user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router_db.post("/projects/{project_id}/upload-reports", status_code=status.HTTP_201_CREATED, response_model=dict)  # Добавил response_model
async def upload_project_files_endpoint(
    project_id: int, 
    folder_path: Annotated[str, Form()], 
    files: List[UploadFile] = File(...), 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        if not files:
            raise HTTPException(status_code=400, detail="No files uploaded.")
        
        # Проверка доступа: нужен хотя бы WRITE
        access_level = get_access_level(db, project_id, current_user.user_id)
        if access_level not in ["WRITE", "ADMIN"]:
            logger.warning(f"Отказано в загрузке файлов в проект {project_id} для {current_user.user_id} (уровень: {access_level})")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Write access required to upload files")
        
        results = await save_reports_to_project(
            folder_path=folder_path,
            project_id=project_id,
            uploaded_files=files
        )
        logger.info(f"Файлы загружены в проект {project_id} для {current_user.user_id}: {len(files)} файлов")
        return {
            "project_id": project_id, 
            "user_id": current_user.user_id, 
            "results": results
        }
    
    except HTTPException:
        # Перебрасываем HTTP ошибки (например, 403)
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"DB ошибка при загрузке файлов в проект {project_id} для {current_user.user_id}: {e}")
        raise HTTPException(status_code=500, detail="Database error during upload")
    except Exception as e:
        logger.error(f"Неожиданная ошибка при загрузке файлов в проект {project_id} для {current_user.user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Не удалось завершить загрузку файлов: {e}"
        )