"""
Unit tests for allergen_rules.py -- the four-way verdict logic.

Each test follows Arrange-Act-Assert: set up the input evidence (Arrange),
call the function under test (Act), then check the result (Assert).
"""

from backend.app.agents.nutrition_allergen.allergen_rules import (
    check_allergen_conflict,
    normalize_allergen_term,
    normalize_allergen_list,
)


def test_normalize_allergen_term_recognizes_synonym():
    assert normalize_allergen_term("Dairy") == "milk"


def test_normalize_allergen_term_returns_none_for_unknown():
    assert normalize_allergen_term("MSG") is None


def test_normalize_allergen_list_deduplicates_and_normalizes():
    result = normalize_allergen_list(["Dairy", "Hazelnut", "MSG"])
    assert result == {"milk", "tree_nuts"}


def test_declared_allergen_match_is_unsuitable():
    evidence = {
        "name": "Nutella",
        "ingredients_text": "Wheat flour, sugar, palm oil, cocoa powder, milk solids, soy lecithin.",
        "allergens": ["gluten", "milk", "soy"],
        "completeness": 0.90,
    }
    result = check_allergen_conflict(evidence, "milk")
    assert result["verdict"] == "UNSUITABLE"
    assert result["rule"] == "declared_allergen_match"
    assert result["confidence"] == "high"


def test_peanut_and_tree_nuts_are_not_conflated():
    """Regression test for the original stub bug: peanut != tree nuts."""
    evidence = {
        "name": "Nutella",
        "ingredients_text": "Wheat flour, sugar, palm oil, cocoa powder, milk solids, soy lecithin.",
        "allergens": ["gluten", "milk", "soy"],
        "completeness": 0.90,
    }
    result = check_allergen_conflict(evidence, "peanut")
    assert result["verdict"] == "SUITABLE"
    assert result["rule"] == "no_match_in_available_data"


def test_no_data_at_all_is_insufficient_evidence():
    evidence = {
        "name": "Mystery Snack",
        "ingredients_text": None,
        "allergens": [],
        "completeness": 0.15,
    }
    result = check_allergen_conflict(evidence, "peanut")
    assert result["verdict"] == "INSUFFICIENT_EVIDENCE"
    assert result["confidence"] == "low"


def test_ingredient_text_match_is_unsuitable_even_if_not_declared():
    evidence = {
        "name": "Imported Snack",
        "ingredients_text": "Contains milk powder and cocoa.",
        "allergens": [],
        "completeness": 0.6,
    }
    result = check_allergen_conflict(evidence, "milk")
    assert result["verdict"] == "UNSUITABLE"
    assert result["rule"] == "ingredient_text_match"
    assert result["confidence"] == "medium"


def test_suitable_confidence_scales_with_completeness():
    """SUITABLE with strong evidence should be more confident than SUITABLE
    with weak evidence -- same verdict, different confidence."""
    strong_evidence = {
        "name": "Nutella",
        "ingredients_text": "Wheat flour, sugar, palm oil, cocoa powder, milk solids, soy lecithin.",
        "allergens": ["gluten", "milk", "soy"],
        "completeness": 0.90,
    }
    weak_evidence = {
        "name": "Imported Biscuit",
        "ingredients_text": "Flour, sugar, vegetable oil",
        "allergens": [],
        "completeness": 0.35,
    }
    strong_result = check_allergen_conflict(strong_evidence, "peanut")
    weak_result = check_allergen_conflict(weak_evidence, "milk")

    assert strong_result["verdict"] == "SUITABLE"
    assert weak_result["verdict"] == "SUITABLE"
    assert strong_result["confidence"] == "high"
    assert weak_result["confidence"] == "low"