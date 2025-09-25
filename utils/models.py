from turtle import title
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Table
from sqlalchemy.dialects.postgresql import ARRAY
from . db import Base
from datetime import datetime
from sqlalchemy.orm import relationship

class ReportFile(Base):
    __tablename__ = "report_files"

    id = Column(Integer, primary_key=True, index=True)

    topic = Column(String, nullable=False)
    years = Column(String, nullable=False)
    area = Column(String, nullable=False)
    file_url = Column(String, nullable=False)

    created_at = Column(DateTime, default=datetime.now())




