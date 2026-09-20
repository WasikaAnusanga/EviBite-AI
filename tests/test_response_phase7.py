import pytest

from backend.app.agents.agent_stubs import (
    AnalysisResponse,
    EvidenceObject,
    ResponseRequest,
)
from backend.app.agents.recommendation_response.service import (
    rank_candidates,
    response_service,
)
from backend.app.models.triage import NutrientConstraint


def test_product_information():
    ev = EvidenceObject(
        evidence_id="off-1",
        name="Cheerios",
        brand="Nestle",
        barcode="7613035654321",
        ingredients_text="Whole grain oat flour, sugar, oat bran.",
        nutrition={"sugars_g_100g": 9.3},
        source_type="OPEN_FOOD_FACTS",
    )
    req = ResponseRequest(
        trace_id="t-1",
        query="Tell me about Cheerios",
        intent="PRODUCT_SEARCH",
        triage_status="COMPLETE",
        evidence=[ev],
    )
    res = response_service(req)
    assert res.status == "OK"
    assert "Cheerios" in res.answer
    assert res.sources[0]["type"] == "OPEN_FOOD_FACTS"
    assert res.sources[0]["barcode"] == "7613035654321"


def test_allergen_answer_safe_framing():
    ev = EvidenceObject(
        evidence_id="ev-alg-1",
        name="Choco Bar",
        ingredients_text="Cocoa, sugar, milk powder.",
        allergens=["milk"],
        source_type="USER_DOCUMENT",
        document_name="Supplier_Allergen_Guide.pdf",
        page_number=8,
    )
    analysis = AnalysisResponse(
        trace_id="t-2",
        safety_status="UNSUITABLE",
        allergen_findings=["Product declares 'milk' in its allergens field."],
    )
    req = ResponseRequest(
        trace_id="t-2",
        query="Can I eat Choco Bar with a milk allergy?",
        intent="ALLERGEN_CHECK",
        triage_status="COMPLETE",
        evidence=[ev],
        analysis=analysis,
    )
    res = response_service(req)
    assert res.status == "OK"
    assert "unsafe to eat" not in res.answer.lower()
    assert "Supplier_Allergen_Guide.pdf — page 8" in res.answer
    assert "physical package" in res.answer.lower()


def test_document_only_citation():
    ev = EvidenceObject(
        evidence_id="doc-123",
        name="Custom Guide Product",
        raw_text="Milk powder is listed in the ingredients.",
        source_type="USER_DOCUMENT",
        document_name="Supplier_Guide.pdf",
        page_number=4,
    )
    req = ResponseRequest(
        trace_id="t-3",
        query="Check custom guide product",
        intent="PRODUCT_SEARCH",
        triage_status="COMPLETE",
        evidence=[ev],
    )
    res = response_service(req)
    assert res.sources[0]["type"] == "USER_DOCUMENT"
    assert res.sources[0]["name"] == "Supplier_Guide.pdf"
    assert res.sources[0]["page"] == 4
    assert "Supplier_Guide.pdf — page 4" in res.answer


def test_off_only_citation():
    ev = EvidenceObject(
        evidence_id="off-99",
        name="Nutella",
        barcode="3017620422003",
        source_type="OPEN_FOOD_FACTS",
    )
    req = ResponseRequest(
        trace_id="t-4",
        query="Nutella barcode",
        intent="BARCODE_LOOKUP",
        triage_status="COMPLETE",
        evidence=[ev],
    )
    res = response_service(req)
    assert res.sources[0]["type"] == "OPEN_FOOD_FACTS"
    assert res.sources[0]["name"] == "Nutella"
    assert res.sources[0]["barcode"] == "3017620422003"


def test_source_conflict_handling():
    analysis = AnalysisResponse(
        trace_id="t-5",
        safety_status="INSUFFICIENT_EVIDENCE",
        conflicting_evidence=[
            {"evidence_id": "ev-1", "reason": "Sources conflict on milk declaration"}
        ],
    )
    req = ResponseRequest(
        trace_id="t-5",
        query="Check conflicting product",
        intent="ALLERGEN_CHECK",
        triage_status="COMPLETE",
        evidence=[],
        analysis=analysis,
    )
    res = response_service(req)
    assert res.status == "PARTIAL"
    assert "conflicting" in res.answer.lower() or "inconsistent" in res.answer.lower()


