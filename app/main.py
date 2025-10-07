from fastapi import FastAPI
import uvicorn
from db.db import Base, engine
from api import db_routes, disk_routes, llm_routes
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
Base.metadata.create_all(bind=engine)

app.include_router(db_routes.router_reports)
app.include_router(disk_routes.router_disk)
app.include_router(llm_routes.router_llm_workflows)

#test route
@app.get("/")
def read_root():
    return {"status": "ok", "message": "Welcome to the API"}


if __name__=="__main__":
    uvicorn.run(app = "main:app", reload=True)