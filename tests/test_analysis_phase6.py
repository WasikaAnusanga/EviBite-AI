import pytest

from backend.app.agents.agent_stubs import AnalysisRequest, EvidenceObject
from backend.app.agents.nutrition_allergen.service import analysis_service
from backend.app.agents.nutrition_allergen.allergen_rules import (
    check_allergen_conflict,
    normalize_allergen_term,
)
from backend.app.agents.nutrition_allergen.dietary_rules import check_dietary_suitability
from backend.app.agents.nutrition_allergen.nutrient_rules import check_nutrient_constraint
from backend.app.models.triage import NutrientConstraint


def test_milk_declaration():
    ev = EvidenceObject(
        evidence_id="ev-1",
        name="Milk Chocolate",
        allergens=["milk"],
        ingredients_text="Sugar, cocoa butter, milk powder, soy lecithin.",
        source_type="OPEN_FOOD_FACTS",
    )
    req = AnalysisRequest(
        trace_id="t-1",
        primary_intent="ALLERGEN_CHECK",
        allergens=["milk"],
        evidence=[ev],
    )
    res = analysis_service(req)
    assert res.safety_status == "UNSUITABLE"
    assert res.risk_level == "HIGH"


def test_whey_to_milk():
    ev = EvidenceObject(
        evidence_id="ev-2",
        name="Protein Powder",
        allergens=[],
        ingredients_text="Whey protein isolate, natural flavor, stevia.",
        source_type="OPEN_FOOD_FACTS",
    )
    res = check_allergen_conflict(ev.model_dump(), "milk")
    assert res["verdict"] == "UNSUITABLE"

    req = AnalysisRequest(
        trace_id="t-2",
        primary_intent="ALLERGEN_CHECK",
        allergens=["milk"],
        evidence=[ev],
    )
    ans = analysis_service(req)
    assert ans.safety_status == "UNSUITABLE"


def test_casein_to_milk():
    ev = EvidenceObject(
        evidence_id="ev-3",
        name="Cheese Snack",
        allergens=[],
        ingredients_text="Micellar casein, sunflower oil, salt.",
        source_type="USER_DOCUMENT",
    )
    res = check_allergen_conflict(ev.model_dump(), "milk")
    assert res["verdict"] == "UNSUITABLE"


def test_hazelnut_to_tree_nut():
    ev = EvidenceObject(
        evidence_id="ev-4",
        name="Hazelnut Spread",
        allergens=[],
        ingredients_text="Sugar, palm oil, hazelnuts, cocoa.",
        source_type="USER_DOCUMENT",
    )
    res = check_allergen_conflict(ev.model_dump(), "tree_nut")
    assert res["verdict"] == "UNSUITABLE"


def test_peanut_not_tree_nut():
    # Product with hazelnut (tree nut) should NOT trigger peanut conflict
    ev_hazelnut = EvidenceObject(
        evidence_id="ev-5",
        name="Hazelnut Bar",
        allergens=["hazelnut"],
        ingredients_text="Hazelnuts, cocoa, sugar.",
        source_type="OPEN_FOOD_FACTS",
    )
    res_peanut = check_allergen_conflict(ev_hazelnut.model_dump(), "peanut")
    assert res_peanut["verdict"] == "SUITABLE"

    # Product with peanut should NOT trigger tree_nut conflict if no tree nuts present
    ev_peanut = EvidenceObject(
        evidence_id="ev-6",
        name="Peanut Butter",
        allergens=["peanut"],
        ingredients_text="Peanuts, salt.",
        source_type="OPEN_FOOD_FACTS",
    )
    res_treenut = check_allergen_conflict(ev_peanut.model_dump(), "tree_nut")
    assert res_treenut["verdict"] == "SUITABLE"


def test_missing_allergen_data():
    ev = EvidenceObject(
        evidence_id="ev-7",
        name="Unknown Food Item",
        allergens=[],
        ingredients_text=None,
        completeness=0.1,
        source_type="OPEN_FOOD_FACTS",
    )
    req = AnalysisRequest(
        trace_id="t-3",
        primary_intent="ALLERGEN_CHECK",
        allergens=["milk"],
        evidence=[ev],
    )
    res = analysis_service(req)
    assert res.safety_status == "INSUFFICIENT_EVIDENCE"


def test_conflicting_sources():
    ev1 = EvidenceObject(
        evidence_id="ev-8a",
        name="Test Choco Bar",
        allergens=["milk"],
        source_type="OPEN_FOOD_FACTS",
        conflicting_evidence=True,
    )
    ev2 = EvidenceObject(
        evidence_id="ev-8b",
        name="Test Choco Bar",
        allergens=["soy"],
        source_type="USER_DOCUMENT",
        conflicting_evidence=True,
    )

    req = AnalysisRequest(
        trace_id="t-4",
        primary_intent="ALLERGEN_CHECK",
        allergens=["milk"],
        evidence=[ev1, ev2],
    )
    res = analysis_service(req)
    assert res.safety_status == "INSUFFICIENT_EVIDENCE"
    assert len(res.conflicting_evidence) >= 1


