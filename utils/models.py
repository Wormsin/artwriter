from turtle import title
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Table
from sqlalchemy.dialects.postgresql import ARRAY
from . db import Base
from datetime import datetime
from sqlalchemy.orm import relationship

class FactsParameter(Base):
    __tablename__ = "facts_parameters"

    id = Column(Integer, primary_key=True, index=True)
    topic = Column(String, nullable=False)
    theme = Column(String, nullable=False)
    sources = Column(Text, nullable=True, default="любые")
    limit = Column(Integer, nullable=True)

    facts = relationship("Fact", back_populates="parameter")  # связь

structure_fact_association = Table(
    "structure_fact_association",
    Base.metadata,
    Column("script_structure_id", Integer, ForeignKey("script_structures.id")),
    Column("fact_id", Integer, ForeignKey("facts.id"))
)

class Fact(Base):
    __tablename__ = "facts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    theme =  Column(String)
    years = Column(ARRAY(Integer))
    #locations = Column(ARRAY(String))
    names = Column(ARRAY(String))
    summary_short = Column(Text)
    source_title = Column(String)
    source_type = Column(String)
    source_url = Column(String)
    created_at = Column(DateTime, default=datetime.now())

    parameter_id = Column(Integer, ForeignKey("facts_parameters.id")) 
    parameter = relationship("FactsParameter", back_populates="facts")
    script_structures = relationship("ScriptStructure", secondary="structure_fact_association", back_populates="facts")


class ScriptStructure(Base):
    __tablename__ = "script_structures"

    id = Column(Integer, primary_key=True, index=True)
    topic = Column(String, nullable=False)
    title = Column(String, nullable=False)
    series_number = Column(Integer, nullable=False)
    summary = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    facts = relationship("Fact", secondary="structure_fact_association", back_populates="script_structures")
