from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy.orm import Session
from typing import List
from db.db import SessionLocal
from db import crud
from db import schemas
import shutil

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

router_reports = APIRouter(
    prefix="/reports",
    tags=["Reports"]
)

@router_reports.get("/{topic}", response_model=List[schemas.ReportSchema])
def read_reports_by_topic(topic: str, db: Session = Depends(get_db)):
    return crud.get_reports_by_topic(db, topic)

@router_reports.get("/reports")
def read_reports(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return crud.get_reports(db, skip=skip, limit=limit)

@router_reports.get("/reports/{topic}/{area}")
def read_reports_by_topic_area(topic: str, area:str, db: Session = Depends(get_db)):
    return crud.get_reports_by_topic_area(db, topic, area)

@router_reports.post("/reports")
def add_reports(reports: List[schemas.ReportSchema], db: Session = Depends(get_db)):
    new_reports = crud.create_reports(db, reports)
    return [{"id": report.id, "topic": report.topic, "area":report.area} for report in new_reports]

@router_reports.post("/upload_reports")
async def upload(file: UploadFile):
    with open(f"./reports/{file.filename}", "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"filename": file.filename, "status": "saved"}