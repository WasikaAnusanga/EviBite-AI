"""
Unit tests for nutrient_rules.py -- threshold checks, comparisons, and
the infer_comparator direction-detection fix.
"""

from backend.app.agents.nutrition_allergen.nutrient_rules import (
    check_nutrient_constraint,
    compare_products_by_nutrient,
    infer_comparator,
)


def test_low_sugar_meets_constraint():
    product = {"nutrition": {"sugars_g_100g": 3.2}}
    result = check_nutrient_constraint(product, "sugars", "low")
    assert result["status"] == "MEETS_CONSTRAINT"
    assert result["confidence"] == "high"


def test_high_sugar_does_not_meet_low_constraint():
    product = {"nutrition": {"sugars_g_100g": 38.5}}
    result = check_nutrient_constraint(product, "sugars", "low")
    assert result["status"] == "DOES_NOT_MEET"


def test_missing_nutrient_value_is_insufficient_evidence():
    product = {"nutrition": {}}
    result = check_nutrient_constraint(product, "sugars", "low")
    assert result["status"] == "INSUFFICIENT_EVIDENCE"


def test_unsupported_nutrient_is_flagged():
    product = {"nutrition": {"sugars_g_100g": 5.0}}
    result = check_nutrient_constraint(product, "vitamin_c", "low")
    assert result["status"] == "UNSUPPORTED_NUTRIENT"


def test_compare_products_picks_lower_value():
    cheerios = {"product_id": "a", "name": "Cheerios", "nutrition": {"sugars_g_100g": 9.3}}
    special_k = {"product_id": "b", "name": "Special K", "nutrition": {"sugars_g_100g": 14.0}}
    result = compare_products_by_nutrient([cheerios, special_k], "sugars", "lower")
    assert result["status"] == "COMPLETE"
    assert result["winner"] == "Cheerios"


def test_compare_products_with_missing_data_is_insufficient():
    cheerios = {"product_id": "a", "name": "Cheerios", "nutrition": {"sugars_g_100g": 9.3}}
    unknown = {"product_id": "b", "name": "Unknown Cereal", "nutrition": {}}
    result = compare_products_by_nutrient([cheerios, unknown], "sugars", "lower")
    assert result["status"] == "INSUFFICIENT_EVIDENCE"


def test_infer_comparator_detects_low_direction():
    assert infer_comparator("Which cereal has less sugar?", "sugar") == "low"


def test_infer_comparator_detects_high_direction():
    """Regression test for the nutrient-comparator bug fix."""
    assert infer_comparator("I want a cereal with more protein", "protein") == "high"


def test_infer_comparator_falls_back_to_default_with_no_direction_word():
    assert infer_comparator("How much sugar does Nutella have?", "sugar") == "low"
    