from services import workflows as wrk
from fastapi import APIRouter

router_llm_workflows = APIRouter(
    prefix="/workflow",
    tags=["LLM Workflows"]
)

@router_llm_workflows.post("/facts/expand")
def expand_database(topic_name: str, web= False):
    result = wrk.expand_database(topic_name = topic_name, use_websearch=web)
    return {"status": "ok", "message": f"File was saved to {result}"}

@router_llm_workflows.post("/facts/search")
def find_facts(topic_name: str):
    result = wrk.find_connections(topic_name = topic_name)
    return {"status": "ok", "message": f"File was saved to {result}"}

@router_llm_workflows.post("/facts/check")
def check_hypothesis(topic_name: str):
    result = wrk.check_hypotheses(topic_name = topic_name)
    return {"status": "ok", "message": f"File was saved to {result}"}

@router_llm_workflows.post("/scenario/structure")
def create_scenario_structure(topic_name: str, num_series: int):
    result = wrk.build_script_structure(topic_name = topic_name, num_series=num_series)
    return {"status": "ok", "message": f"File was saved to {result}"}

@router_llm_workflows.post("/scenario")
def create_scenario(topic_name: str):
    result = wrk.write_script_text(topic_name = topic_name)
    return {"status": "ok", "message": f"File was saved to {result}"}