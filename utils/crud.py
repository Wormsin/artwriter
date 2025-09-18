from sqlalchemy.orm import Session
from . import models
from . import schemas
from typing import List

# -------- Parameters --------
def create_facts_parameter(db: Session, param: schemas.ParameterSchema):
    db_param = models.FactsParameter(
        topic=param.topic,
        theme=param.theme,
        sources=param.sources,
        limit=param.limit
    )
    db.add(db_param)
    db.commit()
    db.refresh(db_param)
    return db_param

def get_facts_parameters(db: Session, skip: int = 0, limit: int = 10):
    return db.query(models.FactsParameter).offset(skip).limit(limit).all()

def get_facts_parameter(db: Session, parameter_id: int):
    return db.query(models.FactsParameter).filter(models.FactsParameter.id == parameter_id).first()

# -------- Facts --------
def create_facts(db: Session, facts_data: List[schemas.FactSchema]):
    created_facts = []
    for fact_data in facts_data:
        fact = models.Fact(
            title=fact_data.title,
            theme = fact_data.theme,
            years = fact_data.years,
            names = fact_data.names,
            summary_short = fact_data.summary_short,
            source_title = fact_data.source_title,
            source_url=fact_data.source_url,
            source_type=fact_data.source_type,
            parameter_id=fact_data.parameter_id
        )
        db.add(fact)
        created_facts.append(fact)
    db.commit()
    for fact in created_facts:
        db.refresh(fact)
    return created_facts

def get_facts_by_parameter(db: Session, parameter_id: int):
    return db.query(models.Fact).filter(models.Fact.parameter_id == parameter_id).all()

def get_facts(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Fact).offset(skip).limit(limit).all()

def get_facts_by_title(db: Session, title: int):
    return db.query(models.Fact).filter(models.Fact.title == title).all()

# -------- Script Structures --------
def create_script_structures(db: Session, structures_data: List[schemas.ScriptStructureSchema]):
    created_structures = []
    for structure_data in structures_data:
        db_structure = models.ScriptStructure(
            topic=structure_data.topic,
            title = structure_data.title,
            series_number=structure_data.series_number,
            summary = structure_data.summary
        )
        # Привязываем факты через fact_ids из структуры
        if structure_data.fact_ids:
            facts = db.query(models.Fact).filter(models.Fact.id.in_(structure_data.fact_ids)).all()
            db_structure.facts = facts
        db.add(db_structure)
        created_structures.append(db_structure)
    db.commit()
    for structure in created_structures:
        db.refresh(structure)
    return created_structures

def get_script_structures(db: Session, skip: int = 0, limit: int = 10):
    return db.query(models.ScriptStructure).offset(skip).limit(limit).all()

def get_structure_by_topic(db: Session, topic: str):
    return db.query(models.ScriptStructure).filter(models.ScriptStructure.topic == topic).all()

def get_structure_by_topic_and_series_number(db: Session, topic: str, series_num: int):
    return (
        db.query(models.ScriptStructure)
        .filter(
            models.ScriptStructure.topic == topic,
            models.ScriptStructure.series_number == series_num
        )
        .all()
    )