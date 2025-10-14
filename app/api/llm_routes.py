from db.models import User
from services import workflows as wrk
from fastapi import APIRouter, Depends
from db.schemas import ProjectInitialization, ScenarioSchema, ScenarioStructureSchema, WorkflowSchema
from db.auth_security import get_current_user 

router_llm_workflows = APIRouter(
    prefix="/workflow",
    tags=["LLM Workflows"]
)

@router_llm_workflows.post("/{project_id}/facts/expand")
def expand_database(
        params: WorkflowSchema,
        current_user: User = Depends(get_current_user)):
    wrk.expand_database(params.folder_path)
    return {"status": "ok", "message": f"File was saved", "user": current_user.username}

@router_llm_workflows.post("/{project_id}/facts/search")
def find_facts(params: WorkflowSchema,
            current_user: User = Depends(get_current_user)):
    wrk.find_connections(params.folder_path)
    return {"status": "ok", "message": f"File was saved", "user": current_user.username}

@router_llm_workflows.post("/{project_id}/facts/check")
def check_hypothesis(params: WorkflowSchema,
            current_user: User = Depends(get_current_user)):
    wrk.check_hypotheses(params.folder_path)
    return {"status": "ok", "message": f"File was saved", "user": current_user.username}

@router_llm_workflows.post("/{project_id}/scenario/structure")
def create_scenario_structure(scenario: ScenarioStructureSchema,
                            current_user: User = Depends(get_current_user)  ):
    wrk.build_script_structure(topic_path = scenario.folder_path, num_series=scenario.num_series)
    return {"status": "ok", "message": f"File was saved", "user": current_user.username}

@router_llm_workflows.post("/{project_id}/scenario")
def create_scenario(project: ScenarioSchema,
                    current_user: User = Depends(get_current_user)):
    wrk.write_script_text(topic_path = project.folder_path, max_output_tokens=project.max_output_tokens)
    return {"status": "ok", "message": f"File was saved", "user": current_user.username}