"""
Allergen conflict detection for the Nutrition & Allergen Analysis Agent.

Verdict logic (per team decision):
  - UNSUITABLE            : allergen found in declared allergens OR ingredients text
  - SUITABLE               : allergen not found in either signal, AND at least
                              ingredients_text was available to check
  - INSUFFICIENT_EVIDENCE  : neither declared allergens nor ingredients_text
                              exist -- there's nothing to reason over at all

SUITABLE here means "not found in available product data" -- not a certified
guarantee. The confidence field and explanation always make that distinction
clear to whoever consumes this (the Response Agent, and ultimately the user).
"""

from typing import Any


ALLERGEN_SYNONYMS: dict[str, set[str]] = {
    "peanut": {"peanut", "peanuts", "groundnut", "groundnuts", "arachis"},
    "milk": {"milk", "dairy", "lactose", "whey", "casein", "butter"},
    "egg": {"egg", "eggs"},
    "soy": {"soy", "soya", "soybean", "soybeans"},
    "gluten": {"gluten", "wheat", "barley", "rye"},
    "tree_nuts": {
        "tree nut", "tree nuts", "nuts", "hazelnut", "hazelnuts",
        "almond", "almonds", "cashew", "cashews", "walnut", "walnuts",
        "pistachio", "pistachios",
    },
    "fish": {"fish"},
    "shellfish": {"shellfish", "crustacean", "crustaceans", "prawn", "shrimp"},
    "sesame": {"sesame"},
    "oats": {"oat", "oats"},
}


def normalize_allergen_term(term: str) -> str | None:
    """Map a raw allergen word/phrase to its canonical key, or None if unrecognized."""
    term_lower = term.strip().lower()
    for canonical, synonyms in ALLERGEN_SYNONYMS.items():
        if term_lower in synonyms:
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


def allergen_in_text(ingredients_text: str, allergen: str) -> bool:
    """
    Check whether any synonym of the canonical allergen appears as a
    substring of the ingredients text. Simple but effective for this
    dataset's free-text ingredient lists.
    """
    text_lower = ingredients_text.lower()
    synonyms = ALLERGEN_SYNONYMS.get(allergen, {allergen})
    return any(synonym in text_lower for synonym in synonyms)


def check_allergen_conflict(evidence: dict[str, Any], allergen: str) -> dict[str, Any]:
    """
    Evaluate a single allergen against a single product's evidence.
    `evidence` matches EvidenceObject shape: allergens, ingredients_text, completeness.
    """
    canonical = normalize_allergen_term(allergen) or allergen.strip().lower()

    declared_raw = evidence.get("allergens", []) or []
    declared = normalize_allergen_list(declared_raw)
    ingredients_text = evidence.get("ingredients_text")
    completeness = evidence.get("completeness", 0.0)

    has_ingredients_text = bool(ingredients_text and ingredients_text.strip())

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

    # 2. No declared allergens AND no ingredients text -- nothing to check at all
    if not has_ingredients_text:
        return {
            "verdict": "INSUFFICIENT_EVIDENCE",
            "rule": "no_allergen_data_available",
            "field": "allergens",
            "value": None,
            "confidence": "low",
            "explanation": (
                f"No allergen declaration or ingredients text available "
                f"to evaluate '{canonical}'."
            ),
        }

    # 3. Ingredients text exists -- check it as a secondary signal
    if allergen_in_text(ingredients_text, canonical):
        return {
            "verdict": "UNSUITABLE",
            "rule": "ingredient_text_match",
            "field": "ingredients_text",
            "value": canonical,
            "confidence": "medium",
            "explanation": (
                f"'{canonical}' appears in the ingredients text, though it "
                f"was not listed in the declared allergens field."
            ),
        }

    # 4. Not found in either signal, and we DID have ingredients text to check
    confidence = "high" if completeness >= 0.75 else "medium" if completeness >= 0.4 else "low"
    return {
        "verdict": "SUITABLE",
        "rule": "no_match_in_available_data",
        "field": None,
        "value": None,
        "confidence": confidence,
        "explanation": (
            f"'{canonical}' was not found in the declared allergens or the "
            f"ingredients text for this product. Based on available data, "
            f"this appears suitable, though product data can be incomplete."
        ),
    }