from db.models import User
from services import workflows as wrk
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from db.db import get_db
from db.schemas import ProjectInitialization, ScenarioSchema, ScenarioStructureSchema, WorkflowSchema, WorkflowFactsSearchSchema
from db.auth_security import get_current_user 
from db.crud_project import get_project_by_id, get_access_level
import logging
from db.crud_user import update_user_token_usage

# Глобальный логгер (подхватит config из main.py)
logger = logging.getLogger(__name__)

router_llm_workflows = APIRouter(  # Переименовал для краткости
    prefix="/workflow",
    tags=["LLM Workflows"]
)

from db.models import User
from services import workflows as wrk
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from db.db import get_db
from db.schemas import ProjectInitialization, ScenarioSchema, ScenarioStructureSchema, WorkflowSchema
from db.auth_security import get_current_user 
from db.crud_project import get_project_by_id, get_access_level
from db.models import User  # Для update_user_token_usage
import logging

# Глобальный логгер (подхватит config из main.py)
logger = logging.getLogger(__name__)

router = APIRouter(  # Переименовал для краткости
    prefix="/workflow",
    tags=["LLM Workflows"]
)

# --- 1. РАСШИРЕНИЕ БАЗЫ ДАННЫХ (FACTS EXPAND) ---
@router_llm_workflows.post("/{project_id}/facts/expand", response_model=dict, status_code=status.HTTP_200_OK)
def expand_database(
    project_id: int,
    params: WorkflowSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # Проверка доступа к проекту (нужен хотя бы READ)
        access_level = get_access_level(db, project_id, current_user.user_id)
        if access_level not in ["READ", "WRITE", "ADMIN"]:
            logger.warning(f"Отказано в доступе к workflow expand для проекта {project_id} от {current_user.user_id}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this project")
        
        # Вызов workflow
        status, tokens = wrk.expand_database(params.folder_path, params.llm_model)
        if status != "success":
            logger.error(f"Workflow expand failed for project {project_id}: {status}")
            raise HTTPException(status_code=500, detail=status)
        
        # Обновление токенов
        update_user_token_usage(db, current_user.user_id, tokens)
        
        logger.info(f"База данных расширена для проекта {project_id} пользователем {current_user.user_id}")
        return {"status": "ok", "message": f"Database expanded successfully", "user": current_user.username}
    except HTTPException:
        # Пропускаем дальше — FastAPI сам обработает корректный статус
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"DB ошибка при расширении БД для проекта {project_id} от {current_user.user_id}: {e}")
        raise HTTPException(status_code=500, detail="Database error during expansion")
    except Exception as e:
        logger.error(f"Неожиданная ошибка при расширении БД для проекта {project_id} от {current_user.user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during workflow")
    

# --- 2. ПОИСК ФАКТОВ И СВЯЗЕЙ (FACTS SEARCH) ---
@router_llm_workflows.post("/{project_id}/facts/search", response_model=dict, status_code=status.HTTP_200_OK)
def find_facts(
    project_id: int,
    params: WorkflowFactsSearchSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # Проверка доступа
        access_level = get_access_level(db, project_id, current_user.user_id)
        if access_level not in ["WRITE", "ADMIN"]:
            logger.warning(f"Отказано в доступе к workflow search для проекта {project_id} от {current_user.user_id}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this project")
        
        # Вызов workflow (main по умолчанию)
        if params.search_type == "main":
            status, tokens = wrk.find_connections_main(params.folder_path, params.llm_model)
        else:
            status, tokens = wrk.find_connections_blind_spots(params.folder_path, params.llm_model)
        if status != "success":
            logger.error(f"Workflow search failed for project {project_id}: {status}")
            raise HTTPException(status_code=500, detail=status)
        
        # Обновление токенов
        update_user_token_usage(db, current_user.user_id, tokens)
        
        logger.info(f"Факты найдены для проекта {project_id} пользователем {current_user.user_id}")
        return {"status": "ok", "message": f"Facts search completed",  "user": current_user.username}
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"DB ошибка при поиске фактов для проекта {project_id} от {current_user.user_id}: {e}")
        raise HTTPException(status_code=500, detail="Database error during search")
    except Exception as e:
        logger.error(f"Неожиданная ошибка при поиске фактов для проекта {project_id} от {current_user.user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during workflow")


