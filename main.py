from fastapi import FastAPI, Depends, UploadFile
import uvicorn
from sqlalchemy.orm import Session
from utils.db import SessionLocal, engine, Base
from utils import crud
from utils.schemas import ReportSchema, DeepResearchSchema
from typing import List
import shutil
from utils.openai_api import run_deep_research
from dotenv import load_dotenv

load_dotenv()

# -------- FastAPI App --------
app = FastAPI()
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -------- Reports Endpoints --------
@app.get("/reports/{topic}", response_model=List[ReportSchema], tags=["Reports"])
def read_reports_by_topic(topic:str, db: Session = Depends(get_db)):
    return crud.get_reports_by_topic(db, topic)

@app.get("/reports", tags=["Reports"])
def read_reports(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return crud.get_reports(db, skip=skip, limit=limit)

@app.get("/reports/{topic}/{area}", tags=["Reports"])
def read_reports_by_topic_area(topic: str, area:str, db: Session = Depends(get_db)):
    return crud.get_reports_by_topic_area(db, topic, area)

@app.post("/reports", tags=["Reports"])
def add_reports(reports: List[ReportSchema], db: Session = Depends(get_db)):
    new_reports = crud.create_reports(db, reports)
    return [{"id": report.id, "topic": report.topic, "area":report.area} for report in new_reports]

@app.post("/upload_reports", tags=["Reports"])
async def upload(file: UploadFile):
    with open(f"./reports/{file.filename}", "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"filename": file.filename, "status": "saved"}


# -------- Openai Endpoints --------
@app.post("/deep_research", tags=["Deep Research"])
def create_report(dr_input: DeepResearchSchema,  db: Session = Depends(get_db)):
    return run_deep_research(topic = dr_input.topic,
                            prompt = dr_input.prompt,
                            output_docx_path=dr_input.file_url)
    



if __name__=="__main__":
    uvicorn.run(app = "main:app", reload=True)