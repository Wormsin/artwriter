import shutil
from fastapi import APIRouter, HTTPException, Depends, status
from pathlib import Path
from db.schemas import FileContent, FileUpdate, FileFolder
from db.models import User
from db.auth_security import get_current_user 
from db.crud_project import get_access_level, delete_project_data
from sqlalchemy.orm import Session
from db.db import get_db
import os
import tempfile
import zipfile
from datetime import datetime
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask
from typing import List
import logging
from services.schemas import ScriptStructureID, ChapterStructureID
import json

# Глобальный логгер (подхватит config из main.py)
logger = logging.getLogger(__name__)

router_files = APIRouter(  # Переименовал для краткости
    prefix="/files",
    tags=["Project Files"]
)


# Список допустимых этапов для редактирования
FILE_STAGES = {
    "plus_facts": "DB/db_extension.txt",
    "interesting_facts_main": "FACTS/ALG_MAIN/HYP/db_facts.txt",
    "interesting_facts_blind": "FACTS/ALG_BLIND/HYP/db_facts.txt",
    "check_facts_main": "FACTS/ALG_MAIN/CHECK/db_facts_checked.txt",
    "check_facts_blind": "FACTS/ALG_BLIND/CHECK/db_facts_checked.txt",
    "facts_lens_main": "FACTS/ALG_MAIN/HYP/LENS",
    "structure": "STRUCTURE/script_structure.txt"
}

def _create_template_stucture(path: Path):
    example_script = [ScriptStructureID(
        serie_number=1,
        serie_name="Имя серии",
        content=[
            ChapterStructureID(
                chapter_number=1,
                chapter_name="Начало",
                chapter_description="Главный герой просыпается и понимает, что структура сценария не написана."
            )
        ]
    )]
    path.parent.mkdir(parents=True, exist_ok=True)
    data = [script.model_dump() for script in example_script] 
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    logger.info(f"✅ Tamplate of script sctructure успешно создан")

