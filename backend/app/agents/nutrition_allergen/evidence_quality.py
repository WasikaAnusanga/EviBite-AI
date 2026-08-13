"""
Evidence quality summarization -- independent of any specific allergen/
nutrient/dietary check, this describes how much we actually know about a
product record.
"""

from typing import Any

KEY_FIELDS = ["ingredients_text", "allergens", "nutrition"]


def summarize_evidence_quality(evidence: dict[str, Any]) -> dict[str, Any]:
    missing_fields = []

    if not evidence.get("ingredients_text"):
        missing_fields.append("ingredients_text")
    if not evidence.get("allergens"):
        missing_fields.append("allergens")
    if not evidence.get("nutrition"):
        missing_fields.append("nutrition")

    return {
        "completeness": evidence.get("completeness", 0.0),
        "fields_missing": missing_fields,
    }