def test_missing_evidence_not_found():
    req = ResponseRequest(
        trace_id="t-6",
        query="unknown product query",
        intent="PRODUCT_SEARCH",
        triage_status="NOT_FOUND",
        evidence=[],
    )
    res = response_service(req)
    assert res.status == "NOT_FOUND"
    assert "couldn't find enough" in res.answer.lower() or "not find" in res.answer.lower()


def test_high_protein_ordering():
    ev_low = EvidenceObject(name="Low Protein Snack", nutrition={"protein_g_100g": 5.0})
    ev_high = EvidenceObject(name="High Protein Bar", nutrition={"protein_g_100g": 22.0})

    ranked = rank_candidates(
        evidence=[ev_low, ev_high],
        query="high protein bar",
        nutrients=["protein"],
    )
    assert ranked[0].name == "High Protein Bar"
    assert ranked[1].name == "Low Protein Snack"


def test_low_sugar_ordering():
    ev_high_sugar = EvidenceObject(name="Sweet Candy", nutrition={"sugars_g_100g": 45.0})
    ev_low_sugar = EvidenceObject(name="Diet Biscuit", nutrition={"sugars_g_100g": 3.0})

    ranked = rank_candidates(
        evidence=[ev_high_sugar, ev_low_sugar],
        query="low sugar biscuit",
        nutrients=["sugar"],
    )
    assert ranked[0].name == "Diet Biscuit"
    assert ranked[1].name == "Sweet Candy"


def test_numeric_filtering():
    c = NutrientConstraint(nutrient="sugar", operator="lt", value=10.0, unit="g")
    ev_pass = EvidenceObject(name="Sugar Free Bar", nutrition={"sugars_g_100g": 2.0})
    ev_fail = EvidenceObject(name="Sugary Bar", nutrition={"sugars_g_100g": 25.0})

    ranked = rank_candidates(
        evidence=[ev_fail, ev_pass],
        query="sugar under 10g",
        nutrients=["sugar"],
        nutrient_constraints=[c],
    )
    assert ranked[0].name == "Sugar Free Bar"
    assert ranked[1].name == "Sugary Bar"


def test_missing_nutrient_ordering():
    ev_valid = EvidenceObject(name="Valid Protein Bar", nutrition={"protein_g_100g": 12.0})
    ev_missing = EvidenceObject(name="Unknown Protein Bar", nutrition={})

    ranked = rank_candidates(
        evidence=[ev_missing, ev_valid],
        query="high protein bar",
        nutrients=["protein"],
    )
    assert ranked[0].name == "Valid Protein Bar"
    assert ranked[1].name == "Unknown Protein Bar"


def test_critical_hallucination_prevention():
    """CRITICAL HALLUCINATION TEST:
    Evidence contains ONLY: sugar=8g, protein=5g.
    Final response MUST NOT introduce: calories, fat, sodium, or ingredients.
    """
    ev = EvidenceObject(
        evidence_id="ev-strict-grounding",
        name="Minimal Test Item",
        ingredients_text=None,
        nutrition={
            "sugars_g_100g": 8.0,
            "protein_g_100g": 5.0,
        },
        source_type="USER_DOCUMENT",
        document_name="Minimal_Spec.txt",
        page_number=1,
    )

    req = ResponseRequest(
        trace_id="t-hallucination-check",
        query="Tell me about Minimal Test Item",
        intent="NUTRITION_QUERY",
        triage_status="COMPLETE",
        evidence=[ev],
    )

    res = response_service(req)
    answer_text = res.answer.lower()

    # Must contain present fields
    assert "sugar: 8.0" in answer_text or "sugar" in answer_text
    assert "protein: 5.0" in answer_text or "protein" in answer_text

    # MUST NOT introduce absent fields!
    assert "calories" not in answer_text
    assert "fat:" not in answer_text
    assert "sodium" not in answer_text
    assert "ingredients:" not in answer_text


def test_duplicate_findings_prevention():
    analysis = AnalysisResponse(
        trace_id="t-dup",
        safety_status="SUITABLE",
        findings=[
            "Product declares no allergens.",
            "Product declares no allergens.",  # Duplicate line
        ],
    )
    ev = EvidenceObject(name="Sample Item", nutrition={"sugars_g_100g": 2.0})

    req = ResponseRequest(
        trace_id="t-dup",
        query="Sample Item query",
        intent="PRODUCT_SEARCH",
        triage_status="COMPLETE",
        evidence=[ev],
        analysis=analysis,
    )
    res = response_service(req)
    count = res.answer.count("Product declares no allergens.")
    assert count == 1
