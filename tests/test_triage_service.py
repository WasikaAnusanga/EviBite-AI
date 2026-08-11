from unittest.mock import patch

from backend.app.agents.triage.llm_extractor import TriageLLMExtraction
from backend.app.agents.triage.service import triage_message
from backend.app.models.triage import (
    Intent,
    ProductEntity,
    RiskLevel,
    RouteAgent,
    TriageRequest,
    TriageStatus,
)


def test_barcode_lookup():
    out = triage_message(TriageRequest(message="5449000000996"))
    assert out.primary_intent == Intent.BARCODE_LOOKUP
    assert out.products[0].barcode == "5449000000996"
    assert out.triage_status == TriageStatus.READY


def test_allergen_query_high_risk():
    out = triage_message(
        TriageRequest(message="Does Nutella contain peanuts?")
    )
    assert out.primary_intent == Intent.ALLERGEN_QUERY
    assert out.risk_level == RiskLevel.HIGH
    assert out.routing.analysis_required is True
    assert "peanut" in out.allergens


def test_multi_intent_allergen_and_nutrition():
    out = triage_message(
        TriageRequest(message="I have a peanut allergy. Can I eat Nutella and how much sugar does it have?")
    )
    assert out.primary_intent == Intent.ALLERGEN_QUERY
    assert Intent.NUTRITION_QUERY in out.secondary_intents
    assert out.risk_level == RiskLevel.HIGH
    assert out.routing.analysis_required is True
    assert any(p.name and p.name.lower() == "nutella" for p in out.products)
    assert "peanut" in out.allergens
    assert "sugars" in out.nutrients
    assert len(out.subtasks) >= 2


def test_clarification_required_when_product_missing():
    out = triage_message(
        TriageRequest(message="Does it contain peanuts?")
    )
    assert out.triage_status == TriageStatus.CLARIFICATION_REQUIRED
    assert out.clarification.required is True
    assert "product" in out.clarification.missing_fields


def test_llm_structured_extraction_integration():
    mock_llm_output = TriageLLMExtraction(
        primary_intent=Intent.ALLERGEN_QUERY,
        secondary_intents=[Intent.NUTRITION_QUERY],
        products=[ProductEntity(name="Nutella")],
        allergens=["peanut"],
        nutrients=["sugars"],
        requested_fields=["allergens", "ingredients", "sugars"],
        subtasks=[
            {"intent": "allergen_query", "query_fragment": "peanut allergy check", "target_fields": ["allergens"]},
            {"intent": "nutrition_query", "query_fragment": "sugar content", "target_fields": ["sugars"]},
        ],
    )

    with patch("backend.app.agents.triage.service.extract_with_llm", return_value=mock_llm_output):
        out = triage_message(
            TriageRequest(message="I have a peanut allergy. Can I eat Nutella and how much sugar does it have?")
        )
        assert out.primary_intent == Intent.ALLERGEN_QUERY
        assert Intent.NUTRITION_QUERY in out.secondary_intents
        assert out.products[0].name == "Nutella"
        assert out.risk_level == RiskLevel.HIGH
        assert RouteAgent.ANALYSIS in out.routing.required_agents
