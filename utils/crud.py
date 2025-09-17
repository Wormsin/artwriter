from sqlalchemy.orm import Session
from . import models
from . import schemas

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
def create_fact(db: Session, fact_data: schemas.FactSchema):
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
    db.commit()
    db.refresh(fact)
    return fact

def get_facts_by_parameter(db: Session, parameter_id: int):
    return db.query(models.Fact).filter(models.Fact.parameter_id == parameter_id).all()

def get_facts(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Fact).offset(skip).limit(limit).all()