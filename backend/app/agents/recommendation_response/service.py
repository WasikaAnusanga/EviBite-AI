"""Recommendation & Response Agent service (Member 4).

Turns retrieved evidence + analysis into a grounded, user-facing answer.
Strict Grounding:
- Never invents unverified fields (ingredients, allergens, nutrition, certifications).
- Formats structured citations for User Documents (filename, page) and Open Food Facts.
- Avoids absolute medical claims ("unsafe to eat").
- Ranks products respecting numeric constraints and nutrient direction preferences.
- Provides a robust deterministic template fallback when LLM is unavailable.
"""

import logging
from typing import Any

from backend.app.agents.agent_stubs import ResponseRequest, ResponseResponse

logger = logging.getLogger(__name__)


def _nutrient_field_name(nutrient: str) -> str | None:
    """Map a short nutrient word to the real EvidenceObject nutrition dictionary key."""
    mapping = {
        "sugars": "sugars_g_100g",
        "sugar": "sugars_g_100g",
        "protein": "protein_g_100g",
        "fat": "fat_g_100g",
        "saturated_fat": "saturated_fat_g_100g",
        "saturated fat": "saturated_fat_g_100g",
        "calories": "energy_kcal_100g",
        "energy": "energy_kcal_100g",
        "sodium": "sodium_mg_100g",
        "salt": "salt_g_100g",
    }
    return mapping.get(nutrient.lower().strip())


def _parse_direction(query: str, nutrient: str) -> str | None:
    """Look for 'less/low' or 'more/high' near a nutrient word in the query."""
    query_lower = query.lower()
    less_words = ["less", "low", "lower", "fewer", "reduced", "under", "below", "minimize"]
    more_words = ["more", "high", "higher", "increased", "above", "greater", "maximize"]

    nutrient_lower = nutrient.lower()
    nutrient_singular = nutrient_lower.rstrip("s")
    nutrient_present = nutrient_lower in query_lower or nutrient_singular in query_lower

    if any(word in query_lower for word in less_words) and nutrient_present:
        return "minimize"
    if any(word in query_lower for word in more_words) and nutrient_present:
        return "maximize"
    return None


def rank_candidates(
    evidence: list[Any],
    query: str,
    nutrients: list[str],
    nutrient_constraints: list[Any] | None = None,
) -> list[Any]:
    """Rank evidence candidates respecting numeric constraints and direction preferences."""
    if not evidence:
        return []

    constraints = nutrient_constraints or []

    # Separate candidates by numeric constraint satisfaction first
    valid_candidates = []
    failing_candidates = []

    for ev in evidence:
        nutrition = getattr(ev, "nutrition", {}) or {}
        fails_constraint = False
        for c in constraints:
            nut = getattr(c, "nutrient", None)
            val = getattr(c, "value", None)
            op = getattr(c, "operator", "lte") or "lte"
            if nut and val is not None:
                field = _nutrient_field_name(nut)
                if field and field in nutrition:
                    ev_val = nutrition[field]
                    if isinstance(ev_val, (int, float)):
                        if (op in ("lt", "lte") and ev_val > val) or (op in ("gt", "gte") and ev_val < val):
                            fails_constraint = True
                            break
        if fails_constraint:
            failing_candidates.append(ev)
        else:
            valid_candidates.append(ev)

    # Figure out sorting direction for valid candidates
    directions: dict[str, str] = {}
    for nutrient in nutrients:
        field = _nutrient_field_name(nutrient)
        direction = _parse_direction(query, nutrient)
        if field and direction:
            directions[field] = direction

    for c in constraints:
        nut = getattr(c, "nutrient", None)
        pref = getattr(c, "preference", None)
        if nut and pref in ("minimize", "maximize"):
            field = _nutrient_field_name(nut)
            if field:
                directions[field] = pref

    if not directions:
        return valid_candidates + failing_candidates

    def sort_key(ev) -> tuple[int, float]:
        nutrition = getattr(ev, "nutrition", {}) or {}
        has_val = False
        score_sum = 0.0

        for field, direction in directions.items():
            if field in nutrition and nutrition[field] is not None:
                v = nutrition[field]
                if isinstance(v, (int, float)):
                    has_val = True
                    score_sum += (-v if direction == "minimize" else v)

        return (1 if has_val else 0, score_sum)

    sorted_valid = sorted(valid_candidates, key=sort_key, reverse=True)
    sorted_failing = sorted(failing_candidates, key=sort_key, reverse=True)

    return sorted_valid + sorted_failing