def test_document_only_allergen_evidence():
    ev_doc = EvidenceObject(
        evidence_id="doc-chunk-99",
        name="Supplier Allergen Guide",
        allergens=["gluten"],
        ingredients_text="Wheat flour, water, yeast.",
        source_type="USER_DOCUMENT",
    )
    req = AnalysisRequest(
        trace_id="t-5",
        primary_intent="ALLERGEN_CHECK",
        allergens=["gluten"],
        evidence=[ev_doc],
    )
    res = analysis_service(req)
    assert res.safety_status == "UNSUITABLE"
    assert "doc-chunk-99" in res.evidence_ids


def test_off_only_allergen_evidence():
    ev_off = EvidenceObject(
        evidence_id="off-12345",
        name="OFF Cereal",
        allergens=["oats"],
        ingredients_text="Whole grain oats, sugar.",
        source_type="OPEN_FOOD_FACTS",
    )
    req = AnalysisRequest(
        trace_id="t-6",
        primary_intent="ALLERGEN_CHECK",
        allergens=["oats"],
        evidence=[ev_off],
    )
    res = analysis_service(req)
    assert res.safety_status == "UNSUITABLE"
    assert "off-12345" in res.evidence_ids


def test_vegan_positive():
    ev = EvidenceObject(
        evidence_id="ev-vegan-1",
        name="Organic Tofu",
        ingredients_text="Soybeans, water, calcium sulfate.",
        dietary_labels=["en:vegan"],
        completeness=0.9,
    )
    res = check_dietary_suitability(ev.model_dump(), "vegan")
    assert res["verdict"] == "SUITABLE"


def test_vegan_incomplete():
    ev = EvidenceObject(
        evidence_id="ev-vegan-2",
        name="Mystery Snack",
        ingredients_text=None,
        completeness=0.2,
    )
    res = check_dietary_suitability(ev.model_dump(), "vegan")
    assert res["verdict"] == "INSUFFICIENT_EVIDENCE"


def test_sugar_under_10g():
    c = NutrientConstraint(nutrient="sugar", operator="lt", value=10.0, unit="g")

    ev_pass = EvidenceObject(name="Low Sugar Snack", nutrition={"sugars_g_100g": 4.5})
    res_pass = check_nutrient_constraint(ev_pass.model_dump(), "sugar", constraint_obj=c)
    assert res_pass["verdict"] == "SUITABLE"

    ev_fail = EvidenceObject(name="High Sugar Snack", nutrition={"sugars_g_100g": 14.0})
    res_fail = check_nutrient_constraint(ev_fail.model_dump(), "sugar", constraint_obj=c)
    assert res_fail["verdict"] == "UNSUITABLE"


def test_protein_above_15g():
    c = NutrientConstraint(nutrient="protein", operator="gt", value=15.0, unit="g")

    ev_pass = EvidenceObject(name="High Protein Bar", nutrition={"protein_g_100g": 20.0})
    res_pass = check_nutrient_constraint(ev_pass.model_dump(), "protein", constraint_obj=c)
    assert res_pass["verdict"] == "SUITABLE"

    ev_fail = EvidenceObject(name="Low Protein Bar", nutrition={"protein_g_100g": 5.0})
    res_fail = check_nutrient_constraint(ev_fail.model_dump(), "protein", constraint_obj=c)
    assert res_fail["verdict"] == "UNSUITABLE"


def test_high_protein_comparator():
    c = NutrientConstraint(nutrient="protein", preference="maximize")
    ev = EvidenceObject(name="Protein Powder", nutrition={"protein_g_100g": 25.0})
    res = check_nutrient_constraint(ev.model_dump(), "protein", comparator="high", constraint_obj=c)
    assert res["verdict"] == "SUITABLE"


def test_low_sugar_comparator():
    c = NutrientConstraint(nutrient="sugar", preference="minimize")
    ev = EvidenceObject(name="Diet Soda", nutrition={"sugars_g_100g": 0.5})
    res = check_nutrient_constraint(ev.model_dump(), "sugar", comparator="low", constraint_obj=c)
    assert res["verdict"] == "SUITABLE"


def test_missing_nutrient():
    ev = EvidenceObject(name="Unmeasured Snack", nutrition={})
    res = check_nutrient_constraint(ev.model_dump(), "sugar", comparator="low")
    assert res["verdict"] == "INSUFFICIENT_EVIDENCE"
    assert res["value"] is None  # Missing nutrient value MUST NOT become 0!


def test_multi_source_nutrition_conflict():
    ev_off = EvidenceObject(
        evidence_id="off-sugar-bar",
        name="Choco Bar",
        nutrition={"sugars_g_100g": 35.0},
        conflicting_evidence=True,
    )
    ev_doc = EvidenceObject(
        evidence_id="doc-sugar-bar",
        name="Choco Bar",
        nutrition={"sugars_g_100g": 10.0},
        conflicting_evidence=True,
    )

    req = AnalysisRequest(
        trace_id="t-multi-conflict",
        primary_intent="NUTRITION_QUERY",
        nutrients=["sugar"],
        evidence=[ev_off, ev_doc],
    )
    res = analysis_service(req)
    assert res.safety_status == "INSUFFICIENT_EVIDENCE"
    assert len(res.conflicting_evidence) >= 2
