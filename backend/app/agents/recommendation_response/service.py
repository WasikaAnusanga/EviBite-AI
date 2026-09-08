"""Recommendation & Response Agent service (Member 4).

Turns retrieved evidence + analysis into a grounded, user-facing answer.
"""

from backend.app.agents.agent_stubs import ResponseRequest, ResponseResponse

def _parse_direction(query: str, nutrient: str) -> str | None:
    """Look for 'less/low' or 'more/high' near a nutrient word in the query.
    Returns 'minimize', 'maximize', or None if no clear signal is found.
    """
    query_lower = query.lower()
    less_words = ["less", "low", "lower", "fewer", "reduced"]
    more_words = ["more", "high", "higher", "increased"]

    nutrient_lower = nutrient.lower()
    nutrient_singular = nutrient_lower.rstrip("s")  # "sugars" -> "sugar"
    nutrient_present = nutrient_lower in query_lower or nutrient_singular in query_lower

    if any(word in query_lower for word in less_words) and nutrient_present:
        return "minimize"
    if any(word in query_lower for word in more_words) and nutrient_present:
        return "maximize"
    return None


def _nutrient_field_name(nutrient: str) -> str | None:
    """Map a short nutrient word (from Triage) to the real EvidenceObject field name."""
    mapping = {
        "sugars": "sugars_g_100g",
        "sugar": "sugars_g_100g",
        "protein": "protein_g_100g",
        "fat": "fat_g_100g",
        "calories": "energy_kcal_100g",
        "energy": "energy_kcal_100g",
        "sodium": "sodium_mg_100g",
    }
    return mapping.get(nutrient.lower())


def rank_candidates(evidence: list, query: str, nutrients: list[str]) -> list:
    """Rank evidence candidates by how well they satisfy nutrient direction preferences
    extracted from the query. Candidates with no scorable preference keep their
    original (Retrieval-assigned) order.
    """
    if not nutrients or not evidence:
        return evidence

    # Figure out which fields matter and in which direction.
    directions: dict[str, str] = {}
    for nutrient in nutrients:
        field = _nutrient_field_name(nutrient)
        direction = _parse_direction(query, nutrient)
        if field and direction:
            directions[field] = direction

    if not directions:
        return evidence  # No usable direction signal — don't reorder blindly.

    def score(ev) -> float:
        total = 0.0
        counted = 0
        for field, direction in directions.items():
            value = ev.nutrition.get(field)
            if value is None:
                continue  # Missing data — don't guess, just skip this field.
            # Lower raw value = better for "minimize", higher = better for "maximize".
            total += (-value if direction == "minimize" else value)
            counted += 1
        # Candidates with no usable nutrition data for the requested fields
        # rank last, not first — missing data is not a reason to prefer them.
        return total if counted > 0 else float("-inf")

    return sorted(evidence, key=score, reverse=True)

def response_service(request: ResponseRequest) -> ResponseResponse:
    # Case 1: query was off-topic / unsupported.
    if request.triage_status == "UNSUPPORTED":
        return ResponseResponse(
            trace_id=request.trace_id,
            answer=(
                "I am a supermarket product intelligence assistant for "
                "packaged foods. I cannot answer queries outside food "
                "product information."
            ),
        )

    has_findings = bool(request.analysis and request.analysis.findings)

    # Case 2: truly nothing to work with — no evidence and no findings.
    if not request.evidence and not has_findings:
        return ResponseResponse(
            trace_id=request.trace_id,
            answer="I could not find product information for your query.",
        )

    # Case 3: we have evidence — rank it first, regardless of whether
    # Analysis also ran.
    if request.evidence:
        ranked = rank_candidates(request.evidence, request.query, request.nutrients)
        top_candidates = ranked[:3]

        if has_findings:
            relevant_findings = [
                f for f in request.analysis.findings
                if any(ev.name in f for ev in top_candidates)
            ]
            unique_findings = list(dict.fromkeys(relevant_findings))
            if unique_findings:
                answer_text = " ".join(unique_findings)
                return ResponseResponse(trace_id=request.trace_id, answer=answer_text)

        lines = [
            f"{ev.name} (Brand: {ev.brand or 'unknown'}). "
            f"Ingredients: {ev.ingredients_text or 'not listed'}."
            for ev in top_candidates
        ]
        return ResponseResponse(trace_id=request.trace_id, answer=" ".join(lines))

    # Case 4: no evidence, but Analysis still had findings to report
    # (e.g. re-analysis of previously retrieved data).
    unique_findings = list(dict.fromkeys(request.analysis.findings))
    return ResponseResponse(
        trace_id=request.trace_id,
        answer=" ".join(unique_findings),
    )