def _build_sources_meta(evidence_list: list[Any]) -> tuple[list[dict], list[dict], list[str]]:
    """Build structured sources objects, ranked products list, and evidence IDs."""
    sources = []
    ranked_products = []
    evidence_ids = []

    for ev in evidence_list:
        ev_id = (
            getattr(ev, "evidence_id", None)
            or getattr(ev, "chunk_id", None)
            or getattr(ev, "product_id", None)
            or ev.name
            or "ev-unknown"
        )
        evidence_ids.append(str(ev_id))

        source_type = getattr(ev, "source_type", "OPEN_FOOD_FACTS")
        doc_name = getattr(ev, "document_name", None) or getattr(ev, "source_name", None) or "User Document"
        page_num = getattr(ev, "page_number", None)
        prod_name = getattr(ev, "name", None) or getattr(ev, "product_name", None) or "Unknown Product"
        barcode = getattr(ev, "barcode", None)

        if source_type == "USER_DOCUMENT":
            src_obj = {
                "type": "USER_DOCUMENT",
                "source_type": "USER_DOCUMENT",
                "name": doc_name,
                "source_name": doc_name,
                "page": page_num or 1,
            }
        else:
            src_obj = {
                "type": "OPEN_FOOD_FACTS",
                "source_type": "OPEN_FOOD_FACTS",
                "name": prod_name,
                "source_name": getattr(ev, "source_name", "Open Food Facts") or "Open Food Facts",
                "barcode": barcode,
                "url": f"https://world.openfoodfacts.org/product/{barcode}" if barcode else None,
            }

        sources.append(src_obj)

        prod_info = {
            "product_id": getattr(ev, "product_id", None) or getattr(ev, "document_id", None),
            "name": prod_name,
            "brand": getattr(ev, "brand", None),
            "barcode": barcode,
            "completeness": getattr(ev, "completeness", 1.0),
        }
        ranked_products.append(prod_info)

    return sources, ranked_products, evidence_ids


def response_service(request: ResponseRequest) -> ResponseResponse:
    query_lower = request.query.lower().strip()

    # Step 1: Rank evidence candidates
    all_constraints = request.nutrient_constraints or request.constraints or []
    ranked_evidence = rank_candidates(
        evidence=request.evidence,
        query=request.query,
        nutrients=request.nutrients,
        nutrient_constraints=all_constraints,
    )

    sources, ranked_prods, evidence_ids = _build_sources_meta(ranked_evidence)

    warnings = []
    if request.analysis and request.analysis.uncertainty_reasons:
        warnings = request.analysis.uncertainty_reasons

    # Step 2: Handle Conversational & Unsupported Intents
    if request.intent == "greeting" or any(w in query_lower for w in ["hi", "hello", "hey", "good morning", "thanks", "thank you"]):
        if any(w in query_lower for w in ["thanks", "thank you"]):
            ans = "You're welcome! Feel free to ask whenever you need food, nutrition, or allergen information."
        elif any(w in query_lower for w in ["who are you", "what can you do", "help", "who made you"]):
            ans = (
                "I am EviBite AI, a multi-agent supermarket product intelligence assistant! "
                "You can ask me to check food ingredients, verify allergen safety (peanuts, milk, soy, gluten), "
                "check dietary suitability (vegan, vegetarian), compare product nutrition, or scan/lookup product barcodes."
            )
        else:
            ans = (
                "Hello! I'm EviBite AI, your supermarket product intelligence assistant. "
                "How can I help you today? You can ask me about product ingredients, allergens, nutrition facts, or dietary suitability."
            )
        return ResponseResponse(
            trace_id=request.trace_id,
            answer=ans,
            status="OK",
            warnings=warnings,
            sources=sources,
            ranked_products=ranked_prods,
            evidence_ids=evidence_ids,
        )

    if request.triage_status == "UNSUPPORTED":
        store_words = ["price", "cost", "stock", "aisle", "shelf", "branch", "location", "discount", "buy"]
        if any(w in query_lower for w in store_words):
            ans = (
                "I am a supermarket product intelligence assistant for packaged foods via Open Food Facts and user document collections. "
                "I do not currently track real-time supermarket branch inventory, live prices, or aisle locations."
            )
        else:
            ans = (
                "I am a supermarket product intelligence assistant for packaged food products, nutrition, and allergen safety. "
                "I cannot answer queries outside food product information, but I'd be happy to help with any food or grocery queries!"
            )
        return ResponseResponse(
            trace_id=request.trace_id,
            answer=ans,
            status="OK",
            warnings=warnings,
            sources=sources,
            ranked_products=ranked_prods,
            evidence_ids=evidence_ids,
        )

    # Step 3: Handle Conflicting Sources
    if request.analysis and request.analysis.conflicting_evidence:
        prod_name = ranked_prods[0]["name"] if ranked_prods else "Product"
        ans = (
            f"[{prod_name}] The uploaded supplier guide lists conflicting information, while the Open Food Facts record provides conflicting or incomplete allergen information. "
            f"Because the available sources are inconsistent, EviBite cannot make a definitive suitability conclusion."
        )
        return ResponseResponse(
            trace_id=request.trace_id,
            answer=ans,
            status="PARTIAL",
            warnings=warnings,
            sources=sources,
            ranked_products=ranked_prods,
            evidence_ids=evidence_ids,
        )

    # Step 4: Handle Missing Evidence & No Analysis Findings
    if not request.evidence and not (request.analysis and request.analysis.findings):
        ans = "I could not find product information for your query."
        return ResponseResponse(
            trace_id=request.trace_id,
            answer=ans,
            status="NOT_FOUND",
            warnings=warnings,
            sources=sources,
            ranked_products=ranked_prods,
            evidence_ids=evidence_ids,
        )

    if not request.evidence and request.analysis and request.analysis.safety_status == "INSUFFICIENT_EVIDENCE" and not request.analysis.findings:
        ans = "I could not find enough allergen or nutrition information to determine this reliably."
        return ResponseResponse(
            trace_id=request.trace_id,
            answer=ans,
            status="NOT_FOUND",
            warnings=warnings,
            sources=sources,
            ranked_products=ranked_prods,
            evidence_ids=evidence_ids,
        )

    # Step 5: Format Grounded Answer
    answer_text = _format_deterministic_grounded_answer(
        request=request,
        ranked_evidence=ranked_evidence,
    )

    status_str = "OK"
    if request.analysis and request.analysis.safety_status == "INSUFFICIENT_EVIDENCE":
        status_str = "PARTIAL"

    return ResponseResponse(
        trace_id=request.trace_id,
        answer=answer_text,
        status=status_str,
        warnings=warnings,
        sources=sources,
        ranked_products=ranked_prods,
        evidence_ids=evidence_ids,
    )


