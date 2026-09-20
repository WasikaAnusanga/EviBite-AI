"""Nutrition & Allergen Analysis Agent -- main service entry point.

Safety-critical deterministic analysis across Open Food Facts and User Documents.
Verdict Priority: UNSUITABLE > INSUFFICIENT_EVIDENCE > SUITABLE.
Gemini / LLMs NEVER decide allergen safety.
"""

import logging
from typing import Any

from backend.app.agents.agent_stubs import AnalysisRequest, AnalysisResponse, EvidenceObject
from backend.app.agents.nutrition_allergen.allergen_rules import check_allergen_conflict
from backend.app.agents.nutrition_allergen.nutrient_rules import check_nutrient_constraint, infer_comparator
from backend.app.agents.nutrition_allergen.dietary_rules import check_dietary_suitability

logger = logging.getLogger(__name__)

VERDICT_PRIORITY = {
    "UNSUITABLE": 3,
    "INSUFFICIENT_EVIDENCE": 1,
    "SUITABLE": 0,
}

VERDICT_TO_RISK = {
    "UNSUITABLE": "HIGH",
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
    conflicting_evidence_list: list[dict[str, Any]] = []

    worst_verdict = "SUITABLE"
    all_constraints = request.nutrient_constraints or request.constraints

    has_source_conflict = False

    # 1. Inspect retrieved evidence for pre-flagged conflicts across sources
    for ev in request.evidence:
        ev_id = (
            getattr(ev, "evidence_id", None)
            or getattr(ev, "chunk_id", None)
            or getattr(ev, "product_id", None)
            or getattr(ev, "document_id", None)
            or ev.name
            or "unknown"
        )
        if str(ev_id) not in evidence_ids:
            evidence_ids.append(str(ev_id))

        if getattr(ev, "conflicting_evidence", False):
            has_source_conflict = True
            conflicting_evidence_list.append(
                {
                    "evidence_id": str(ev_id),
                    "source_type": getattr(ev, "source_type", "UNKNOWN"),
                    "name": ev.name,
                    "reason": "Retrieved sources contain conflicting ingredient or nutrition data for this product.",
                }
            )

    # 2. Evaluate rules across evidence objects
    for ev in request.evidence:
        ev_dict = ev.model_dump()

        # Allergen Rule Check
        for allergen in request.allergens:
            result = check_allergen_conflict(ev_dict, allergen)
            msg = f"[{ev.name or 'Product'}] {result['explanation']}"
            findings.append(msg)
            allergen_findings.append(msg)
            worst_verdict = _update_worst(worst_verdict, result["verdict"])
            if result["verdict"] == "INSUFFICIENT_EVIDENCE":
                uncertainty_reasons.append(msg)

        # Nutrient Constraints Check
        checked_nutrients = set()
        if all_constraints:
            for c in all_constraints:
                nut = getattr(c, "nutrient", None)
                if nut:
                    comp = "high" if getattr(c, "preference", None) == "maximize" else "low"
                    result = check_nutrient_constraint(ev_dict, nut, comp, constraint_obj=c)
                    msg = f"[{ev.name or 'Product'}] {result['explanation']}"
                    findings.append(msg)
                    nutrient_findings.append(msg)
                    checked_nutrients.add(nut)
                    worst_verdict = _update_worst(worst_verdict, result["verdict"])
                    if result["verdict"] == "INSUFFICIENT_EVIDENCE":
                        uncertainty_reasons.append(msg)

        for nutrient in request.nutrients:
            if nutrient in checked_nutrients:
                continue
            comparator = infer_comparator(request.original_query, nutrient)
            result = check_nutrient_constraint(ev_dict, nutrient, comparator)
            msg = f"[{ev.name or 'Product'}] {result['explanation']}"
            findings.append(msg)
            nutrient_findings.append(msg)
            worst_verdict = _update_worst(worst_verdict, result["verdict"])
            if result["verdict"] == "INSUFFICIENT_EVIDENCE":
                uncertainty_reasons.append(msg)

        # Dietary Requirements Check
        for requirement in request.dietary_requirements:
            result = check_dietary_suitability(ev_dict, requirement)
            msg = f"[{ev.name or 'Product'}] {result['explanation']}"
            findings.append(msg)
            dietary_findings.append(msg)
            worst_verdict = _update_worst(worst_verdict, result["verdict"])
            if result["verdict"] == "INSUFFICIENT_EVIDENCE":
                uncertainty_reasons.append(msg)

    # 3. Handle Conflicting Evidence across sources
    if has_source_conflict:
        worst_verdict = "INSUFFICIENT_EVIDENCE"
        conflict_msg = (
            "Retrieved evidence from Open Food Facts and User Documents contains conflicting information for this product. "
            "For safety-critical decisions (such as allergen safety), please verify directly against the physical product packaging or retailer."
        )
        uncertainty_reasons.append(conflict_msg)
        findings.append(conflict_msg)

    # Handle empty evidence scenario
    if not request.evidence:
        worst_verdict = "INSUFFICIENT_EVIDENCE"
        uncertainty_reasons.append("No evidence objects were provided for analysis.")

    if not findings:
        findings.append("No allergen, nutrient, or dietary constraints were specified for this query.")

    confidence = "high" if worst_verdict in ("SUITABLE", "UNSUITABLE") and not has_source_conflict else "medium"

    return AnalysisResponse(
        trace_id=request.trace_id,
        safety_status=worst_verdict,
        risk_level=VERDICT_TO_RISK.get(worst_verdict, "MEDIUM"),
        confidence=confidence,
        allergen_findings=allergen_findings,
        dietary_findings=dietary_findings,
        nutrient_findings=nutrient_findings,
        findings=findings,
        reasons=uncertainty_reasons,
        uncertainty_reasons=uncertainty_reasons,
        evidence_ids=evidence_ids,
        conflicting_evidence=conflicting_evidence_list,
    )


def _update_worst(current_worst: str, new_verdict: str) -> str:
    # Map legacy "UNCERTAIN" to "INSUFFICIENT_EVIDENCE"
    if new_verdict == "UNCERTAIN":
        new_verdict = "INSUFFICIENT_EVIDENCE"

    if new_verdict not in VERDICT_PRIORITY:
        return current_worst

    if VERDICT_PRIORITY[new_verdict] > VERDICT_PRIORITY[current_worst]:
        return new_verdict
    return current_worst