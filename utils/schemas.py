from pydantic import BaseModel
from typing import List, Optional

class ReportSchema(BaseModel):
    topic: str
    years: str
    area:str
    file_url:str

class DeepResearchSchema(ReportSchema):
    prompt: str