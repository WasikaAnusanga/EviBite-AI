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

from backend.app.agents.recommendation_response.service import rank_candidates
from backend.app.agents.agent_stubs import EvidenceObject


def _make_cereal(name, sugars, protein):
    return EvidenceObject(
        product_id=name.lower().replace(" ", "-"),
        name=name,
        brand="TestBrand",
        nutrition={
            "sugars_g_100g": sugars,
            "protein_g_100g": protein,
        },
        completeness=0.9,
        source="open_food_facts",
    )


def test_rank_candidates_prefers_lower_sugar():
    high_sugar = _make_cereal("Sugary Puffs", sugars=30.0, protein=5.0)
    low_sugar = _make_cereal("Bran Basics", sugars=5.0, protein=5.0)

    ranked = rank_candidates(
        evidence=[high_sugar, low_sugar],
        query="cereal with less sugar",
        nutrients=["sugars"],
    )

    assert ranked[0].name == "Bran Basics"


def test_rank_candidates_prefers_higher_protein():
    low_protein = _make_cereal("Light Flakes", sugars=10.0, protein=2.0)
    high_protein = _make_cereal("Protein Crunch", sugars=10.0, protein=15.0)

    ranked = rank_candidates(
        evidence=[low_protein, high_protein],
        query="cereal with more protein",
        nutrients=["protein"],
    )

    assert ranked[0].name == "Protein Crunch"


def test_rank_candidates_no_direction_returns_original_order():
    a = _make_cereal("Cereal A", sugars=10.0, protein=5.0)
    b = _make_cereal("Cereal B", sugars=8.0, protein=6.0)

    ranked = rank_candidates(
        evidence=[a, b],
        query="tell me about cereals",  # no less/more wording
        nutrients=["sugars"],
    )

    assert [c.name for c in ranked] == ["Cereal A", "Cereal B"]


def test_rank_candidates_missing_data_sinks_to_bottom():
    has_data = _make_cereal("Has Data", sugars=8.0, protein=5.0)
    missing_data = EvidenceObject(
        product_id="missing-data",
        name="Missing Data",
        brand="TestBrand",
        nutrition={},  # no sugars field at all
        completeness=0.5,
        source="open_food_facts",
    )

    ranked = rank_candidates(
        evidence=[missing_data, has_data],
        query="cereal with less sugar",
        nutrients=["sugars"],
    )

    assert ranked[0].name == "Has Data"