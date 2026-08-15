from backend.app.agents.agent_stubs import ResponseRequest, AnalysisResponse
from backend.app.agents.recommendation_response.service import response_service


def test_deduplicates_identical_findings():
    """Repeated identical findings should collapse into one occurrence."""
    request = ResponseRequest(
        trace_id="TEST-001",
        query="Does Nutella contain nuts?",
        intent="allergen_query",
        triage_status="READY",
        evidence=[],
        analysis=AnalysisResponse(
            trace_id="TEST-001",
            safety_status="UNSUITABLE",
            risk_level="HIGH",
            findings=[
                "[Nutella] Product declares 'tree_nuts' in its allergens field.",
                "[Nutella] Product declares 'tree_nuts' in its allergens field.",
                "[Nutella Plant-Based] Product declares 'tree_nuts' in its allergens field.",
            ],
        ),
    )

    result = response_service(request)

    assert result.trace_id == "TEST-001"
    assert result.answer.count("[Nutella]") == 1
    assert "[Nutella Plant-Based]" in result.answer


def test_unsupported_query_returns_refusal():
    """Off-topic queries should get the polite refusal, not evidence text."""
    request = ResponseRequest(
        trace_id="TEST-002",
        query="What's the weather today?",
        intent="unknown",
        triage_status="UNSUPPORTED",
        evidence=[],
        analysis=None,
    )

    result = response_service(request)

    assert "supermarket product intelligence assistant" in result.answer


def test_no_evidence_no_analysis_returns_not_found_message():
    """When nothing was retrieved and no analysis ran, respond honestly."""
    request = ResponseRequest(
        trace_id="TEST-003",
        query="Tell me about a product that doesn't exist",
        intent="product_search",
        triage_status="READY",
        evidence=[],
        analysis=None,
    )

    result = response_service(request)

    assert "could not find" in result.answer.lower()