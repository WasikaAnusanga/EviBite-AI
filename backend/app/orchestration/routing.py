"""Conditional Agent Routing Logic for EviBite AI.

Defines required execution paths across Agent 1 (Triage), Agent 2 (Retrieval),
Agent 3 (Analysis), and Agent 4 (Response).
"""

from backend.app.models.triage import (
    Intent,
    RouteAgent,
    RoutingDecision,
)


def build_routing(intent: Intent, has_safety_constraints: bool = False) -> RoutingDecision:
    # 1. No retrieval routes
    if intent in {Intent.GREETING, Intent.OUT_OF_DOMAIN, Intent.UNKNOWN}:
        return RoutingDecision(
            next_agent=RouteAgent.RESPONSE,
            required_agents=[RouteAgent.RESPONSE],
            analysis_required=False,
        )

    # 2. Retrieval-only routes (unless explicit safety/nutrient constraints exist)
    if intent in {Intent.PRODUCT_SEARCH, Intent.BARCODE_LOOKUP}:
        if has_safety_constraints:
            return RoutingDecision(
                next_agent=RouteAgent.RETRIEVAL,
                required_agents=[RouteAgent.RETRIEVAL, RouteAgent.ANALYSIS, RouteAgent.RESPONSE],
                analysis_required=True,
            )
        return RoutingDecision(
            next_agent=RouteAgent.RETRIEVAL,
            required_agents=[RouteAgent.RETRIEVAL, RouteAgent.RESPONSE],
            analysis_required=False,
        )

    # 3. Full 4-Agent pipeline routes (Retrieval -> Analysis -> Response)
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
