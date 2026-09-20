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
    allergen_findings: list[str] = []
    dietary_findings: list[str] = []
    nutrient_findings: list[str] = []
    uncertainty_reasons: list[str] = []
    evidence_ids: list[str] = []
    worst_verdict = "SUITABLE"

    all_constraints = request.nutrient_constraints or request.constraints

    for ev in request.evidence:
        ev_dict = ev.model_dump()
        ev_id = getattr(ev, "evidence_id", None) or getattr(ev, "product_id", None) or ev.name or "unknown"
        if ev_id not in evidence_ids:
            evidence_ids.append(str(ev_id))

        for allergen in request.allergens:
            result = check_allergen_conflict(ev_dict, allergen)
            msg = f"[{ev.name}] {result['explanation']}"
            findings.append(msg)
            allergen_findings.append(msg)
            worst_verdict = _update_worst(worst_verdict, result["verdict"])
            if result["verdict"] in ("UNCERTAIN", "INSUFFICIENT_EVIDENCE"):
                uncertainty_reasons.append(msg)

        # Check explicit nutrient constraints first
        checked_nutrients = set()
        if all_constraints:
            for c in all_constraints:
                nut = getattr(c, "nutrient", None)
                if nut:
                    comp = "high" if getattr(c, "preference", None) == "maximize" else "low"
                    result = check_nutrient_constraint(ev_dict, nut, comp, constraint_obj=c)
                    msg = f"[{ev.name}] {result['explanation']}"
                    findings.append(msg)
                    nutrient_findings.append(msg)
                    checked_nutrients.add(nut)
                    if result["status"] == "DOES_NOT_MEET":
                        worst_verdict = _update_worst(worst_verdict, "UNSUITABLE")
                    elif result["status"] == "INSUFFICIENT_EVIDENCE":
                        uncertainty_reasons.append(msg)
                        worst_verdict = _update_worst(worst_verdict, "INSUFFICIENT_EVIDENCE")

        for nutrient in request.nutrients:
            if nutrient in checked_nutrients:
                continue
            comparator = infer_comparator(request.original_query, nutrient)
            result = check_nutrient_constraint(ev_dict, nutrient, comparator)
            msg = f"[{ev.name}] {result['explanation']}"
            findings.append(msg)
            nutrient_findings.append(msg)
            if result["status"] == "DOES_NOT_MEET":
                worst_verdict = _update_worst(worst_verdict, "UNSUITABLE")
            elif result["status"] == "INSUFFICIENT_EVIDENCE":
                uncertainty_reasons.append(msg)
                worst_verdict = _update_worst(worst_verdict, "INSUFFICIENT_EVIDENCE")

        for requirement in request.dietary_requirements:
            result = check_dietary_suitability(ev_dict, requirement)
            msg = f"[{ev.name}] {result['explanation']}"
            findings.append(msg)
            dietary_findings.append(msg)
            worst_verdict = _update_worst(worst_verdict, result["verdict"])
            if result["verdict"] in ("UNCERTAIN", "INSUFFICIENT_EVIDENCE"):
                uncertainty_reasons.append(msg)

    if not findings:
        findings.append("No allergen, nutrient, or dietary constraints were specified for this query.")

    return AnalysisResponse(
        trace_id=request.trace_id,
        safety_status=worst_verdict,
        risk_level=VERDICT_TO_RISK.get(worst_verdict, "LOW"),
        confidence="high" if worst_verdict in ("SUITABLE", "UNSUITABLE") else "medium",
        allergen_findings=allergen_findings,
        dietary_findings=dietary_findings,
        nutrient_findings=nutrient_findings,
        findings=findings,
        reasons=uncertainty_reasons,
        uncertainty_reasons=uncertainty_reasons,
        evidence_ids=evidence_ids,
        conflicting_evidence=[],
    )


def _update_worst(current_worst: str, new_verdict: str) -> str:
    if new_verdict not in VERDICT_PRIORITY:
        return current_worst
    if VERDICT_PRIORITY[new_verdict] > VERDICT_PRIORITY[current_worst]:
        return new_verdict
    return current_worst