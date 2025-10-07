from services import yandex_api
from fastapi import APIRouter, File, UploadFile
from typing import List
from pathlib import Path
from db.schemas import ProjectInitialization

router_disk = APIRouter(
    prefix="/disk",
    tags=["Yandex disk"]
)


@router_disk.post("/upload/files")
def upload_file_disk(disk_folder: str, files: List[UploadFile] = File(...)):
    results = []
    for file in files:
        result =  yandex_api.save_file(disk_folder, file)
        results.append(result)
    return results

@router_disk.post("/upload/project")
def create_project_filesystem(topic_name: str):
    results = []
    result =  yandex_api.create_folder(f"/{topic_name}")
    results.append(result)
    folders = ["БД", "ФАКТЫ", "СТРУКТУРА", "СЦЕНАРИИ"]
    for folder in folders:
        result =  yandex_api.create_folder(f"/{topic_name}/{folder}")
        results.append(result)
    return results

@router_disk.post("/local/project")
def create_local_project_filesystem(project: ProjectInitialization):
    folders = ["БД", "ФАКТЫ", "СТРУКТУРА", "СЦЕНАРИИ"]
    base_dir = Path(f"{project.topic_name}")
    for folder in folders:
        (base_dir / folder).mkdir(parents=True, exist_ok=True)
    return {"status": "ok", "message": "Filesystem was created!"}