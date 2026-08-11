from backend.app.models.triage import (
    Intent,
    RouteAgent,
    RoutingDecision,
)


def build_routing(intent: Intent) -> RoutingDecision:
    if intent in {Intent.PRODUCT_SEARCH, Intent.BARCODE_LOOKUP}:
        return RoutingDecision(
            next_agent=RouteAgent.RETRIEVAL,
            required_agents=[RouteAgent.RETRIEVAL, RouteAgent.RESPONSE],
            analysis_required=False,
        )

    if intent in {
        Intent.ALLERGEN_QUERY,
        Intent.NUTRITION_QUERY,
        Intent.COMPARISON,
        Intent.DIETARY_QUERY,
        Intent.RECOMMENDATION,
    }:
        return RoutingDecision(
            next_agent=RouteAgent.RETRIEVAL,
            required_agents=[
                RouteAgent.RETRIEVAL,
                RouteAgent.ANALYSIS,
                RouteAgent.RESPONSE,
            ],
            analysis_required=True,
        )

    return RoutingDecision(
        next_agent=RouteAgent.RESPONSE,
        required_agents=[RouteAgent.RESPONSE],
        analysis_required=False,
    )
