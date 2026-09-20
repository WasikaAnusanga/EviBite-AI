"""Nutrient constraint checking for the Nutrition & Allergen Analysis Agent.

Deterministic numeric constraint checking.
Missing nutrient values must NOT become 0 -- missing value yields INSUFFICIENT_EVIDENCE.
"""

from typing import Any, Literal

Comparator = Literal["low", "high"]

NUTRIENT_FIELD_MAP: dict[str, str] = {
    "sugars": "sugars_g_100g",
    "sugar": "sugars_g_100g",
    "protein": "protein_g_100g",
    "fat": "fat_g_100g",
    "saturated_fat": "saturated_fat_g_100g",
    "saturated fat": "saturated_fat_g_100g",
    "sodium": "sodium_mg_100g",
    "salt": "salt_g_100g",
    "energy": "energy_kcal_100g",
    "calories": "energy_kcal_100g",
    "fiber": "fiber_g_100g",
    "fibre": "fiber_g_100g",
    "carbohydrates": "carbohydrates_g_100g",
    "carbs": "carbohydrates_g_100g",
}

DEFAULT_THRESHOLDS: dict[str, dict[Comparator, float]] = {
    "sugars_g_100g": {"low": 5.0, "high": 22.5},
    "fat_g_100g": {"low": 3.0, "high": 17.5},
    "saturated_fat_g_100g": {"low": 1.5, "high": 5.0},
    "sodium_mg_100g": {"low": 120.0, "high": 600.0},
    "salt_g_100g": {"low": 0.3, "high": 1.5},
    "protein_g_100g": {"low": 5.0, "high": 12.0},
    "fiber_g_100g": {"low": 3.0, "high": 6.0},
}


def check_nutrient_constraint(
    evidence: dict[str, Any],
    nutrient: str,
    comparator: Comparator = "low",
    constraint_obj: Any | None = None,
) -> dict[str, Any]:
    field = NUTRIENT_FIELD_MAP.get(nutrient.strip().lower())
    if field is None:
        return {
            "status": "UNSUPPORTED_NUTRIENT",
            "verdict": "INSUFFICIENT_EVIDENCE",
            "confidence": "low",
            "field": None,
            "value": None,
            "explanation": f"'{nutrient}' is not a nutrient this agent currently tracks.",
        }

    nutrition_data = evidence.get("nutrition") or {}
    value = nutrition_data.get(field)

    # Missing nutrient values must NOT become 0!
    if value is None:
        return {
            "status": "INSUFFICIENT_EVIDENCE",
            "verdict": "INSUFFICIENT_EVIDENCE",
            "confidence": "low",
            "field": field,
            "value": None,
            "explanation": f"No '{field}' value on record for this product.",
        }

    # Explicit numeric constraint (e.g., sugar < 10g or protein > 15g)
    if constraint_obj and getattr(constraint_obj, "value", None) is not None:
        target_val = constraint_obj.value
        op = getattr(constraint_obj, "operator", "lte") or "lte"
        if op == "lt":
            meets = value < target_val
        elif op == "lte":
            meets = value <= target_val
        elif op == "gt":
            meets = value > target_val
        elif op == "gte":
            meets = value >= target_val
        elif op == "eq":
            meets = value == target_val
        else:
            meets = value <= target_val

        verdict = "SUITABLE" if meets else "UNSUITABLE"
        return {
            "status": "MEETS_CONSTRAINT" if meets else "DOES_NOT_MEET",
            "verdict": verdict,
            "confidence": "high",
            "field": field,
            "value": value,
            "threshold": target_val,
            "explanation": (
                f"{field} is {value}, which "
                f"{'meets' if meets else 'does not meet'} the target constraint of {op} {target_val}."
            ),
        }

    threshold = DEFAULT_THRESHOLDS.get(field, {}).get(comparator)
    if threshold is None:
        return {
            "status": "UNSUPPORTED_NUTRIENT",
            "verdict": "INSUFFICIENT_EVIDENCE",
            "confidence": "low",
            "field": field,
            "value": value,
            "explanation": f"No threshold defined for '{comparator} {nutrient}'.",
        }

    meets = value <= threshold if comparator == "low" else value >= threshold
    verdict = "SUITABLE" if meets else "UNSUITABLE"

    return {
        "status": "MEETS_CONSTRAINT" if meets else "DOES_NOT_MEET",
        "verdict": verdict,
        "confidence": "high",
        "field": field,
        "value": value,
        "threshold": threshold,
        "explanation": (
            f"{field} is {value}, which "
            f"{'meets' if meets else 'does not meet'} the '{comparator}' "
            f"threshold of {threshold}."
        ),
    }


def compare_products_by_nutrient(
    products: list[dict[str, Any]], nutrient: str, goal: Literal["lower", "higher"]
) -> dict[str, Any]:
    """Compare a nutrient across multiple products (for COMPARISON intent)."""
    field = NUTRIENT_FIELD_MAP.get(nutrient.strip().lower())
    if field is None:
        return {"status": "UNSUPPORTED_NUTRIENT", "explanation": f"'{nutrient}' not tracked."}

    readings = []
    for p in products:
        value = p.get("nutrition", {}).get(field)
        readings.append({"product_id": p.get("product_id"), "name": p.get("name"), "value": value})

    missing = [r for r in readings if r["value"] is None]
    if missing:
        missing_names = ", ".join(r["name"] or "Unknown" for r in missing)
        return {
            "status": "INSUFFICIENT_EVIDENCE",
            "readings": readings,
            "explanation": f"Missing '{field}' data for: {missing_names}. Comparison cannot be completed reliably.",
        }

    best = min(readings, key=lambda r: r["value"]) if goal == "lower" else max(readings, key=lambda r: r["value"])
    return {
        "status": "COMPLETE",
        "readings": readings,
        "winner": best["name"],
        "explanation": f"'{best['name']}' has the {goal} {field} ({best['value']}) among compared products.",
    }


LOW_DIRECTION_WORDS = {"low", "less", "fewer", "lower", "reduce", "minimal", "little", "under", "below"}
HIGH_DIRECTION_WORDS = {"high", "more", "higher", "rich", "plenty", "lots", "above", "greater"}


def infer_comparator(query: str, nutrient: str, default: Literal["low", "high"] = "low") -> Literal["low", "high"]:
    """Look for direction words near the nutrient mention in the raw query."""
    text = query.lower()
    if any(word in text for word in HIGH_DIRECTION_WORDS):
        return "high"
    if any(word in text for word in LOW_DIRECTION_WORDS):
        return "low"
    return default