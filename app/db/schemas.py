from pydantic import BaseModel
from typing import List, Optional

#----------------DB-----------------------
# --- ВХОДНЫЕ МОДЕЛИ (для запросов) ---

class UserCreate(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class ProjectShare(BaseModel):
    project_id: int
    target_username: str
    permission_level: str # 'READ' или 'WRITE'

# --- ВЫХОДНЫЕ МОДЕЛИ (для ответов) ---

class ProjectResponse(BaseModel):
    """Схема для возврата информации о проекте."""
    project_id: int
    owner_id: int
    topic_name: str
    file_path: str
    # Добавьте config, чтобы Pydantic мог работать с ORM
    class Config:
        from_attributes = True # (Для SQLAlchemy 2.0)

class Token(BaseModel):
    access_token: str
    token_type: str
#----------------Projects-----------------------

class ProjectInitialization(BaseModel):
    topic_name: str

class WorkflowSchema(BaseModel):
    folder_path: str
    llm_model: str = "gemini-2.5-flash"

class ScenarioStructureSchema(WorkflowSchema):
    num_series: int

class ScenarioSchema(WorkflowSchema):
    temperature: float



class FileFolder(BaseModel):
    folder_path: str
    
class FileContent(BaseModel):
    """Схема для отправки контента файла клиенту."""
    file_name: str
    content: str

class FileUpdate(BaseModel):
    """Схема для получения обновленного контента от клиента."""
    folder_path: str
    stage_name: str
    content: str