from sqlalchemy.orm import Session
from . import models
from . import schemas
from typing import List

# -------- Reports --------
def create_reports(db: Session, reports_data: List[schemas.ReportSchema]):
    created_reports = []
    for report_data in reports_data:
        report = models.ReportFile(
            topic=report_data.topic,
            area = report_data.area,
            years = report_data.years,
            file_url = report_data.file_url
        )
        db.add(report)
        created_reports.append(report)
    db.commit()
    for report in created_reports:
        db.refresh(report)
    return created_reports

def get_reports_by_topic(db: Session, topic: str, area:str):
    return db.query(models.ReportFile).filter(models.ReportFile.topic == topic).all()

def get_reports(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.ReportFile).offset(skip).limit(limit).all()

def get_reports_by_topic_area(db: Session, topic: str, are:str):
    return db.query(models.ReportFile).filter(models.ReportFile.topic == topic).all()

    