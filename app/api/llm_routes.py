from services import workflows as wrk
from fastapi import APIRouter
from db.schemas import DBExpansion, ProjectInitialization, ScenarioSchema, ScenarioStructureSchema

router_llm_workflows = APIRouter(
    prefix="/workflow",
    tags=["LLM Workflows"]
)

@router_llm_workflows.post("/facts/expand")
def expand_database(params: DBExpansion):
    result = wrk.expand_database(topic_name = params.topic_name, use_websearch=params.use_websearch)
    return {"status": "ok", "message": f"File was saved to {result}"}

@router_llm_workflows.post("/facts/search")
def find_facts(project: ProjectInitialization):
    result = wrk.find_connections(topic_name = project.topic_name)
    return {"status": "ok", "message": f"File was saved to {result}"}

@router_llm_workflows.post("/facts/check")
def check_hypothesis(project: ProjectInitialization):
    result = wrk.check_hypotheses(topic_name = project.topic_name)
    return {"status": "ok", "message": f"File was saved to {result}"}

@router_llm_workflows.post("/scenario/structure")
def create_scenario_structure(scenario: ScenarioStructureSchema):
    result = wrk.build_script_structure(topic_name = scenario.topic_name, num_series=scenario.num_series)
    return {"status": "ok", "message": f"File was saved to {result}"}

@router_llm_workflows.post("/scenario")
def create_scenario(project: ScenarioSchema):
    result = wrk.write_script_text(topic_name = project.topic_name, max_output_tokens=project.max_output_tokens)
    return {"status": "ok", "message": f"File was saved to {result}"}