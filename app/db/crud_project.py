import os
import shutil
from typing import Literal, Optional, List, Dict
from db.schemas import ProjectInitialization, ProjectResponseWithAccess
from db.models import Project, ProjectAccess
from sqlalchemy.orm import Session
from pathlib import Path
from fastapi import UploadFile
import logging

logger = logging.getLogger(__name__)

PROJECTS_ROOT_DIR = "projects_root"
PermissionLevel = Literal['READ', 'WRITE', 'ADMIN']

def get_project_by_id(db: Session, project_id: int) -> Optional[Project]:
    """
    Находит проект в базе данных по его уникальному ID.
    Возвращает объект Project или None, если проект не найден.
    """
    try:
        project = db.query(Project).filter(Project.project_id == project_id).first()
        if project:
            logger.info(f"Проект {project_id} найден для пользователя {project.owner_id}")
        else:
            logger.warning(f"Проект {project_id} не найден")
        return project
    except Exception as e:
        logger.error(f"Ошибка при поиске проекта {project_id}: {e}")
        raise


def create_user_project(db: Session, project_data: ProjectInitialization, owner_id: int):
    """Создать проект в БД и папку на диске."""
    try:
        existing_project = db.query(Project).filter_by(
            owner_id=owner_id,
            topic_name=project_data.topic_name
        ).first()
        
        if existing_project:
            logger.error(f"Проект с именем '{project_data.topic_name}' уже существует для пользователя {owner_id}")
            raise ValueError(f"Проект с именем '{project_data.topic_name}' уже существует для пользователя {owner_id}")
        
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
        logger.info(f"Создана папка проекта: {final_file_path}")
        
        db_project.file_path = final_file_path
        db.commit()
        
        # 4. Добавление владельца в права доступа (ADMIN)
        # Владелец всегда должен иметь полный доступ
        db_access = ProjectAccess(
            project_id=db_project.project_id,
            user_id=owner_id,
            permission_level="ADMIN"
        )
        db.add(db_access)
        db.commit()
        
        logger.info(f"Проект {db_project.project_id} создан для владельца {owner_id}")
        return db_project
    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка создания проекта для {owner_id}: {e}")
        raise


def get_user_accessible_projects(db: Session, user_id: int):
    """Получить список проектов, к которым у пользователя есть любой доступ."""
    try:
        # 1. Проекты, где пользователь является владельцем
        #owned_projects = db.query(Project).filter(Project.owner_id == user_id)
        
        # 2. Проекты, к которым предоставлен доступ
        accessible_projects = db.query(Project, ProjectAccess.permission_level).join(ProjectAccess).filter(
            ProjectAccess.user_id == user_id
        ).distinct()
        
        all_projects = []
        for project, perm_level in accessible_projects:
            # Добавляем временное поле для from_orm
            project.permission_level = perm_level
            all_projects.append(ProjectResponseWithAccess.model_validate(project))
        #all_projects = list(set(owned_projects.all() + accessible_projects.all()))
        logger.info(f"Пользователь {user_id} имеет доступ к {len(all_projects)} проектам")
        return all_projects
    except Exception as e:
        logger.error(f"Ошибка получения проектов для {user_id}: {e}")
        raise


def delete_project(db: Session, project_id: int):
    """Удалить проект из БД и его файлы с диска (осторожно!)."""
    try:
        db_project = db.query(Project).filter(Project.project_id == project_id).first()
        
        if db_project:
            # 1. Удаление записей о доступе
            db.query(ProjectAccess).filter(ProjectAccess.project_id == project_id).delete()
            
            # 2. Удаление папки с файлами (КРИТИЧЕСКИЙ ШАГ!)
            if os.path.exists(db_project.file_path):
                shutil.rmtree(db_project.file_path)
                logger.info(f"Удалена папка проекта: {db_project.file_path}")
            
            # 3. Удаление самого проекта
            db.delete(db_project)
            db.commit()
            logger.info(f"Проект {project_id} удален")
            return True
        else:
            logger.warning(f"Проект {project_id} не найден для удаления")
            return False
    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка удаления проекта {project_id}: {e}")
        raise


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
    try:
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
            logger.info(f"Доступ обновлен для пользователя {user_id} к проекту {project_id}: {level}")
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
            logger.info(f"Доступ создан для пользователя {user_id} к проекту {project_id}: {level}")
            return {"action": "created", "level": level}
    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка обновления доступа для {user_id} к {project_id}: {e}")
        raise


