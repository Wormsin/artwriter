from fastapi import FastAPI
import uvicorn
from db.db import Base, engine
from api import disk_routes, llm_routes, auth_routes, db_routes, files_routes
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
Base.metadata.create_all(bind=engine)

app.include_router(auth_routes.router_auth)
app.include_router(db_routes.router_db)
#app.include_router(disk_routes.router_disk)
app.include_router(llm_routes.router_llm_workflows)
app.include_router(files_routes.router_files)

#test route
@app.get("/")
def read_root():
    return {"status": "ok", "message": "Welcome to the API"}


if __name__=="__main__":
    uvicorn.run(app = "main:app", reload=True)