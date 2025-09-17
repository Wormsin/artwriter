from fastapi import FastAPI, Depends
import uvicorn
from sqlalchemy.orm import Session
from utils.db import SessionLocal, engine, Base
from utils import crud
from utils.schemas import FactSchema, ParameterSchema
from typing import List

# -------- FastAPI App --------
app = FastAPI()
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -------- Parameters Endpoints --------
@app.post("/parameters", response_model=ParameterSchema, tags=["Facts Filters"])
def add_parameters(param: ParameterSchema, db: Session = Depends(get_db)):
    return crud.create_facts_parameter(db, param)

@app.get("/parameters", response_model=List[ParameterSchema], tags=["Facts Filters"])
def read_parameters(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return crud.get_facts_parameters(db, skip=skip, limit=limit)

@app.get("/parameters/{parameter_id}", response_model=ParameterSchema, tags=["Facts Filters"])
def read_parameter(parameter_id: int, db: Session = Depends(get_db)):
    return crud.get_facts_parameter(db, parameter_id)

# -------- Facts Endpoints --------
@app.get("/facts/by-parameter/{parameter_id}", response_model=List[FactSchema], tags=["Facts"])
def read_facts_by_parameter(parameter_id: int, db: Session = Depends(get_db)):
    return crud.get_facts_by_parameter(db, parameter_id)

@app.get("/facts", tags=["Facts"])
def read_facts(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return crud.get_facts(db, skip=skip, limit=limit)

@app.post("/facts", tags=["Facts"])
def add_fact(fact: FactSchema, db: Session = Depends(get_db)):
    new_fact = crud.create_fact(db, fact)
    return {"id": new_fact.id, "title": new_fact.title}


if __name__=="__main__":
    uvicorn.run(app = "main:app", reload=True)