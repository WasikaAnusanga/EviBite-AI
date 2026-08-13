"""
Dietary suitability checking (vegan, vegetarian, gluten-free) for the
Nutrition & Allergen Analysis Agent.

Same evidence-based approach as allergen_rules.py: a verdict is only
UNSUITABLE when disqualifying ingredients are actually found. Absence of
those ingredients in available text yields SUITABLE, consistent with the
team's agreed approach -- but always with an honest confidence signal.
"""

from typing import Any

# Ingredient keywords that disqualify a product from each dietary category.
# Deliberately conservative (broad matching) since false negatives here
# (missing a disqualifying ingredient) are worse than false positives.
DISQUALIFYING_INGREDIENTS: dict[str, set[str]] = {
    "vegan": {
        "milk", "dairy", "whey", "casein", "lactose", "butter", "cream",
        "egg", "honey", "gelatin", "gelatine", "meat", "beef", "pork",
        "chicken", "fish", "anchovy", "shellfish", "lard", "collagen",
    },
    "vegetarian": {
        "meat", "beef", "pork", "chicken", "fish", "anchovy", "shellfish",
        "gelatin", "gelatine", "lard", "collagen",
    },
    "gluten-free": {"wheat", "gluten", "barley", "rye", "malt"},
    "dairy-free": {"milk", "dairy", "whey", "casein", "lactose", "butter", "cream"},
}


def check_dietary_suitability(evidence: dict[str, Any], requirement: str) -> dict[str, Any]:
    req = requirement.strip().lower()
    disqualifiers = DISQUALIFYING_INGREDIENTS.get(req)

    if disqualifiers is None:
        return {
            "verdict": "UNSUPPORTED_REQUIREMENT",
            "confidence": "low",
            "explanation": f"'{requirement}' is not a dietary requirement this agent currently tracks.",
        }

    ingredients_text = evidence.get("ingredients_text")
    declared_allergens = evidence.get("allergens", []) or []
    completeness = evidence.get("completeness", 0.0)

    has_ingredients_text = bool(ingredients_text and ingredients_text.strip())
    has_any_signal = has_ingredients_text or bool(declared_allergens)

    if not has_any_signal:
        return {
            "verdict": "INSUFFICIENT_EVIDENCE",
            "confidence": "low",
            "explanation": f"No ingredients or allergen data available to assess '{requirement}' suitability.",
        }

    # Check both ingredients text and declared allergens for disqualifiers
    found: list[str] = []
    haystack = " ".join(declared_allergens).lower()
    if has_ingredients_text:
        haystack += " " + ingredients_text.lower()

    for term in disqualifiers:
        if term in haystack:
            found.append(term)

    if found:
        return {
            "verdict": "UNSUITABLE",
            "confidence": "high",
            "matched_terms": found,
            "explanation": (
                f"Product contains ingredient(s) inconsistent with '{requirement}': "
                f"{', '.join(found)}."
            ),
        }

    confidence = "high" if completeness >= 0.75 else "medium" if completeness >= 0.4 else "low"
    return {
        "verdict": "SUITABLE",
        "confidence": confidence,
        "matched_terms": [],
        "explanation": (
            f"No ingredients inconsistent with '{requirement}' were found in available "
            f"product data, though data can be incomplete."
        ),
    }