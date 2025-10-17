from fastapi import APIRouter, HTTPException, Depends
from pathlib import Path
from db.schemas import FileContent, FileUpdate, FileFolder
from db.models import User
from db.auth_security import get_current_user 

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