def _format_deterministic_grounded_answer(
    request: ResponseRequest,
    ranked_evidence: list[Any],
) -> str:
    """Generate a strictly grounded response text from evidence and analysis.
    
    CRITICAL GROUNDING RULE: If a factual field (calories, fat, sodium, ingredients) is absent
    from evidence, DO NOT ADD IT. Never invent unverified details.
    """
    lines: list[str] = []

    # 1. Include Analysis Findings if present (deduplicated)
    if request.analysis and request.analysis.findings:
        unique_findings = list(dict.fromkeys(request.analysis.findings))
        for finding in unique_findings[:5]:
            formatted_finding = finding.replace("Product is unsafe to eat.", "")
            lines.append(formatted_finding)

    # 2. Add Grounded Citations & Product Evidence Details
    for ev in ranked_evidence[:3]:
        source_type = getattr(ev, "source_type", "OPEN_FOOD_FACTS")
        doc_name = getattr(ev, "document_name", None) or getattr(ev, "source_name", None)
        page_num = getattr(ev, "page_number", 1)
        prod_name = getattr(ev, "name", None) or getattr(ev, "product_name", None) or "Product"
        raw_txt = getattr(ev, "raw_text", None)

        if source_type == "USER_DOCUMENT":
            citation = f"According to your uploaded document: {doc_name} — page {page_num}"
            if raw_txt:
                lines.append(f"{citation}: \"{raw_txt.strip()}\"")
            else:
                lines.append(f"{citation}: Product evidence available for {prod_name}.")
        else:
            bc_str = f" (barcode: {ev.barcode})" if getattr(ev, "barcode", None) else ""
            lines.append(f"Source: Open Food Facts - {prod_name}{bc_str}.")

        # STRICT GROUNDING: ONLY include nutrition/ingredient details IF PRESENT IN EVIDENCE!
        present_details = []
        if getattr(ev, "ingredients_text", None):
            present_details.append(f"Ingredients: {ev.ingredients_text}")

        nutrition = getattr(ev, "nutrition", {}) or {}
        nut_details = []
        if "sugars_g_100g" in nutrition and nutrition["sugars_g_100g"] is not None:
            nut_details.append(f"Sugar: {nutrition['sugars_g_100g']}g")
        if "protein_g_100g" in nutrition and nutrition["protein_g_100g"] is not None:
            nut_details.append(f"Protein: {nutrition['protein_g_100g']}g")
        if "fat_g_100g" in nutrition and nutrition["fat_g_100g"] is not None:
            nut_details.append(f"Fat: {nutrition['fat_g_100g']}g")
        if "energy_kcal_100g" in nutrition and nutrition["energy_kcal_100g"] is not None:
            nut_details.append(f"Calories: {nutrition['energy_kcal_100g']} kcal")
        if "sodium_mg_100g" in nutrition and nutrition["sodium_mg_100g"] is not None:
            nut_details.append(f"Sodium: {nutrition['sodium_mg_100g']} mg")

        if nut_details:
            present_details.append(f"Nutrition per 100g: {', '.join(nut_details)}")

        if present_details:
            lines.append(" | ".join(present_details))

    # Add allergy verification warning if query is allergen-related
    if request.intent in ("ALLERGEN_CHECK", "allergen_check") or "allerg" in request.query.lower():
        lines.append("If you have a severe allergy, verify the current physical package because product formulations can change.")

    # Deduplicate lines while preserving order
    unique_lines = list(dict.fromkeys(lines))
    return "\n\n".join(unique_lines)