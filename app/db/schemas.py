from pydantic import BaseModel
from typing import List, Optional

class ReportSchema(BaseModel):
    topic: str
    years: str
    area:str
    file_url:str

class DeepResearchSchema(ReportSchema):
    prompt: str

class ProjectInitialization(BaseModel):
    topic_name: str

class DBExpansion(ProjectInitialization):
    use_websearch: bool

class ScenarioStructureSchema(ProjectInitialization):
    num_series: int

class ScenarioSchema(ProjectInitialization):
    max_output_tokens: int