@router_files.get("/{project_id}/{stage_name}", response_model=FileContent)
async def read_file_content(
    project_id: int,
    stage_name: str,
    params: FileFolder,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # Проверка доступа (нужен хотя бы READ)
        access_level = get_access_level(db, project_id, current_user.user_id)
        if access_level not in ["READ", "WRITE", "ADMIN"]:
            logger.warning(f"Отказано в доступе к файлу {stage_name} проекта {project_id} от {current_user.user_id}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this project")
        
        if stage_name not in FILE_STAGES:
            raise HTTPException(status_code=400, detail=f"Неизвестный этап: {stage_name}")

        file_name = FILE_STAGES[stage_name]
        file_path = Path(params.folder_path) / file_name

        # Создаем директории, если нужно (для папок вроде LENS)
        if "/" in file_name:
            dir_path = file_path.parent
            dir_path.mkdir(parents=True, exist_ok=True)
        
        if not file_path.exists() and stage_name == "structure":
            _create_template_stucture(file_path)

        # Если файл не существует, создаем пустой
        if not file_path.exists():
            file_path.touch()  # Создаем пустой файл
            content = ""
            logger.info(f"Создан пустой файл {file_name} для {stage_name} в проекте {project_id}")
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        
        logger.info(f"Файл {file_name} прочитан для {stage_name} в проекте {project_id} пользователем {current_user.user_id}")
        return FileContent(file_name=file_name, content=content)
        
    except Exception as e:
        logger.error(f"Ошибка чтения файла {stage_name} для проекта {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка чтения файла: {e}")


@router_files.post("/update/{project_id}", response_model=dict)
async def update_file_content(
    project_id: int,
    data: FileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Обновляет содержимое файла на сервере."""
    try:
        stage_name = data.stage_name
        
        # Проверка доступа (нужен WRITE или выше)
        access_level = get_access_level(db, project_id, current_user.user_id)
        if access_level not in ["WRITE", "ADMIN"]:
            logger.warning(f"Отказано в обновлении файла {stage_name} проекта {project_id} от {current_user.user_id} (уровень: {access_level})")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Write access required")
        
        if stage_name not in FILE_STAGES:
            raise HTTPException(status_code=400, detail=f"Неизвестный этап: {stage_name}")

        file_name = FILE_STAGES[stage_name]
        file_path = Path(data.folder_path) / file_name

        # Создаем директории, если нужно
        if "/" in file_name:
            dir_path = file_path.parent
            dir_path.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(data.content)
            
        logger.info(f"Файл {file_name} обновлен для {stage_name} в проекте {project_id} пользователем {current_user.user_id}")
        return {"status": "success", "message": f"Файл {file_name} успешно обновлен."}
        
    except Exception as e:
        logger.error(f"Ошибка обновления файла {data.stage_name} для проекта {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка записи файла: {e}")


@router_files.get("/algorithms/{project_id}", response_model=List[str])
async def get_algorithms(
    project_id: int,
    params: FileFolder,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Возвращает список доступных алгоритмов (подпапок ALG_* в FACTS)."""
    try:
        # Проверка доступа (нужен хотя бы READ)
        access_level = get_access_level(db, project_id, current_user.user_id)
        if access_level not in ["READ", "WRITE", "ADMIN"]:
            logger.warning(f"Отказано в доступе к алгоритмам проекта {project_id} от {current_user.user_id}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this project")
        
        facts_dir = Path(params.folder_path) / "FACTS"
        if not facts_dir.exists():
            logger.info(f"Папка FACTS не найдена для проекта {project_id}")
            return []  # Пустой список, если папки нет
        
        alg_folders = [d.name for d in facts_dir.iterdir() if d.is_dir() and d.name.startswith("ALG_")]
        alg_folders.sort()  # Сортируем для consistency
        
        logger.info(f"Список алгоритмов возвращен для проекта {project_id}: {alg_folders}")
        return alg_folders
        
    except Exception as e:
        logger.error(f"Ошибка получения алгоритмов для проекта {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

def _create_zip_of_folder(target_dir: str, files_type = ".docx") -> str:
    # получаем список .docx в директории (только в корне, без рекурсии; можно добавить рекурсию, если нужно)
    docs = [f for f in os.listdir(target_dir)
            if os.path.isfile(os.path.join(target_dir, f)) and f.endswith(files_type)]

    if not docs:
        return ""  # признак отсутствия файлов

    # Создаём временный zip-файл
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    tmp_zip = tempfile.NamedTemporaryFile(delete=False, prefix=f"docx_archive_{ts}_", suffix=".zip")
    tmp_zip_path = tmp_zip.name
    tmp_zip.close()

    # Записываем файлы в zip
    with zipfile.ZipFile(tmp_zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for filename in docs:
            # защита от path-traversal: используем только basename
            safe_name = os.path.basename(filename)
            abs_path = os.path.abspath(os.path.join(target_dir, safe_name))
            # Дополнительная проверка: путь должен находиться в DOCS_DIR
            if not abs_path.startswith(os.path.abspath(target_dir) + os.sep):
                continue
            zf.write(abs_path, arcname=safe_name)

    return tmp_zip_path

def _remove_file(path: str):
    try:
        os.remove(path)
    except Exception:
        pass

@router_files.get("/download/scenario/{project_id}")
async def download_all(
    project_id: int,
    params: FileFolder,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # Проверка доступа (нужен хотя бы READ)
        access_level = get_access_level(db, project_id, current_user.user_id)
        if access_level not in ["READ", "WRITE", "ADMIN"]:
            logger.warning(f"Отказано в скачивании сценария проекта {project_id} от {current_user.user_id}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this project")
        
        scenario_dir = os.path.join(params.folder_path, "SCENARIO") 
        zip_path = _create_zip_of_folder(scenario_dir)
        if not zip_path:
            logger.warning(f"Нет .docx файлов в SCENARIO для проекта {project_id}")
            raise HTTPException(status_code=404, detail="В папке нет .docx файлов")

        filename = os.path.basename(zip_path)
        # BackgroundTask удалит временный файл после завершения отправки
        logger.info(f"Скачан ZIP сценария для проекта {project_id} пользователем {current_user.user_id}")
        return FileResponse(
            path=zip_path,
            media_type="application/zip",
            filename=filename,
            background=BackgroundTask(_remove_file, zip_path),
        )
        
    except Exception as e:
        logger.error(f"Ошибка скачивания сценария для проекта {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during download")


@router_files.get("/download/lens/{project_id}")
async def download_lens_zip(
    project_id: int,
    params: FileFolder,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Выгружает ZIP всех файлов из FACTS/ALG_MAIN/HYP/LENS."""
    try:
        # Проверка доступа (нужен хотя бы READ)
        access_level = get_access_level(db, project_id, current_user.user_id)
        if access_level not in ["READ", "WRITE", "ADMIN"]:
            logger.warning(f"Отказано в скачивании LENS проекта {project_id} от {current_user.user_id}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this project")
        
        lens_dir = os.path.join(params.folder_path, "FACTS/ALG_MAIN/HYP/LENS")
        
        zip_path = _create_zip_of_folder(lens_dir, files_type=".txt")
        if not zip_path or not os.listdir(lens_dir):
            logger.warning(f"Папка LENS пуста или не существует для проекта {project_id}")
            raise HTTPException(status_code=404, detail="No files in LENS folder")
        
        filename = os.path.basename(zip_path)
        # BackgroundTask удалит временный файл после завершения отправки
        logger.info(f"Скачан ZIP LENS для проекта {project_id} пользователем {current_user.user_id}")
        return FileResponse(
            path=zip_path,
            media_type="application/zip",
            filename=filename,
            background=BackgroundTask(_remove_file, zip_path),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка скачивания LENS для проекта {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during download")
    


@router_files.delete("/project/{project_id}")
async def delete_project_and_folder(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Удаляет проект из БД и его папку на сервере. 
    Требуется уровень доступа 'ADMIN' (только владелец может удалить проект).
    """
    
    # 1. Проверка доступа: только владелец (ADMIN) может удалить проект
    access_level = get_access_level(db, project_id, current_user.user_id)
    if access_level != "ADMIN":
        logger.warning(f"Отказано в удалении проекта {project_id} от {current_user.user_id} (уровень: {access_level})")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the project owner (ADMIN) can delete the project.")

    # 2. Удаление из БД (Project и ProjectAccess)
    project_name, folder_path = delete_project_data(db, project_id) # Добавьте импорт этой функции
    
    if not project_name:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Проект с ID {project_id} не найден.")

    # 3. Удаление папки проекта с сервера
    try:
        if folder_path and os.path.exists(folder_path):
            shutil.rmtree(folder_path)
            logger.info(f"Папка проекта {folder_path} удалена.")
        else:
            logger.warning(f"Папка проекта {folder_path} не найдена на сервере, но запись в БД удалена.")
            
    except OSError as e:
        logger.error(f"Ошибка при удалении папки проекта {project_id}: {e}")
        # Если не удалось удалить папку, все равно сообщаем об успехе в БД
        return {"status": "warning", "message": f"Проект '{project_name}' удален из БД, но возникла ошибка при удалении папки: {e}"}

    logger.info(f"Проект '{project_name}' (ID: {project_id}) полностью удален.")
    return {"status": "success", "message": f"Проект '{project_name}' полностью удален."}