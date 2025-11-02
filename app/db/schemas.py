from pydantic import BaseModel
from typing import List, Optional, Dict

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
class ProjectResponseWithAccess(ProjectResponse):
    permission_level: str

class Token(BaseModel):
    access_token: str
    token_type: str

# Новые схемы для токенов (опционально, для API эндпоинтов)
class UserTokenUsage(BaseModel):
    """Схема для возврата использования токенов."""
    user_id: int
    token_usage: Dict[str, int]  # {"YYYY-MM": tokens, ...}

class UpdateTokensRequest(BaseModel):
    """Схема для запроса обновления токенов."""
    tokens: int


#----------------Projects-----------------------
# --- ВХОДНЫЕ МОДЕЛИ (для запросов) ---

class ProjectInitialization(BaseModel):
    topic_name: str

class WorkflowSchema(BaseModel):
    folder_path: str
    llm_model: str = "gemini-2.5-flash"

class WorkflowFactsSearchSchema(WorkflowSchema):
    search_type: str

class ScenarioStructureSchema(WorkflowSchema):
    num_series: int

class ScenarioSchema(WorkflowSchema):
    temperature: float


class FileFolder(BaseModel):
    folder_path: str

class FileUpdate(BaseModel):
    """Схема для получения обновленного контента от клиента."""
    folder_path: str
    stage_name: str
    content: str

# --- ВЫХОДНЫЕ МОДЕЛИ (для ответов) ---
class FileContent(BaseModel):
    """Схема для отправки контента файла клиенту."""
    file_name: str
    content: str
    