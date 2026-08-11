from backend.app.models.messages import ChatRequest
from backend.app.orchestration.orchestrator import run_orchestration


def test_orchestration_allergen_flow():
    req = ChatRequest(message="I have a peanut allergy. Can I eat Nutella and how much sugar does it have?")
    res = run_orchestration(req)

    assert res.trace_id.startswith("REQ-")
    assert res.execution_path == ["triage", "retrieval", "analysis", "response"]
    assert len(res.execution_steps) == 4
    assert res.triage_output["primary_intent"] == "allergen_query"
    assert "Nutella" in res.final_response or "Product" in res.final_response


def test_orchestration_unsupported_flow():
    req = ChatRequest(message="What will be the weather condition tomorrow?")
    res = run_orchestration(req)

    assert res.execution_path == ["triage", "response"]
    assert "outside food product information" in res.final_response.lower() or "assistant" in res.final_response.lower()


def test_orchestration_clarification_flow():
    req = ChatRequest(message="Does it contain peanuts?")
    res = run_orchestration(req)

    assert res.execution_path == ["triage"]
    assert "product" in res.final_response.lower() or "check" in res.final_response.lower()
