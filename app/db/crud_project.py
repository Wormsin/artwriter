import os
import shutil
from typing import Literal, Optional
from db.schemas import ProjectInitialization
from db.models import Project, ProjectAccess
from sqlalchemy.orm import Session


PROJECTS_ROOT_DIR = "projects_root"
PermissionLevel = Literal['READ', 'WRITE', 'ADMIN']

def get_project_by_id(db: Session, project_id: int) -> Optional[Project]:
    """
    Находит проект в базе данных по его уникальному ID.
    Возвращает объект Project или None, если проект не найден.
    """
    return db.query(Project).filter(Project.project_id == project_id).first()


def create_user_project(db: Session, project_data: ProjectInitialization, owner_id: int):
    """Создать проект в БД и папку на диске."""
    # 1. Создание папки проекта на диске
    # Используем уникальный ID, который будет присвоен после добавления в БД
    
    # 2. Создание записи в БД
    db_project = Project(
        owner_id=owner_id,
        topic_name=project_data.topic_name,
        # Временный file_path, обновим после получения project_id
        file_path="" 
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    
    # 3. Обновление file_path с использованием полученного project_id
    project_folder_name = f"proj_{db_project.project_id}_{db_project.topic_name.replace(' ', '_')}"
    final_file_path = os.path.join(PROJECTS_ROOT_DIR, str(owner_id), project_folder_name)
    
    os.makedirs(final_file_path, exist_ok=True) # Создаем папку на сервере
    
    db_project.file_path = final_file_path
    db.commit()
    
    # 4. Добавление владельца в права доступа (WRITE)
    # Владелец всегда должен иметь полный доступ
    db_access = ProjectAccess(
        project_id=db_project.project_id,
        user_id=owner_id,
        permission_level="WRITE"
    )
    db.add(db_access)
    db.commit()

    return db_project


def get_user_accessible_projects(db: Session, user_id: int):
    """Получить список проектов, к которым у пользователя есть любой доступ."""
    # Получаем проекты, где пользователь либо владелец, либо имеет запись в ProjectAccess
    
    # 1. Проекты, где пользователь является владельцем
    owned_projects = db.query(Project).filter(Project.owner_id == user_id)
    
    # 2. Проекты, к которым предоставлен доступ
    accessible_projects = db.query(Project).join(ProjectAccess).filter(
        ProjectAccess.user_id == user_id
    ).distinct()
    
    # Объединяем и убираем дубликаты
    # Это упрощенное объединение, в SQLAlchemy можно сделать более элегантно
    return list(set(owned_projects.all() + accessible_projects.all()))


def delete_project(db: Session, project_id: int):
    """Удалить проект из БД и его файлы с диска (осторожно!)."""
    db_project = db.query(Project).filter(Project.project_id == project_id).first()
    
    if db_project:
        # 1. Удаление записей о доступе
        db.query(ProjectAccess).filter(ProjectAccess.project_id == project_id).delete()
        
        # 2. Удаление папки с файлами (КРИТИЧЕСКИЙ ШАГ!)
        if os.path.exists(db_project.file_path):
            shutil.rmtree(db_project.file_path) # Нужен import shutil
            
        # 3. Удаление самого проекта
        db.delete(db_project)
        db.commit()
        return True
    return False


def add_project_access(
    db: Session, 
    project_id: int, 
    user_id: int, 
    level: PermissionLevel
):
    """
    Создает или обновляет уровень доступа пользователя к проекту.
    Если доступ уже существует, он обновляется.
    """
    
    # Сначала проверяем, существует ли уже запись о доступе для этого пользователя и проекта
    db_access = db.query(ProjectAccess).filter(
        ProjectAccess.project_id == project_id,
        ProjectAccess.user_id == user_id
    ).first()

    if db_access:
        # UPDATE: Если запись найдена, просто обновляем уровень доступа
        db_access.permission_level = level
        db.commit()
        db.refresh(db_access)
        return {"action": "updated", "level": level}
    else:
        # CREATE: Если запись не найдена, создаем новую
        new_access = ProjectAccess(
            project_id=project_id,
            user_id=user_id,
            permission_level=level
        )
        db.add(new_access)
        db.commit()
        db.refresh(new_access)
        return {"action": "created", "level": level}


def get_access_level(db: Session, project_id: int, user_id: int) -> Optional[str]:
    """
    Возвращает строковое значение уровня доступа ('READ', 'WRITE', 'ADMIN') 
    или None, если доступ не найден.
    """
    
    # 1. Проверяем, является ли пользователь владельцем (Владелец всегда имеет WRITE/ADMIN)
    project = db.query(Project).filter(Project.project_id == project_id).first()
    
    if project and project.owner_id == user_id:
        # Владелец проекта автоматически имеет наивысшие права
        return "WRITE" # Можно использовать "ADMIN", если это определено в вашей логике

    # 2. Если не владелец, ищем запись в таблице прав доступа
    access_record = db.query(ProjectAccess).filter(
        ProjectAccess.project_id == project_id,
        ProjectAccess.user_id == user_id
    ).first()

    if access_record:
        return access_record.permission_level
    
    # Если не владелец и нет записи о доступе
    return None