def get_access_level(db: Session, project_id: int, user_id: int) -> Optional[str]:
    """
    Возвращает строковое значение уровня доступа ('READ', 'WRITE', 'ADMIN') 
    или None, если доступ не найден.
    """
    try:
        # 1. Проверяем, является ли пользователь владельцем (Владелец всегда имеет ADMIN)
        project = db.query(Project).filter(Project.project_id == project_id).first()
        
        if project and project.owner_id == user_id:
            # Владелец проекта автоматически имеет наивысшие права
            logger.debug(f"Пользователь {user_id} — владелец проекта {project_id}, доступ: ADMIN")
            return "ADMIN" # Можно использовать "ADMIN", если это определено в вашей логике

        # 2. Если не владелец, ищем запись в таблице прав доступа
        access_record = db.query(ProjectAccess).filter(
            ProjectAccess.project_id == project_id,
            ProjectAccess.user_id == user_id
        ).first()

        if access_record:
            logger.debug(f"Доступ пользователя {user_id} к проекту {project_id}: {access_record.permission_level}")
            return access_record.permission_level
        
        # Если не владелец и нет записи о доступе
        logger.debug(f"Нет доступа для {user_id} к {project_id}")
        return None
    except Exception as e:
        logger.error(f"Ошибка проверки доступа {user_id} к {project_id}: {e}")
        raise


async def save_reports_to_project(
    folder_path: str,
    project_id: int, 
    uploaded_files: List[UploadFile]
) -> List[Dict]:
    results = []
    
    target_dir = Path(folder_path) / "DB"
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Создана папка DB для проекта {project_id}: {target_dir}")
    except Exception as e:
        logger.error(f"Не удалось создать папку для проекта ID {project_id}: {e}")
        raise Exception(f"Не удалось создать папку для проекта ID {project_id}: {e}")

    for file in uploaded_files:
        target_file_path = target_dir / file.filename
        try:
            contents = await file.read()
            with open(target_file_path, "wb") as f:
                f.write(contents)
            await file.seek(0) 

            results.append({
                "filename": file.filename,
                "location": str(target_file_path),
                "status": "success"
            })
            logger.info(f"Файл {file.filename} сохранен для проекта {project_id}")
            
        except Exception as e:
            results.append({
                "filename": file.filename,
                "status": "failed",
                "error": f"Ошибка сохранения: {e}"
            })
            logger.error(f"Ошибка при сохранении файла {file.filename} для {project_id}: {e}")
            raise Exception(f"Ошибка при сохранении файла {file.filename}: {e}")

    return results


def delete_project_data(db: Session, project_id: int):
    """
    Удаляет проект, включая все связанные записи о доступе.
    """
    db.query(ProjectAccess).filter(ProjectAccess.project_id == project_id).delete(synchronize_session=False)
    logger.info(f"Удалены записи ProjectAccess для проекта {project_id}.")

    # 2. Получение и удаление самого проекта (Таблица 2)
    project = db.query(Project).filter(Project.project_id == project_id).first()
    if not project:
        logger.warning(f"Проект с ID {project_id} не найден для удаления.")
        return None, None # Возвращаем отсутствие проекта
    
    folder_path = project.file_path
    
    db.delete(project)
    db.commit()
    logger.info(f"Проект {project_id} удален из БД.")
    
    return project.topic_name, folder_path