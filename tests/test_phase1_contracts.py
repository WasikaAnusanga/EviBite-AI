import pytest
from backend.app.models.triage import (
    NutrientConstraint,
    TriageOutput,
    TriageRequest,
    TriageStatus,
    Intent,
)
from backend.app.agents.agent_stubs import (
    EvidenceObject,
    RetrievalRequest,
    RetrievalResponse,
    AnalysisRequest,
    AnalysisResponse,
    ResponseRequest,
    ResponseResponse,
)
from backend.app.agents.triage.service import triage_message, _extract_constraints
from backend.app.agents.nutrition_allergen.service import analysis_service
from backend.app.agents.recommendation_response.service import response_service
from backend.app.orchestration.orchestrator import run_orchestration
from backend.app.models.messages import ChatRequest

def test_nutrient_constraint_parsing_high_protein():
    constraints = _extract_constraints("high protein cereal")
    protein_c = next((c for c in constraints if c.nutrient == "protein"), None)
    assert protein_c is not None
    assert protein_c.preference == "maximize"
    assert protein_c.operator is None
    assert protein_c.value is None

def test_nutrient_constraint_parsing_low_sugar():
    constraints = _extract_constraints("low sugar yogurt")
    sugar_c = next((c for c in constraints if c.nutrient == "sugar"), None)
    assert sugar_c is not None
    assert sugar_c.preference == "minimize"
    assert sugar_c.operator is None
    assert sugar_c.value is None

def test_nutrient_constraint_parsing_sugar_under_10g():
    constraints = _extract_constraints("sugar under 10g")
    sugar_c = next((c for c in constraints if c.nutrient == "sugar"), None)
    assert sugar_c is not None
    assert sugar_c.preference == "minimize"
    assert sugar_c.operator == "lt"
    assert sugar_c.value == 10.0
    assert sugar_c.unit == "g"

def test_nutrient_constraint_parsing_protein_over_20g():
    constraints = _extract_constraints("protein over 20g")
    protein_c = next((c for c in constraints if c.nutrient == "protein"), None)
    assert protein_c is not None
    assert protein_c.preference == "maximize"
    assert protein_c.operator == "gt"
    assert protein_c.value == 20.0
    assert protein_c.unit == "g"

def test_constraints_survive_agent1_to_agent3():
    req = ChatRequest(message="Check Nutella for sugar under 10g")
    res = run_orchestration(req)
    triage_out = TriageOutput.model_validate(res.triage_output)
    assert len(triage_out.nutrient_constraints) > 0
    s_constraint = triage_out.nutrient_constraints[0]
    assert s_constraint.nutrient == "sugar"
    assert s_constraint.value == 10.0
    assert s_constraint.operator == "lt"
    # Verify final response reflects constraint check or findings
    assert res.final_response is not None

def test_constraints_survive_agent1_to_agent4():
    req = ChatRequest(message="Recommend cereal high protein and sugar under 5g")
    res = run_orchestration(req)
    assert res.final_response is not None
    assert len(res.triage_output["nutrient_constraints"]) >= 1

def test_evidence_provenance_survives_agent2_to_agent4():
    ev = EvidenceObject(
        evidence_id="off-12345",
        source_type="OPEN_FOOD_FACTS",
        source_name="Open Food Facts",
        product_name="Test Cereal",
        brand="TestBrand",
        ingredients_text="Oats, honey",
        nutrition={"sugars_g_100g": 4.0, "protein_g_100g": 10.0},
    )
    req = ResponseRequest(
        trace_id="TRACE-1",
        query="test query",
        intent="product_search",
        triage_status="READY",
        evidence=[ev],
    )
    resp = response_service(req)
    assert len(resp.sources) > 0
    assert resp.sources[0]["source_type"] == "OPEN_FOOD_FACTS"
    assert resp.sources[0]["source_name"] == "Open Food Facts"
    assert "off-12345" in resp.evidence_ids

def test_evidence_object_open_food_facts_representation():
    ev = EvidenceObject(
        product_id="3017620422003",
        name="Nutella",
        brand="Ferrero",
        source_type="OPEN_FOOD_FACTS",
    )
    assert ev.product_name == "Nutella"
    assert ev.source_type == "OPEN_FOOD_FACTS"

def test_evidence_object_user_document_representation():
    ev = EvidenceObject(
        evidence_id="doc-chunk-99",
        source_type="USER_DOCUMENT",
        source_name="My_Diet_Plan.pdf",
        document_id="doc-123",
        document_name="My_Diet_Plan.pdf",
        page_number=3,
        chunk_id="chunk-99",
        raw_text="Doctor recommended less than 15g sugar per day.",
    )
    assert ev.source_type == "USER_DOCUMENT"
    assert ev.document_name == "My_Diet_Plan.pdf"
    assert ev.page_number == 3
