"""Allergen conflict detection for the Nutrition & Allergen Analysis Agent.

Strict safety-critical deterministic Python evaluation.

Key rules:
- ABSENCE OF EVIDENCE IS NOT EVIDENCE OF ABSENCE.
- Strict canonical mapping (whey/casein -> milk, hazelnut/almond/cashew -> tree_nuts).
- Peanut != tree_nuts (Peanut and tree-nut allergies remain separate).
- Exact word-boundary regex matching to prevent false substring matches (e.g. nut in donut/peanut).
- Verdicts: SUITABLE, UNSUITABLE, INSUFFICIENT_EVIDENCE.
"""

import re
from typing import Any

ALLERGEN_SYNONYMS: dict[str, set[str]] = {
    "peanut": {"peanut", "peanuts", "groundnut", "groundnuts", "arachis"},
    "milk": {"milk", "dairy", "lactose", "whey", "casein", "butter", "milk powder", "cream", "cheese"},
    "egg": {"egg", "eggs", "albumen"},
    "soy": {"soy", "soya", "soybean", "soybeans"},
    "gluten": {"gluten", "wheat", "barley", "rye"},
    "tree_nuts": {
        "tree nut", "tree nuts", "tree_nut", "tree_nuts", "hazelnut", "hazelnuts",
        "almond", "almonds", "cashew", "cashews", "walnut", "walnuts",
        "pistachio", "pistachios", "pecan", "pecans", "macadamia",
    },
    "fish": {"fish"},
    "shellfish": {"shellfish", "crustacean", "crustaceans", "prawn", "shrimp", "crab", "lobster"},
    "sesame": {"sesame", "sesame seed", "sesame seeds"},
    "oats": {"oat", "oats"},
}


def normalize_allergen_term(term: str) -> str | None:
    """Map a raw allergen word/phrase to its canonical key, or None if unrecognized."""
    term_lower = term.strip().lower()

    if term_lower in ("tree nut", "tree nuts", "tree_nut", "tree_nuts", "hazelnut", "almond", "cashew"):
        return "tree_nuts"

    for canonical, synonyms in ALLERGEN_SYNONYMS.items():
        if term_lower == canonical or term_lower in synonyms:
            return canonical
    return None


def normalize_allergen_list(raw_allergens: list[str]) -> set[str]:
    """Normalize a list of raw allergen strings into a set of canonical keys."""
    normalized: set[str] = set()
    for raw in raw_allergens:
        canonical = normalize_allergen_term(raw)
        if canonical:
            normalized.add(canonical)
    return normalized


def allergen_in_text(ingredients_text: str, canonical_allergen: str) -> bool:
    """Check whether any synonym of the canonical allergen appears with word boundaries."""
    synonyms = ALLERGEN_SYNONYMS.get(canonical_allergen, {canonical_allergen})
    for synonym in synonyms:
        pattern = r"\b" + re.escape(synonym) + r"\b"
        if re.search(pattern, ingredients_text, re.IGNORECASE):
            return True
    return False


def check_allergen_conflict(evidence: dict[str, Any], allergen: str) -> dict[str, Any]:
    """Evaluate a single allergen against a single product's evidence."""
    canonical = normalize_allergen_term(allergen) or allergen.strip().lower()

    declared_raw = evidence.get("allergens", []) or []
    declared = normalize_allergen_list(declared_raw)
    ingredients_text = evidence.get("ingredients_text")
    completeness = evidence.get("completeness", 0.0)

    has_ingredients_text = bool(ingredients_text and ingredients_text.strip())
    has_declared = bool(declared)

    # 1. Explicit conflict via declared allergens field
    if canonical in declared:
        return {
            "verdict": "UNSUITABLE",
            "rule": "declared_allergen_match",
            "field": "allergens",
            "value": canonical,
            "confidence": "high",
            "explanation": f"Product declares '{canonical}' in its allergens field.",
        }

    # Check direct synonym match in raw declared allergens
    synonyms = ALLERGEN_SYNONYMS.get(canonical, {canonical})
    for raw_alg in declared_raw:
        if raw_alg.strip().lower() in synonyms:
            return {
                "verdict": "UNSUITABLE",
                "rule": "declared_allergen_synonym_match",
                "field": "allergens",
                "value": canonical,
                "confidence": "high",
                "explanation": f"Product declares '{raw_alg}' (synonym of {canonical}) in its allergens field.",
            }

    # 2. Check ingredients text with word boundary regex
    if has_ingredients_text and allergen_in_text(ingredients_text, canonical):
        return {
            "verdict": "UNSUITABLE",
            "rule": "ingredient_text_match",
            "field": "ingredients_text",
            "value": canonical,
            "confidence": "medium",
            "explanation": f"'{canonical}' (or derivative) appears in the ingredients text.",
        }

    # 3. ABSENCE OF EVIDENCE IS NOT EVIDENCE OF ABSENCE:
    if not has_ingredients_text and not has_declared:
        return {
            "verdict": "INSUFFICIENT_EVIDENCE",
            "rule": "no_allergen_data_available",
            "field": "allergens",
            "value": None,
            "confidence": "low",
            "explanation": f"No allergen declaration or ingredients text available to evaluate '{canonical}'.",
        }

    if not has_ingredients_text and completeness < 0.6:
        return {
            "verdict": "INSUFFICIENT_EVIDENCE",
            "rule": "incomplete_allergen_data",
            "field": "allergens",
            "value": None,
            "confidence": "low",
            "explanation": f"Incomplete ingredient data available to reliably verify absence of '{canonical}'.",
        }

    # 4. Ingredients text or declared allergens available, and canonical allergen was NOT found
    confidence = "high" if completeness >= 0.75 else "medium" if completeness >= 0.40 else "low"
    return {
        "verdict": "SUITABLE",
        "rule": "no_match_in_available_data",
        "field": None,
        "value": None,
        "confidence": confidence,
        "explanation": (
            f"'{canonical}' was not found in the declared allergens or ingredients text for this product. "
            f"Based on available product data, it appears suitable, though product data can be incomplete."
        ),
    }