# --- 3. ПРОВЕРКА ГИПОТЕЗ (FACTS CHECK) ---
@router_llm_workflows.post("/{project_id}/facts/check", response_model=dict, status_code=status.HTTP_200_OK)
def check_hypothesis(
    project_id: int,
    params: WorkflowFactsSearchSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # Проверка доступа
        access_level = get_access_level(db, project_id, current_user.user_id)
        if access_level not in ["WRITE", "ADMIN"]:
            logger.warning(f"Отказано в доступе к workflow check для проекта {project_id} от {current_user.user_id}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this project")
        
        # Вызов workflow
        status, tokens = wrk.check_hypotheses(params.folder_path, params.llm_model, params.search_type)
        if status != "success":
            logger.error(f"Workflow check failed for project {project_id} ({params.search_type}): {status}")
            raise HTTPException(status_code=500, detail=status)
        
        # Обновление токенов
        update_user_token_usage(db, current_user.user_id, tokens)
        
        logger.info(f"Гипотезы проверены ({params.search_type}) для проекта {project_id} пользователем {current_user.user_id}")
        return {"status": "ok", "message": f"Hypotheses checked successfully ({params.search_type})", "user": current_user.username}
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"DB ошибка при проверке гипотез для проекта {project_id} от {current_user.user_id}: {e}")
        raise HTTPException(status_code=500, detail="Database error during check")
    except Exception as e:
        logger.error(f"Неожиданная ошибка при проверке гипотез для проекта {project_id} от {current_user.user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during workflow")

# --- 4. СОЗДАНИЕ СТРУКТУРЫ СЦЕНАРИЯ ---
@router_llm_workflows.post("/{project_id}/scenario/structure", response_model=dict, status_code=status.HTTP_200_OK)
def create_scenario_structure(
    project_id: int,
    scenario: ScenarioStructureSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # Проверка доступа
        access_level = get_access_level(db, project_id, current_user.user_id)
        if access_level not in ["WRITE", "ADMIN"]:
            logger.warning(f"Отказано в доступе к workflow structure для проекта {project_id} от {current_user.user_id}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this project")
        
        # Вызов workflow
        status, tokens = wrk.build_script_structure(
            topic_path=scenario.folder_path, 
            num_series=scenario.num_series, 
            llm_model_name=scenario.llm_model
        )
        if status != "success":
            logger.error(f"Workflow structure failed for project {project_id}: {status}")
            raise HTTPException(status_code=500, detail=status)
        
        # Обновление токенов
        update_user_token_usage(db, current_user.user_id, tokens)
        
        logger.info(f"Структура сценария создана для проекта {project_id} пользователем {current_user.user_id}")
        return {"status": "ok", "message": f"Scenario structure created", "user": current_user.username}
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"DB ошибка при создании структуры сценария для проекта {project_id} от {current_user.user_id}: {e}")
        raise HTTPException(status_code=500, detail="Database error during structure creation")
    except Exception as e:
        logger.error(f"Неожиданная ошибка при создании структуры сценария для проекта {project_id} от {current_user.user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during workflow")



# --- 5. СОЗДАНИЕ СЦЕНАРИЯ (ТЕКСТ) ---
@router_llm_workflows.post("/{project_id}/scenario", response_model=dict, status_code=status.HTTP_200_OK)
def create_scenario(
    project_id: int,
    project: ScenarioSchema,  # Переименовал param для ясности
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # Проверка доступа
        access_level = get_access_level(db, project_id, current_user.user_id)
        if access_level not in ["WRITE", "ADMIN"]:
            logger.warning(f"Отказано в доступе к workflow scenario для проекта {project_id} от {current_user.user_id}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this project")
        
        # Вызов workflow
        status, tokens = wrk.write_script_text(
            topic_path=project.folder_path, 
            temperature=project.temperature, 
            llm_model_name=project.llm_model
        )
        if status != "success":
            logger.error(f"Workflow scenario failed for project {project_id}: {status}")
            raise HTTPException(status_code=500, detail=status)
        
        # Обновление токенов
        update_user_token_usage(db, current_user.user_id, tokens)
        
        logger.info(f"Сценарий создан для проекта {project_id} пользователем {current_user.user_id}")
        return {"status": "ok", "message": f"Scenario text generated", "user": current_user.username}
    
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"DB ошибка при создании сценария для проекта {project_id} от {current_user.user_id}: {e}")
        raise HTTPException(status_code=500, detail="Database error during scenario creation")
    except Exception as e:
        logger.error(f"Неожиданная ошибка при создании сценария для проекта {project_id} от {current_user.user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during workflow")
