"""Dietary suitability checking (vegan, vegetarian, gluten-free, dairy-free) for the
Nutrition & Allergen Analysis Agent.

Strict safety-critical deterministic evaluation:
- Absence of known meat/dairy in incomplete data is NOT automatically confirmed vegan (returns INSUFFICIENT_EVIDENCE).
- Do not claim "certified" unless explicit certification labels are present in evidence.
"""

from typing import Any
import re

DISQUALIFYING_INGREDIENTS: dict[str, set[str]] = {
    "vegan": {
        "milk", "dairy", "whey", "casein", "lactose", "butter", "cream",
        "egg", "eggs", "honey", "gelatin", "gelatine", "meat", "beef", "pork",
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
    dietary_labels = evidence.get("dietary_labels", []) or []
    completeness = evidence.get("completeness", 0.0)

    has_ingredients_text = bool(ingredients_text and ingredients_text.strip())
    has_any_signal = has_ingredients_text or bool(declared_allergens)

    # 1. No ingredient/allergen signal -> INSUFFICIENT_EVIDENCE
    if not has_any_signal:
        return {
            "verdict": "INSUFFICIENT_EVIDENCE",
            "confidence": "low",
            "explanation": f"No ingredients or allergen data available to assess '{requirement}' suitability.",
        }

    # 2. Check for explicit disqualifying ingredients with word boundary matching
    haystack = " ".join(declared_allergens).lower()
    if has_ingredients_text:
        haystack += " " + ingredients_text.lower()

    found: list[str] = []
    for term in disqualifiers:
        pattern = r"\b" + re.escape(term) + r"\b"
        if re.search(pattern, haystack, re.IGNORECASE):
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

    # 3. Product lacking known disqualifying ingredients in incomplete data is NOT automatically confirmed vegan
    if not has_ingredients_text or completeness < 0.5:
        return {
            "verdict": "INSUFFICIENT_EVIDENCE",
            "confidence": "low",
            "matched_terms": [],
            "explanation": (
                f"Incomplete ingredient data available. Cannot confirm '{requirement}' suitability "
                f"without complete ingredient declaration."
            ),
        }

    # 4. Check explicit certification labels
    is_certified = any(req in label.lower() for label in dietary_labels)
    cert_text = f" (explicitly labeled {req})" if is_certified else " (uncertified based on ingredient inspection)"

    return {
        "verdict": "SUITABLE",
        "confidence": "high" if is_certified else "medium",
        "matched_terms": [],
        "explanation": (
            f"No ingredients inconsistent with '{requirement}' were found in available product data{cert_text}."
        ),
    }