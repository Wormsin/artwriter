from pydantic import BaseModel
from typing import List, Optional

class FactSchema(BaseModel):
    title: str
    theme: str
    years: list[int]
    names: list[str]
    summary_short: str
    #summary_long: str
   # quotes: list[str]
    source_url: str
    source_title: str
    source_type: str
    parameter_id: int

class ParameterSchema(BaseModel):
    topic: str
    theme: str
    sources: Optional[str] = "любые достоверные источники"
    limit: Optional[int] = None
