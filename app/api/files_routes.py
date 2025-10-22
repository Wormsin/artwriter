from fastapi import APIRouter, HTTPException, Depends
from pathlib import Path
from db.schemas import FileContent, FileUpdate, FileFolder
from db.models import User
from db.auth_security import get_current_user 
import os
import tempfile
import zipfile
from datetime import datetime
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask


router_files = APIRouter(
    prefix="/files",
    tags=["Project Files"]
)


# Список допустимых этапов для редактирования
FILE_STAGES = {
    "plus_facts": "ФАКТЫ/db_extension.txt",
    "interesting_facts": "ФАКТЫ/db_facts.txt",
    "check_facts": "ФАКТЫ/db_facts_checked.txt",
    "structure": "СТРУКТУРА/script_structure.txt"
}

@router_files.get("/{project_id}/{stage_name}", response_model=FileContent)
async def read_file_content(stage_name: str,
                            params: FileFolder,
                            current_user: User = Depends(get_current_user)):
    
    if stage_name not in FILE_STAGES:
        raise HTTPException(status_code=400, detail=f"Неизвестный этап: {stage_name}")

    file_name = FILE_STAGES[stage_name]
    file_path = Path(params.folder_path) / file_name

    try:
        if not file_path.exists():
            # Если файл не существует, возвращаем пустой контент, чтобы можно было начать редактирование
            return FileContent(file_name=file_name, content="")
            
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return FileContent(file_name=file_name, content=content)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка чтения файла: {e}")


@router_files.post("/update/{project_id}")
async def update_file_content(data: FileUpdate,
                              current_user: User = Depends(get_current_user)):
    """Обновляет содержимое файла на сервере."""
    stage_name = data.stage_name
    
    if stage_name not in FILE_STAGES:
        raise HTTPException(status_code=400, detail=f"Неизвестный этап: {stage_name}")

    file_name = FILE_STAGES[stage_name]
    file_path = Path(data.folder_path) / file_name

    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(data.content)
            
        return {"status": "success", "message": f"Файл {file_name} успешно обновлен."}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка записи файла: {e}")
    


def _create_zip_of_docx(target_dir: str) -> str:
    # получаем список .docx в директории (только в корне, без рекурсии; можно добавить рекурсию, если нужно)
    docs = [f for f in os.listdir(target_dir)
            if os.path.isfile(os.path.join(target_dir, f)) and f.lower().endswith(".docx")]

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
async def download_all(params: FileFolder,
                        current_user: User = Depends(get_current_user)):
    zip_path = _create_zip_of_docx(os.path.join(params.folder_path, "СЦЕНАРИЙ"))
    if not zip_path:
        raise HTTPException(status_code=404, detail="В папке нет .docx файлов")

    filename = os.path.basename(zip_path)
    # BackgroundTask удалит временный файл после завершения отправки
    return FileResponse(
        path=zip_path,
        media_type="application/zip",
        filename=filename,
        background=BackgroundTask(_remove_file, zip_path),
    )