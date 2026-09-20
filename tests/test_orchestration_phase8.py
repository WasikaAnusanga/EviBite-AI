import pytest

from backend.app.models.messages import ChatRequest
from backend.app.orchestration.orchestrator import run_orchestration
from backend.app.sources.user_documents import invalidate_user_index
from backend.app.services.document_service import save_user_document, delete_user_document
from backend.app.db.database import get_db


def test_greeting_route_skips_retrieval_and_analysis():
    req = ChatRequest(message="Hello EviBite!")
    res = run_orchestration(req)

    assert res.trace_id.startswith("REQ-")
    assert res.execution_path == ["triage", "response"]
    assert "retrieval" not in res.execution_path
    assert "analysis" not in res.execution_path

    # Verify execution step trace IDs and durations
    for step in res.execution_steps:
        assert step.duration_ms >= 0
        assert step.summary != ""


def test_simple_lookup_skips_analysis():
    req = ChatRequest(message="Search for Nutella")
    res = run_orchestration(req)

    assert res.execution_path == ["triage", "retrieval", "response"]
    assert "analysis" not in res.execution_path


def test_allergen_check_executes_full_pipeline():
    req = ChatRequest(message="Does Test Choco Bar contain milk?")
    res = run_orchestration(req)

    assert res.execution_path == ["triage", "retrieval", "analysis", "response"]
    assert "retrieval" in res.execution_path
    assert "analysis" in res.execution_path


def test_recommendation_executes_full_pipeline():
    req = ChatRequest(message="Recommend low sugar cereal options")
    res = run_orchestration(req)

    assert res.execution_path == ["triage", "retrieval", "analysis", "response"]


def test_clarification_stops_immediately():
    req = ChatRequest(message="Does it contain milk?")
    res = run_orchestration(req)

    assert res.execution_path == ["triage"]
    assert "retrieval" not in res.execution_path
    assert "analysis" not in res.execution_path
    assert "response" not in res.execution_path


def test_authenticated_user_identity_reaches_retrieval():
    user_id = "test_user_phase8_auth"
    db = get_db()
    db.user_documents.delete_many({"user_id": user_id})
    db.document_chunks.delete_many({"user_id": user_id})

    doc_text = "Product: Phase8 Spec Bar\nIngredients: Cocoa, sugar, milk."
    doc = save_user_document(
        user_id=user_id,
        content_bytes=doc_text.encode("utf-8"),
        original_filename="Phase8_Spec.txt",
        content_type="text/plain",
    )

    req = ChatRequest(
        message="Search Phase8 Spec Bar",
        user_id=user_id,
    )
    res = run_orchestration(req)

    assert "retrieval" in res.execution_path
    # Clean up
    delete_user_document(user_id, doc.document_id)
    invalidate_user_index(user_id)


def test_trace_id_consistency_across_all_steps():
    req = ChatRequest(message="Can I eat Cheerios if I have a wheat allergy?")
    res = run_orchestration(req)

    trace_id = res.trace_id
    assert trace_id.startswith("REQ-")
    assert res.triage_output["trace_id"] == trace_id


def test_execution_steps_summary_and_duration():
    req = ChatRequest(message="How much sugar is in Nutella?")
    res = run_orchestration(req)

    for step in res.execution_steps:
        assert hasattr(step, "duration_ms")
        assert hasattr(step, "summary")
        assert isinstance(step.duration_ms, int)
        assert isinstance(step.summary, str)
        assert len(step.summary) > 0
