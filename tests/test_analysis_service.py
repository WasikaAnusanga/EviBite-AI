"""
Integration-style unit tests for service.py -- covers aggregation logic
(the 'most cautious verdict wins' rule) using real Pydantic models,
matching exactly what the Orchestrator sends in production.
"""

from backend.app.agents.agent_stubs import AnalysisRequest, EvidenceObject
from backend.app.agents.nutrition_allergen.service import analysis_service


def _nutella() -> EvidenceObject:
    return EvidenceObject(
        product_id="off-nutella",
        name="Nutella",
        ingredients_text="Wheat flour, sugar, palm oil, cocoa powder, milk solids, soy lecithin.",
        allergens=["gluten", "milk", "soy"],
        nutrition={"sugars_g_100g": 56.3, "protein_g_100g": 6.3},
        completeness=0.92,
    )


def test_no_conflict_allergen_query_returns_suitable():
    request = AnalysisRequest(
        trace_id="T1",
        primary_intent="allergen_query",
        allergens=["peanut"],
        evidence=[_nutella()],
    )
    response = analysis_service(request)
    assert response.safety_status == "SUITABLE"
    assert response.risk_level == "LOW"


def test_dietary_conflict_escalates_to_unsuitable_and_high_risk():
    request = AnalysisRequest(
        trace_id="T2",
        primary_intent="dietary_query",
        dietary_requirements=["vegan"],
        evidence=[_nutella()],
    )
    response = analysis_service(request)
    assert response.safety_status == "UNSUITABLE"
    assert response.risk_level == "HIGH"


def test_most_cautious_verdict_wins_across_multiple_checks():
    """If ANY check finds a conflict, the overall status must reflect it --
    even if other checks in the same request came back SUITABLE."""
    request = AnalysisRequest(
        trace_id="T3",
        primary_intent="allergen_query",
        allergens=["peanut"],          # SUITABLE on its own
        dietary_requirements=["vegan"], # UNSUITABLE on its own
        evidence=[_nutella()],
    )
    response = analysis_service(request)
    assert response.safety_status == "UNSUITABLE"


def test_nutrient_comparator_uses_original_query_direction():
    """Regression test: nutrient checks must respect the query's actual
    direction, not always default to 'low'."""
    high_protein_product = EvidenceObject(
        product_id="off-cereal",
        name="Test Cereal",
        nutrition={"protein_g_100g": 14.0},
        completeness=0.9,
    )
    request = AnalysisRequest(
        trace_id="T4",
        primary_intent="nutrition_query",
        nutrients=["protein"],
        evidence=[high_protein_product],
        original_query="I want a cereal with more protein",
    )
    response = analysis_service(request)
    assert "meets the 'high' threshold" in response.findings[0]


def test_no_constraints_returns_default_finding():
    request = AnalysisRequest(trace_id="T5", primary_intent="product_search", evidence=[_nutella()])
    response = analysis_service(request)
    assert response.safety_status == "SUITABLE"
    assert "No allergen, nutrient, or dietary constraints" in response.findings[0]