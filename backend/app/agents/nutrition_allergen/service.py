"""
Nutrition & Allergen Analysis Agent -- main service entry point.
"""

from typing import Any

from backend.app.agents.agent_stubs import AnalysisRequest, AnalysisResponse, EvidenceObject
from backend.app.agents.nutrition_allergen.allergen_rules import check_allergen_conflict
from backend.app.agents.nutrition_allergen.nutrient_rules import check_nutrient_constraint, infer_comparator
from backend.app.agents.nutrition_allergen.dietary_rules import check_dietary_suitability

VERDICT_PRIORITY = {
    "UNSUITABLE": 3,
    "UNCERTAIN": 2,
    "INSUFFICIENT_EVIDENCE": 1,
    "SUITABLE": 0,
}

VERDICT_TO_RISK = {
    "UNSUITABLE": "HIGH",
    "UNCERTAIN": "MEDIUM",
    "INSUFFICIENT_EVIDENCE": "MEDIUM",
    "SUITABLE": "LOW",
}


def analysis_service(request: AnalysisRequest) -> AnalysisResponse:
    findings: list[str] = []
    uncertainty_reasons: list[str] = []
    worst_verdict = "SUITABLE"

    for ev in request.evidence:
        ev_dict = ev.model_dump()

        for allergen in request.allergens:
            result = check_allergen_conflict(ev_dict, allergen)
            findings.append(f"[{ev.name}] {result['explanation']}")
            worst_verdict = _update_worst(worst_verdict, result["verdict"])
            if result["verdict"] in ("UNCERTAIN", "INSUFFICIENT_EVIDENCE"):
                uncertainty_reasons.append(f"[{ev.name}] {result['explanation']}")

        for nutrient in request.nutrients:
            comparator = infer_comparator(request.original_query, nutrient)
            result = check_nutrient_constraint(ev_dict, nutrient, comparator)
            findings.append(f"[{ev.name}] {result['explanation']}")
            if result["status"] == "INSUFFICIENT_EVIDENCE":
                uncertainty_reasons.append(f"[{ev.name}] {result['explanation']}")

        for requirement in request.dietary_requirements:
            result = check_dietary_suitability(ev_dict, requirement)
            findings.append(f"[{ev.name}] {result['explanation']}")
            worst_verdict = _update_worst(worst_verdict, result["verdict"])
            if result["verdict"] in ("UNCERTAIN", "INSUFFICIENT_EVIDENCE"):
                uncertainty_reasons.append(f"[{ev.name}] {result['explanation']}")

    if not findings:
        findings.append("No allergen, nutrient, or dietary constraints were specified for this query.")

    return AnalysisResponse(
        trace_id=request.trace_id,
        safety_status=worst_verdict,
        risk_level=VERDICT_TO_RISK[worst_verdict],
        findings=findings,
        uncertainty_reasons=uncertainty_reasons,
    )


def _update_worst(current_worst: str, new_verdict: str) -> str:
    if new_verdict not in VERDICT_PRIORITY:
        return current_worst
    if VERDICT_PRIORITY[new_verdict] > VERDICT_PRIORITY[current_worst]:
        return new_verdict
    return current_worst