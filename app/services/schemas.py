from pydantic import BaseModel, Field
import uuid


class ChapterStructure(BaseModel):
    chapter_number: int
    chapter_name: str
    chapter_description: str

class ChapterTextScructure(ChapterStructure):
    text: str = ""

class ScriptStructure(BaseModel):
    serie_number: int
    serie_name: str
    content: list[ChapterStructure]

class ScenarioStructure(BaseModel):
    serie_number: int
    serie_name: str
    content: list[ChapterTextScructure]

class ChapterStructureID(ChapterStructure):
    chapter_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
class ScriptStructureID(ScriptStructure):
    serie_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: list[ChapterStructureID]