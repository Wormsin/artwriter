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

class ScenarioStructureSchema(WorkflowSchema):
    num_series: int

class ScenarioSchema(WorkflowSchema):
    max_output_tokens: int