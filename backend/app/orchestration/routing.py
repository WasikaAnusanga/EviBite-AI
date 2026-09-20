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
        Intent.ALLERGEN_CHECK,
        Intent.DIETARY_COMPLIANCE,
        Intent.NUTRITION_QUERY,
        Intent.PRODUCT_COMPARISON,
        Intent.NUTRIENT_COMPARISON,
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
