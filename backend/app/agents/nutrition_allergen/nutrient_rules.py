"""
Nutrient constraint checking for the Nutrition & Allergen Analysis Agent.

Nutrient values are directly measured/reported numbers, not absence-based
inference -- so unlike allergens, a confident MEETS/DOES_NOT_MEET answer
is honest whenever the value is actually present.
"""

from typing import Any, Literal

Comparator = Literal["low", "high"]

NUTRIENT_FIELD_MAP: dict[str, str] = {
    "sugars": "sugars_g_100g",
    "sugar": "sugars_g_100g",
    "protein": "protein_g_100g",
    "fat": "fat_g_100g",
    "sodium": "sodium_mg_100g",
    "salt": "salt_g_100g",
    "energy": "energy_kcal_100g",
    "calories": "energy_kcal_100g",
    "fiber": "fiber_g_100g",
}

# UK FSA "traffic light" style bands, per 100g/100ml. Reasonable defaults,
# not medical/regulatory advice -- worth flagging as such in the report.
DEFAULT_THRESHOLDS: dict[str, dict[Comparator, float]] = {
    "sugars_g_100g": {"low": 5.0, "high": 22.5},
    "fat_g_100g": {"low": 3.0, "high": 17.5},
    "sodium_mg_100g": {"low": 120.0, "high": 600.0},
    "salt_g_100g": {"low": 0.3, "high": 1.5},
    "protein_g_100g": {"low": 5.0, "high": 12.0},
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
            "confidence": "low",
            "field": None,
            "value": None,
            "explanation": f"'{nutrient}' is not a nutrient this agent currently tracks.",
        }

    value = evidence.get("nutrition", {}).get(field)
    if value is None:
        return {
            "status": "INSUFFICIENT_EVIDENCE",
            "confidence": "low",
            "field": field,
            "value": None,
            "explanation": f"No '{field}' value on record for this product.",
        }

    # If explicit numeric constraint was passed (e.g. sugar < 10g or protein > 20g)
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

        return {
            "status": "MEETS_CONSTRAINT" if meets else "DOES_NOT_MEET",
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
            "confidence": "low",
            "field": field,
            "value": value,
            "explanation": f"No threshold defined for '{comparator} {nutrient}'.",
        }

    meets = value <= threshold if comparator == "low" else value >= threshold

    return {
        "status": "MEETS_CONSTRAINT" if meets else "DOES_NOT_MEET",
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
        missing_names = ", ".join(r["name"] for r in missing)
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

LOW_DIRECTION_WORDS = {"low", "less", "fewer", "lower", "reduce", "minimal", "little"}
HIGH_DIRECTION_WORDS = {"high", "more", "higher", "rich", "plenty", "lots"}


def infer_comparator(query: str, nutrient: str, default: Literal["low", "high"] = "low") -> Literal["low", "high"]:
    """
    Look for direction words near the nutrient mention in the raw query.
    Falls back to `default` if no direction word is found -- an honest
    fallback, not a silent guess, since the caller controls what default
    means and can log/flag when it's used.
    """
    text = query.lower()
    if any(word in text for word in HIGH_DIRECTION_WORDS):
        return "high"
    if any(word in text for word in LOW_DIRECTION_WORDS):
        return "low"
    return default