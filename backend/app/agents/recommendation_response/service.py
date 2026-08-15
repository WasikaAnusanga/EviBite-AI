"""Recommendation & Response Agent service (Member 4).

Turns retrieved evidence + analysis into a grounded, user-facing answer.
"""

from backend.app.agents.agent_stubs import ResponseRequest, ResponseResponse


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

    # Case 2: analysis ran and produced findings — deduplicate them.
    if request.analysis and request.analysis.findings:
        unique_findings = list(dict.fromkeys(request.analysis.findings))
        answer_text = " ".join(unique_findings)
        return ResponseResponse(trace_id=request.trace_id, answer=answer_text)

    # Case 3: no analysis, but we have evidence — describe products plainly.
    if request.evidence:
        lines = [
            f"{ev.name} (Brand: {ev.brand or 'unknown'}). "
            f"Ingredients: {ev.ingredients_text or 'not listed'}."
            for ev in request.evidence
        ]
        return ResponseResponse(trace_id=request.trace_id, answer=" ".join(lines))

    # Case 4: nothing at all was found.
    return ResponseResponse(
        trace_id=request.trace_id,
        answer="I could not find product information for your query.",
    )