"""
Unit tests for dietary_rules.py -- vegan/vegetarian/gluten-free/dairy-free
suitability checks.
"""

from backend.app.agents.nutrition_allergen.dietary_rules import check_dietary_suitability


def test_nutella_is_unsuitable_for_vegan():
    evidence = {
        "ingredients_text": "Wheat flour, sugar, palm oil, cocoa powder, milk solids, soy lecithin.",
        "allergens": ["gluten", "milk", "soy"],
        "completeness": 0.90,
    }
    result = check_dietary_suitability(evidence, "vegan")
    assert result["verdict"] == "UNSUITABLE"
    assert "milk" in result["matched_terms"]


def test_unsupported_requirement_is_flagged():
    evidence = {
        "ingredients_text": "Flour, sugar, oil.",
        "allergens": [],
        "completeness": 0.8,
    }
    result = check_dietary_suitability(evidence, "keto")
    assert result["verdict"] == "UNSUPPORTED_REQUIREMENT"


def test_no_data_is_insufficient_evidence():
    evidence = {"ingredients_text": None, "allergens": [], "completeness": 0.1}
    result = check_dietary_suitability(evidence, "vegan")
    assert result["verdict"] == "INSUFFICIENT_EVIDENCE"


def test_no_disqualifying_ingredients_is_suitable():
    evidence = {
        "ingredients_text": "Rice, water, salt.",
        "allergens": [],
        "completene"
        "ss": 0.9,
    }
    result = check_dietary_suitability(evidence, "vegan")
    assert result["verdict"] == "SUITABLE"

    