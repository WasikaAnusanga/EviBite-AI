from fastapi import APIRouter
from backend.app.models.triage import TriageRequest, TriageOutput
from backend.app.agents.triage.service import triage_message

router = APIRouter(prefix="/agents", tags=["agents"])

@router.post("/triage", response_model=TriageOutput)
def triage(request: TriageRequest) -> TriageOutput:
    return triage_message(request)
